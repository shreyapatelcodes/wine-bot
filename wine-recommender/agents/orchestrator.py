"""
Orchestrator: Coordinates the two-agent pipeline for wine recommendations.
Handles the sequential flow: User Input → Agent 1 → Agent 2 → Recommendations
"""

from typing import List, Optional
from models import UserPreferences, WineRecommendation
from agents.preference_interpreter import PreferenceInterpreter
from agents.wine_searcher import WineSearcher


class WineRecommendationOrchestrator:
    """
    Orchestrates the wine recommendation pipeline.
    Simple sequential coordinator: Agent 1 → Agent 2
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
            top_n: Number of recommendations to return (default: 3)
            verbose: Enable verbose debugging output

        Returns:
            List of WineRecommendation objects (up to top_n wines)
        """
        if verbose:
            print("=" * 70)
            print("WINE RECOMMENDATION PIPELINE")
            print("=" * 70)
            print(f"User Input: {user_prefs.description}")
            print(f"Budget: ${user_prefs.budget_min}-${user_prefs.budget_max}")
            if user_prefs.food_pairing:
                print(f"Food Pairing: {user_prefs.food_pairing}")
            if user_prefs.wine_type_pref:
                print(f"Wine Type: {user_prefs.wine_type_pref}")
            print()

        # Step 1: Agent 1 - Interpret preferences using WSET knowledge
        if verbose:
            print("STEP 1: Preference Interpretation (Agent 1)")
            print("-" * 70)

        search_query = self.agent1.interpret(user_prefs, verbose=verbose)

        if verbose:
            print()

        # Step 2: Agent 2 - Search wine products and generate explanations
        if verbose:
            print("STEP 2: Wine Search & Recommendations (Agent 2)")
            print("-" * 70)

        recommendations = self.agent2.search(
            search_query=search_query,
            user_prefs_description=user_prefs.description,
            top_n=top_n,
            verbose=verbose
        )

        # Step 3: Handle edge cases
        if not recommendations:
            if verbose:
                print("\n[Orchestrator] No matches found. Attempting relaxed search...")

            # Try relaxing filters
            recommendations = self._relaxed_search(
                search_query,
                user_prefs,
                top_n,
                verbose
            )

        if verbose:
            print()
            print("=" * 70)
            print(f"PIPELINE COMPLETE: {len(recommendations)} recommendation(s)")
            print("=" * 70)
            print()

        return recommendations

    def _relaxed_search(
        self,
        search_query,
        user_prefs: UserPreferences,
        top_n: int,
        verbose: bool
    ) -> List[WineRecommendation]:
        """
        Fallback search with relaxed filters if no matches found.

        Args:
            search_query: Original SearchQuery
            user_prefs: Original UserPreferences
            top_n: Number of results
            verbose: Verbose mode

        Returns:
            List of recommendations with relaxed criteria
        """
        # Try expanding price range by 25%
        price_min, price_max = search_query.price_range
        price_buffer = (price_max - price_min) * 0.25
        relaxed_price_min = max(10.0, price_min - price_buffer)
        relaxed_price_max = price_max + price_buffer

        if verbose:
            print(f"[Orchestrator] Expanding price range: ${relaxed_price_min:.2f}-${relaxed_price_max:.2f}")

        # Create relaxed search query
        from models import SearchQuery
        relaxed_query = SearchQuery(
            query_text=search_query.query_text,
            price_range=(relaxed_price_min, relaxed_price_max),
            wine_type_filter=None  # Remove wine type filter
        )

        recommendations = self.agent2.search(
            search_query=relaxed_query,
            user_prefs_description=user_prefs.description,
            top_n=top_n,
            verbose=verbose
        )

        return recommendations


# Convenience function for standalone usage
def get_wine_recommendations(
    user_prefs: UserPreferences,
    top_n: int = 3,
    verbose: bool = False
) -> List[WineRecommendation]:
    """
    Convenience function to get wine recommendations.

    Args:
        user_prefs: UserPreferences object
        top_n: Number of recommendations (default: 3)
        verbose: Enable verbose output

    Returns:
        List of WineRecommendation objects
    """
    orchestrator = WineRecommendationOrchestrator()
    return orchestrator.get_recommendations(user_prefs, top_n, verbose)
