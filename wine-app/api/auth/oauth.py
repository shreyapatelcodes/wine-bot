"""
OAuth handler for Google Sign-In (web only).
"""

import base64
import json
from datetime import datetime, timezone
from typing import Optional
import httpx

from config import Config
from models.database import User, SessionLocal


def _decode_jwt_payload(token: str) -> Optional[dict]:
    """Decode the payload from a JWT without verification (verification done by Google)."""
    try:
        # JWT is header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None

        # Decode payload (add padding if needed)
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding

        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return None


def verify_google_token(id_token: str) -> Optional[dict]:
    """
    Verify a Google ID token and return user info.

    Args:
        id_token: Google ID token from client

    Returns:
        Dict with user info (sub, email, name, picture) or None if invalid
    """
    try:
        with httpx.Client() as client:
            response = client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            )

            if response.status_code != 200:
                print(f"[OAuth] Token verification failed: {response.status_code} - {response.text}")
                return None

            data = response.json()

            # Verify the token was issued for our app
            if data.get("aud") != Config.GOOGLE_CLIENT_ID:
                print(f"[OAuth] Client ID mismatch: token aud={data.get('aud')}, expected={Config.GOOGLE_CLIENT_ID}")
                return None

            # The tokeninfo endpoint doesn't return picture, so decode it from the JWT
            picture = data.get("picture")
            if not picture:
                jwt_payload = _decode_jwt_payload(id_token)
                if jwt_payload:
                    picture = jwt_payload.get("picture")

            return {
                "sub": data.get("sub"),
                "email": data.get("email"),
                "name": data.get("name"),
                "picture": picture,
            }
    except Exception as e:
        print(f"[OAuth] Exception during token verification: {e}")
        return None


def google_auth(id_token: str) -> tuple[Optional[User], bool]:
    """
    Authenticate user with Google ID token.
    Creates a new user if one doesn't exist.

    Args:
        id_token: Google ID token from client

    Returns:
        Tuple of (User, is_new_user) or (None, False) if authentication failed
    """
    user_info = verify_google_token(id_token)
    if not user_info:
        return None, False

    db = SessionLocal()
    try:
        # Check if user exists by OAuth ID
        user = db.query(User).filter(
            User.oauth_provider == "google",
            User.oauth_id == user_info["sub"]
        ).first()

        is_new = False

        if not user:
            # Check if email is already used
            existing = db.query(User).filter(User.email == user_info["email"]).first()
            if existing:
                # Email already exists - could be same user, link accounts
                existing.oauth_provider = "google"
                existing.oauth_id = user_info["sub"]
                existing.avatar_url = user_info.get("picture")
                existing.last_login_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(existing)
                return existing, False

            # Create new user
            user = User(
                email=user_info["email"],
                display_name=user_info.get("name"),
                avatar_url=user_info.get("picture"),
                oauth_provider="google",
                oauth_id=user_info["sub"],
            )
            db.add(user)
            is_new = True

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)

        return user, is_new

    except Exception as e:
        print(f"[OAuth] Database error: {e}")
        db.rollback()
        return None, False
    finally:
        db.close()
