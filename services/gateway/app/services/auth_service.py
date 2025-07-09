import os
import logging
import json # For parsing JSON responses from the auth service
import requests # For making HTTP requests to the auth service
from flask import request, jsonify # Assuming these are used elsewhere in the module

logger = logging.getLogger(__name__)

def validate_token_and_get_payload(request):
    """
    Validates a JWT token by calling an external authentication service.

    Args:
        request (flask.request): The Flask request object containing the Authorization header.

    Returns:
        tuple: (decoded_payload_dict, None) on successful validation (200 OK from auth service),
               (None, (error_message_dict, status_code)) on validation failure or error.
    """
    # --- 1. Retrieve Authorization header ---
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.warning("Token validation attempt: Missing Authorization header.")
        return None, (jsonify({"error": "Authorization header is missing"}), 401)

    # --- 2. Get Auth Service Address ---
    auth_svc_address = os.getenv("AUTH_SVC_ADDRESS")
    if not auth_svc_address:
        logger.critical("AUTH_SVC_ADDRESS environment variable is not set. Cannot validate tokens externally.")
        return None, (jsonify({"error": "Server configuration error: Auth service address not found"}), 500)

    auth_svc_url = f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/validate"

    # --- 3. Call External Authentication Service ---
    try:
        logger.info(f"Calling external auth service at {auth_svc_url} for token validation.")
        response = requests.post(
            auth_svc_url,
            headers={"Authorization": auth_header}, # Forward the original Authorization header
            timeout=5 # Set a reasonable timeout for the external call
        )

        # --- 4. Process Response from Auth Service ---
        if response.status_code == 200:
            try:
                # The auth service should return a JSON payload on success
                decoded_payload = response.json()
                logger.info(f"Token validated successfully by auth service for username: {decoded_payload.get('username')}")
                return decoded_payload, None # Success: return payload, no error
            except json.JSONDecodeError as e:
                logger.error(f"Auth service returned 200 OK but response body is not valid JSON. Response: '{response.text[:100]}...'. Error: {e}", exc_info=True)
                return None, (jsonify({"error": "Auth service returned malformed success response"}), 500)
        else:
            # Auth service returned a non-200 status code (e.g., 401, 403)
            error_message = "Token validation failed by auth service"
            try:
                # Try to parse the error message from the auth service's response body
                auth_service_error = response.json()
                if isinstance(auth_service_error, dict) and "error" in auth_service_error:
                    error_message = f"Auth service error: {auth_service_error['error']}"
            except json.JSONDecodeError:
                # If auth service error response is not JSON, use generic message
                logger.warning(f"Auth service returned non-JSON error response. Status: {response.status_code}. Response: '{response.text[:100]}...'")
            
            logger.warning(f"Token validation failed by auth service. Status: {response.status_code}. Message: {error_message}")
            return None, (jsonify({"error": error_message}), response.status_code)

    except requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to auth service at {auth_svc_url}.")
        return None, (jsonify({"error": "Authentication service timeout"}), 504) # 504 Gateway Timeout
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to auth service at {auth_svc_url}: {e}", exc_info=True)
        return None, (jsonify({"error": "Authentication service unreachable"}), 503) # 503 Service Unavailable
    except Exception as e:
        logger.critical(f"An unexpected error occurred during external token validation: {e}", exc_info=True)
        return None, (jsonify({"error": "An unexpected server error occurred during authentication"}), 500)


def login(request):
    auth = request.authorization
    if not auth:
        return None, ("missing credentials", 401)

    basicAuth = (auth.username, auth.password)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login", auth=basicAuth
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)