"""Test script to run scraper on a small sample of wines."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.wine_com_scraper import WineComScraper
from scrapers.data_enricher import WineDataEnricher
from scrapers.scraper_config import ScraperConfig


class TestConfig(ScraperConfig):
    """Test configuration with smaller limits."""
    MAX_WINES = 10
    WINE_TYPES_TO_SCRAPE = {
        "red": 5,
        "white": 3,
        "sparkling": 2,
    }


def main():
    """Run the scraper on 10 wines for testing."""
    print("=" * 60)
    print("Wine.com Scraper - TEST MODE (10 wines)")
    print("=" * 60)

    # Phase 1: Scrape
    print("\n🍷 PHASE 1: Scraping Wine.com (10 wines)")
    print("-" * 60)

    scraper = WineComScraper(config=TestConfig())
    raw_wines = scraper.scrape_all()

    if not raw_wines:
        print("❌ No wines scraped! Exiting.")
        return

    print(f"\n✅ Scraped {len(raw_wines)} wines")

    # Save raw data
    raw_path = Path(__file__).parent.parent / "data" / "test_raw_wines.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_wines, f, indent=2, ensure_ascii=False)
    print(f"💾 Raw data: {raw_path}")

    # Show sample raw wine
    if raw_wines:
        print("\n📋 Sample raw wine:")
        sample = raw_wines[0]
        print(f"  Name: {sample.get('name')}")
        print(f"  Price: ${sample.get('price_usd')}")
        print(f"  Varietal: {sample.get('varietal')}")
        print(f"  Region: {sample.get('region')}")
        print(f"  Description length: {len(sample.get('description', ''))} chars")

    # Phase 2: Enrich
    print("\n🤖 PHASE 2: Enriching with GPT-4")
    print("-" * 60)

    enricher = WineDataEnricher()
    enriched_wines = []

    for i, wine in enumerate(raw_wines, 1):
        try:
            print(f"  Enriching wine {i}/{len(raw_wines)}: {wine.get('name')[:40]}...")
            enriched = enricher.enrich_wine_data(wine)
            enriched_wines.append(enriched.model_dump())
        except Exception as e:
            print(f"    ⚠️  Error: {e}")

    print(f"\n✅ Enriched {len(enriched_wines)} wines")

    # Save enriched data
    output_path = Path(__file__).parent.parent / "data" / "test_wines_catalog.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_wines, f, indent=2, ensure_ascii=False)
    print(f"💾 Enriched data: {output_path}")

    # Show detailed sample
    if enriched_wines:
        print("\n" + "=" * 60)
        print("SAMPLE ENRICHED WINE")
        print("=" * 60)
        sample = enriched_wines[0]
        print(f"Name: {sample['name']}")
        print(f"Producer: {sample['producer']}")
        print(f"Type: {sample['wine_type']}")
        print(f"Varietal: {sample['varietal']}")
        print(f"Region: {sample['region']}, {sample['country']}")
        print(f"Price: ${sample['price_usd']}")
        print(f"Rating: {sample.get('rating', 'N/A')}")
        print(f"\nSubjective Attributes:")
        print(f"  Body: {sample['body']}")
        print(f"  Sweetness: {sample['sweetness']}")
        print(f"  Acidity: {sample['acidity']}")
        print(f"  Tannin: {sample.get('tannin', 'N/A')}")
        print(f"  Characteristics: {', '.join(sample['characteristics'])}")
        print(f"  Flavor Notes: {', '.join(sample['flavor_notes'])}")
        print(f"\nURL: {sample['wine_com_url']}")

    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE!")
    print("=" * 60)
    print(f"Scraped and enriched {len(enriched_wines)}/10 wines successfully.")
    print("\nIf this looks good, run the full scraper with:")
    print("  python run_scraper.py")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
