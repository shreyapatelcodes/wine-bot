"""
Correction Agent for handling undo operations and filter modifications.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from models.database import User, CellarBottle, ChatSession


class CorrectionAgent:
    """
    Agent for handling corrections, undos, and filter modifications.
    """

    def __init__(self, db: Session, user: Optional[User] = None):
        self.db = db
        self.user = user

    def undo_last_action(
        self,
        session: ChatSession,
        action_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Undo the last reversible action.

        Args:
            session: Chat session with action history
            action_data: The action data from context manager

        Returns:
            Dict with 'success', 'message', 'undone_action'
        """
        if not action_data:
            return {
                "success": False,
                "message": "Nothing to undo.",
                "undone_action": None
            }

        action_type = action_data.get("type")
        data = action_data.get("data", {})

        if action_type == "cellar_add":
            return self._undo_cellar_add(data)
        elif action_type == "cellar_remove":
            return self._undo_cellar_remove(data)
        elif action_type == "rate":
            return self._undo_rate(data)
        else:
            return {
                "success": False,
                "message": f"Cannot undo action type: {action_type}",
                "undone_action": action_type
            }

    def _undo_cellar_add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Undo a cellar add operation."""
        bottle_id = data.get("cellar_bottle_id")
        wine_name = data.get("wine_name", "the wine")

        if not bottle_id:
            return {
                "success": False,
                "message": "Could not find the bottle to remove.",
                "undone_action": "cellar_add"
            }

        bottle = self.db.query(CellarBottle).filter(
            CellarBottle.id == bottle_id
        ).first()

        if not bottle:
            return {
                "success": False,
                "message": f"The bottle is no longer in your cellar.",
                "undone_action": "cellar_add"
            }

        # Remove the bottle
        self.db.delete(bottle)
        self.db.commit()

        return {
            "success": True,
            "message": f"Undone! Removed {wine_name} from your cellar.",
            "undone_action": "cellar_add"
        }

    def _undo_cellar_remove(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Undo a cellar remove operation (restore the bottle)."""
        # This would require storing more data about the removed bottle
        # For now, we can't fully restore
        wine_name = data.get("wine_name", "the wine")

        return {
            "success": False,
            "message": f"I can't restore {wine_name} automatically. You can add it back manually.",
            "undone_action": "cellar_remove"
        }

    def _undo_rate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Undo a rating operation."""
        bottle_id = data.get("bottle_id")
        previous_rating = data.get("previous_rating")
        wine_name = data.get("wine_name", "the wine")

        if not bottle_id:
            return {
                "success": False,
                "message": "Could not find the rated bottle.",
                "undone_action": "rate"
            }

        bottle = self.db.query(CellarBottle).filter(
            CellarBottle.id == bottle_id
        ).first()

        if not bottle:
            return {
                "success": False,
                "message": "The bottle is no longer in your cellar.",
                "undone_action": "rate"
            }

        # Restore previous rating (or clear it)
        bottle.rating = previous_rating
        self.db.commit()

        if previous_rating:
            return {
                "success": True,
                "message": f"Restored {wine_name}'s rating to {previous_rating}/5.",
                "undone_action": "rate"
            }
        else:
            return {
                "success": True,
                "message": f"Removed the rating from {wine_name}.",
                "undone_action": "rate"
            }

    def modify_filters(
        self,
        original_filters: Dict[str, Any],
        modification: str
    ) -> Dict[str, Any]:
        """
        Modify search/recommendation filters based on user correction.

        Args:
            original_filters: Original filter values
            modification: User's modification request (e.g., "actually under $30")

        Returns:
            Updated filters dict
        """
        import re

        new_filters = original_filters.copy()

        # Parse price modifications
        price_match = re.search(r'under\s*\$?(\d+)', modification.lower())
        if price_match:
            new_filters["price_max"] = float(price_match.group(1))

        price_around = re.search(r'around\s*\$?(\d+)', modification.lower())
        if price_around:
            amount = float(price_around.group(1))
            new_filters["price_min"] = amount * 0.7
            new_filters["price_max"] = amount * 1.3

        price_above = re.search(r'(?:above|over|more than)\s*\$?(\d+)', modification.lower())
        if price_above:
            new_filters["price_min"] = float(price_above.group(1))

        # Parse wine type modifications
        modification_lower = modification.lower()
        if "red" in modification_lower and "white" not in modification_lower:
            new_filters["wine_type"] = "red"
        elif "white" in modification_lower and "red" not in modification_lower:
            new_filters["wine_type"] = "white"
        elif "rosé" in modification_lower or "rose" in modification_lower:
            new_filters["wine_type"] = "rosé"
        elif "sparkling" in modification_lower or "champagne" in modification_lower:
            new_filters["wine_type"] = "sparkling"

        # Handle "not" / "no" exclusions
        if "not red" in modification_lower or "no red" in modification_lower:
            new_filters["exclude_type"] = "red"
        if "not white" in modification_lower or "no white" in modification_lower:
            new_filters["exclude_type"] = "white"

        return new_filters
