import jwt, datetime, os
from flask import Blueprint, request, jsonify, current_app
from . import mysql

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth:
        return jsonify({"error": "missing credentials"}), 401

    cur = mysql.connection.cursor()
    res = cur.execute("SELECT email, password FROM user WHERE email=%s", (auth.username,))
    
    if res > 0:
        user = cur.fetchone()
        if auth.password != user[1]:
            return jsonify({"error": "invalid credentials"}), 401
        token = create_jwt(user[0], os.environ.get("JWT_SECRET"), True)
        return jsonify({"token": token}), 200
    return jsonify({"error": "invalid credentials"}), 401

@auth_bp.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers.get("Authorization")
    if not encoded_jwt:
        return jsonify({"error": "missing token"}), 401
    try:
        token = encoded_jwt.split(" ")[1]
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
        return jsonify(decoded), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "token expired"}), 403
    except jwt.InvalidTokenError:
        return jsonify({"error": "invalid token"}), 403

def create_jwt(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            "iat": datetime.datetime.utcnow(),
            "admin": authz,
        },
        secret,
        algorithm="HS256"
    )
