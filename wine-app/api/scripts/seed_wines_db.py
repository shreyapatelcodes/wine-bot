"""
Script to populate the PostgreSQL wines table from the wines_catalog.json file.

Usage:
    cd wine-app/api
    python scripts/seed_wines_db.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

from models.database import SessionLocal, Wine, Base, engine


def load_wines_catalog():
    """Load wines from the catalog JSON file."""
    catalog_path = api_dir.parent.parent / "wine-recommender" / "data" / "wines_catalog.json"

    if not catalog_path.exists():
        print(f"Error: Wine catalog not found at {catalog_path}")
        sys.exit(1)

    with open(catalog_path, "r") as f:
        wines = json.load(f)

    return wines


def seed_wines():
    """Seed the wines table from the catalog."""
    print("=" * 60)
    print("Wine Database Seeding Script")
    print("=" * 60)
    print()

    # Ensure tables exist
    print("Step 1: Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    print("   Tables ready.")
    print()

    # Load wines from catalog
    print("Step 2: Loading wines from catalog...")
    wines_data = load_wines_catalog()
    print(f"   Loaded {len(wines_data)} wines from catalog")
    print()

    # Insert wines into database
    print("Step 3: Inserting wines into PostgreSQL...")
    db = SessionLocal()

    try:
        inserted = 0
        updated = 0
        errors = 0

        for wine_data in wines_data:
            try:
                # Build metadata dict for JSONB column
                metadata = {
                    "body": wine_data.get("body"),
                    "sweetness": wine_data.get("sweetness"),
                    "acidity": wine_data.get("acidity"),
                    "tannin": wine_data.get("tannin"),
                    "characteristics": wine_data.get("characteristics", []),
                    "flavor_notes": wine_data.get("flavor_notes", []),
                    "description": wine_data.get("description"),
                    "rating": wine_data.get("rating"),
                    "vivino_url": wine_data.get("vivino_url"),
                }

                # Check if wine already exists
                existing = db.query(Wine).filter(Wine.id == wine_data["id"]).first()

                if existing:
                    # Update existing wine
                    existing.name = wine_data["name"]
                    existing.producer = wine_data.get("producer")
                    existing.vintage = wine_data.get("vintage")
                    existing.wine_type = wine_data["wine_type"]
                    existing.varietal = wine_data.get("varietal")
                    existing.country = wine_data.get("country")
                    existing.region = wine_data.get("region")
                    existing.price_usd = wine_data.get("price_usd")
                    existing.wine_metadata = metadata
                    updated += 1
                else:
                    # Insert new wine
                    wine = Wine(
                        id=wine_data["id"],
                        name=wine_data["name"],
                        producer=wine_data.get("producer"),
                        vintage=wine_data.get("vintage"),
                        wine_type=wine_data["wine_type"],
                        varietal=wine_data.get("varietal"),
                        country=wine_data.get("country"),
                        region=wine_data.get("region"),
                        price_usd=wine_data.get("price_usd"),
                        wine_metadata=metadata,
                    )
                    db.add(wine)
                    inserted += 1

                # Commit in batches
                if (inserted + updated) % 100 == 0:
                    db.commit()
                    print(f"   Progress: {inserted + updated}/{len(wines_data)}")

            except Exception as e:
                errors += 1
                print(f"   Error processing wine {wine_data.get('id', 'unknown')}: {e}")
                db.rollback()

        # Final commit
        db.commit()
        print()

        # Verify
        print("Step 4: Verifying...")
        total = db.query(Wine).count()
        print(f"   Total wines in database: {total}")
        print()

        print("=" * 60)
        print("Seeding complete!")
        print(f"   Inserted: {inserted}")
        print(f"   Updated: {updated}")
        print(f"   Errors: {errors}")
        print("=" * 60)

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_wines()
