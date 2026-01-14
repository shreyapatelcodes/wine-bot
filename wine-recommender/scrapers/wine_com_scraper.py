"""Wine.com web scraper using requests + BeautifulSoup."""

import json
import random
import re
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .scraper_config import ScraperConfig


class WineComScraper:
    """Scraper for Wine.com product data."""

    def __init__(self, config: ScraperConfig = None, output_dir: Path = None):
        """
        Initialize the Wine.com scraper.

        Args:
            config: Scraper configuration (uses ScraperConfig if None)
            output_dir: Directory for output files (defaults to ../data/scraped)
        """
        self.config = config or ScraperConfig()
        self.output_dir = output_dir or (Path(__file__).parent.parent / "data" / "scraped")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.wines_scraped = []
        self.checkpoint_file = self.output_dir / "checkpoint.json"
        self.session = requests.Session()

    def scrape_all(self) -> List[Dict]:
        """
        Main scraping method - scrapes all wine types up to MAX_WINES.

        Returns:
            List of scraped wine dictionaries
        """
        print(f"Starting Wine.com scraper (target: {self.config.MAX_WINES} wines)")

        # Load checkpoint if exists
        self._load_checkpoint()

        total_target = self.config.MAX_WINES
        wines_needed = total_target - len(self.wines_scraped)

        if wines_needed <= 0:
            print(f"Already have {len(self.wines_scraped)} wines, nothing to scrape!")
            return self.wines_scraped

        print(f"Resuming from {len(self.wines_scraped)} wines, need {wines_needed} more")

        # Scrape each wine type
        for wine_type, target_count in self.config.WINE_TYPES_TO_SCRAPE.items():
            if len(self.wines_scraped) >= total_target:
                break

            print(f"\n--- Scraping {wine_type} wines (target: {target_count}) ---")
            self._scrape_wine_type(wine_type, target_count)

        print(f"\n✅ Scraping complete! Total wines: {len(self.wines_scraped)}")
        return self.wines_scraped

    def _scrape_wine_type(self, wine_type: str, target_count: int):
        """
        Scrape wines of a specific type.

        Args:
            wine_type: Type of wine (red, white, sparkling, rose)
            target_count: Target number of wines to scrape for this type
        """
        page_num = 1
        wines_of_type = 0
        max_pages = (target_count // self.config.WINES_PER_PAGE) + 5  # Add buffer

        while wines_of_type < target_count and page_num <= max_pages:
            if len(self.wines_scraped) >= self.config.MAX_WINES:
                break

            print(f"  Page {page_num}...", end=" ", flush=True)

            # Scrape listing page
            wines = self._scrape_listing_page(wine_type, page_num)

            if not wines:
                print("(no more wines)")
                break

            print(f"found {len(wines)} wines")

            # Process each wine
            for wine_data in wines:
                if wines_of_type >= target_count or len(self.wines_scraped) >= self.config.MAX_WINES:
                    break

                # Scrape detail page for full description
                wine_url = wine_data.get("wine_com_url")
                if wine_url:
                    description = self._scrape_wine_detail(wine_url)
                    if description:
                        wine_data["description"] = description
                        wine_data["wine_type"] = wine_type

                        # Validate required fields
                        if self._validate_wine(wine_data):
                            self.wines_scraped.append(wine_data)
                            wines_of_type += 1

                            # Checkpoint
                            if len(self.wines_scraped) % self.config.CHECKPOINT_INTERVAL == 0:
                                self._save_checkpoint()
                                print(f"    ✓ Checkpoint: {len(self.wines_scraped)} wines saved")

                    # Politeness delay
                    time.sleep(random.uniform(*self.config.DELAY_BETWEEN_REQUESTS))

            page_num += 1

        print(f"  Collected {wines_of_type} {wine_type} wines")

    def _scrape_listing_page(self, wine_type: str, page_num: int) -> List[Dict]:
        """
        Scrape a listing page for basic wine info.

        Args:
            wine_type: Type of wine
            page_num: Page number to scrape

        Returns:
            List of wine dictionaries with basic info
        """
        # Construct URL (based on working example)
        if page_num == 1:
            url = f"{self.config.BASE_URL}/list/wine/{self.config.WINE_CATEGORY_ID}?ratingmin={self.config.MIN_RATING}"
        else:
            url = f"{self.config.BASE_URL}/list/wine/{self.config.WINE_CATEGORY_ID}/{page_num}?ratingmin={self.config.MIN_RATING}"

        # Add wine type filter if needed
        # Note: May need to adjust based on Wine.com's actual filter parameters

        try:
            headers = {
                "User-Agent": random.choice(self.config.USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0"
            }
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")
            wines = []

            # Find all wine product items
            product_items = soup.find_all("li", class_="prodItem")

            for item in product_items:
                wine_data = self._extract_wine_data(item)
                if wine_data:
                    wines.append(wine_data)

            return wines

        except requests.RequestException as e:
            print(f"\n  Error scraping listing page {page_num}: {e}")
            return []

    def _extract_wine_data(self, item) -> Optional[Dict]:
        """
        Extract wine data from a product item.

        Args:
            item: BeautifulSoup element for a product

        Returns:
            Dictionary of wine data or None
        """
        try:
            # Extract basic fields using CSS selectors from working example
            name_elem = item.find("span", class_="prodItemInfo_name")
            price_elem = item.find("span", class_="productPrice_price-regWhole")
            varietal_elem = item.find("span", class_="prodItemInfo_varietal")
            origin_elem = item.find("span", class_="prodItemInfo_originText")
            rating_elem = item.find("span", class_="averageRating_average")

            # Extract product URL
            link_elem = item.find("a", class_="prodItemInfo_link")
            wine_url = None
            if link_elem and link_elem.get("href"):
                wine_url = urljoin(self.config.BASE_URL, link_elem["href"])

            # Parse fields
            name = name_elem.string.strip() if name_elem and name_elem.string else None
            price = self._parse_price(price_elem)
            varietal = varietal_elem.string.strip() if varietal_elem and varietal_elem.string else None
            origin = origin_elem.string.strip() if origin_elem and origin_elem.string else None
            rating = self._parse_rating(rating_elem)

            if not name or not price or not wine_url:
                return None

            # Parse producer and vintage from name
            producer, vintage = self._parse_producer_and_vintage(name)

            # Parse country and region from origin
            country, region = self._parse_origin(origin)

            return {
                "name": name,
                "producer": producer,
                "vintage": vintage,
                "varietal": varietal,
                "country": country,
                "region": region,
                "price_usd": price,
                "rating": rating,
                "wine_com_url": wine_url
            }

        except Exception as e:
            print(f"\n  Error extracting wine data: {e}")
            return None

    def _scrape_wine_detail(self, wine_url: str) -> Optional[str]:
        """
        Scrape wine detail page for full description.

        Args:
            wine_url: URL of the wine product page

        Returns:
            Wine description string or None
        """
        try:
            headers = {
                "User-Agent": random.choice(self.config.USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            response = self.session.get(wine_url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")

            # Try multiple possible selectors for description
            description = None
            selectors = [
                ("div", {"class": "viewFullDescription"}),
                ("div", {"class": "product-description"}),
                ("div", {"class": "pipDescription"}),
                ("div", {"class": "productFullDesc"}),
                ("p", {"class": "tastingNotes"}),
                ("div", {"itemprop": "description"}),
            ]

            for tag, attrs in selectors:
                elem = soup.find(tag, attrs)
                if elem:
                    # Extract text, removing extra whitespace
                    text = elem.get_text(separator=" ", strip=True)
                    if text and len(text) > 50:  # Ensure it's substantive
                        description = text
                        break

            return description

        except requests.RequestException as e:
            print(f"\n  Error scraping detail page {wine_url}: {e}")
            return None

    def _parse_price(self, price_elem) -> Optional[float]:
        """Parse price from element."""
        if not price_elem or not price_elem.string:
            return None
        try:
            # Remove $ and commas, convert to float
            price_str = price_elem.string.strip().replace("$", "").replace(",", "")
            return float(price_str)
        except (ValueError, AttributeError):
            return None

    def _parse_rating(self, rating_elem) -> Optional[float]:
        """Parse rating from element."""
        if not rating_elem or not rating_elem.string:
            return None
        try:
            return float(rating_elem.string.strip())
        except (ValueError, AttributeError):
            return None

    def _parse_producer_and_vintage(self, name: str) -> tuple[Optional[str], Optional[int]]:
        """
        Parse producer and vintage from wine name.

        Args:
            name: Full wine name

        Returns:
            Tuple of (producer, vintage)
        """
        # Extract vintage year (4-digit year)
        vintage_match = re.search(r'\b(19\d{2}|20\d{2})\b', name)
        vintage = int(vintage_match.group(1)) if vintage_match else None

        # Producer is typically first part before wine name/varietal
        # Simplified: take first 1-2 words
        parts = name.split()
        if len(parts) >= 2:
            producer = " ".join(parts[:2])
        elif len(parts) == 1:
            producer = parts[0]
        else:
            producer = name

        return producer, vintage

    def _parse_origin(self, origin: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse country and region from origin string.

        Args:
            origin: Origin string (e.g., "Napa Valley, California")

        Returns:
            Tuple of (country, region)
        """
        if not origin:
            return None, None

        # Simple heuristic: if contains known US regions, country is USA
        us_states = [
            "California", "Oregon", "Washington", "New York", "Texas",
            "Virginia", "Napa", "Sonoma", "Paso Robles", "Willamette"
        ]

        country = None
        region = origin

        # Check if it's a US wine
        if any(state in origin for state in us_states):
            country = "United States"
        else:
            # Split by comma - often format is "Region, Country"
            parts = [p.strip() for p in origin.split(",")]
            if len(parts) >= 2:
                region = parts[0]
                country = parts[-1]
            else:
                country = origin
                region = origin

        return country, region

    def _validate_wine(self, wine_data: Dict) -> bool:
        """
        Validate that wine has required fields.

        Args:
            wine_data: Wine dictionary

        Returns:
            True if valid, False otherwise
        """
        # Must have description for GPT-4 enrichment
        if not wine_data.get("description"):
            return False

        # Check other required fields
        for field in self.config.REQUIRED_FIELDS:
            if not wine_data.get(field):
                return False

        return True

    def _save_checkpoint(self):
        """Save progress checkpoint."""
        checkpoint = {
            "total_wines": len(self.wines_scraped),
            "timestamp": time.time(),
            "wines": self.wines_scraped
        }
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)

    def _load_checkpoint(self):
        """Load progress from checkpoint if exists."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    checkpoint = json.load(f)
                    self.wines_scraped = checkpoint.get("wines", [])
                    print(f"Loaded checkpoint: {len(self.wines_scraped)} wines")
            except Exception as e:
                print(f"Error loading checkpoint: {e}")
