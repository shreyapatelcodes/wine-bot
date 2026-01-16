"""
Configuration management for Wine App API.
Loads settings from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://localhost:5432/wine_app"
    )

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))  # 30 days

    # OAuth - Google (web only)
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")

    # Pinecone
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_KNOWLEDGE_INDEX = os.getenv("PINECONE_KNOWLEDGE_INDEX", "wine-knowledge")
    PINECONE_PRODUCTS_INDEX = os.getenv("PINECONE_PRODUCTS_INDEX", "wine-products")

    # App URLs (for OAuth redirects)
    API_URL = os.getenv("API_URL", "http://localhost:5000")
    WEB_URL = os.getenv("WEB_URL", "http://localhost:5173")

    @classmethod
    def validate(cls) -> list[str]:
        """Check for missing required configuration. Returns list of missing keys."""
        required = [
            "OPENAI_API_KEY",
            "PINECONE_API_KEY",
        ]
        missing = [key for key in required if not getattr(cls, key)]
        return missing
