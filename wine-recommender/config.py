"""
Configuration module for wine recommendation system.
Loads environment variables and manages application settings.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file in project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration."""

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

    # Pinecone Indexes
    WSET_INDEX_NAME = "wine-knowledge"  # Existing WSET knowledge base
    WINE_PRODUCTS_INDEX_NAME = "wine-products"  # New wine catalog index

    # OpenAI Models
    EMBEDDING_MODEL = "text-embedding-3-small"
    CHAT_MODEL = "gpt-4o-mini"

    # Embedding Configuration
    EMBEDDING_DIMENSION = 1536  # Dimension for text-embedding-3-small

    # Search Configuration
    TOP_K_WSET = 3  # Number of WSET chunks to retrieve
    TOP_K_WINES = 5  # Number of wine candidates to retrieve (return top 3)

    # LLM Configuration
    TEMPERATURE = 0.7
    MAX_TOKENS_AGENT1 = 500  # Agent 1 search query generation
    MAX_TOKENS_AGENT2 = 150  # Agent 2 explanation generation

    # Data Paths
    DATA_DIR = Path(__file__).parent / "data"
    WINES_CATALOG_PATH = DATA_DIR / "wines_catalog.json"

    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        if not cls.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not found in environment variables")

    @classmethod
    def get_summary(cls):
        """Get a summary of current configuration (for debugging)."""
        return {
            "wset_index": cls.WSET_INDEX_NAME,
            "wine_products_index": cls.WINE_PRODUCTS_INDEX_NAME,
            "embedding_model": cls.EMBEDDING_MODEL,
            "chat_model": cls.CHAT_MODEL,
            "embedding_dimension": cls.EMBEDDING_DIMENSION,
            "top_k_wset": cls.TOP_K_WSET,
            "top_k_wines": cls.TOP_K_WINES,
            "wines_catalog_path": str(cls.WINES_CATALOG_PATH),
        }


# Validate configuration on import
Config.validate()
