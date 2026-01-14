"""Main script to run the Wine.com scraper and generate wines_catalog.json."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.wine_com_scraper import WineComScraper
from scrapers.data_enricher import WineDataEnricher
from scrapers.scraper_config import ScraperConfig


def main():
    """Run the complete scraping and enrichment pipeline."""
    print("=" * 60)
    print("Wine.com Scraper & Enrichment Pipeline")
    print("=" * 60)

    # Phase 1: Scrape Wine.com
    print("\n🍷 PHASE 1: Scraping Wine.com")
    print("-" * 60)

    scraper = WineComScraper(config=ScraperConfig())
    raw_wines = scraper.scrape_all()

    if not raw_wines:
        print("❌ No wines scraped! Exiting.")
        return

    print(f"\n✅ Scraped {len(raw_wines)} wines successfully")

    # Save raw data for backup
    raw_path = Path(__file__).parent.parent / "data" / "raw_scraped_wines.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_wines, f, indent=2, ensure_ascii=False)
    print(f"💾 Raw data saved to: {raw_path}")

    # Phase 2: Enrich with GPT-4
    print("\n🤖 PHASE 2: Enriching with GPT-4")
    print("-" * 60)
    print("Analyzing wine descriptions to extract subjective attributes...")

    enricher = WineDataEnricher()
    enriched_wines = []
    failed_count = 0

    for i, wine in enumerate(raw_wines, 1):
        try:
            enriched = enricher.enrich_wine_data(wine)
            enriched_wines.append(enriched.model_dump())

            if i % 50 == 0:
                print(f"   Processed {i}/{len(raw_wines)} wines...")

        except Exception as e:
            failed_count += 1
            wine_name = wine.get("name", "Unknown")
            print(f"\n⚠️  Error enriching wine '{wine_name}': {e}")

    print(f"\n✅ Enriched {len(enriched_wines)} wines")
    if failed_count > 0:
        print(f"⚠️  {failed_count} wines failed enrichment")

    # Save final catalog
    output_path = Path(__file__).parent.parent / "data" / "wines_catalog.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_wines, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Final catalog saved to: {output_path}")

    # Print summary stats
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total wines scraped: {len(raw_wines)}")
    print(f"Successfully enriched: {len(enriched_wines)}")
    print(f"Failed: {failed_count}")

    # Wine type breakdown
    if enriched_wines:
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
        print("\n\n⚠️  Scraper interrupted by user")
        print("Progress has been saved to checkpoint file.")
        print("Run again to resume from checkpoint.")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
