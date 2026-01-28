"""
Profile Agent for managing and synthesizing user taste preferences.
"""

from typing import Optional, Dict, Any, List
from openai import OpenAI
from sqlalchemy.orm import Session

from config import Config
from models.database import User, CellarBottle, UserTasteProfile


class ProfileAgent:
    """
    Agent for managing user taste profiles.
    Synthesizes preferences from ratings and provides insights.
    """

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def get_profile(self) -> Dict[str, Any]:
        """
        Get the user's taste profile with synthesized insights.

        Returns:
            Dict with profile data and insights
        """
        profile = self.db.query(UserTasteProfile).filter(
            UserTasteProfile.user_id == self.user.id
        ).first()

        if not profile or (profile.rating_count or 0) < 3:
            return {
                "has_profile": False,
                "message": "I'm still getting to know your taste. Rate a few more wines and I'll be able to give personalized recommendations!",
                "ratings_needed": 3 - (profile.rating_count if profile else 0)
            }

        # Build profile summary
        profile_data = {
            "has_profile": True,
            "rating_count": profile.rating_count,
            "average_rating": round(profile.average_rating, 1) if profile.average_rating else None,
            "preferred_types": profile.preferred_types or {},
            "preferred_regions": profile.preferred_regions or [],
            "preferred_varietals": profile.preferred_varietals or [],
            "preferred_countries": profile.preferred_countries or [],
            "price_range": {
                "min": profile.price_range_min,
                "max": profile.price_range_max
            } if profile.price_range_min or profile.price_range_max else None,
            "flavor_profile": profile.flavor_profile
        }

        # Generate insights
        insights = self._generate_insights(profile_data)
        profile_data["insights"] = insights

        return profile_data

    def get_profile_for_recommendations(self) -> Optional[Dict[str, Any]]:
        """
        Get profile data optimized for recommendation filtering.

        Returns:
            Dict with filter preferences or None if insufficient data
        """
        profile = self.db.query(UserTasteProfile).filter(
            UserTasteProfile.user_id == self.user.id
        ).first()

        if not profile or (profile.rating_count or 0) < 3:
            return None

        # Get top type preferences
        type_prefs = profile.preferred_types or {}
        top_types = sorted(type_prefs.items(), key=lambda x: x[1], reverse=True)

        return {
            "preferred_types": [t[0] for t in top_types[:2]] if top_types else None,
            "preferred_regions": (profile.preferred_regions or [])[:3],
            "preferred_varietals": (profile.preferred_varietals or [])[:3],
            "price_min": profile.price_range_min,
            "price_max": profile.price_range_max,
            "avoid_types": [t[0] for t in top_types if t[1] < 0]  # Negative scores
        }

    def update_from_rating(
        self,
        wine_type: Optional[str],
        region: Optional[str],
        varietal: Optional[str],
        price: Optional[float],
        rating: float,
        characteristics: Optional[List[str]] = None
    ) -> None:
        """
        Update profile based on a new rating.
        Called after user rates a wine.
        """
        profile = self.db.query(UserTasteProfile).filter(
            UserTasteProfile.user_id == self.user.id
        ).first()

        if not profile:
            profile = UserTasteProfile(user_id=self.user.id)
            self.db.add(profile)

        # Update rating count and average
        old_count = profile.rating_count or 0
        profile.rating_count = old_count + 1

        if profile.average_rating:
            profile.average_rating = (
                (profile.average_rating * old_count + rating) / profile.rating_count
            )
        else:
            profile.average_rating = rating

        # Determine weight based on rating (higher ratings = stronger signal)
        weight = (rating - 2.5) / 2.5  # -1 to +1 range

        # Update type preferences
        if wine_type:
            type_prefs = profile.preferred_types or {}
            current = type_prefs.get(wine_type, 0)
            type_prefs[wine_type] = current + weight
            profile.preferred_types = type_prefs

        # Update regions (only for highly rated wines)
        if region and rating >= 4:
            regions = profile.preferred_regions or []
            if region not in regions:
                regions.append(region)
            profile.preferred_regions = regions[:15]

        # Update varietals
        if varietal and rating >= 4:
            varietals = profile.preferred_varietals or []
            if varietal not in varietals:
                varietals.append(varietal)
            profile.preferred_varietals = varietals[:15]

        # Update price range
        if price:
            if rating >= 4:  # Good value indicator
                if not profile.price_range_min or price < profile.price_range_min:
                    profile.price_range_min = price
                if not profile.price_range_max or price > profile.price_range_max:
                    profile.price_range_max = price

        # Update flavor profile
        if characteristics and rating >= 4:
            flavor = profile.flavor_profile or {"liked_notes": [], "disliked_notes": []}
            for char in characteristics:
                if char not in flavor["liked_notes"]:
                    flavor["liked_notes"].append(char)
            profile.flavor_profile = flavor

        self.db.commit()

    def get_exploration_suggestions(self) -> Dict[str, Any]:
        """
        Suggest new wines/regions to explore based on current preferences.

        Returns:
            Dict with exploration suggestions
        """
        profile = self.get_profile()

        if not profile.get("has_profile"):
            return {
                "suggestions": [
                    "Start by trying wines from different regions",
                    "Compare a few red and white wines to discover your preference",
                    "Rate your favorites to get personalized recommendations"
                ]
            }

        # Generate exploration suggestions
        prompt = f"""Based on this wine taste profile, suggest 3 new wines/regions to explore:

Profile:
- Favorite types: {profile.get('preferred_types', {})}
- Favorite regions: {profile.get('preferred_regions', [])}
- Favorite varietals: {profile.get('preferred_varietals', [])}
- Average rating: {profile.get('average_rating')}

Suggest wines that would expand their palate while likely appealing to their preferences.
Format as a JSON array of objects with 'suggestion' and 'reason' fields."""

        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a wine expert. Respond with JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=400
            )

            import json
            import re
            content = response.choices[0].message.content.strip()
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                suggestions = json.loads(json_match.group())
                return {"suggestions": suggestions}
        except Exception as e:
            print(f"Suggestion generation error: {e}")

        return {
            "suggestions": [
                {"suggestion": "Try a wine from a region you haven't explored", "reason": "Expand your palate"},
            ]
        }

    def _generate_insights(self, profile_data: Dict[str, Any]) -> str:
        """Generate natural language insights about the profile."""
        type_prefs = profile_data.get("preferred_types", {})
        regions = profile_data.get("preferred_regions", [])
        varietals = profile_data.get("preferred_varietals", [])

        # Find top preferences
        top_type = max(type_prefs.items(), key=lambda x: x[1])[0] if type_prefs else None

        insights = []

        if top_type:
            insights.append(f"You tend to prefer {top_type} wines")

        if regions:
            if len(regions) == 1:
                insights.append(f"with a fondness for wines from {regions[0]}")
            else:
                insights.append(f"especially from {', '.join(regions[:2])}")

        if varietals:
            insights.append(f"You've rated {varietals[0]} particularly highly")

        avg = profile_data.get("average_rating")
        if avg:
            if avg >= 4:
                insights.append("You're a discerning taster with high standards!")
            elif avg >= 3:
                insights.append("You have balanced taste and appreciate variety")

        return ". ".join(insights) + "." if insights else "Still learning about your preferences!"
