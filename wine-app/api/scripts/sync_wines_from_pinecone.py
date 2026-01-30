#!/usr/bin/env python3
"""
Sync wines from Pinecone to PostgreSQL database.
Run this script to populate the wines table with all products from the Kaggle dataset.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from models.database import SessionLocal, Wine
from utils.embeddings import get_pinecone_index


def sync_wines_from_pinecone(batch_size: int = 100):
    """
    Fetch all wines from Pinecone and sync to PostgreSQL.

    Args:
        batch_size: Number of wines to process at a time
    """
    print("Starting wine sync from Pinecone to PostgreSQL...")
    print(f"Pinecone index: {Config.PINECONE_PRODUCTS_INDEX}")

    db = SessionLocal()

    try:
        # Get Pinecone index
        index = get_pinecone_index(Config.PINECONE_PRODUCTS_INDEX)

        # Get index stats to see how many vectors we have
        stats = index.describe_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
        print(f"Total wines in Pinecone: {total_vectors}")

        # Pinecone doesn't have a "list all IDs" operation, so we need to use pagination
        # We'll query with a dummy vector to get IDs, then fetch them in batches
        print("\nFetching wine IDs from Pinecone...")

        # Alternative: If you have a list of IDs from your Kaggle dataset, use those
        # For now, we'll use the list_paginated approach (if available) or query approach

        # Get all wine IDs by querying the index
        # Note: This is a workaround. Ideally, you'd have the IDs from your data pipeline.
        wine_ids = []

        # Create a dummy embedding to query
        import numpy as np
        dummy_vector = np.zeros(1536).tolist()  # Assuming 1536-dim embeddings

        # Query to get top wines (you may need to adjust top_k based on your data size)
        # Note: Pinecone limits queries to top 10,000
        query_limit = min(10000, total_vectors) if total_vectors > 0 else 10000

        print(f"Querying for up to {query_limit} wines...")
        results = index.query(
            vector=dummy_vector,
            top_k=query_limit,
            include_metadata=True
        )

        print(f"Retrieved {len(results.get('matches', []))} wines from query")

        # Process wines in batches
        wines_created = 0
        wines_updated = 0
        wines_skipped = 0

        for i, match in enumerate(results.get('matches', []), 1):
            wine_id = match['id']
            metadata = match.get('metadata', {})

            if not metadata:
                print(f"Warning: Wine {wine_id} has no metadata, skipping...")
                wines_skipped += 1
                continue

            # Check if wine already exists
            existing_wine = db.query(Wine).filter(Wine.id == wine_id).first()

            if existing_wine:
                # Update existing wine
                existing_wine.name = metadata.get('name', existing_wine.name)
                existing_wine.producer = metadata.get('producer')
                existing_wine.vintage = metadata.get('vintage') if metadata.get('vintage', 0) > 0 else None
                existing_wine.wine_type = metadata.get('wine_type', existing_wine.wine_type)
                existing_wine.varietal = metadata.get('varietal')
                existing_wine.country = metadata.get('country')
                existing_wine.region = metadata.get('region')
                existing_wine.price_usd = metadata.get('price_usd')
                existing_wine.wine_metadata = {
                    k: v for k, v in metadata.items()
                    if k not in ['name', 'producer', 'vintage', 'wine_type', 'varietal', 'country', 'region', 'price_usd']
                }
                wines_updated += 1
            else:
                # Create new wine
                wine = Wine(
                    id=wine_id,
                    name=metadata.get('name', 'Unknown'),
                    producer=metadata.get('producer'),
                    vintage=metadata.get('vintage') if metadata.get('vintage', 0) > 0 else None,
                    wine_type=metadata.get('wine_type', 'red'),
                    varietal=metadata.get('varietal'),
                    country=metadata.get('country'),
                    region=metadata.get('region'),
                    price_usd=metadata.get('price_usd'),
                    wine_metadata={
                        k: v for k, v in metadata.items()
                        if k not in ['name', 'producer', 'vintage', 'wine_type', 'varietal', 'country', 'region', 'price_usd']
                    }
                )
                db.add(wine)
                wines_created += 1

            # Commit in batches
            if i % batch_size == 0:
                db.commit()
                print(f"Processed {i}/{len(results['matches'])} wines... (Created: {wines_created}, Updated: {wines_updated}, Skipped: {wines_skipped})")

        # Final commit
        db.commit()

        print("\n" + "=" * 60)
        print("Sync complete!")
        print(f"Wines created: {wines_created}")
        print(f"Wines updated: {wines_updated}")
        print(f"Wines skipped: {wines_skipped}")
        print(f"Total processed: {wines_created + wines_updated + wines_skipped}")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during sync: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync wines from Pinecone to PostgreSQL")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of wines to commit at a time (default: 100)"
    )

    args = parser.parse_args()

    sync_wines_from_pinecone(batch_size=args.batch_size)
