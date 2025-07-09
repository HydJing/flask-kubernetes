from flask import Blueprint, request, jsonify 
from app.services import auth_service as validate, storage_service as storage
import json
import logging

logger = logging.getLogger(__name__)

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")

@upload_bp.route("/", methods=["POST"])
def upload():

    # --- 1. Token Validation ---
    # Assuming auth_service.token returns (decoded_payload, error_response_tuple)
    # where error_response_tuple is (message, status_code)
    access_payload, error_response  = validate.validate_token_and_get_payload(request)
    if error_response :
        logger.warning(f"Upload attempt failed due to token validation: {error_response}")
        return error_response # This already contains jsonify and status code 

    # --- 2. Authorization Check (Admin Privileges) ---
    if not access_payload.get("admin"):
        logger.warning(f"Upload attempt by non-admin user: {access_payload.get('username')}")
        return jsonify({"error": "Not authorized: Admin privileges required"}), 403 # 403 Forbidden

    # --- 3. File Count Validation ---
    if len(request.files) == 0:
        logger.warning("Upload attempt: No file provided.")
        return jsonify({"error": "No file provided"}), 400 # Bad Request
    if len(request.files) > 1:
        logger.warning(f"Upload attempt: Exactly 1 file required, but {len(request.files)} received.")
        return jsonify({"error": "Exactly one file is required per upload"}), 400 # Bad Request

    # --- 4. Process Uploaded File(s) ---
     # Iterate through files (though we expect only one based on validation)
    for filename, f_stream in request.files.items():
        logger.info(f"Received file '{filename}' from user '{access_payload.get('username')}'")
        # Call storage_service.upload without fs_videos and channel
        # storage_service.upload now internally accesses current_app for these resources
        response_message, status_code = storage.upload(f_stream, access_payload)
        # storage_service.upload now returns (message, status_code)
        if status_code != 202: # Check for non-202 status codes (indicating an error)
            logger.error(f"Storage service upload failed for file '{filename}': {response_message} (Status: {status_code})")
            return jsonify({"error": response_message}), status_code
        else:
            logger.info(f"File '{filename}' successfully queued for processing.")
            # If you want to return specific info about the uploaded file, you can
            # modify storage_service.upload to return fid or other metadata.
            # For now, we'll return a generic success for the single file.

    return jsonify({"message": "File uploaded and queued successfully!"}), 202 # 202 Accepted
