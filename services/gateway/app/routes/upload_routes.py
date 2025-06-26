from flask import Blueprint, request
from app.services import validate, storage
from app.extensions import fs_videos, channel
import json

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")

@upload_bp.route("/", methods=["POST"])
def upload():
    access, err = validate.token(request)
    if err:
        return err

    access = json.loads(access)
    if not access.get("admin"):
        return "not authorized", 401

    if len(request.files) != 1:
        return "exactly 1 file required", 400

    for _, f in request.files.items():
        err = storage.upload(f, fs_videos, channel, access)
        if err:
            return err

    return "success!", 200
