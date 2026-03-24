from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth

'''
def require_api_key(f):
    """Decorator to require API key authentication for device/iot endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the expected key from environment
        expected_key = os.environ.get("SENSOR_API_KEY")

        if not expected_key:
            return jsonify({"error": "API key not configured on server"}), 500

        # Get the provided key from request headers
        provided_key = request.headers.get("X-API-Key")

        if not provided_key:
            return jsonify({"error": "Missing X-API-Key header"}), 401

        # Compare keys
        if provided_key != expected_key:
            return jsonify({"error": "Unauthorized"}), 401

        # Allow the route to execute normally
        return f(*args, **kwargs)
    return decorated_function
'''

def require_jwt(f):
    """Decorator to require JWT authentication for API endpoints.

    Verifies the JWT token from the Authorization header and injects
    the user ID into the route function as a keyword argument 'uid'.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401

        # Check for "Bearer " prefix
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Invalid Authorization header format"}), 401

        token = auth_header.split(" ")[1]

        try:
            # Verify the JWT token using Firebase Admin SDK
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token["uid"]
            # Inject uid into the route function
            return f(*args, uid=uid, **kwargs)
        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401
    return decorated_function
