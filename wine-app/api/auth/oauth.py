"""
OAuth handler for Google Sign-In (web only).
"""

from datetime import datetime, timezone
from typing import Optional
import httpx

from config import Config
from models.database import User, SessionLocal


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
                return None

            data = response.json()

            # Verify the token was issued for our app
            if data.get("aud") != Config.GOOGLE_CLIENT_ID:
                return None

            return {
                "sub": data.get("sub"),
                "email": data.get("email"),
                "name": data.get("name"),
                "picture": data.get("picture"),
            }
    except Exception:
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

    except Exception:
        db.rollback()
        return None, False
    finally:
        db.close()
