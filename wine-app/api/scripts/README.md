# Wine Database Sync Scripts

Scripts for syncing wines from Kaggle dataset to PostgreSQL.

## Option 1: Load from CSV (Recommended)

If you have the Kaggle CSV file, this is the most efficient approach:

```bash
# From the api directory
python scripts/load_wines_from_csv.py /path/to/kaggle_wines.csv

# With custom batch size
python scripts/load_wines_from_csv.py /path/to/kaggle_wines.csv --batch-size 1000
```

**Expected CSV format:**
- `name` - Wine name (required)
- `producer` or `winery` - Producer name
- `vintage` or `year` - Vintage year
- `wine_type` or `type` - Wine type (red, white, rosé, sparkling)
- `varietal`, `variety`, or `grape` - Grape varietal
- `country` - Country of origin
- `region` - Wine region
- `price` or `price_usd` - Price in USD
- Any additional columns will be stored in `wine_metadata`

## Option 2: Sync from Pinecone

If you don't have the CSV but wines are already in Pinecone:

```bash
# From the api directory
python scripts/sync_wines_from_pinecone.py

# With custom batch size
python scripts/sync_wines_from_pinecone.py --batch-size 200
```

**Note:** This method can only fetch up to 10,000 wines due to Pinecone query limits.

## After Loading

Once wines are loaded, you can simplify the save/cellar endpoints by removing the Pinecone fallback logic since all wines will be in PostgreSQL.

## Verifying the Data

Check how many wines were loaded:

```bash
# Using psql
psql $DATABASE_URL -c "SELECT COUNT(*) FROM wines;"

# See sample wines
psql $DATABASE_URL -c "SELECT id, name, producer, wine_type, price_usd FROM wines LIMIT 10;"
```
