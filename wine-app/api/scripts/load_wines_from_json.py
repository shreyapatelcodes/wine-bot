#!/usr/bin/env python3
"""
Load wines from processed Kaggle JSON file to PostgreSQL database.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from models.database import SessionLocal, Wine


def load_wines_from_json(json_path: str, batch_size: int = 500):
    """
    Load wines from processed JSON file to PostgreSQL.

    Args:
        json_path: Path to the processed wines JSON file
        batch_size: Number of wines to commit at a time

    Expected JSON format:
        [
            {
                "name": "Wine Name",
                "producer": "Producer Name",
                "vintage": 2021,
                "varietal": "Chardonnay",
                "country": "USA",
                "region": "California",
                "price_usd": 15.99,
                "wine_type": "white",
                "description": "Full description...",
                ...
            },
            ...
        ]
    """
    print(f"Loading wines from: {json_path}")

    json_file = Path(json_path)
    if not json_file.exists():
        print(f"Error: File not found: {json_path}")
        return

    db = SessionLocal()

    try:
        # Load JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            wines_data = json.load(f)

        print(f"Loaded {len(wines_data)} wines from JSON")
        print("\nProcessing wines...")

        wines_created = 0
        wines_updated = 0
        wines_skipped = 0

        for i, wine_data in enumerate(wines_data, 1):
            # Get ID from JSON (matches Pinecone IDs)
            wine_id = wine_data.get('id')
            if not wine_id:
                print(f"  Warning: Wine {i} has no ID, skipping")
                wines_skipped += 1
                continue

            # Skip if required fields are missing
            if not wine_data.get('name') or not wine_data.get('wine_type'):
                wines_skipped += 1
                if i % 100 == 0:
                    print(f"  Skipping wine {i}: missing required fields")
                continue

            # Normalize wine type
            wine_type = wine_data.get('wine_type', 'red').lower()
            if wine_type not in ['red', 'white', 'rosé', 'rose', 'sparkling']:
                # Default to red if unknown
                wine_type = 'red'
            if wine_type == 'rose':
                wine_type = 'rosé'

            # Parse vintage
            vintage = wine_data.get('vintage')
            if vintage and isinstance(vintage, (int, float)):
                vintage = int(vintage)
                if not (1900 <= vintage <= 2030):
                    vintage = None
            else:
                vintage = None

            # Extract core fields and put rest in metadata
            core_fields = {'name', 'producer', 'vintage', 'varietal', 'country', 'region', 'price_usd', 'wine_type', 'id'}
            wine_metadata = {
                k: v for k, v in wine_data.items()
                if k not in core_fields and v is not None and v != ""
            }

            # Convert lists to strings for JSON storage if needed
            if 'characteristics' in wine_metadata and isinstance(wine_metadata['characteristics'], list):
                wine_metadata['characteristics'] = wine_metadata['characteristics']
            if 'flavor_notes' in wine_metadata and isinstance(wine_metadata['flavor_notes'], list):
                wine_metadata['flavor_notes'] = wine_metadata['flavor_notes']

            # Check if wine exists
            existing_wine = db.query(Wine).filter(Wine.id == wine_id).first()

            if existing_wine:
                # Update
                existing_wine.name = wine_data.get('name')
                existing_wine.producer = wine_data.get('producer')
                existing_wine.vintage = vintage
                existing_wine.wine_type = wine_type
                existing_wine.varietal = wine_data.get('varietal')
                existing_wine.country = wine_data.get('country')
                existing_wine.region = wine_data.get('region')
                existing_wine.price_usd = wine_data.get('price_usd')
                existing_wine.wine_metadata = wine_metadata
                wines_updated += 1
            else:
                # Create
                wine = Wine(
                    id=wine_id,
                    name=wine_data.get('name'),
                    producer=wine_data.get('producer'),
                    vintage=vintage,
                    wine_type=wine_type,
                    varietal=wine_data.get('varietal'),
                    country=wine_data.get('country'),
                    region=wine_data.get('region'),
                    price_usd=wine_data.get('price_usd'),
                    wine_metadata=wine_metadata
                )
                db.add(wine)
                wines_created += 1

            # Commit in batches
            if i % batch_size == 0:
                db.commit()
                print(f"Processed {i}/{len(wines_data)} wines... (Created: {wines_created}, Updated: {wines_updated}, Skipped: {wines_skipped})")

        # Final commit
        db.commit()

        print("\n" + "=" * 60)
        print("Import complete!")
        print(f"Total wines in file: {len(wines_data)}")
        print(f"Wines created: {wines_created}")
        print(f"Wines updated: {wines_updated}")
        print(f"Wines skipped: {wines_skipped}")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during import: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load wines from JSON to PostgreSQL")
    parser.add_argument(
        "json_path",
        type=str,
        nargs='?',
        default="../../wine-recommender/data/wines_catalog.json",
        help="Path to the wines catalog JSON file (default: ../../wine-recommender/data/wines_catalog.json)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of wines to commit at a time (default: 500)"
    )

    args = parser.parse_args()

    load_wines_from_json(args.json_path, batch_size=args.batch_size)
