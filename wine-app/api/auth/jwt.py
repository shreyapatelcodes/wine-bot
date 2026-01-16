"""
JWT token utilities for authentication.
"""

from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional
import uuid

from flask import request, jsonify, g
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    verify_jwt_in_request,
    JWTManager,
)
from sqlalchemy.orm import Session

from config import Config
from models.database import User, SessionLocal


# JWT Manager instance (initialized in app.py)
jwt = JWTManager()


def create_tokens(user: User) -> dict:
    """
    Create access and refresh tokens for a user.

    Args:
        user: User model instance

    Returns:
        Dict with access_token, refresh_token, and expiration info
    """
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "display_name": user.display_name,
        },
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": Config.JWT_ACCESS_TOKEN_EXPIRES,
    }


def get_current_user(db: Session) -> Optional[User]:
    """
    Get the current authenticated user from JWT token.

    Args:
        db: Database session

    Returns:
        User instance or None if not authenticated
    """
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            return db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    except Exception:
        pass
    return None


def jwt_required(fn):
    """
    Decorator that requires a valid JWT token.
    Sets g.current_user to the authenticated user.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()

            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
                if not user:
                    return jsonify({"error": "User not found"}), 401
                g.current_user = user
                g.db = db
                return fn(*args, **kwargs)
            finally:
                db.close()

        except Exception as e:
            return jsonify({"error": "Invalid or expired token"}), 401

    return wrapper


def jwt_optional(fn):
    """
    Decorator that optionally validates JWT token.
    Sets g.current_user to the authenticated user or None.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        db = SessionLocal()
        try:
            g.db = db
            g.current_user = None

            try:
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
                if user_id:
                    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
                    g.current_user = user
            except Exception:
                pass

            return fn(*args, **kwargs)
        finally:
            db.close()

    return wrapper


@jwt.user_identity_loader
def user_identity_lookup(user):
    """Convert user to JWT identity (string user ID)."""
    if isinstance(user, User):
        return str(user.id)
    return user


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Load user from JWT identity."""
    identity = jwt_data["sub"]
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == uuid.UUID(identity)).first()
    finally:
        db.close()
