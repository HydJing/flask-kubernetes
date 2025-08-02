import json
import logging
import io
import os # Keep os for other potential env vars, though not directly used for mongo_auth_db here

from flask import Blueprint, request, jsonify, send_file, current_app
from app.services import auth_service
from bson.objectid import ObjectId, InvalidId
import gridfs
# from flask_pymongo import PyMongo # Not needed if PyMongo is initialized globally in app.py/extensions.py
# from pymongo import MongoClient # Not needed here, as Flask-PyMongo manages clients


logger = logging.getLogger(__name__)

download_bp = Blueprint("download", __name__, url_prefix="/download")

@download_bp.route("/", methods=["GET"])
def download():
    """
    Handles MP3 file downloads from MongoDB GridFS.
    Requires a valid JWT with admin privileges and a 'fid' query parameter.
    """
    # --- 1. Token Validation ---
    access_payload, error_response = auth_service.validate_token_and_get_payload(request)
    if error_response:
        logger.warning(f"Download attempt failed due to token validation: {error_response}")
        return error_response

    # --- 2. Authorization Check (Admin Privileges) ---
    if not access_payload.get("admin"):
        logger.warning(f"Download attempt by non-admin user: {access_payload.get('username')}")
        return jsonify({"error": "Not authorized: Admin privileges required"}), 403

    # --- 3. Retrieve and Validate File ID (fid) ---
    fid_str = request.args.get("fid")
    if not fid_str:
        logger.warning("Download attempt: 'fid' query parameter is missing.")
        return jsonify({"error": "'fid' query parameter is required"}), 400

    try:
        fid_obj = ObjectId(fid_str)
    except InvalidId:
        logger.warning(f"Download attempt: Invalid 'fid' format received: '{fid_str}'")
        return jsonify({"error": "Invalid file ID format"}), 400

    # --- 4. Access MongoDB and GridFS (using Flask-PyMongo managed connection) ---
    try:
        # Access the MongoDB database object for MP3s from current_app context.
        # This assumes 'pymongo' extension is properly initialized and 'mongo_mp3' is a key
        # within current_app.extensions['pymongo'] (as per your previous logs).
        mongo_mp3_db = current_app.extensions['pymongo']['mongo_mp3'].db
        
        if mongo_mp3_db is None:
            logger.critical("DOWNLOAD FUNCTION: MongoDB MP3 database object (mongo_mp3_db) is None. Check MongoDB connection setup in app.py/extensions.py.")
            return jsonify({"error": "Internal server error: MP3 storage not initialized"}), 500

        # Create GridFS instance for MP3s using the obtained database object.
        # GridFS instances are cheap to create per request if needed, or can be cached.
        fs_mp3s_instance = gridfs.GridFS(mongo_mp3_db)
        logger.info(f"DOWNLOAD FUNCTION: GridFS instance created for MP3s. GridFS instance ID: {id(fs_mp3s_instance)}")

    except KeyError:
        logger.critical("DOWNLOAD FUNCTION: 'pymongo' or 'mongo_mp3' key not found in current_app.extensions. Ensure Flask-PyMongo is correctly initialized and registered.")
        return jsonify({"error": "Internal server error: MongoDB extension not configured"}), 500
    except Exception as e:
        logger.critical(f"DOWNLOAD FUNCTION: Unexpected error accessing MongoDB/GridFS: {e}", exc_info=True)
        return jsonify({"error": "Internal server error during storage access"}), 500

    # --- 5. Retrieve File from GridFS and Serve ---
    try:
        # Use the GridFS instance to get the file.
        # 'out' will be a GridOut object, which is a file-like object.
        out = fs_mp3s_instance.get(fid_obj)
        
        # --- DEBUGGING STEP: Read into BytesIO and check size ---
        # Read the entire content of the GridOut object into an in-memory BytesIO buffer.
        # This ensures the full file is read from MongoDB before sending.
        file_buffer = io.BytesIO(out.read())
        
        # Get the size of the data in the buffer
        buffer_size = file_buffer.getbuffer().nbytes
        
        logger.info(f"Retrieved MP3 with FID: {fid_str}. GridFS reported length: {out.length} bytes. "
                    f"BytesIO buffer size: {buffer_size} bytes. Serving file.")
        
        # IMPORTANT: Seek the buffer back to the beginning before sending it
        file_buffer.seek(0)
        # --- END DEBUGGING STEP ---
        
        # Determine the download filename.
        # GridOut objects often have a 'filename' attribute if stored with one.
        # If your converter worker doesn't set a filename during fs_mp3s.put(),
        # consider adding `filename=f"{video_fid}.mp3"` there for better download names.
        download_filename = out.filename if hasattr(out, 'filename') and out.filename else f"{fid_str}.mp3"
        
        # Pass the BytesIO buffer to send_file
        return send_file(file_buffer, download_name=download_filename, mimetype="audio/mpeg")
    except gridfs.NoFile:
        logger.warning(f"Download attempt: MP3 file with FID '{fid_str}' not found in GridFS.")
        return jsonify({"error": "File not found"}), 404 # Not Found
    except Exception as e:
        logger.error(f"DOWNLOAD FUNCTION: An unexpected error occurred while retrieving or sending file '{fid_str}': {e}", exc_info=True)
        return jsonify({"error": "Internal server error during file download"}), 500
