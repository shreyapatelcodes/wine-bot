"""Configuration for Wine.com scraper."""


class ScraperConfig:
    """Configuration parameters for the Wine.com scraper."""

    # Wine.com base URL and category
    BASE_URL = "https://www.wine.com"
    WINE_CATEGORY_ID = "7155"  # Main wine category

    # Scraping parameters
    MAX_WINES = 5000
    WINES_PER_PAGE = 24  # Wine.com default
    DELAY_BETWEEN_REQUESTS = (2, 5)  # seconds (min, max)

    # Quality filters
    MIN_RATING = 3.5  # Only wines with 3.5+ rating
    REQUIRED_FIELDS = ["name", "price_usd", "wine_type", "country"]

    # Wine type filters for diversity
    WINE_TYPES_TO_SCRAPE = {
        "red": 2000,      # Target 2000 red wines
        "white": 1500,    # Target 1500 white wines
        "sparkling": 750, # Target 750 sparkling
        "rose": 750       # Target 750 rosé
    }

    # Checkpoint settings
    CHECKPOINT_INTERVAL = 50  # Save progress every N wines

    # User agent rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
