"""
Pinecone vector store management for wine products.
Handles index creation, wine data upload, and querying.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from models.schemas import Wine
from utils.embeddings import create_embedding


def create_wine_products_index():
    """
    Create the 'wine-products' Pinecone index if it doesn't exist.
    Uses same configuration as existing 'wine-knowledge' index.
    """
    pc = Pinecone(api_key=Config.PINECONE_API_KEY)

    # Check if index already exists
    existing_indexes = [index.name for index in pc.list_indexes()]

    if Config.WINE_PRODUCTS_INDEX_NAME in existing_indexes:
        print(f"Index '{Config.WINE_PRODUCTS_INDEX_NAME}' already exists.")
        return pc.Index(Config.WINE_PRODUCTS_INDEX_NAME)

    # Create new index with serverless AWS configuration
    print(f"Creating index '{Config.WINE_PRODUCTS_INDEX_NAME}'...")
    pc.create_index(
        name=Config.WINE_PRODUCTS_INDEX_NAME,
        dimension=Config.EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"  # Match existing wine-knowledge index
        )
    )

    print(f"Index '{Config.WINE_PRODUCTS_INDEX_NAME}' created successfully.")
    return pc.Index(Config.WINE_PRODUCTS_INDEX_NAME)


def load_wines_from_json(json_path: str = None) -> List[Wine]:
    """
    Load wine data from JSON file.

    Args:
        json_path: Path to wines_catalog.json (defaults to Config.WINES_CATALOG_PATH)

    Returns:
        List of Wine pydantic models
    """
    if json_path is None:
        json_path = Config.WINES_CATALOG_PATH

    with open(json_path, 'r', encoding='utf-8') as f:
        wine_data = json.load(f)

    wines = [Wine(**wine_dict) for wine_dict in wine_data]
    print(f"Loaded {len(wines)} wines from {json_path}")
    return wines


def upload_wines_to_pinecone(wines: List[Wine], batch_size: int = 100):
    """
    Upload wine data to Pinecone with embeddings and metadata.

    Args:
        wines: List of Wine objects
        batch_size: Number of wines to upload per batch
    """
    pc = Pinecone(api_key=Config.PINECONE_API_KEY)
    index = pc.Index(Config.WINE_PRODUCTS_INDEX_NAME)

    print(f"Uploading {len(wines)} wines to Pinecone...")

    # Prepare vectors for upsert
    vectors = []
    for wine in wines:
        # Create embedding from wine description
        embedding = create_embedding(wine.description)

        # Prepare metadata (flatten for Pinecone)
        metadata = {
            "name": wine.name,
            "producer": wine.producer,
            "vintage": wine.vintage if wine.vintage else 0,
            "wine_type": wine.wine_type,
            "varietal": wine.varietal,
            "country": wine.country,
            "region": wine.region,
            "body": wine.body,
            "sweetness": wine.sweetness,
            "acidity": wine.acidity,
            "tannin": wine.tannin if wine.tannin else "n/a",
            "characteristics": json.dumps(wine.characteristics),  # Store as JSON string
            "flavor_notes": json.dumps(wine.flavor_notes),  # Store as JSON string
            "description": wine.description,
            "price_usd": float(wine.price_usd),
            "rating": float(wine.rating) if wine.rating else 0.0,
            "wine_com_url": wine.wine_com_url
        }

        vectors.append({
            "id": wine.id,
            "values": embedding,
            "metadata": metadata
        })

        # Upsert in batches
        if len(vectors) >= batch_size:
            index.upsert(vectors=vectors)
            print(f"Uploaded {len(vectors)} wines...")
            vectors = []

    # Upload remaining wines
    if vectors:
        index.upsert(vectors=vectors)
        print(f"Uploaded {len(vectors)} wines...")

    print(f"Successfully uploaded {len(wines)} wines to Pinecone.")


def get_index_stats() -> Dict[str, Any]:
    """
    Get statistics about the wine-products index.

    Returns:
        Dictionary with index statistics
    """
    pc = Pinecone(api_key=Config.PINECONE_API_KEY)
    index = pc.Index(Config.WINE_PRODUCTS_INDEX_NAME)

    stats = index.describe_index_stats()
    return {
        "total_vectors": stats.total_vector_count,
        "dimension": stats.dimension,
        "index_fullness": stats.index_fullness
    }


def delete_index():
    """
    Delete the wine-products index (use with caution!).
    Useful for resetting during development.
    """
    pc = Pinecone(api_key=Config.PINECONE_API_KEY)

    existing_indexes = [index.name for index in pc.list_indexes()]
    if Config.WINE_PRODUCTS_INDEX_NAME in existing_indexes:
        pc.delete_index(Config.WINE_PRODUCTS_INDEX_NAME)
        print(f"Deleted index '{Config.WINE_PRODUCTS_INDEX_NAME}'.")
    else:
        print(f"Index '{Config.WINE_PRODUCTS_INDEX_NAME}' does not exist.")
