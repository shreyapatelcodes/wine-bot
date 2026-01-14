"""
Agent 2: Wine Searcher
Searches wine products vector database and generates personalized recommendations.
"""

import json
from typing import List
from config import Config
from models import SearchQuery, Wine, WineRecommendation
from utils import (
    search_wine_products,
    get_openai_client,
    create_agent2_explanation_prompt
)


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
            top_n: Number of recommendations to return (default: 3)
            verbose: Enable verbose output

        Returns:
            List of WineRecommendation objects with explanations
        """
        # Step 1: Search wine products vector database
        price_min, price_max = search_query.price_range

        matches = search_wine_products(
            query_text=search_query.query_text,
            price_min=price_min,
            price_max=price_max,
            wine_type=search_query.wine_type_filter,
            top_k=Config.TOP_K_WINES  # Get more than needed for better selection
        )

        if verbose:
            print(f"\n[Agent 2] Vector search returned {len(matches)} wines")
            for i, match in enumerate(matches, 1):
                print(f"   {i}. {match['metadata']['name']} (score: {match['score']:.3f})")

        if not matches:
            if verbose:
                print("[Agent 2] No wines found matching criteria.")
            return []

        # Step 2: Convert matches to Wine objects and create recommendations
        recommendations = []
        for i, match in enumerate(matches[:top_n]):  # Take top N
            wine = self._match_to_wine(match)

            # Generate personalized explanation
            explanation = self._generate_explanation(
                user_prefs_description,
                search_query.query_text,
                wine
            )

            recommendation = WineRecommendation(
                wine=wine,
                explanation=explanation,
                relevance_score=match['score']
            )
            recommendations.append(recommendation)

            if verbose:
                print(f"\n[Agent 2] Recommendation {i+1}:")
                print(f"   Wine: {wine.name} ({wine.varietal})")
                print(f"   Score: {match['score']:.3f}")
                print(f"   Explanation: {explanation}")

        return recommendations

    def _match_to_wine(self, match: dict) -> Wine:
        """Convert Pinecone match to Wine object."""
        metadata = match['metadata']

        # Parse comma-separated strings back to lists
        characteristics = [c.strip() for c in metadata['characteristics'].split(',')] if metadata.get('characteristics') else []
        flavor_notes = [f.strip() for f in metadata['flavor_notes'].split(',')] if metadata.get('flavor_notes') else []

        wine = Wine(
            id=match['id'],
            name=metadata['name'],
            producer=metadata['producer'],
            vintage=metadata.get('vintage') if metadata.get('vintage', 0) > 0 else None,
            wine_type=metadata['wine_type'],
            varietal=metadata['varietal'],
            country=metadata['country'],
            region=metadata['region'],
            body=metadata['body'],
            sweetness=metadata['sweetness'],
            acidity=metadata['acidity'],
            tannin=metadata['tannin'] if metadata['tannin'] != "n/a" else None,
            characteristics=characteristics,
            flavor_notes=flavor_notes,
            description=metadata.get('description', ''),
            price_usd=metadata.get('price_usd'),
            rating=metadata.get('rating') if metadata.get('rating', 0) > 0 else None,
            vivino_url=metadata['vivino_url']
        )

        return wine

    def _generate_explanation(
        self,
        user_prefs: str,
        search_query: str,
        wine: Wine
    ) -> str:
        """
        Generate personalized explanation for why wine matches user preferences.

        Args:
            user_prefs: Original user preferences
            search_query: Generated search query
            wine: Wine object

        Returns:
            1-2 sentence personalized explanation
        """
        prompt = create_agent2_explanation_prompt(
            user_preferences=user_prefs,
            search_query=search_query,
            wine_name=wine.name,
            wine_varietal=wine.varietal,
            wine_region=wine.region,
            wine_characteristics=wine.characteristics,
            wine_flavor_notes=wine.flavor_notes
        )

        response = self.client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS_AGENT2
        )

        explanation = response.choices[0].message.content.strip()
        return explanation


# Convenience function for standalone usage
def search_wines(
    search_query: SearchQuery,
    user_prefs_description: str,
    top_n: int = 3,
    verbose: bool = False
) -> List[WineRecommendation]:
    """
    Convenience function to search for wine recommendations.

    Args:
        search_query: SearchQuery object from Agent 1
        user_prefs_description: Original user preferences
        top_n: Number of recommendations to return
        verbose: Enable verbose output

    Returns:
        List of WineRecommendation objects
    """
    agent = WineSearcher()
    return agent.search(search_query, user_prefs_description, top_n, verbose)
