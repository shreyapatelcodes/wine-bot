"""
Wine Recommendation Engine
Powered by WSET Level 3 knowledge and vector semantic search.
"""

from .models import UserPreferences, SearchQuery, Wine, WineRecommendation
from .agents import get_wine_recommendations
from .config import Config

__version__ = "1.0.0"

__all__ = [
    "UserPreferences",
    "SearchQuery",
    "Wine",
    "WineRecommendation",
    "get_wine_recommendations",
    "Config"
]
