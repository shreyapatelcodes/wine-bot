"""
Quick test script to verify the wine recommendation system.
Run after seeding the vector database.

Usage: python wine-recommender/test_system.py
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wine_recommender import get_wine_recommendations, UserPreferences, Config


def test_recommendation_system():
    """Test the end-to-end recommendation pipeline."""

    print("=" * 80)
    print("WINE RECOMMENDATION SYSTEM - TEST")
    print("=" * 80)
    print()

    # Print configuration
    print("Configuration:")
    print(f"  WSET Index: {Config.WSET_INDEX_NAME}")
    print(f"  Wine Products Index: {Config.WINE_PRODUCTS_INDEX_NAME}")
    print(f"  Embedding Model: {Config.EMBEDDING_MODEL}")
    print(f"  Chat Model: {Config.CHAT_MODEL}")
    print()

    # Test Case 1: Bold red for steak
    print("=" * 80)
    print("TEST CASE 1: Bold red wine for steak dinner ($40-$60)")
    print("=" * 80)
    print()

    user_prefs = UserPreferences(
        description="Bold red wine for a steak dinner",
        budget_min=40.0,
        budget_max=60.0,
        food_pairing="steak",
        wine_type_pref="red"
    )

    try:
        recommendations = get_wine_recommendations(
            user_prefs,
            top_n=3,
            verbose=True  # Show detailed agent outputs
        )

        if recommendations:
            print()
            print("RECOMMENDATIONS:")
            print("-" * 80)
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec.wine.name} ({rec.wine.varietal})")
                print(f"   Price: ${rec.wine.price_usd:.2f}")
                print(f"   Region: {rec.wine.region}, {rec.wine.country}")
                print(f"   Score: {rec.relevance_score:.3f}")
                print(f"   Explanation: {rec.explanation}")
                print(f"   URL: {rec.wine.wine_com_url}")
        else:
            print("\nNo recommendations found!")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_recommendation_system()
    sys.exit(0 if success else 1)
