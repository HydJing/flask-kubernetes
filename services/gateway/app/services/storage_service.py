# app/services/storage_service.py

import json
import logging
import os
from flask import current_app 
from pymongo.errors import PyMongoError
from pika.exceptions import AMQPConnectionError, ChannelClosedByBroker
import gridfs 
from app.extensions import get_rabbitmq_channel, mongo_video

logger = logging.getLogger(__name__)

def upload(f, access):
    """
    Handles the upload of a video file to MongoDB GridFS and publishes a message to RabbitMQ.

    Args:
        f (file-like object): The video file to be uploaded.
        access (dict): Dictionary containing user access information (e.g., {"username": "user1"}).

    Returns:
        tuple: A tuple containing (response_message, HTTP_status_code).
    """
    logger.info(f"UPLOAD FUNCTION: Request received. App ID: {id(current_app)}")
    
    # mongo_video is already initialized via init_app in extensions.py
    mongo_video_db = mongo_video.db
    
    if mongo_video_db is None:
        logger.critical("UPLOAD FUNCTION: MongoDB video database object (mongo_video_db) is None. Check MongoDB connection setup.")
        return "Internal server error: Storage not initialized", 500

    # Create GridFS instance per request (or per function call)
    # This is lightweight and ensures it's tied to the current connection context
    fs = gridfs.GridFS(mongo_video_db)
    logger.info(f"UPLOAD FUNCTION: GridFS instance created for this request. ID: {id(fs)}")

    # --- Get RabbitMQ Channel for this request ---
    try:
        channel = get_rabbitmq_channel() 
    except ConnectionError as e:
        logger.critical(f"UPLOAD FUNCTION: Failed to get RabbitMQ channel: {e}")
        return "Internal server error: Messaging not initialized", 500
    
    # --- CRITICAL DEBUG: Log state of resources ---
    logger.info(f"UPLOAD FUNCTION: Request received. App ID: {id(current_app)}")
    logger.info(f"UPLOAD FUNCTION: mongo_video_db state: {mongo_video_db} (ID: {id(mongo_video_db)})")
    logger.info(f"UPLOAD FUNCTION: channel state: {channel} (ID: {id(channel)})")

    fid = None

    # --- 1. Upload file to MongoDB GridFS ---
    print(mongo_video_db)
    fid = fs.put(f)

    # --- 2. Prepare message for RabbitMQ ---
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access.get("username"),
    }

    if not message["username"]:
        logger.warning(f"UPLOAD FUNCTION: Message prepared without username for FID: {fid}. Access info: {access}")

    # --- 3. Publish message to RabbitMQ ---
    try:
        video_queue = current_app.config.get("VIDEO_QUEUE", "video_queue_default")
        channel.basic_publish(
            exchange="",
            routing_key=video_queue,
            body=json.dumps(message).encode('utf-8'),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
        logger.info(f"UPLOAD FUNCTION: Message published to RabbitMQ for FID: {fid}")
        return "File uploaded and queued for processing", 202
    except (AMQPConnectionError, ChannelClosedByBroker) as e:
        logger.error(f"UPLOAD FUNCTION: RabbitMQ publish failed for FID {fid}: {e}", exc_info=True)
        if fid:
            try:
                fs.delete(fid)
                logger.warning(f"UPLOAD FUNCTION: Deleted video {fid} from GridFS due to RabbitMQ publish failure.")
            except PyMongoError as delete_err:
                logger.error(f"UPLOAD FUNCTION: Failed to delete video {fid} from GridFS after RabbitMQ publish failure: {delete_err}")
        return "Failed to queue video for processing (RabbitMQ error)", 503
    except json.JSONEncodeError as e:
        logger.error(f"UPLOAD FUNCTION: Failed to encode message to JSON for FID {fid}: {e}", exc_info=True)
        if fid:
            try:
                fs.delete(fid)
                logger.warning(f"UPLOAD FUNCTION: Deleted video {fid} from GridFS due to JSON encoding failure.")
            except PyMongoError as delete_err:
                logger.error(f"UPLOAD FUNCTION: Failed to delete video {fid} from GridFS after JSON encoding failure: {delete_err}")
        return "Internal server error: Message serialization failed", 500
    except Exception as e:
        logger.error(f"UPLOAD FUNCTION: An unexpected error occurred during RabbitMQ publish for FID {fid}: {e}", exc_info=True)
        if fid:
            try:
                fs.delete(fid)
                logger.warning(f"UPLOAD FUNCTION: Deleted video {fid} from GridFS due to unexpected publish error.")
            except PyMongoError as delete_err:
                logger.error(f"UPLOAD FUNCTION: Failed to delete video {fid} from GridFS after unexpected publish error: {delete_err}")
        return "Internal server error during message queuing", 500