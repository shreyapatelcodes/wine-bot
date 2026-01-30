#!/usr/bin/env python3
"""
Load wines from Kaggle CSV file to PostgreSQL database.
This is more efficient than fetching from Pinecone if you have the source data.
"""

import sys
import csv
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from models.database import SessionLocal, Wine


def load_wines_from_csv(csv_path: str, batch_size: int = 500):
    """
    Load wines from Kaggle CSV file to PostgreSQL.

    Args:
        csv_path: Path to the Kaggle wines CSV file
        batch_size: Number of wines to commit at a time

    Expected CSV columns (adjust based on your actual schema):
        - id (or generate from row index)
        - name
        - producer (winery)
        - vintage (year)
        - wine_type (red, white, rosé, sparkling)
        - varietal (grape variety)
        - country
        - region
        - price_usd (price)
        - Any additional metadata fields
    """
    print(f"Loading wines from: {csv_path}")

    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f"Error: File not found: {csv_path}")
        return

    db = SessionLocal()

    try:
        wines_created = 0
        wines_updated = 0
        wines_skipped = 0
        row_count = 0

        with open(csv_file, 'r', encoding='utf-8') as f:
            # Auto-detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.DictReader(f, delimiter=delimiter)

            print(f"CSV columns found: {reader.fieldnames}")
            print("\nProcessing wines...")

            for i, row in enumerate(reader, 1):
                row_count = i

                # Generate ID or use from CSV
                # Adjust this based on your CSV structure
                wine_id = row.get('id') or f"wine_{i:06d}"

                # Skip if required fields are missing
                if not row.get('name') or not row.get('wine_type'):
                    wines_skipped += 1
                    continue

                # Parse vintage (handle different formats)
                vintage = None
                if row.get('vintage') or row.get('year'):
                    try:
                        vintage_val = int(row.get('vintage') or row.get('year'))
                        if 1900 <= vintage_val <= 2030:
                            vintage = vintage_val
                    except (ValueError, TypeError):
                        pass

                # Parse price
                price_usd = None
                if row.get('price') or row.get('price_usd'):
                    try:
                        price_str = row.get('price') or row.get('price_usd')
                        # Remove currency symbols
                        price_str = price_str.replace('$', '').replace(',', '').strip()
                        price_usd = float(price_str)
                    except (ValueError, TypeError, AttributeError):
                        pass

                # Normalize wine type
                wine_type = (row.get('wine_type') or row.get('type') or 'red').lower()
                if wine_type not in ['red', 'white', 'rosé', 'sparkling']:
                    # Try to infer
                    if 'white' in wine_type:
                        wine_type = 'white'
                    elif 'rosé' in wine_type or 'rose' in wine_type:
                        wine_type = 'rosé'
                    elif 'sparkling' in wine_type or 'champagne' in wine_type:
                        wine_type = 'sparkling'
                    else:
                        wine_type = 'red'

                # Collect extra metadata
                core_fields = {'id', 'name', 'producer', 'winery', 'vintage', 'year', 'wine_type', 'type',
                               'varietal', 'variety', 'grape', 'country', 'region', 'price', 'price_usd'}
                wine_metadata = {
                    k: v for k, v in row.items()
                    if k not in core_fields and v and v.strip()
                }

                # Check if wine exists
                existing_wine = db.query(Wine).filter(Wine.id == wine_id).first()

                if existing_wine:
                    # Update
                    existing_wine.name = row.get('name')
                    existing_wine.producer = row.get('producer') or row.get('winery')
                    existing_wine.vintage = vintage
                    existing_wine.wine_type = wine_type
                    existing_wine.varietal = row.get('varietal') or row.get('variety') or row.get('grape')
                    existing_wine.country = row.get('country')
                    existing_wine.region = row.get('region')
                    existing_wine.price_usd = price_usd
                    existing_wine.wine_metadata = wine_metadata
                    wines_updated += 1
                else:
                    # Create
                    wine = Wine(
                        id=wine_id,
                        name=row.get('name'),
                        producer=row.get('producer') or row.get('winery'),
                        vintage=vintage,
                        wine_type=wine_type,
                        varietal=row.get('varietal') or row.get('variety') or row.get('grape'),
                        country=row.get('country'),
                        region=row.get('region'),
                        price_usd=price_usd,
                        wine_metadata=wine_metadata
                    )
                    db.add(wine)
                    wines_created += 1

                # Commit in batches
                if i % batch_size == 0:
                    db.commit()
                    print(f"Processed {i} rows... (Created: {wines_created}, Updated: {wines_updated}, Skipped: {wines_skipped})")

        # Final commit
        db.commit()

        print("\n" + "=" * 60)
        print("Import complete!")
        print(f"Total rows processed: {row_count}")
        print(f"Wines created: {wines_created}")
        print(f"Wines updated: {wines_updated}")
        print(f"Wines skipped: {wines_skipped}")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load wines from CSV to PostgreSQL")
    parser.add_argument(
        "csv_path",
        type=str,
        help="Path to the Kaggle wines CSV file"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of wines to commit at a time (default: 500)"
    )

    args = parser.parse_args()

    load_wines_from_csv(args.csv_path, batch_size=args.batch_size)
