"""
Decide Agent for helping users choose wines from their cellar.
Provides context-aware recommendations based on occasion, food, and preferences.
"""

from typing import Optional, Dict, Any, List
from openai import OpenAI
from sqlalchemy.orm import Session

from config import Config
from models.database import User, CellarBottle


class DecideAgent:
    """
    Agent for recommending wines from the user's cellar.
    Considers occasion, food pairing, and user preferences.
    """

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def recommend_from_cellar(
        self,
        request: str,
        occasion: Optional[str] = None,
        food_pairing: Optional[str] = None,
        wine_type: Optional[str] = None,
        guest_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recommend wines from the user's cellar.

        Args:
            request: User's natural language request
            occasion: Optional occasion (dinner party, casual, celebration)
            food_pairing: Optional food to pair with
            wine_type: Optional wine type filter
            guest_count: Optional number of guests

        Returns:
            Dict with recommendations and explanations
        """
        # Get owned bottles from cellar
        bottles = self.db.query(CellarBottle).filter(
            CellarBottle.user_id == self.user.id,
            CellarBottle.status == "owned",
            CellarBottle.quantity > 0
        ).all()

        if not bottles:
            return {
                "recommendations": [],
                "message": "Your cellar is empty! Let's find some wines to add.",
                "count": 0
            }

        # Filter by wine type if specified
        if wine_type:
            bottles = [
                b for b in bottles
                if (b.wine and b.wine.wine_type == wine_type) or
                   (b.custom_wine_type and b.custom_wine_type.lower() == wine_type.lower())
            ]

        if not bottles:
            return {
                "recommendations": [],
                "message": f"You don't have any {wine_type} wines. Would you like a different suggestion?",
                "count": 0
            }

        # Build wine descriptions for LLM
        wine_descriptions = []
        for b in bottles[:15]:  # Limit for context
            wine_desc = self._describe_bottle(b)
            wine_descriptions.append(wine_desc)

        wines_text = "\n".join(wine_descriptions)

        # Build context
        context_parts = []
        if occasion:
            context_parts.append(f"Occasion: {occasion}")
        if food_pairing:
            context_parts.append(f"Food: {food_pairing}")
        if guest_count:
            context_parts.append(f"Guests: {guest_count}")

        context = "\n".join(context_parts) if context_parts else "General recommendation"

        # Generate recommendations
        prompt = f"""You are Pip, a wine sommelier helping pick wines from someone's cellar.

USER'S CELLAR:
{wines_text}

CONTEXT:
{context}

USER REQUEST: {request}

Select 1-3 wines from their cellar and explain why each would be a good choice.
Consider:
- Food pairing compatibility (if food mentioned)
- Occasion appropriateness
- Wine characteristics
- User ratings (if available)

Format your response conversationally as Pip. Reference specific wines by their names.
For each recommendation, briefly explain why it's a good pick."""

        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are Pip, a friendly wine expert helping choose from a cellar."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )

            recommendation_text = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Decide agent error: {e}")
            recommendation_text = "I'd be happy to help you pick a wine! Let me know what you're having or the occasion."

        # Find mentioned wines in response
        recommended_bottles = self._extract_recommended_bottles(
            recommendation_text, bottles
        )

        return {
            "recommendations": [self._format_bottle(b) for b in recommended_bottles],
            "message": recommendation_text,
            "count": len(recommended_bottles),
            "total_available": len(bottles)
        }

    def quick_pick(
        self,
        category: str = "any"
    ) -> Dict[str, Any]:
        """
        Quick pick a wine from cellar based on simple category.

        Args:
            category: "red", "white", "sparkling", "special", or "any"

        Returns:
            Single wine recommendation
        """
        bottles = self.db.query(CellarBottle).filter(
            CellarBottle.user_id == self.user.id,
            CellarBottle.status == "owned",
            CellarBottle.quantity > 0
        ).all()

        if not bottles:
            return {
                "recommendation": None,
                "message": "Your cellar is empty!"
            }

        # Filter by category
        if category == "special":
            # Pick highest rated or most expensive
            bottles.sort(key=lambda b: (b.rating or 0, self._get_price(b) or 0), reverse=True)
        elif category in ["red", "white", "rosé", "sparkling"]:
            bottles = [
                b for b in bottles
                if (b.wine and b.wine.wine_type == category) or
                   (b.custom_wine_type == category)
            ]

        if not bottles:
            return {
                "recommendation": None,
                "message": f"No {category} wines found in your cellar."
            }

        # Pick top option
        if category == "special":
            pick = bottles[0]
        else:
            # Random-ish but prefer higher rated
            import random
            weighted = []
            for b in bottles:
                weight = max(1, (b.rating or 3) - 2)
                weighted.extend([b] * int(weight * 2))
            pick = random.choice(weighted) if weighted else bottles[0]

        wine_name = pick.wine.name if pick.wine else pick.custom_wine_name

        return {
            "recommendation": self._format_bottle(pick),
            "message": f"How about the {wine_name}? It's a great choice!"
        }

    def suggest_for_food(self, food: str) -> Dict[str, Any]:
        """
        Suggest wines from cellar that pair well with a food.

        Args:
            food: Food to pair with

        Returns:
            Recommendations with pairing explanations
        """
        return self.recommend_from_cellar(
            request=f"What should I drink with {food}?",
            food_pairing=food
        )

    def _describe_bottle(self, bottle: CellarBottle) -> str:
        """Create a text description of a bottle for LLM context."""
        if bottle.wine:
            wine = bottle.wine
            desc = f"- {wine.name}"
            if wine.producer:
                desc += f" by {wine.producer}"
            desc += f" ({wine.wine_type})"
            if wine.varietal:
                desc += f" - {wine.varietal}"
            if wine.region:
                desc += f" from {wine.region}"
            if wine.price_usd:
                desc += f" - ${wine.price_usd}"
            if bottle.rating:
                desc += f" [Rated: {bottle.rating}/5]"
            desc += f" (Qty: {bottle.quantity})"
            return desc
        else:
            desc = f"- {bottle.custom_wine_name or 'Unknown Wine'}"
            if bottle.custom_wine_producer:
                desc += f" by {bottle.custom_wine_producer}"
            if bottle.custom_wine_type:
                desc += f" ({bottle.custom_wine_type})"
            if bottle.custom_wine_varietal:
                desc += f" - {bottle.custom_wine_varietal}"
            if bottle.rating:
                desc += f" [Rated: {bottle.rating}/5]"
            desc += f" (Qty: {bottle.quantity})"
            return desc

    def _extract_recommended_bottles(
        self,
        text: str,
        bottles: List[CellarBottle]
    ) -> List[CellarBottle]:
        """Extract which bottles were mentioned in the recommendation text."""
        text_lower = text.lower()
        recommended = []

        for bottle in bottles:
            wine_name = bottle.wine.name if bottle.wine else bottle.custom_wine_name
            if wine_name and wine_name.lower() in text_lower:
                recommended.append(bottle)

        # If we couldn't match by name, return top bottles
        if not recommended and bottles:
            recommended = sorted(
                bottles,
                key=lambda b: (b.rating or 0),
                reverse=True
            )[:3]

        return recommended[:3]

    def _format_bottle(self, bottle: CellarBottle) -> Dict[str, Any]:
        """Format bottle for response."""
        if bottle.wine:
            return {
                "bottle_id": str(bottle.id),
                "wine_id": bottle.wine.id,
                "wine_name": bottle.wine.name,
                "producer": bottle.wine.producer,
                "vintage": bottle.wine.vintage,
                "wine_type": bottle.wine.wine_type,
                "varietal": bottle.wine.varietal,
                "region": bottle.wine.region,
                "price_usd": bottle.wine.price_usd,
                "quantity": bottle.quantity,
                "rating": bottle.rating
            }
        else:
            return {
                "bottle_id": str(bottle.id),
                "wine_name": bottle.custom_wine_name,
                "producer": bottle.custom_wine_producer,
                "vintage": bottle.custom_wine_vintage,
                "wine_type": bottle.custom_wine_type,
                "varietal": bottle.custom_wine_varietal,
                "region": bottle.custom_wine_region,
                "price_usd": bottle.purchase_price,
                "quantity": bottle.quantity,
                "rating": bottle.rating
            }

    def _get_price(self, bottle: CellarBottle) -> Optional[float]:
        """Get price of a bottle."""
        if bottle.wine:
            return bottle.wine.price_usd
        return bottle.purchase_price
