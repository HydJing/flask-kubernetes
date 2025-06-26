from flask import Blueprint

health_bp = Blueprint("health", __name__, url_prefix="/")

@health_bp.route("/healthz", methods=["GET"])
def health_check():
    return {"status": "ok"}, 200
