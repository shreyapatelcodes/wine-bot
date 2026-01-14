"""Data enricher using GPT-4 to extract subjective wine attributes from descriptions."""

import json
import sys
import time
from pathlib import Path
from typing import Dict

from openai import OpenAI

# Add parent directory to path to import from wine-recommender
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.schemas import Wine
from config import Config


class WineDataEnricher:
    """Enriches scraped wine data with GPT-4 extracted attributes."""

    def __init__(self):
        """Initialize the data enricher with OpenAI client."""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.wine_counter = 0

    def enrich_wine_data(self, scraped_wine: Dict) -> Wine:
        """
        Enrich scraped wine data with GPT-4 extracted subjective attributes.

        Args:
            scraped_wine: Dictionary with basic scraped data

        Returns:
            Wine Pydantic model with all fields populated

        Raises:
            ValueError: If required fields are missing or enrichment fails
        """
        # Validate required scraped fields
        required_fields = ["name", "wine_com_url", "description"]
        for field in required_fields:
            if not scraped_wine.get(field):
                raise ValueError(f"Missing required field: {field}")

        # Extract subjective attributes using GPT-4
        subjective_attrs = self._extract_subjective_attributes(
            name=scraped_wine.get("name", ""),
            producer=scraped_wine.get("producer", ""),
            varietal=scraped_wine.get("varietal", "Unknown"),
            origin=scraped_wine.get("region", scraped_wine.get("country", "")),
            description=scraped_wine["description"],
            wine_type=scraped_wine.get("wine_type", "")
        )

        # Generate unique ID
        self.wine_counter += 1
        timestamp = int(time.time())
        wine_id = f"wine_{timestamp}_{self.wine_counter:04d}"

        # Build full description for embeddings
        full_description = self._build_full_description(scraped_wine, subjective_attrs)

        # Create Wine model
        wine = Wine(
            id=wine_id,
            name=scraped_wine["name"],
            producer=scraped_wine.get("producer") or self._extract_producer_fallback(scraped_wine["name"]),
            vintage=scraped_wine.get("vintage"),
            wine_type=scraped_wine.get("wine_type", "red"),
            varietal=scraped_wine.get("varietal") or "Unknown",
            country=scraped_wine.get("country") or "Unknown",
            region=scraped_wine.get("region") or scraped_wine.get("country", "Unknown"),
            body=subjective_attrs["body"],
            sweetness=subjective_attrs["sweetness"],
            acidity=subjective_attrs["acidity"],
            tannin=subjective_attrs.get("tannin"),
            characteristics=subjective_attrs["characteristics"],
            flavor_notes=subjective_attrs["flavor_notes"],
            description=full_description,
            price_usd=scraped_wine.get("price_usd") or 0.0,
            rating=scraped_wine.get("rating"),
            wine_com_url=scraped_wine["wine_com_url"]
        )

        return wine

    def _extract_subjective_attributes(
        self,
        name: str,
        producer: str,
        varietal: str,
        origin: str,
        description: str,
        wine_type: str
    ) -> Dict:
        """
        Use GPT-4 to extract subjective wine attributes from description.

        Args:
            name: Wine name
            producer: Producer/winery
            varietal: Grape varietal
            origin: Region/country
            description: Full wine description
            wine_type: Wine type (red, white, etc.)

        Returns:
            Dictionary with subjective attributes
        """
        prompt = f"""Analyze this specific wine based ONLY on its description. Extract the unique characteristics mentioned or implied in the text:

Wine: {name}
Producer: {producer}
Varietal: {varietal}
Region: {origin}

Description from Wine.com:
"{description}"

Extract in JSON format based SOLELY on the description above:
1. body: "light", "medium", or "full" - look for words like "light", "crisp", "bold", "robust", "full-bodied"
2. sweetness: "dry", "off-dry", "medium", or "sweet" - look for mentions of sweetness, residual sugar, or dry/crisp
3. acidity: "low", "medium", or "high" - look for "bright", "crisp", "zesty", "refreshing" (high), "smooth", "soft" (low)
4. tannin: "low", "medium", "high" (reds only, null for whites) - look for "silky", "velvety" (low), "structured", "grippy" (high)
5. characteristics: array of 3-5 unique descriptors extracted from the description ["elegant", "complex", "mineral"]
6. flavor_notes: array of 4-7 specific flavors/aromas mentioned in the description ["black cherry", "tobacco", "leather"]

CRITICAL: Extract characteristics that make THIS wine unique. Do not use generic varietal defaults. If the description says "bright acidity", mark acidity as high. If it says "silky tannins", mark tannin as low. Extract actual flavor notes mentioned.

Return ONLY valid JSON with these exact keys: body, sweetness, acidity, tannin, characteristics, flavor_notes."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional sommelier analyzing wine characteristics. Return only valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Validate and set defaults if needed
            result["body"] = result.get("body", "medium")
            result["sweetness"] = result.get("sweetness", "dry")
            result["acidity"] = result.get("acidity", "medium")

            # Tannin: null for whites, otherwise extract
            if wine_type in ["white", "sparkling"]:
                result["tannin"] = None
            else:
                result["tannin"] = result.get("tannin", "medium")

            result["characteristics"] = result.get("characteristics", ["balanced", "food-friendly"])
            result["flavor_notes"] = result.get("flavor_notes", ["fruit", "spice"])

            return result

        except Exception as e:
            print(f"\n  Warning: GPT-4 enrichment failed for {name}: {e}")
            # Retry once
            try:
                time.sleep(2)
                return self._extract_subjective_attributes(
                    name, producer, varietal, origin, description, wine_type
                )
            except Exception:
                # Final fallback: minimal defaults
                return {
                    "body": "medium",
                    "sweetness": "dry",
                    "acidity": "medium",
                    "tannin": "medium" if wine_type == "red" else None,
                    "characteristics": ["balanced", "classic"],
                    "flavor_notes": ["fruit", "oak"]
                }

    def _build_full_description(self, scraped_wine: Dict, subjective_attrs: Dict) -> str:
        """
        Build full description for embeddings by combining scraped data and enriched attributes.

        Args:
            scraped_wine: Original scraped data
            subjective_attrs: GPT-4 extracted attributes

        Returns:
            Full description string
        """
        wine_type = scraped_wine.get("wine_type", "wine")
        varietal = scraped_wine.get("varietal", "")
        region = scraped_wine.get("region", scraped_wine.get("country", ""))
        original_desc = scraped_wine.get("description", "")

        # Build enhanced description
        body = subjective_attrs["body"]
        sweetness = subjective_attrs["sweetness"]
        acidity = subjective_attrs["acidity"]
        tannin = subjective_attrs.get("tannin")
        characteristics = ", ".join(subjective_attrs["characteristics"])
        flavors = ", ".join(subjective_attrs["flavor_notes"])

        # Construct full description
        full_desc = f"{body.capitalize()}-bodied {wine_type} wine"
        if varietal:
            full_desc += f" from {varietal}"
        if region:
            full_desc += f" in {region}"

        full_desc += f". {sweetness.capitalize()} with {acidity} acidity"
        if tannin:
            full_desc += f" and {tannin} tannins"

        full_desc += f". Characteristics: {characteristics}. "
        full_desc += f"Flavor notes: {flavors}. "
        full_desc += original_desc

        return full_desc

    def _extract_producer_fallback(self, name: str) -> str:
        """
        Fallback method to extract producer from name.

        Args:
            name: Wine name

        Returns:
            Producer name
        """
        # Take first 1-2 words as producer
        parts = name.split()
        if len(parts) >= 2:
            return " ".join(parts[:2])
        return parts[0] if parts else "Unknown"
