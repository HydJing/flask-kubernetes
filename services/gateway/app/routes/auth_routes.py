from flask import Blueprint, request
from app.services import auth_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["POST"])
def login():
    token, err = auth_service.login(request)
    return token if not err else err
