"""
Cellar Agent for managing user's wine collection.
Handles adding, querying, removing, and rating wines in the cellar.
"""

import json
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from openai import OpenAI
from sqlalchemy.orm import Session

from config import Config
from models.database import User, Wine, CellarBottle, UserTasteProfile


class CellarAgent:
    """
    Agent for cellar management operations.
    Supports natural language queries and operations.
    """

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def add_to_cellar(
        self,
        wine_id: Optional[str] = None,
        wine_name: Optional[str] = None,
        producer: Optional[str] = None,
        vintage: Optional[int] = None,
        wine_type: Optional[str] = None,
        varietal: Optional[str] = None,
        region: Optional[str] = None,
        country: Optional[str] = None,
        purchase_price: Optional[float] = None,
        purchase_location: Optional[str] = None,
        status: str = "owned"
    ) -> Dict[str, Any]:
        """
        Add a wine to the user's cellar.

        Returns:
            Dict with 'success', 'bottle_id', 'message', and 'is_new'
        """
        # Check if wine already exists in cellar
        if wine_id:
            existing = self.db.query(CellarBottle).filter(
                CellarBottle.user_id == self.user.id,
                CellarBottle.wine_id == wine_id
            ).first()

            if existing:
                # If wine was previously "tried", change back to "owned" (re-purchased)
                # but keep the rating
                was_tried = existing.status == "tried"
                if was_tried:
                    existing.status = "owned"
                    self.db.commit()
                    return {
                        "success": True,
                        "bottle_id": str(existing.id),
                        "message": "Added back to your cellar!",
                        "is_new": False
                    }
                else:
                    # Already in cellar as owned
                    return {
                        "success": True,
                        "bottle_id": str(existing.id),
                        "message": "This wine is already in your cellar.",
                        "is_new": False
                    }

        # Create new cellar entry
        cellar_bottle = CellarBottle(
            user_id=self.user.id,
            wine_id=wine_id,
            custom_wine_name=wine_name if not wine_id else None,
            custom_wine_producer=producer if not wine_id else None,
            custom_wine_vintage=vintage if not wine_id else None,
            custom_wine_type=wine_type if not wine_id else None,
            custom_wine_varietal=varietal if not wine_id else None,
            custom_wine_region=region if not wine_id else None,
            custom_wine_country=country if not wine_id else None,
            status=status,
            purchase_price=purchase_price,
            purchase_location=purchase_location
        )

        self.db.add(cellar_bottle)
        self.db.commit()
        self.db.refresh(cellar_bottle)

        # Get wine name for response
        display_name = wine_name
        if wine_id:
            wine = self.db.query(Wine).filter(Wine.id == wine_id).first()
            if wine:
                display_name = wine.name

        return {
            "success": True,
            "bottle_id": str(cellar_bottle.id),
            "message": f"Added {display_name or 'wine'} to your cellar!",
            "is_new": True
        }

    def query_cellar(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        wine_type: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query the user's cellar with natural language or filters.

        Returns:
            Dict with 'bottles', 'count', and 'message'
        """
        # If natural language query provided, extract filters
        filters = {}
        if query:
            filters = self._parse_cellar_query(query)

        # Override with explicit filters
        if status:
            filters["status"] = status
        if wine_type:
            filters["wine_type"] = wine_type
        if price_min:
            filters["price_min"] = price_min
        if price_max:
            filters["price_max"] = price_max

        # Default to "owned" status if not explicitly querying tried wines or ratings
        # This ensures "show me my cellar" only shows owned wines
        if not filters.get("status") and not filters.get("min_rating") and not filters.get("max_rating"):
            filters["status"] = "owned"

        # Build query
        db_query = self.db.query(CellarBottle).filter(
            CellarBottle.user_id == self.user.id
        )

        if filters.get("status"):
            db_query = db_query.filter(CellarBottle.status == filters["status"])

        bottles = db_query.order_by(CellarBottle.added_at.desc()).all()

        # Apply additional filters in Python (for custom wines and flexible matching)
        filtered_bottles = []
        for bottle in bottles:
            # Get wine attributes from catalog wine or custom fields
            if bottle.wine:
                bottle_type = bottle.wine.wine_type
                bottle_price = bottle.wine.price_usd
                bottle_varietal = bottle.wine.varietal
                bottle_region = bottle.wine.region
                bottle_country = bottle.wine.country
            else:
                bottle_type = bottle.custom_wine_type
                bottle_price = bottle.purchase_price
                bottle_varietal = bottle.custom_wine_varietal
                bottle_region = bottle.custom_wine_region
                bottle_country = bottle.custom_wine_country

            # Apply wine type filter
            if filters.get("wine_type"):
                if not bottle_type or bottle_type.lower() != filters["wine_type"].lower():
                    continue

            # Apply varietal filter (case-insensitive, partial match)
            if filters.get("varietal"):
                filter_varietal = filters["varietal"].lower()
                if not bottle_varietal or filter_varietal not in bottle_varietal.lower():
                    continue

            # Apply region filter (case-insensitive, partial match)
            if filters.get("region"):
                filter_region = filters["region"].lower()
                if not bottle_region or filter_region not in bottle_region.lower():
                    continue

            # Apply country filter (case-insensitive, partial match - also checks region for US states)
            if filters.get("country"):
                filter_country = filters["country"].lower()
                country_match = bottle_country and filter_country in bottle_country.lower()
                region_match = bottle_region and filter_country in bottle_region.lower()
                if not (country_match or region_match):
                    continue

            # Apply minimum rating filter
            if filters.get("min_rating"):
                if not bottle.rating or bottle.rating < filters["min_rating"]:
                    continue

            # Apply maximum rating filter (for wines they didn't like)
            if filters.get("max_rating"):
                if not bottle.rating or bottle.rating > filters["max_rating"]:
                    continue

            # Apply price filters
            if filters.get("price_min") and bottle_price:
                if bottle_price < filters["price_min"]:
                    continue
            if filters.get("price_max") and bottle_price:
                if bottle_price > filters["price_max"]:
                    continue

            filtered_bottles.append(bottle)

        # Format results
        results = []
        for bottle in filtered_bottles[:limit]:
            results.append(self._format_bottle(bottle))

        # Generate summary message
        status_text = filters.get("status", "all")
        type_text = filters.get("wine_type", "")

        if not filtered_bottles:
            message = "No wines found matching your criteria."
        elif len(filtered_bottles) == 1:
            message = f"Found 1 {type_text} wine in your cellar."
        else:
            message = f"Found {len(filtered_bottles)} {type_text} wines in your cellar."

        return {
            "bottles": results,
            "count": len(filtered_bottles),
            "total_count": len(bottles),
            "message": message,
            "filters_applied": filters
        }

    def remove_from_cellar(
        self,
        bottle_id: str,
        quantity: int = 1,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Remove a wine from the cellar.

        Returns:
            Dict with 'success', 'confirmation_required', 'message'
        """
        bottle = self.db.query(CellarBottle).filter(
            CellarBottle.id == bottle_id,
            CellarBottle.user_id == self.user.id
        ).first()

        if not bottle:
            return {
                "success": False,
                "message": "Wine not found in your cellar.",
                "confirmation_required": False
            }

        wine_name = bottle.wine.name if bottle.wine else bottle.custom_wine_name

        # Check if confirmation needed
        if not confirm:
            return {
                "success": False,
                "confirmation_required": True,
                "message": f"Remove {wine_name} from your cellar?",
                "bottle_id": bottle_id,
                "wine_name": wine_name
            }

        # Remove or decrement quantity
        if bottle.quantity <= quantity:
            self.db.delete(bottle)
            message = f"Removed {wine_name} from your cellar."
        else:
            bottle.quantity -= quantity
            message = f"Removed {quantity} bottle(s) of {wine_name}. {bottle.quantity} remaining."

        self.db.commit()

        return {
            "success": True,
            "message": message,
            "confirmation_required": False
        }

    def rate_wine(
        self,
        bottle_id: str,
        rating: float,
        tasting_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rate a wine and optionally add tasting notes.

        Returns:
            Dict with 'success', 'message', and updated 'bottle'
        """
        if rating < 1 or rating > 5:
            return {
                "success": False,
                "message": "Rating must be between 1 and 5."
            }

        bottle = self.db.query(CellarBottle).filter(
            CellarBottle.id == bottle_id,
            CellarBottle.user_id == self.user.id
        ).first()

        if not bottle:
            return {
                "success": False,
                "message": "Wine not found in your cellar."
            }

        # Update rating
        bottle.rating = rating
        bottle.tried_date = datetime.now(timezone.utc)

        if tasting_notes:
            bottle.tasting_notes = tasting_notes

        # Mark as tried if owned
        if bottle.status == "owned":
            bottle.status = "tried"

        self.db.commit()

        # Update user taste profile
        self._update_taste_profile(bottle, rating)

        wine_name = bottle.wine.name if bottle.wine else bottle.custom_wine_name

        return {
            "success": True,
            "message": f"Rated {wine_name} {rating}/5!",
            "bottle": self._format_bottle(bottle)
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cellar statistics for the user.

        Returns:
            Dict with various stats
        """
        bottles = self.db.query(CellarBottle).filter(
            CellarBottle.user_id == self.user.id
        ).all()

        total_owned = len([b for b in bottles if b.status == "owned"])
        total_tried = len([b for b in bottles if b.status == "tried"])

        # Type breakdown
        type_counts = {"red": 0, "white": 0, "rosé": 0, "sparkling": 0}
        for bottle in bottles:
            wine_type = bottle.wine.wine_type if bottle.wine else bottle.custom_wine_type
            if wine_type and wine_type.lower() in type_counts:
                type_counts[wine_type.lower()] += 1

        # Average rating
        rated_bottles = [b for b in bottles if b.rating]
        avg_rating = sum(b.rating for b in rated_bottles) / len(rated_bottles) if rated_bottles else None

        return {
            "total_bottles": total_owned,
            "wines_tried": total_tried,
            "type_breakdown": type_counts,
            "average_rating": avg_rating,
            "ratings_count": len(rated_bottles)
        }

    def _parse_cellar_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language cellar query into filters."""
        prompt = f"""Convert this cellar query into filters. Extract any relevant criteria the user mentions.

Query: {query}

Extract any of these filters that apply:
- status: "owned" (wines in cellar), "tried" (wines they've tasted), "saved" (wines they want to try), or null
- wine_type: "red", "white", "rosé", "sparkling", or null
- varietal: grape variety like "Chardonnay", "Pinot Noir", "Cabernet Sauvignon", etc. or null
- region: wine region like "Napa Valley", "Burgundy", "Tuscany", etc. or null
- country: country like "France", "Italy", "USA", "California", etc. or null
- min_rating: minimum rating (1-5) for "liked" or "enjoyed" wines, or null
- max_rating: maximum rating (1-5) for wines they "didn't like" or "weren't a fan of", or null
- price_min: number or null
- price_max: number or null

Note: For "liked", "loved", "enjoyed", "favorite" wines, set min_rating to 4.
Note: For "didn't like", "wasn't a fan", "not great", "disappointing" wines, set max_rating to 3.
Note: US states like "California", "Oregon", "Washington" should go in country field.

The user has three places for wines:
1. Cellar (owned): wines they currently have/own
2. Tried list: wines they've tasted
3. Want to try (saved): wines they'd like to try in the future

Examples:
- "my reds" -> {{"wine_type": "red", "status": "owned"}}
- "what's in my cellar" -> {{"status": "owned"}}
- "show me my cellar" -> {{"status": "owned"}}
- "wines I own" -> {{"status": "owned"}}
- "what have I tried" -> {{"status": "tried"}}
- "my tried list" -> {{"status": "tried"}}
- "wines I've tasted" -> {{"status": "tried"}}
- "what Chardonnays have I tried" -> {{"status": "tried", "varietal": "Chardonnay"}}
- "Pinot Noirs I've had" -> {{"status": "tried", "varietal": "Pinot Noir"}}
- "wines I want to try" -> {{"status": "saved"}}
- "what do I want to try" -> {{"status": "saved"}}
- "my want to try list" -> {{"status": "saved"}}
- "saved wines" -> {{"status": "saved"}}
- "wines to try" -> {{"status": "saved"}}
- "wines from California I own" -> {{"status": "owned", "country": "California"}}
- "French wines I've tried" -> {{"status": "tried", "country": "France"}}
- "Napa Valley reds" -> {{"wine_type": "red", "region": "Napa Valley"}}
- "what have I liked" -> {{"min_rating": 4}}
- "wines I've enjoyed" -> {{"min_rating": 4}}
- "favorite reds" -> {{"wine_type": "red", "min_rating": 4}}
- "Italian wines I've loved" -> {{"country": "Italy", "min_rating": 4}}
- "wines I didn't like" -> {{"max_rating": 3}}
- "what didn't I like" -> {{"max_rating": 3}}
- "wines I wasn't a fan of" -> {{"max_rating": 3}}
- "reds I didn't enjoy" -> {{"wine_type": "red", "max_rating": 3}}
- "disappointing wines" -> {{"max_rating": 3}}
- "sparkling wines under $50" -> {{"wine_type": "sparkling", "price_max": 50}}

Respond with ONLY valid JSON, no explanation:"""

        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "Extract filters from query. Respond only with JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                filters = json.loads(json_match.group())
                # Clean up null values
                return {k: v for k, v in filters.items() if v is not None}

        except Exception as e:
            print(f"Query parsing error: {e}")

        return {}

    def _format_bottle(self, bottle: CellarBottle) -> Dict[str, Any]:
        """Format a CellarBottle for response."""
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
                "country": bottle.wine.country,
                "price_usd": bottle.wine.price_usd,
                "status": bottle.status,
                "rating": bottle.rating,
                "tasting_notes": bottle.tasting_notes
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
                "country": bottle.custom_wine_country,
                "price_usd": bottle.purchase_price,
                "status": bottle.status,
                "rating": bottle.rating,
                "tasting_notes": bottle.tasting_notes
            }

    def _update_taste_profile(self, bottle: CellarBottle, rating: float) -> None:
        """Update user taste profile based on rating."""
        # Get or create taste profile
        profile = self.db.query(UserTasteProfile).filter(
            UserTasteProfile.user_id == self.user.id
        ).first()

        if not profile:
            profile = UserTasteProfile(user_id=self.user.id)
            self.db.add(profile)

        # Update rating stats
        profile.rating_count = (profile.rating_count or 0) + 1
        if profile.average_rating:
            # Running average
            profile.average_rating = (
                (profile.average_rating * (profile.rating_count - 1) + rating) /
                profile.rating_count
            )
        else:
            profile.average_rating = rating

        # Update type preferences (weight by rating)
        wine_type = bottle.wine.wine_type if bottle.wine else bottle.custom_wine_type
        if wine_type and rating >= 3.5:  # Only update for positive ratings
            type_prefs = profile.preferred_types or {}
            current = type_prefs.get(wine_type, 0)
            type_prefs[wine_type] = current + (rating - 2.5) / 2.5  # Normalized boost
            profile.preferred_types = type_prefs

        # Update region preferences
        region = bottle.wine.region if bottle.wine else bottle.custom_wine_region
        if region and rating >= 4:
            regions = profile.preferred_regions or []
            if region not in regions:
                regions.append(region)
                profile.preferred_regions = regions[:10]  # Keep top 10

        # Update varietal preferences
        varietal = bottle.wine.varietal if bottle.wine else bottle.custom_wine_varietal
        if varietal and rating >= 4:
            varietals = profile.preferred_varietals or []
            if varietal not in varietals:
                varietals.append(varietal)
                profile.preferred_varietals = varietals[:10]

        self.db.commit()
