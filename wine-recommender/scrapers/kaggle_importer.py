"""
Import and enrich wine data from Kaggle dataset.

Dataset: https://www.kaggle.com/datasets/elvinrustam/wine-dataset

Instructions:
1. Download the dataset from Kaggle (requires Kaggle account)
2. Place the CSV file in wine-recommender/data/kaggle/
3. Run this script to process and enrich the data
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.data_enricher import WineDataEnricher
from models.schemas import Wine


class KaggleWineImporter:
    """Import and process Kaggle wine dataset."""

    def __init__(self, csv_path: Path):
        """
        Initialize importer.

        Args:
            csv_path: Path to the Kaggle CSV file
        """
        self.csv_path = csv_path
        self.enricher = WineDataEnricher()

    def load_csv(self) -> pd.DataFrame:
        """Load the Kaggle CSV file."""
        print(f"Loading CSV from: {self.csv_path}")
        df = pd.read_csv(self.csv_path)
        print(f"Loaded {len(df)} wines from Kaggle")
        return df

    def process_wines(self, df: pd.DataFrame, max_wines: int = 5000) -> list[Dict]:
        """
        Process Kaggle wines and convert to our format.

        Args:
            df: Pandas DataFrame with Kaggle data
            max_wines: Maximum wines to process

        Returns:
            List of processed wine dictionaries
        """
        processed_wines = []
        skipped = 0

        # Limit to max_wines
        df = df.head(max_wines)

        for idx, row in df.iterrows():
            try:
                wine_data = self._convert_kaggle_to_scraped_format(row)

                # Validate required fields
                if not wine_data or not wine_data.get("description"):
                    skipped += 1
                    continue

                processed_wines.append(wine_data)

                if (idx + 1) % 100 == 0:
                    print(f"  Processed {idx + 1}/{len(df)} wines...")

            except Exception as e:
                skipped += 1
                print(f"\n  Warning: Skipped wine at row {idx}: {e}")

        print(f"\nProcessed: {len(processed_wines)} wines, Skipped: {skipped}")
        return processed_wines

    def _convert_kaggle_to_scraped_format(self, row: pd.Series) -> Optional[Dict]:
        """
        Convert a Kaggle row to our scraped wine format.

        Args:
            row: Pandas Series with Kaggle data

        Returns:
            Dictionary in scraped format or None
        """
        # Extract fields (handle NaN values)
        name = str(row.get("Title", "")).strip()
        description = str(row.get("Description", "")).strip()
        characteristics = str(row.get("Characteristics", "")).strip()
        price_str = str(row.get("Price", ""))
        grape = str(row.get("Grape", "")).strip()
        country = str(row.get("Country", "")).strip()
        region = str(row.get("Region", "")).strip()
        wine_type = str(row.get("Type", "")).strip()
        vintage_str = str(row.get("Vintage", ""))
        style = str(row.get("Style", "")).strip()

        # Clean up 'nan' strings
        if region == "nan" or not region:
            region = country
        if description == "nan":
            description = ""
        if characteristics == "nan":
            characteristics = ""
        if style == "nan":
            style = ""

        # Validate minimum required fields
        if not name or (not description and not characteristics):
            return None

        # Parse price
        price = self._parse_price(price_str)
        if not price or price < 5 or price > 5000:  # Sanity check
            price = None

        # Parse vintage
        vintage = self._parse_vintage(vintage_str)

        # Parse wine type
        wine_type_normalized = self._normalize_wine_type(wine_type)
        if not wine_type_normalized:
            wine_type_normalized = "red"  # Default fallback

        # Combine description and characteristics
        full_description = self._build_description(description, characteristics, style)

        # Parse producer from name (typically first word(s))
        producer = self._extract_producer(name)

        # Build scraped format dictionary
        return {
            "name": name,
            "producer": producer,
            "vintage": vintage,
            "varietal": grape or "Blend",
            "country": country or "Unknown",
            "region": region or country or "Unknown",
            "price_usd": price,
            "rating": None,  # Kaggle dataset doesn't have ratings
            "description": full_description,
            "wine_type": wine_type_normalized,
            "wine_com_url": f"https://www.wine.com/search/{name.replace(' ', '-').lower()}"  # Generic search link
        }

    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parse price from string."""
        if pd.isna(price_str) or not price_str:
            return None

        # Remove currency symbols and extract number
        price_clean = re.sub(r'[^\d.]', '', str(price_str))
        if not price_clean:
            return None

        try:
            return float(price_clean)
        except ValueError:
            return None

    def _parse_vintage(self, vintage_str: str) -> Optional[int]:
        """Parse vintage year."""
        if pd.isna(vintage_str) or not vintage_str:
            return None

        # Extract 4-digit year
        match = re.search(r'\b(19\d{2}|20\d{2})\b', str(vintage_str))
        if match:
            return int(match.group(1))
        return None

    def _normalize_wine_type(self, wine_type: str) -> Optional[str]:
        """Normalize wine type to our schema."""
        if pd.isna(wine_type) or not wine_type:
            return None

        wine_type_lower = str(wine_type).lower()

        if "red" in wine_type_lower:
            return "red"
        elif "white" in wine_type_lower:
            return "white"
        elif "rosé" in wine_type_lower or "rose" in wine_type_lower:
            return "rosé"
        elif "sparkling" in wine_type_lower or "champagne" in wine_type_lower or "prosecco" in wine_type_lower:
            return "sparkling"
        else:
            return None

    def _build_description(self, description: str, characteristics: str, style: str) -> str:
        """Build full description from available fields."""
        parts = []

        if description and description != "nan":
            parts.append(description)
        if characteristics and characteristics != "nan":
            parts.append(f"Characteristics: {characteristics}")
        if style and style != "nan":
            parts.append(f"Style: {style}")

        return " ".join(parts)

    def _extract_producer(self, name: str) -> str:
        """Extract producer from wine name."""
        # Typically first 1-2 words before vintage or varietal
        parts = name.split()
        if len(parts) >= 2:
            return " ".join(parts[:2])
        return parts[0] if parts else "Unknown"

    def enrich_all(self, processed_wines: list[Dict]) -> list[Dict]:
        """
        Enrich all wines with GPT-4.

        Args:
            processed_wines: List of processed wine dictionaries

        Returns:
            List of enriched Wine model dictionaries
        """
        enriched_wines = []
        failed = 0

        print(f"\n🤖 Enriching {len(processed_wines)} wines with GPT-4...")

        for i, wine in enumerate(processed_wines, 1):
            try:
                enriched = self.enricher.enrich_wine_data(wine)
                enriched_wines.append(enriched.model_dump())

                if i % 50 == 0:
                    print(f"  Enriched {i}/{len(processed_wines)} wines...")

            except Exception as e:
                failed += 1
                print(f"\n  ⚠️  Error enriching '{wine.get('name')}': {e}")

        print(f"\n✅ Enriched {len(enriched_wines)} wines")
        if failed > 0:
            print(f"⚠️  {failed} wines failed enrichment")

        return enriched_wines


def main():
    """Main import pipeline."""
    print("=" * 60)
    print("Kaggle Wine Dataset Importer")
    print("=" * 60)

    # Check for CSV file
    data_dir = Path(__file__).parent.parent / "data" / "kaggle"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Look for CSV files
    csv_files = list(data_dir.glob("*.csv"))

    if not csv_files:
        print(f"\n❌ No CSV files found in {data_dir}")
        print("\nPlease download the Kaggle dataset:")
        print("1. Visit: https://www.kaggle.com/datasets/elvinrustam/wine-dataset")
        print("2. Click 'Download' (requires Kaggle account)")
        print("3. Extract the CSV file to: wine-recommender/data/kaggle/")
        print("4. Run this script again")
        return

    csv_path = csv_files[0]
    print(f"\nFound CSV: {csv_path.name}")

    # Initialize importer
    importer = KaggleWineImporter(csv_path)

    # Load CSV
    df = importer.load_csv()

    # Show sample
    print(f"\nDataset columns: {list(df.columns)}")
    print(f"Sample wine: {df.iloc[0]['Title']}")

    # Process wines
    print("\n📋 Processing wines...")
    # Start with just 10 for testing, can increase to 5000 later
    max_wines = 10 if len(sys.argv) == 1 else int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"Processing up to {max_wines} wines...")
    processed_wines = importer.process_wines(df, max_wines=max_wines)

    # Save raw processed data
    raw_path = Path(__file__).parent.parent / "data" / "kaggle_processed_wines.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(processed_wines, f, indent=2, ensure_ascii=False)
    print(f"💾 Processed data saved: {raw_path}")

    # Enrich with GPT-4
    enriched_wines = importer.enrich_all(processed_wines)

    # Save final catalog
    output_path = Path(__file__).parent.parent / "data" / "wines_catalog.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_wines, f, indent=2, ensure_ascii=False)
    print(f"💾 Final catalog saved: {output_path}")

    # Print statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total wines imported: {len(enriched_wines)}")

    if enriched_wines:
        # Wine type breakdown
        wine_types = {}
        for wine in enriched_wines:
            wt = wine.get("wine_type", "unknown")
            wine_types[wt] = wine_types.get(wt, 0) + 1

        print("\nWine Type Breakdown:")
        for wine_type, count in sorted(wine_types.items()):
            print(f"  {wine_type.capitalize()}: {count}")

        # Price range
        prices = [w.get("price_usd", 0) for w in enriched_wines if w.get("price_usd")]
        if prices:
            print(f"\nPrice Range: ${min(prices):.2f} - ${max(prices):.2f}")
            print(f"Average Price: ${sum(prices)/len(prices):.2f}")

        # Countries
        countries = set(w.get("country") for w in enriched_wines if w.get("country"))
        print(f"\nCountries: {len(countries)}")
        print(f"  {', '.join(sorted(countries)[:10])}")

    print("\n" + "=" * 60)
    print("🎉 NEXT STEPS")
    print("=" * 60)
    print("1. Upload to Pinecone:")
    print("   cd wine-recommender/data")
    print("   python seed_vector_db.py")
    print()
    print("2. Test the chatbot:")
    print("   streamlit run wine_chatbot_ui.py")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
