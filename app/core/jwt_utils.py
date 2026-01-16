"""
JWT Token Utilities for Authentication
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets

from app.config import settings

# Generate a default secret if not configured
JWT_SECRET = settings.JWT_SECRET or secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def create_access_token(user_id: str, email: str, name: str) -> str:
    """Create a JWT access token for the user"""
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Extract user info from token"""
    payload = decode_token(token)
    if payload:
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name")
        }
    return None
