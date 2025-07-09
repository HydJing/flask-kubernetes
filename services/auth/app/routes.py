import jwt, datetime, os, logging, json
from flask import Blueprint, request, jsonify, current_app
from .extensions import mysql

# Get a logger for this module
logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

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
    """
    Validates a JWT token provided in the Authorization header.
    Expected header format: "Bearer <token>"
    """
    # --- 1. Retrieve and validate Authorization header ---
    auth_header  = request.headers.get("Authorization")
    if not auth_header :
        logger.warning("Validation attempt: Missing Authorization header.")
        return jsonify({"error": "Authorization header is missing"}), 401
    
    # Check if the header starts with "Bearer "
    if not auth_header.startswith("Bearer "):
        logger.warning(f"Validation attempt: Invalid Authorization header format. Expected 'Bearer <token>', got '{auth_header[:30]}...'")
        return jsonify({"error": "Invalid Authorization header format. Must be 'Bearer <token>'"}), 401

    try:
        # Extract the token part
        token = auth_header .split(" ")[1]

        if not token: # Check if token part is empty after split
            logger.warning("Validation attempt: Token string is empty after 'Bearer ' prefix.")
            return jsonify({"error": "Token string is empty"}), 401
        
    except IndexError:
        # This handles cases like "Bearer" with no token following
        logger.warning(f"Validation attempt: Malformed Authorization header. No token found after 'Bearer'. Header: '{auth_header}'")
        return jsonify({"error": "Malformed Authorization header"}), 401
    

    # --- 2. Retrieve JWT Secret ---
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        logger.critical("JWT_SECRET environment variable is not set. Cannot validate tokens.")
        # This is a critical configuration error, not a client error.
        # It should ideally be caught at application startup.
        return jsonify({"error": "Server configuration error: JWT secret not found"}), 500

    # --- 3. Decode and Validate JWT ---
    try:
        decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        logger.info(f"JWT validated successfully for username: {decoded.get('username')}")
        return jsonify(decoded), 200
    except jwt.ExpiredSignatureError:
        logger.warning(f"JWT validation failed: Token expired. Token start: {token[:10]}...")
        return jsonify({"error": "Token has expired"}), 401 # 401 Unauthorized is more appropriate for expired tokens
    except jwt.InvalidSignatureError:
        logger.warning(f"JWT validation failed: Invalid signature. Token start: {token[:10]}...")
        return jsonify({"error": "Invalid token signature"}), 401 # Token tampered with or wrong secret
    except jwt.DecodeError as e:
        # Catch general decoding issues (e.g., malformed token structure, invalid padding)
        logger.warning(f"JWT validation failed: Decoding error. Error: {e}. Token start: {token[:10]}...")
        return jsonify({"error": "Invalid token format or structure"}), 401
    except jwt.InvalidAlgorithmError:
        # If the token claims a different algorithm than expected (e.g., RS256 instead of HS256)
        logger.warning(f"JWT validation failed: Invalid algorithm. Token start: {token[:10]}...")
        return jsonify({"error": "Invalid token algorithm"}), 401
    except jwt.InvalidAudienceError:
        logger.warning(f"JWT validation failed: Invalid audience. Token start: {token[:10]}...")
        return jsonify({"error": "Invalid token audience"}), 401
    except jwt.InvalidIssuerError:
        logger.warning(f"JWT validation failed: Invalid issuer. Token start: {token[:10]}...")
        return jsonify({"error": "Invalid token issuer"}), 401
    except Exception as e:
        # Catch any other unexpected errors during JWT processing
        logger.error(f"An unexpected error occurred during JWT validation: {e}", exc_info=True)
        return jsonify({"error": "An unexpected server error occurred during token validation"}), 500


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
