"""
Photo Agent for wine label recognition and smart retry guidance.
"""

from typing import Optional, Dict, Any
from openai import OpenAI
from sqlalchemy.orm import Session

from config import Config


class PhotoAgent:
    """
    Agent for handling wine label photo analysis.
    Provides smart retry guidance when analysis fails.
    """

    def __init__(self, db: Session):
        self.db = db
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def analyze_failure(
        self,
        confidence: float,
        analysis_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze why image analysis failed and provide guidance.

        Args:
            confidence: Confidence score from analysis
            analysis_result: The analysis result if any

        Returns:
            Dict with 'failure_type', 'message', 'suggestions'
        """
        additional_info = ""
        if analysis_result:
            additional_info = analysis_result.get("additional_info", "")

        # Determine failure type
        failure_type = self._classify_failure(confidence, additional_info)

        # Generate appropriate guidance
        guidance = self._generate_guidance(failure_type, confidence)

        return {
            "failure_type": failure_type,
            "message": guidance["message"],
            "suggestions": guidance["suggestions"],
            "can_retry": failure_type != "not_wine"
        }

    def _classify_failure(
        self,
        confidence: float,
        additional_info: str
    ) -> str:
        """Classify the type of failure."""
        info_lower = additional_info.lower()

        # Check for specific failure indicators
        if "not a wine" in info_lower or "not wine" in info_lower:
            return "not_wine"
        if "blurry" in info_lower or "blur" in info_lower:
            return "blurry"
        if "dark" in info_lower or "lighting" in info_lower:
            return "lighting"
        if "glare" in info_lower or "reflection" in info_lower:
            return "glare"
        if "partial" in info_lower or "cropped" in info_lower:
            return "partial"
        if "back" in info_lower:
            return "wrong_side"
        if confidence < 0.2:
            return "unreadable"
        if confidence < 0.5:
            return "low_confidence"

        return "unknown"

    def _generate_guidance(
        self,
        failure_type: str,
        confidence: float
    ) -> Dict[str, Any]:
        """Generate user-friendly guidance for the failure type."""
        messages = {
            "not_wine": {
                "message": "That doesn't look like a wine label. I can only identify wine bottles.",
                "suggestions": [
                    "Make sure you're photographing a wine bottle label",
                    "You can also just tell me the wine name directly"
                ]
            },
            "blurry": {
                "message": "The image is a bit blurry and I can't read the label clearly.",
                "suggestions": [
                    "Hold your camera steady when taking the photo",
                    "Tap to focus on the label before shooting",
                    "Try getting a bit closer to the label"
                ]
            },
            "lighting": {
                "message": "The lighting makes it hard to read the label.",
                "suggestions": [
                    "Move to a brighter area or turn on a light",
                    "Avoid shadows falling on the label",
                    "Natural daylight works best"
                ]
            },
            "glare": {
                "message": "There's glare on the label making it hard to read.",
                "suggestions": [
                    "Angle the bottle slightly to reduce reflections",
                    "Move away from direct light sources",
                    "Glossy labels can be tricky - try a slight angle"
                ]
            },
            "partial": {
                "message": "I can only see part of the label.",
                "suggestions": [
                    "Make sure the entire front label is in the frame",
                    "Get the wine name and producer in view",
                    "Step back a bit if you're too close"
                ]
            },
            "wrong_side": {
                "message": "This looks like the back label. I need the front!",
                "suggestions": [
                    "Flip the bottle to show the front label",
                    "The front label usually has the wine name and producer"
                ]
            },
            "unreadable": {
                "message": "I couldn't read the text on this label.",
                "suggestions": [
                    "Try better lighting",
                    "Make sure the camera is focused on the label",
                    "Or just tell me the wine name and I'll help from there"
                ]
            },
            "low_confidence": {
                "message": "I'm not confident about this identification.",
                "suggestions": [
                    "Try a clearer photo of the front label",
                    "Make sure the wine name is visible",
                    "You can also type the wine name if you know it"
                ]
            },
            "unknown": {
                "message": "I had trouble with that image.",
                "suggestions": [
                    "Try a new photo with good lighting",
                    "Focus on the main label with the wine name",
                    "Or simply tell me the wine name"
                ]
            }
        }

        return messages.get(failure_type, messages["unknown"])

    def format_success_response(
        self,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format a successful analysis into a user-friendly response.

        Args:
            analysis: The successful analysis result

        Returns:
            Formatted response dict
        """
        name = analysis.get("name", "")
        producer = analysis.get("producer", "")
        vintage = analysis.get("vintage")
        wine_type = analysis.get("wine_type", "")
        region = analysis.get("region", "")
        country = analysis.get("country", "")
        confidence = analysis.get("confidence", 0)

        # Build response message
        message_parts = []

        if name:
            if producer:
                message_parts.append(f"I found **{name}** by {producer}")
            else:
                message_parts.append(f"I found **{name}**")

        if vintage:
            message_parts.append(f"({vintage})")

        if region and country:
            message_parts.append(f"from {region}, {country}")
        elif region:
            message_parts.append(f"from {region}")
        elif country:
            message_parts.append(f"from {country}")

        message = " ".join(message_parts) if message_parts else "I identified a wine"

        if confidence >= 0.9:
            message += "."
        elif confidence >= 0.7:
            message += ". I'm fairly confident about this."
        else:
            message += ". Let me know if that doesn't look right."

        return {
            "message": message,
            "wine_info": {
                "name": name,
                "producer": producer,
                "vintage": vintage,
                "wine_type": wine_type,
                "region": region,
                "country": country
            },
            "confidence": confidence,
            "suggested_actions": [
                {"type": "add_cellar", "label": "Add to cellar"},
                {"type": "tell_more", "label": "Tell me more"},
                {"type": "find_similar", "label": "Find similar wines"}
            ]
        }

    def suggest_alternative(self) -> str:
        """
        Return a message suggesting the user type the wine name instead.
        """
        return (
            "Having trouble with the photo? No worries! "
            "Just type the wine name and I'll help you from there."
        )
