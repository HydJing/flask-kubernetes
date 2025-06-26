from flask import Blueprint, request, send_file
from app.services import auth_service
from app.extensions import fs_mp3s
from bson.objectid import ObjectId
import json

download_bp = Blueprint("download", __name__, url_prefix="/download")

@download_bp.route("/", methods=["GET"])
def download():
    access, err = auth_service.token(request)
    if err:
        return err

    access = json.loads(access)
    if not access.get("admin"):
        return "not authorized", 401

    fid = request.args.get("fid")
    if not fid:
        return "fid is required", 400

    try:
        out = fs_mp3s.get(ObjectId(fid))
        return send_file(out, download_name=f"{fid}.mp3")
    except Exception as err:
        print(err)
        return "internal server error", 500
