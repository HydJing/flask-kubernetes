import json
import logging
from flask import Blueprint, request, jsonify, send_file, current_app
from app.services import auth_service
from bson.objectid import ObjectId, InvalidId
from flask_pymongo import PyMongo
import gridfs
import io # Import io for BytesIO

logger = logging.getLogger(__name__)

download_bp = Blueprint("download", __name__, url_prefix="/download")

@download_bp.route("/", methods=["GET"])
def download():
    """
    Handles MP3 file downloads from MongoDB GridFS.
    Requires a valid JWT with admin privileges and a 'fid' query parameter.
    """


    client = MongoClient(
            host=MONGO_HOST,
            port=MONGO_PORT,
            username=MONGO_USERNAME,
            password=MONGO_PASSWORD,
            authSource=MONGO_AUTH_DB
        )
    client.admin.command('ismaster')
    fs_mp3s = gridfs.GridFS(client['mp3s'])
    grid_file = fs_mp3s.get(ObjectId("6871076ac7aae7f1e44ac266"))



    access_payload, error_response = auth_service.validate_token_and_get_payload(request)
    if error_response:
        logger.warning(f"Download attempt failed due to token validation: {error_response}")
        return error_response

    if not access_payload.get("admin"):
        logger.warning(f"Download attempt by non-admin user: {access_payload.get('username')}")
        return jsonify({"error": "Not authorized: Admin privileges required"}), 403

    fid_str = request.args.get("fid")
    if not fid_str:
        logger.warning("Download attempt: 'fid' query parameter is missing.")
        return jsonify({"error": "'fid' query parameter is required"}), 400

    try:
        fid_obj = ObjectId(fid_str)
    except InvalidId:
        logger.warning(f"Download attempt: Invalid 'fid' format received: '{fid_str}'")
        return jsonify({"error": "Invalid file ID format"}), 400

    try:
        mongo_mp3_db = current_app.extensions['pymongo']['mongo_mp3'].db
        
        if mongo_mp3_db is None:
            logger.critical("DOWNLOAD FUNCTION: MongoDB MP3 database object (mongo_mp3_db) is None. Check MongoDB connection setup.")
            return jsonify({"error": "Internal server error: MP3 storage not initialized"}), 500

        fs_mp3s_instance = gridfs.GridFS(mongo_mp3_db)
        logger.info(f"DOWNLOAD FUNCTION: GridFS instance created for MP3s. ID: {id(fs_mp3s_instance)}")

    except Exception as e:
        logger.critical(f"DOWNLOAD FUNCTION: Unexpected error accessing MongoDB/GridFS: {e}", exc_info=True)
        return jsonify({"error": "Internal server error during storage access"}), 500

    try:
        out = fs_mp3s_instance.get(fid_obj)
        
        # --- NEW DEBUGGING STEP: Read into BytesIO and check size ---
        # Read the entire content of the GridOut object into an in-memory BytesIO buffer
        file_buffer = io.BytesIO(out.read())
        
        # Get the size of the data in the buffer
        buffer_size = file_buffer.getbuffer().nbytes
        
        logger.info(f"Retrieved MP3 with FID: {fid_str}. GridFS reported length: {out.length} bytes. "
                    f"BytesIO buffer size: {buffer_size} bytes. Serving file.")
        
        # IMPORTANT: Seek the buffer back to the beginning before sending it
        file_buffer.seek(0)
        # --- END NEW DEBUGGING STEP ---
        
        download_filename = out.filename if hasattr(out, 'filename') and out.filename else f"{fid_str}.mp3"
        
        # Pass the BytesIO buffer to send_file
        return send_file(file_buffer, download_name=download_filename, mimetype="audio/mpeg")
    except gridfs.NoFile:
        logger.warning(f"Download attempt: MP3 file with FID '{fid_str}' not found in GridFS.")
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logger.error(f"DOWNLOAD FUNCTION: An unexpected error occurred while retrieving or sending file '{fid_str}': {e}", exc_info=True)
        return jsonify({"error": "Internal server error during file download"}), 500
