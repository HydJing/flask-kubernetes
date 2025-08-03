# app/extensions.py

import logging
import os
import pika
from flask import g, current_app
from flask_pymongo import PyMongo
import pika
import gridfs # Import gridfs here

logger = logging.getLogger(__name__)

# Flask-PyMongo instances - these are Flask extensions, not direct MongoClient instances
mongo_video = PyMongo()
mongo_mp3 = PyMongo()

def init_extensions(app):
    """
    Initializes Flask extensions like PyMongo.
    This function is called once during app creation.
    """
    logger.info(f"INIT_EXTENSIONS: Starting initialization for app ID: {id(app)}")

    # Retrieve URIs from app.config (set in __init__.py)
    mongo_video_uri = app.config.get('MONGO_URI_VIDEO')
    mongo_mp3_uri = app.config.get('MONGO_URI_MP3')

    # Initialize PyMongo extensions
    try:
        mongo_video.init_app(app, uri=mongo_video_uri)
        logger.info(f"INIT_EXTENSIONS: PyMongo for video initialized with app. DB name: {mongo_video_uri.split('/')[-1].split('?')[0]}")

        mongo_mp3.init_app(app, uri=mongo_mp3_uri)
        logger.info(f"INIT_EXTENSIONS: PyMongo for MP3 initialized with app. DB name: {mongo_mp3_uri.split('/')[-1].split('?')[0]}")

        # PyMongo handles connection pooling and lifecycle.
        # We don't need to explicitly ping here, as PyMongo will connect on first use.
        # If the URI is bad, PyMongo operations will raise errors.
        logger.info("INIT_EXTENSIONS: PyMongo extensions configured. Connections will be established on first use.")

        if 'pymongo' not in app.extensions:
            app.extensions['pymongo'] = {}
    
        app.extensions['pymongo']['mongo_video'] = mongo_video
        app.extensions['pymongo']['mongo_mp3'] = mongo_mp3
        logger.info("INIT_EXTENSIONS: App extension pymongo has set DBs.")
        logger.info(f"App Pymongo Config: mongo_video = '{app.extensions['pymongo']['mongo_video']}'")
        logger.info(f"App Pymongo Config: mongo_mp3 = '{app.extensions['pymongo']['mongo_mp3']}'")

    except Exception as e:
        logger.critical(f"INIT_EXTENSIONS: CRITICAL ERROR during MongoDB initialization: {e}", exc_info=True)
        # Re-raise to prevent app startup with broken DB config
        raise

    # --- RabbitMQ Connection Management ---
    # We'll manage RabbitMQ connection/channel per-request using Flask's `g` object.
    # Register a teardown function for the request context.
    @app.teardown_appcontext
    def close_rabbitmq_connection_on_teardown(exception=None):
        """
        Closes the RabbitMQ connection stored in Flask's `g` object for the current request.
        """
        if 'rabbitmq_connection' in g and g.rabbitmq_connection and not g.rabbitmq_connection.is_closed:
            try:
                g.rabbitmq_connection.close()
                logger.info(f"TEARDOWN: RabbitMQ connection (ID: {id(g.rabbitmq_connection)}) closed for request context.")
            except Exception as e:
                logger.error(f"TEARDOWN: Error closing RabbitMQ connection (ID: {id(g.rabbitmq_connection)}): {e}")
        else:
            logger.debug("TEARDOWN: No RabbitMQ connection to close for this request context.")

    logger.info("INIT_EXTENSIONS: All extensions initialized successfully.")


def get_rabbitmq_channel():
    """
    Provides a RabbitMQ channel for the current request.
    It will create a new connection/channel if one doesn't exist for this request.
    """
    if 'rabbitmq_channel' not in g or g.rabbitmq_channel is None or g.rabbitmq_channel.is_closed:
        logger.info("RABBITMQ_GET: Establishing new RabbitMQ connection and channel for current request.")
        rabbitmq_host = current_app.config.get("RABBITMQ_HOST")
        rabbitmq_port = current_app.config.get("RABBITMQ_PORT")

        if not rabbitmq_host or not rabbitmq_port:
            logger.critical("RABBITMQ_GET: RabbitMQ host or port not configured. Cannot establish connection.")
            raise ConnectionError("RabbitMQ configuration missing.")

        try:
            # Create a new connection for this request context
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=rabbitmq_host,
                port=rabbitmq_port,
                heartbeat=600, # Recommended for long-lived connections
                blocked_connection_timeout=300 # Timeout for blocked connections
            ))
            channel = connection.channel()
            logger.info(f"RABBITMQ_GET: RabbitMQ connection established to {rabbitmq_host}:{rabbitmq_port}. Conn ID: {id(connection)}, Channel ID: {id(channel)}")

            # Store in Flask's g object for the duration of the request
            g.rabbitmq_connection = connection
            g.rabbitmq_channel = channel

            # Declare queues (idempotent operation, safe to call on each new channel)
            video_queue = current_app.config.get("VIDEO_QUEUE", "video")
            mp3_queue = current_app.config.get("MP3_QUEUE", "mp3")
            channel.queue_declare(queue=video_queue, durable=True)
            channel.queue_declare(queue=mp3_queue, durable=True)
            logger.info(f"RABBITMQ_GET: Queues '{video_queue}' and '{mp3_queue}' declared.")

        except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosedByBroker) as e:
            logger.error(f"RABBITMQ_GET: Failed to connect to RabbitMQ at {rabbitmq_host}:{rabbitmq_port}: {e}", exc_info=True)
            # Ensure any partially created connection/channel is cleaned up
            if 'rabbitmq_connection' in g and g.rabbitmq_connection and not g.rabbitmq_connection.is_closed:
                g.rabbitmq_connection.close()
            g.rabbitmq_connection = None
            g.rabbitmq_channel = None
            raise ConnectionError(f"RabbitMQ connection failed: {e}")
        except Exception as e:
            logger.critical(f"RABBITMQ_GET: An unexpected error occurred during RabbitMQ connection: {e}", exc_info=True)
            # Ensure any partially created connection/channel is cleaned up
            if 'rabbitmq_connection' in g and g.rabbitmq_connection and not g.rabbitmq_connection.is_closed:
                g.rabbitmq_connection.close()
            g.rabbitmq_connection = None
            g.rabbitmq_channel = None
            raise ConnectionError(f"Unexpected RabbitMQ connection error: {e}")

    return g.rabbitmq_channel