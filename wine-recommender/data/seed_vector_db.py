"""
Script to populate the Pinecone wine-products index with wine data.
Run this once to set up the vector database.

Usage:
    cd wine-ai-chatbot
    python wine-recommender/data/seed_vector_db.py
"""

import sys
from pathlib import Path

# Add wine-recommender directory to path
wine_rec_dir = Path(__file__).parent.parent
sys.path.insert(0, str(wine_rec_dir))

from data.vector_store import (
    create_wine_products_index,
    load_wines_from_json,
    upload_wines_to_pinecone,
    get_index_stats
)
from config import Config


def main():
    """Main seeding function."""
    print("=" * 60)
    print("Wine Products Vector Database Seeding Script")
    print("=" * 60)
    print()

    # Step 1: Create index if it doesn't exist
    print("Step 1: Creating Pinecone index (if needed)...")
    create_wine_products_index()
    print()

    # Step 2: Load wines from JSON
    print("Step 2: Loading wines from catalog...")
    wines = load_wines_from_json()
    print(f"   Loaded {len(wines)} wines")
    print()

    # Step 3: Upload wines to Pinecone
    print("Step 3: Uploading wines to Pinecone with embeddings...")
    print("   (This may take a minute...)")
    upload_wines_to_pinecone(wines)
    print()

    # Step 4: Verify upload
    print("Step 4: Verifying upload...")
    stats = get_index_stats()
    print(f"   Total vectors in index: {stats['total_vectors']}")
    print(f"   Dimension: {stats['dimension']}")
    print(f"   Index fullness: {stats['index_fullness']:.2%}")
    print()

    print("=" * 60)
    print("Seeding complete! Wine products index is ready.")
    print(f"Index name: {Config.WINE_PRODUCTS_INDEX_NAME}")
    print(f"Total wines: {stats['total_vectors']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
