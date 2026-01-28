"""
Pydantic data models for the wine recommendation system.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """User input preferences for wine recommendations."""

    description: str = Field(
        ...,
        description="Natural language description of wine preferences or occasion"
    )
    budget_min: float = Field(
        default=10.0,
        ge=0,
        description="Minimum budget in USD"
    )
    budget_max: float = Field(
        default=200.0,
        ge=0,
        description="Maximum budget in USD"
    )
    food_pairing: Optional[str] = Field(
        default=None,
        description="Food to pair with wine (e.g., 'steak', 'seafood', 'pasta')"
    )
    wine_type_pref: Optional[str] = Field(
        default=None,
        description="Preferred wine type: 'red', 'white', 'rosé', or 'sparkling'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Bold red wine for a steak dinner",
                "budget_min": 40.0,
                "budget_max": 60.0,
                "food_pairing": "steak",
                "wine_type_pref": "red"
            }
        }


class SearchQuery(BaseModel):
    """Intermediate representation from Agent 1 to Agent 2."""

    query_text: str = Field(
        ...,
        description="Rich natural language description of ideal wine for semantic search"
    )
    price_range: tuple[float, float] = Field(
        ...,
        description="Price range (min, max) in USD"
    )
    wine_type_filter: Optional[str] = Field(
        default=None,
        description="Wine type filter: 'red', 'white', 'rosé', or 'sparkling'"
    )

    # Extended filters for better targeting
    region_filter: Optional[str] = Field(
        default=None,
        description="Specific wine region filter"
    )
    country_filter: Optional[str] = Field(
        default=None,
        description="Country of origin filter"
    )
    varietal_filter: Optional[str] = Field(
        default=None,
        description="Specific grape varietal filter"
    )
    occasion: Optional[str] = Field(
        default=None,
        description="Occasion context (dinner party, casual, celebration)"
    )

    # Preserved user request for better explanations
    user_request: Optional[str] = Field(
        default=None,
        description="Original user request (preserved for attribution)"
    )
    category_knowledge: Optional[str] = Field(
        default=None,
        description="WSET category knowledge (for explanations, not attribution)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query_text": "Full-bodied Cabernet Sauvignon from Napa Valley with high tannins and bold structure. Rich flavors of blackberry, cassis, and dark fruit with prominent oak influence showing vanilla and mocha notes. Dry with medium-plus acidity and firm tannins that pair excellently with grilled steak and aged cheeses.",
                "price_range": (40.0, 60.0),
                "wine_type_filter": "red",
                "region_filter": "Napa Valley",
                "user_request": "bold red wine for steak dinner",
                "category_knowledge": "Full-bodied red wines with high tannins pair well with red meat"
            }
        }


class Wine(BaseModel):
    """Wine product data model."""

    id: str = Field(..., description="Unique wine identifier")
    name: str = Field(..., description="Wine name")
    producer: str = Field(..., description="Wine producer/winery")
    vintage: Optional[int] = Field(None, description="Wine vintage year")
    wine_type: str = Field(..., description="Wine type: red, white, rosé, sparkling")
    varietal: str = Field(..., description="Primary grape varietal")
    country: str = Field(..., description="Country of origin")
    region: str = Field(..., description="Wine region")
    body: str = Field(..., description="Wine body: light, medium, full")
    sweetness: str = Field(..., description="Sweetness level: dry, off-dry, medium, sweet")
    acidity: str = Field(..., description="Acidity level: low, medium, high")
    tannin: Optional[str] = Field(None, description="Tannin level: low, medium, high (for reds)")
    characteristics: List[str] = Field(..., description="Wine characteristics")
    flavor_notes: List[str] = Field(..., description="Flavor notes and aromas")
    description: str = Field(..., description="Full wine description for embeddings")
    price_usd: float = Field(..., description="Price in USD")
    rating: Optional[float] = Field(None, description="Rating out of 5")
    vivino_url: str = Field(..., description="Vivino search URL")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "wine_001",
                "name": "Justin Cabernet Sauvignon",
                "producer": "Justin Vineyards",
                "vintage": 2020,
                "wine_type": "red",
                "varietal": "Cabernet Sauvignon",
                "country": "USA",
                "region": "Paso Robles",
                "body": "full",
                "sweetness": "dry",
                "acidity": "medium",
                "tannin": "high",
                "characteristics": ["bold", "structured", "fruity", "oaky"],
                "flavor_notes": ["blackberry", "cassis", "vanilla", "mocha"],
                "description": "Full-bodied Cabernet Sauvignon from Paso Robles with high tannins and bold structure...",
                "price_usd": 42.00,
                "rating": 4.3,
                "vivino_url": "https://www.vivino.com/en/search/wines?q=Justin+Cabernet+Sauvignon+2020"
            }
        }


class WineRecommendation(BaseModel):
    """Final wine recommendation output with explanation."""

    wine: Wine = Field(..., description="Wine product details")
    explanation: str = Field(
        ...,
        description="Personalized 1-2 sentence explanation for recommendation"
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Vector similarity score (0-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "wine": {
                    "id": "wine_001",
                    "name": "Justin Cabernet Sauvignon",
                    "producer": "Justin Vineyards",
                    "price_usd": 42.00,
                    # ... other wine fields
                },
                "explanation": "This full-bodied Paso Robles Cabernet delivers the bold, structured character you're looking for with rich blackberry and oak notes that complement grilled steak perfectly.",
                "relevance_score": 0.87
            }
        }
