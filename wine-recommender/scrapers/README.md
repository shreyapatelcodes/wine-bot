# Wine.com Scraper

This scraper collects real wine data from Wine.com to build a commercial wine catalog for the recommendation system.

## Overview

The scraper uses a two-phase approach:

1. **Phase 1: Scrape Wine.com** - Collect basic wine data (name, price, varietal, region, ratings, descriptions)
2. **Phase 2: Enrich with GPT-4** - Analyze descriptions to extract subjective attributes (body, sweetness, acidity, tannin, characteristics, flavor notes)

## Quick Start

### 1. Install Dependencies

```bash
cd wine-recommender
pip install -r requirements.txt
```

### 2. Configure (Optional)

Edit `scrapers/scraper_config.py` to adjust:
- `MAX_WINES` - Target number of wines (default: 5000)
- `MIN_RATING` - Minimum wine rating filter (default: 3.5)
- `DELAY_BETWEEN_REQUESTS` - Politeness delay (default: 2-5 seconds)
- `WINE_TYPES_TO_SCRAPE` - Target count per wine type

### 3. Run the Scraper

```bash
cd scrapers
python run_scraper.py
```

The scraper will:
- Scrape Wine.com for wines across different types (red, white, sparkling, rosé)
- Visit each product page to get full descriptions
- Use GPT-4 to extract unique characteristics from descriptions
- Save results to `data/wines_catalog.json`

**Estimated time:** 7-8 hours for 5,000 wines
**Cost:** ~$1.35 for GPT-4o-mini enrichment

### 4. Upload to Pinecone

Once scraping completes:

```bash
cd ../data
python seed_vector_db.py
```

### 5. Test the Chatbot

```bash
cd ../..
streamlit run wine_chatbot_ui.py
```

## Features

### Resume Capability

The scraper automatically saves checkpoints every 50 wines to `data/scraped/checkpoint.json`. If interrupted, simply run again to resume.

### Data Validation

Wines are validated to ensure:
- Required fields present (name, price, country, wine_type)
- Description exists (needed for GPT-4 enrichment)
- Price and ratings are within valid ranges

Wines without descriptions are skipped to ensure unique characteristics.

### Unique Wine Profiles

Unlike generic scrapers, this enricher analyzes each wine's actual description to extract:
- **Body:** light, medium, or full (from words like "crisp", "bold", "robust")
- **Sweetness:** dry, off-dry, medium, or sweet
- **Acidity:** low, medium, or high (from "bright", "zesty", "smooth")
- **Tannin:** low, medium, or high (from "silky", "structured", "grippy")
- **Characteristics:** Unique descriptors (e.g., "elegant", "mineral", "complex")
- **Flavor Notes:** Actual flavors mentioned (e.g., "black cherry", "tobacco", "vanilla")

This ensures every Pinot Noir has its own unique profile based on Wine.com's tasting notes.

## File Structure

```
scrapers/
├── __init__.py                 # Package init
├── README.md                   # This file
├── scraper_config.py           # Configuration
├── wine_com_scraper.py         # Core scraping logic
├── data_enricher.py            # GPT-4 enrichment
└── run_scraper.py              # Main execution script
```

## Output Format

Generates `data/wines_catalog.json` with wines matching the Wine schema:

```json
[
  {
    "id": "wine_1705234567_0001",
    "name": "Justin Cabernet Sauvignon 2020",
    "producer": "Justin Vineyards",
    "vintage": 2020,
    "wine_type": "red",
    "varietal": "Cabernet Sauvignon",
    "country": "United States",
    "region": "Paso Robles",
    "body": "full",
    "sweetness": "dry",
    "acidity": "medium",
    "tannin": "high",
    "characteristics": ["bold", "structured", "oaky", "age-worthy"],
    "flavor_notes": ["blackberry", "cassis", "vanilla", "mocha", "cedar"],
    "description": "Full-bodied red wine from Cabernet Sauvignon...",
    "price_usd": 42.00,
    "rating": 4.3,
    "wine_com_url": "https://www.wine.com/product/..."
  }
]
```

## Legal Considerations

This scraper:
- Uses polite delays (2-5 seconds) to avoid overloading Wine.com
- Respects robots.txt guidelines
- Includes checkpoint/resume to minimize redundant requests
- Is for commercial use in the wine chatbot (not redistribution)

**Note:** User accepts responsibility for compliance with Wine.com's Terms of Service.

## Troubleshooting

### Scraper fails with 403 errors or CAPTCHA

**UPDATE:** Wine.com now uses Cloudflare CAPTCHA protection, which blocks simple HTTP requests. The working GitHub example we found is outdated.

**Solutions:**

1. **Use Playwright/Selenium (Recommended for large-scale scraping)**
   - Browser automation can handle JavaScript and may bypass some protections
   - See implementation plan in `/Users/shreyapatel/.claude/plans/logical-fluttering-newt.md`
   - Would require rewriting the scraper to use Playwright instead of requests

2. **Use a CAPTCHA-solving service**
   - Services like 2Captcha, Anti-Captcha can solve Cloudflare challenges
   - Adds cost (~$1-3 per 1000 CAPTCHAs)
   - Slower scraping (10-30 seconds per CAPTCHA)

3. **Alternative Data Sources (Recommended for MVP)**
   - **Kaggle Wine Datasets**: Free, no scraping needed, but may lack purchase links
   - **Vivino API**: May have public or partner access
   - **Wine-Searcher**: Different site, may have less protection
   - **Wine.com partnership**: Contact their business development for official API access

4. **Smaller manual dataset**
   - Manually curate 100-200 wines with GPT-4 to generate unique profiles
   - Faster path to MVP testing
   - Can expand later with proper data source

### GPT-4 enrichment failing

- Check OpenAI API key is set in `.env`
- Verify you have API credits
- Check for rate limits (scraper includes retry logic)

### Wines have no descriptions

- Wine.com may have changed their HTML structure
- Check CSS selectors in `wine_com_scraper.py`
- Update selectors in `_scrape_wine_detail()` method

### Checkpoint not resuming

- Ensure `data/scraped/checkpoint.json` exists
- Check file permissions
- Delete checkpoint to start fresh if corrupted

## Customization

### Target Specific Regions

Modify URL construction in `_scrape_listing_page()` to add region filters.

### Change Rating Threshold

Edit `MIN_RATING` in `scraper_config.py` (e.g., 4.0 for higher quality).

### Adjust Wine Type Distribution

Edit `WINE_TYPES_TO_SCRAPE` dictionary to change target counts per type.

## Support

For issues or questions, refer to the main project README or check Wine.com's website structure for changes.
