# Kaggle Wine Dataset Import Guide

Since Wine.com has Cloudflare CAPTCHA protection, we'll use the Kaggle wine dataset as an alternative source.

## Dataset Information

**Source:** https://www.kaggle.com/datasets/elvinrustam/wine-dataset

**Included Data:**
- ✅ Wine names and descriptions
- ✅ Characteristics (flavor notes, tasting notes)
- ✅ Pricing
- ✅ Grape varieties
- ✅ Countries and regions
- ✅ Vintage years
- ✅ Wine styles and types

**Advantages:**
- No scraping needed
- No CAPTCHA challenges
- Free and legal (CC0 Public Domain)
- ~4,700+ downloads, proven dataset
- Rich descriptions for GPT-4 enrichment

**Limitations:**
- No direct Wine.com purchase links (we'll generate search links instead)
- No ratings (can add later or generate based on price/region)
- May have fewer wines than scraping would yield

## Step-by-Step Instructions

### 1. Download the Dataset

**Option A: Kaggle Website (Easiest)**
1. Go to https://www.kaggle.com/datasets/elvinrustam/wine-dataset
2. Click the "Download" button (requires free Kaggle account)
3. Extract the ZIP file
4. You'll get a CSV file (e.g., `wine_dataset.csv`)

**Option B: Kaggle CLI (For Power Users)**
```bash
# Install Kaggle CLI
pip install kaggle

# Configure API credentials (get from kaggle.com/settings)
mkdir ~/.kaggle
# Download kaggle.json from your Kaggle account settings
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Download dataset
kaggle datasets download -d elvinrustam/wine-dataset
unzip wine-dataset.zip
```

### 2. Place the CSV File

Move the CSV file to your project:

```bash
cd /Users/shreyapatel/Desktop/Code/wine-ai-chatbot/wine-recommender
mkdir -p data/kaggle
mv ~/Downloads/wine_dataset.csv data/kaggle/
```

### 3. Run the Importer

```bash
cd scrapers
python kaggle_importer.py
```

This will:
1. Load the Kaggle CSV
2. Convert to our Wine schema format
3. Use GPT-4 to enrich with subjective attributes (body, sweetness, acidity, etc.)
4. Generate `data/wines_catalog.json`

**Estimated time:**
- Processing: 1-2 minutes
- GPT-4 enrichment: 10-20 minutes for 1,000 wines

**Cost:** ~$0.30-0.50 for GPT-4o-mini enrichment

### 4. Upload to Pinecone

```bash
cd ../data
python seed_vector_db.py
```

### 5. Test the Chatbot

```bash
cd ../..
streamlit run wine_chatbot_ui.py
```

## What the Importer Does

### Data Processing Pipeline

1. **Load CSV** - Reads Kaggle dataset
2. **Field Mapping:**
   - Title → name
   - Grape → varietal
   - Description + Characteristics → description
   - Price → price_usd
   - Country/Region → country/region
   - Type → wine_type (red/white/sparkling/rosé)
   - Vintage → vintage

3. **GPT-4 Enrichment:**
   - Analyzes wine descriptions
   - Extracts unique characteristics for each wine
   - Generates body, sweetness, acidity, tannin levels
   - Identifies flavor notes and characteristics
   - **No generic defaults** - each wine gets unique profile

4. **Output:**
   - `data/wines_catalog.json` - Ready for Pinecone upload
   - Compatible with existing vector_store.py loader

## Customization

### Limit Number of Wines

Edit `kaggle_importer.py` line ~200:

```python
processed_wines = importer.process_wines(df, max_wines=1000)  # Change to desired count
```

### Filter by Wine Type

Add filtering before processing:

```python
# Only import red wines
df = df[df['Type'].str.contains('red', case=False, na=False)]
```

### Adjust Price Range

Add price filtering:

```python
# Only wines $10-$100
df = df[(df['Price'] >= 10) & (df['Price'] <= 100)]
```

## Troubleshooting

### "No CSV files found"

Make sure you:
1. Downloaded the dataset from Kaggle
2. Extracted the ZIP file
3. Placed the CSV in `wine-recommender/data/kaggle/`

### "Missing required field: description"

Some wines may lack descriptions. The importer skips these automatically. This is expected and ensures quality.

### GPT-4 enrichment errors

- Check `.env` has valid `OPENAI_API_KEY`
- Verify you have API credits
- Check internet connection

### Empty wine_catalog.json

- Check the CSV file isn't corrupted
- Look for error messages during processing
- Try with `max_wines=10` to test

## Comparison: Kaggle vs. Wine.com Scraping

| Aspect | Kaggle Dataset | Wine.com Scraping |
|--------|---------------|-------------------|
| **Setup Time** | 5 minutes | Hours (Playwright needed) |
| **Data Quality** | Good descriptions | Excellent, current |
| **Purchase Links** | Generic search links | Direct Wine.com URLs |
| **Legal Risk** | Zero (Public Domain) | ToS compliance |
| **Maintenance** | One-time import | Requires re-scraping |
| **Cost** | ~$0.50 (GPT-4) | ~$1.50 + potential CAPTCHA |
| **Scalability** | Limited by dataset size | Scales to Wine.com catalog |

## Recommended Workflow

**For MVP/Testing:**
1. Use Kaggle dataset (fast, legal, good quality)
2. Test your chatbot with real users
3. Validate the recommendation system works

**For Production:**
1. Start with Kaggle data
2. Pursue Wine.com partnership for official API access
3. Or explore other wine retailers with less protection
4. Gradually expand dataset with proper data sources

## Next Steps After Import

Once you have `wines_catalog.json`:

1. **Validate the data:**
   ```bash
   cd data
   python -c "import json; wines = json.load(open('wines_catalog.json')); print(f'Loaded {len(wines)} wines')"
   ```

2. **Upload to Pinecone:**
   ```bash
   python seed_vector_db.py
   ```

3. **Test recommendations:**
   ```bash
   streamlit run wine_chatbot_ui.py
   ```

4. **Monitor quality:**
   - Try diverse queries (cheap wines, expensive wines, specific regions)
   - Check if recommendations feel relevant
   - Verify Wine.com search links work

## Support

If you encounter issues:
1. Check this guide's Troubleshooting section
2. Review error messages in console
3. Verify Kaggle CSV format matches expected columns
4. Test with small batch first (`max_wines=10`)
