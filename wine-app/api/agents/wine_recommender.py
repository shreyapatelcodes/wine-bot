"""
Wine Recommendation Engine - Two-agent pipeline for wine recommendations.
Copied from wine-recommender project for standalone deployment.

Pipeline:
  User Input → Agent 1 (Preference Interpreter) → Agent 2 (Wine Searcher) → Recommendations
"""

import json
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from config import Config
from utils.embeddings import (
    search_wset_knowledge,
    search_wine_products,
    get_openai_client
)
from utils.prompts import (
    AGENT1_SYSTEM_PROMPT,
    create_agent1_user_prompt,
    create_agent2_explanation_prompt
)


# =============================================================================
# Data Models
# =============================================================================

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


class SearchQuery(BaseModel):
    """Intermediate representation from Agent 1 to Agent 2."""

    query_text: str = Field(
        ...,
        description="Rich natural language description of ideal wine for semantic search"
    )
    price_range: tuple = Field(
        ...,
        description="Price range (min, max) in USD"
    )
    wine_type_filter: Optional[str] = Field(
        default=None,
        description="Wine type filter: 'red', 'white', 'rosé', or 'sparkling'"
    )
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
    user_request: Optional[str] = Field(
        default=None,
        description="Original user request (preserved for attribution)"
    )
    category_knowledge: Optional[str] = Field(
        default=None,
        description="WSET category knowledge (for explanations, not attribution)"
    )


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
    characteristics: List[str] = Field(default_factory=list, description="Wine characteristics")
    flavor_notes: List[str] = Field(default_factory=list, description="Flavor notes and aromas")
    description: str = Field(default="", description="Full wine description for embeddings")
    price_usd: float = Field(..., description="Price in USD")
    rating: Optional[float] = Field(None, description="Rating out of 5")
    vivino_url: str = Field(default="", description="Vivino search URL")


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


# =============================================================================
# Agent 1: Preference Interpreter
# =============================================================================

# Filter extraction prompt
FILTER_EXTRACTION_PROMPT = """Extract wine filters from this request. Return ONLY valid JSON.

Request: {request}

Extract these fields (use null if not mentioned):
- price_min: number (e.g., "over $30" -> 30)
- price_max: number (e.g., "under $40" -> 40, "around $50" -> 60)
- wine_type: "red", "white", "rosé", or "sparkling"
- region: specific wine region (e.g., "Napa Valley", "Bordeaux")
- country: country name
- varietal: grape variety (e.g., "Cabernet Sauvignon", "Pinot Noir")
- food_pairing: food mentioned (e.g., "steak", "seafood")
- occasion: event type (e.g., "dinner party", "casual", "celebration")
- characteristics: list of descriptors (e.g., ["bold", "fruity", "crisp"])

Price rules:
- "cheap" -> price_max: 20
- "affordable" -> price_max: 30
- "nice bottle" -> price_min: 30, price_max: 60
- "splurge" or "special occasion" -> price_min: 50

Return JSON only:"""


class PreferenceInterpreter:
    """
    Agent 1: Interprets user preferences using WSET knowledge to generate search queries.
    """

    def __init__(self):
        self.client = get_openai_client()

    def extract_filters(self, user_request: str) -> Dict[str, Any]:
        """Extract structured filters from natural language request."""
        prompt = FILTER_EXTRACTION_PROMPT.format(request=user_request)

        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "Extract filters. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                filters = json.loads(json_match.group())
                return {k: v for k, v in filters.items() if v is not None}

        except Exception as e:
            print(f"Filter extraction error: {e}")

        return {}

    def interpret(self, user_prefs: UserPreferences, verbose: bool = False) -> SearchQuery:
        """
        Interpret user preferences and generate a rich search query.

        Args:
            user_prefs: User's wine preferences
            verbose: If True, print debugging information

        Returns:
            SearchQuery object with query_text, price_range, and wine_type_filter
        """
        # Step 0: Extract filters from natural language
        extracted_filters = self.extract_filters(user_prefs.description)

        if verbose:
            print(f"\n[Agent 1] Extracted filters: {extracted_filters}")

        # Step 1: Query WSET knowledge for relevant wine information
        wset_query = self._build_wset_query(user_prefs)
        wset_chunks = search_wset_knowledge(wset_query, top_k=3)

        if verbose:
            print(f"\n[Agent 1] WSET Query: {wset_query}")
            print(f"[Agent 1] Retrieved {len(wset_chunks)} WSET chunks")

        # Step 2: Build context from WSET chunks
        wset_context = self._format_wset_context(wset_chunks)

        # Step 3: Generate rich search query using LLM
        query_text = self._generate_search_query(
            user_prefs.description,
            wset_context,
            user_prefs.food_pairing
        )

        if verbose:
            print(f"\n[Agent 1] Generated Search Query:\n{query_text}\n")

        # Step 4: Merge explicit filters with extracted filters
        price_min = user_prefs.budget_min
        price_max = user_prefs.budget_max

        if extracted_filters.get("price_min") and price_min == 10.0:
            price_min = extracted_filters["price_min"]
        if extracted_filters.get("price_max") and price_max == 200.0:
            price_max = extracted_filters["price_max"]

        wine_type = user_prefs.wine_type_pref or extracted_filters.get("wine_type")

        # Step 5: Build SearchQuery object
        search_query = SearchQuery(
            query_text=query_text,
            price_range=(price_min, price_max),
            wine_type_filter=wine_type,
            region_filter=extracted_filters.get("region"),
            country_filter=extracted_filters.get("country"),
            varietal_filter=extracted_filters.get("varietal"),
            occasion=extracted_filters.get("occasion"),
            user_request=user_prefs.description,
            category_knowledge=wset_context[:500] if wset_context else None
        )

        return search_query

    def _build_wset_query(self, user_prefs: UserPreferences) -> str:
        """Build a query for WSET knowledge base."""
        query_parts = [user_prefs.description]

        if user_prefs.food_pairing:
            query_parts.append(f"food pairing with {user_prefs.food_pairing}")

        if user_prefs.wine_type_pref:
            query_parts.append(f"{user_prefs.wine_type_pref} wine characteristics")

        return " ".join(query_parts)

    def _format_wset_context(self, chunks: list) -> str:
        """Format WSET knowledge chunks into context string."""
        context_parts = []
        for chunk in chunks:
            context_parts.append(f"Section: {chunk['heading']}\n{chunk['text']}")
        return "\n\n".join(context_parts)

    def _generate_search_query(
        self,
        user_description: str,
        wset_context: str,
        food_pairing: str = None
    ) -> str:
        """Generate rich search query text using LLM with WSET context."""
        user_prompt = create_agent1_user_prompt(
            user_description,
            wset_context,
            food_pairing
        )

        response = self.client.chat.completions.create(
            model=Config.OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": AGENT1_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()


# =============================================================================
# Agent 2: Wine Searcher
# =============================================================================

class WineSearcher:
    """
    Agent 2: Searches wine products using semantic similarity and generates recommendations.
    """

    def __init__(self):
        self.client = get_openai_client()

    def search(
        self,
        search_query: SearchQuery,
        user_prefs_description: str,
        top_n: int = 3,
        verbose: bool = False
    ) -> List[WineRecommendation]:
        """
        Search for wines matching the search query and generate recommendations.

        Args:
            search_query: SearchQuery from Agent 1
            user_prefs_description: Original user preferences for explanation generation
            top_n: Number of recommendations to return
            verbose: Enable verbose output

        Returns:
            List of WineRecommendation objects with explanations
        """
        price_min, price_max = search_query.price_range

        matches = search_wine_products(
            query_text=search_query.query_text,
            price_min=price_min,
            price_max=price_max,
            wine_type=search_query.wine_type_filter,
            top_k=top_n * 2
        )

        if verbose:
            print(f"\n[Agent 2] Vector search returned {len(matches)} wines")

        if not matches:
            return []

        recommendations = []
        user_request = getattr(search_query, 'user_request', None) or user_prefs_description
        category_knowledge = getattr(search_query, 'category_knowledge', None)

        for match in matches[:top_n]:
            wine = self._match_to_wine(match)

            explanation = self._generate_explanation(
                user_prefs_description,
                search_query.query_text,
                wine,
                user_request=user_request,
                category_knowledge=category_knowledge
            )

            recommendation = WineRecommendation(
                wine=wine,
                explanation=explanation,
                relevance_score=match['score']
            )
            recommendations.append(recommendation)

            if verbose:
                print(f"\n[Agent 2] Recommendation: {wine.name} (score: {match['score']:.3f})")

        return recommendations

    def _match_to_wine(self, match: dict) -> Wine:
        """Convert Pinecone match to Wine object."""
        metadata = match['metadata']

        characteristics = [c.strip() for c in metadata.get('characteristics', '').split(',')] if metadata.get('characteristics') else []
        flavor_notes = [f.strip() for f in metadata.get('flavor_notes', '').split(',')] if metadata.get('flavor_notes') else []

        return Wine(
            id=match['id'],
            name=metadata.get('name', ''),
            producer=metadata.get('producer', ''),
            vintage=metadata.get('vintage') if metadata.get('vintage', 0) > 0 else None,
            wine_type=metadata.get('wine_type', ''),
            varietal=metadata.get('varietal', ''),
            country=metadata.get('country', ''),
            region=metadata.get('region', ''),
            body=metadata.get('body', ''),
            sweetness=metadata.get('sweetness', ''),
            acidity=metadata.get('acidity', ''),
            tannin=metadata.get('tannin') if metadata.get('tannin') != "n/a" else None,
            characteristics=characteristics,
            flavor_notes=flavor_notes,
            description=metadata.get('description', ''),
            price_usd=metadata.get('price_usd', 0),
            rating=metadata.get('rating') if metadata.get('rating', 0) > 0 else None,
            vivino_url=metadata.get('vivino_url', '')
        )

    def _generate_explanation(
        self,
        user_prefs: str,
        search_query: str,
        wine: Wine,
        user_request: str = None,
        category_knowledge: str = None
    ) -> str:
        """Generate personalized explanation for why wine matches user preferences."""
        prompt = create_agent2_explanation_prompt(
            user_preferences=user_prefs,
            search_query=search_query,
            wine_name=wine.name,
            wine_varietal=wine.varietal,
            wine_region=wine.region,
            wine_characteristics=wine.characteristics,
            wine_flavor_notes=wine.flavor_notes,
            user_request=user_request,
            category_knowledge=category_knowledge
        )

        response = self.client.chat.completions.create(
            model=Config.OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )

        return response.choices[0].message.content.strip()


# =============================================================================
# Orchestrator
# =============================================================================

class WineRecommendationOrchestrator:
    """
    Orchestrates the wine recommendation pipeline.
    Sequential flow: Agent 1 → Agent 2
    """

    def __init__(self):
        self.agent1 = PreferenceInterpreter()
        self.agent2 = WineSearcher()

    def get_recommendations(
        self,
        user_prefs: UserPreferences,
        top_n: int = 3,
        verbose: bool = False
    ) -> List[WineRecommendation]:
        """
        Get wine recommendations for user preferences.

        Args:
            user_prefs: UserPreferences object with user input
            top_n: Number of recommendations to return
            verbose: Enable verbose debugging output

        Returns:
            List of WineRecommendation objects
        """
        if verbose:
            print("=" * 70)
            print("WINE RECOMMENDATION PIPELINE")
            print("=" * 70)
            print(f"User Input: {user_prefs.description}")

        # Step 1: Agent 1 - Interpret preferences
        search_query = self.agent1.interpret(user_prefs, verbose=verbose)

        # Step 2: Agent 2 - Search and recommend
        recommendations = self.agent2.search(
            search_query=search_query,
            user_prefs_description=user_prefs.description,
            top_n=top_n,
            verbose=verbose
        )

        # Step 3: Handle edge cases with relaxed search
        if not recommendations:
            if verbose:
                print("\n[Orchestrator] No matches found. Attempting relaxed search...")

            recommendations = self._relaxed_search(
                search_query, user_prefs, top_n, verbose
            )

        if verbose:
            print(f"\nPIPELINE COMPLETE: {len(recommendations)} recommendation(s)")

        return recommendations

    def _relaxed_search(
        self,
        search_query: SearchQuery,
        user_prefs: UserPreferences,
        top_n: int,
        verbose: bool
    ) -> List[WineRecommendation]:
        """Fallback search with relaxed filters."""
        price_min, price_max = search_query.price_range
        price_buffer = (price_max - price_min) * 0.25
        relaxed_price_min = max(10.0, price_min - price_buffer)
        relaxed_price_max = price_max + price_buffer

        if verbose:
            print(f"[Orchestrator] Expanding price range: ${relaxed_price_min:.2f}-${relaxed_price_max:.2f}")

        relaxed_query = SearchQuery(
            query_text=search_query.query_text,
            price_range=(relaxed_price_min, relaxed_price_max),
            wine_type_filter=None
        )

        return self.agent2.search(
            search_query=relaxed_query,
            user_prefs_description=user_prefs.description,
            top_n=top_n,
            verbose=verbose
        )


# =============================================================================
# Convenience Function
# =============================================================================

def get_wine_recommendations(
    user_prefs: UserPreferences,
    top_n: int = 3,
    verbose: bool = False
) -> List[WineRecommendation]:
    """
    Convenience function to get wine recommendations.

    Args:
        user_prefs: UserPreferences object
        top_n: Number of recommendations
        verbose: Enable verbose output

    Returns:
        List of WineRecommendation objects
    """
    orchestrator = WineRecommendationOrchestrator()
    return orchestrator.get_recommendations(user_prefs, top_n, verbose)
