"""
Chat Orchestrator for Pip wine assistant.
Classifies user intent and routes to appropriate handlers.
"""

import json
import re
import uuid
from typing import Optional, Dict, Any, List, Tuple
from openai import OpenAI
from sqlalchemy.orm import Session

from config import Config
from models.database import User, ChatSession, Wine, CellarBottle, SavedBottle
from agents.context_manager import ContextManager
from agents.cellar_agent import CellarAgent
from agents.prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    ENTITY_EXTRACTION_PROMPT,
    GREETING_RESPONSE_PROMPT,
    CLARIFICATION_PROMPT,
    EDUCATION_GENERAL_PROMPT,
)
from utils.embeddings import search_wset_knowledge


class IntentResult:
    """Result of intent classification."""

    def __init__(
        self,
        intent: str,
        confidence: float,
        requires_clarification: bool = False,
        clarification_reason: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None
    ):
        self.intent = intent
        self.confidence = confidence
        self.requires_clarification = requires_clarification
        self.clarification_reason = clarification_reason
        self.entities = entities or {}


class ChatOrchestrator:
    """
    Main orchestrator for the Pip chat interface.
    Routes user messages to appropriate handlers based on intent.
    """

    CONFIDENCE_THRESHOLD = 0.6  # Below this, ask for clarification

    def __init__(self, db: Session, user: Optional[User] = None):
        self.db = db
        self.user = user
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.context_manager = ContextManager(db)

    def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        image_base64: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and return a response.

        Args:
            message: User's message text
            session_id: Optional existing session ID
            image_base64: Optional base64-encoded image
            history: Optional message history from client

        Returns:
            Dict with response, intent, actions, cards, session_id, etc.
        """
        # Get or create session
        session = self.context_manager.get_or_create_session(
            session_id=session_id,
            user=self.user
        )

        # Store user message
        self.context_manager.add_message(session, "user", message)

        # Get conversation history for context
        if history is None:
            history = self.context_manager.get_formatted_history(session)

        # Handle image upload
        if image_base64:
            return self._handle_image(session, message, image_base64)

        message_lower = message.lower()

        # Check for pending delete confirmation BEFORE intent classification
        session_context = session.context or {}
        pending_delete = session_context.get("pending_delete")
        if pending_delete:
            is_confirmation = any(word in message_lower for word in ["yes", "confirm", "remove", "delete"])
            is_cancellation = any(word in message_lower for word in ["no", "cancel", "never mind", "nevermind"])

            if is_confirmation:
                # Execute the delete
                bottle_id_str = pending_delete.get("bottle_id")
                try:
                    bottle_id = uuid.UUID(bottle_id_str)
                except (ValueError, TypeError):
                    bottle_id = None

                bottle = self.db.query(CellarBottle).filter(
                    CellarBottle.id == bottle_id,
                    CellarBottle.user_id == self.user.id
                ).first() if bottle_id else None

                if bottle:
                    wine_name = bottle.wine.name if bottle.wine else bottle.custom_wine_name
                    self.db.delete(bottle)
                    self.db.commit()

                    # Clear pending delete
                    self.context_manager.update_session_context(session, {"pending_delete": None})

                    response_text = f"Removed {wine_name} from your cellar."
                    self.context_manager.add_message(session, "assistant", response_text)

                    return self._build_response(
                        session=session,
                        response=response_text,
                        intent="cellar_remove"
                    )

            elif is_cancellation:
                # Clear pending delete
                self.context_manager.update_session_context(session, {"pending_delete": None})

                response_text = "No problem, I won't remove it."
                self.context_manager.add_message(session, "assistant", response_text)

                return self._build_response(
                    session=session,
                    response=response_text,
                    intent="cellar_remove"
                )

        # Check for pending move to tried confirmation
        # Refresh session to get latest context
        self.db.refresh(session)
        session_context = session.context or {}
        pending_move = session_context.get("pending_move_to_tried")
        if pending_move:
            is_confirmation = any(word in message_lower for word in ["yes", "move", "tried", "finished", "done"])
            is_cancellation = any(word in message_lower for word in ["no", "keep", "cellar", "cancel"])

            if is_confirmation:
                bottle_id_str = pending_move.get("bottle_id")
                try:
                    bottle_id = uuid.UUID(bottle_id_str)
                except (ValueError, TypeError):
                    bottle_id = None

                bottle = self.db.query(CellarBottle).filter(
                    CellarBottle.id == bottle_id,
                    CellarBottle.user_id == self.user.id
                ).first() if bottle_id else None

                if bottle:
                    wine_name = pending_move.get("wine_name", "this wine")
                    bottle.status = "tried"
                    self.db.commit()

                    # Clear pending move
                    self.context_manager.update_session_context(session, {"pending_move_to_tried": None})

                    response_text = f"Moved {wine_name} to your tried wines."
                    self.context_manager.add_message(session, "assistant", response_text)

                    return self._build_response(
                        session=session,
                        response=response_text,
                        intent="rate"
                    )

            elif is_cancellation:
                # Clear pending move
                self.context_manager.update_session_context(session, {"pending_move_to_tried": None})

                wine_name = pending_move.get("wine_name", "this wine")
                response_text = f"No problem, {wine_name} will stay in your cellar."
                self.context_manager.add_message(session, "assistant", response_text)

                return self._build_response(
                    session=session,
                    response=response_text,
                    intent="rate"
                )

        # Check for recommendation preference gathering flow
        # Refresh session to get latest context
        self.db.refresh(session)
        session_context = session.context or {}
        gathering_prefs = session_context.get("gathering_recommendation_prefs")
        if gathering_prefs:
            # Create a copy to ensure SQLAlchemy detects changes
            rec_prefs = dict(session_context.get("recommendation_prefs", {}))

            # Check for budget responses
            if any(word in message_lower for word in ["under 20", "under $20", "budget_under_20"]):
                rec_prefs["price_max"] = 20
            elif any(word in message_lower for word in ["20-40", "$20-40", "20 to 40", "budget_20_40"]):
                rec_prefs["price_min"] = 20
                rec_prefs["price_max"] = 40
            elif any(word in message_lower for word in ["40+", "$40+", "over 40", "above 40", "budget_40_plus"]):
                rec_prefs["price_min"] = 40
            elif any(word in message_lower for word in ["no budget", "any budget", "doesn't matter", "budget_any"]):
                pass  # No price constraint

            # If we just got budget, ask about food pairing
            if "food_pairing" not in rec_prefs and "asked_food" not in rec_prefs:
                rec_prefs["asked_food"] = True
                self.context_manager.update_session_context(session, {"recommendation_prefs": rec_prefs})

                response_text = "Got it! **Are you pairing this with any food?** (or just tell me what you're eating)"
                self.context_manager.add_message(session, "assistant", response_text)

                return self._build_response(
                    session=session,
                    response=response_text,
                    intent="recommend",
                    actions=[
                        {"type": "pairing_meat", "label": "Meat/Steak"},
                        {"type": "pairing_fish", "label": "Fish/Seafood"},
                        {"type": "pairing_pasta", "label": "Pasta"},
                        {"type": "pairing_none", "label": "No pairing"},
                    ]
                )

            # Check for food pairing responses
            if "asked_food" in rec_prefs and "food_pairing" not in rec_prefs:
                if any(word in message_lower for word in ["meat", "steak", "beef", "pairing_meat"]):
                    rec_prefs["food_pairing"] = "steak"
                elif any(word in message_lower for word in ["fish", "seafood", "pairing_fish"]):
                    rec_prefs["food_pairing"] = "seafood"
                elif any(word in message_lower for word in ["pasta", "italian", "pairing_pasta"]):
                    rec_prefs["food_pairing"] = "pasta"
                elif any(word in message_lower for word in ["no pairing", "no food", "just drinking", "pairing_none", "none"]):
                    rec_prefs["food_pairing"] = None
                else:
                    # Use whatever they said as the pairing
                    rec_prefs["food_pairing"] = message

                # Ask about wine type preference
                rec_prefs["asked_type"] = True
                self.context_manager.update_session_context(session, {"recommendation_prefs": rec_prefs})

                response_text = "Perfect! **Any preference for red, white, or something else?** (you can also say sparkling, natural, etc.)"
                self.context_manager.add_message(session, "assistant", response_text)

                return self._build_response(
                    session=session,
                    response=response_text,
                    intent="recommend",
                    actions=[
                        {"type": "type_red", "label": "Red"},
                        {"type": "type_white", "label": "White"},
                        {"type": "type_rose", "label": "Rosé"},
                        {"type": "type_any", "label": "Surprise me"},
                    ]
                )

            # Check for wine type responses
            if "asked_type" in rec_prefs:
                if any(word in message_lower for word in ["red", "type_red"]):
                    rec_prefs["wine_type"] = "red"
                elif any(word in message_lower for word in ["white", "type_white"]):
                    rec_prefs["wine_type"] = "white"
                elif any(word in message_lower for word in ["rosé", "rose", "type_rose"]):
                    rec_prefs["wine_type"] = "rosé"
                elif any(word in message_lower for word in ["sparkling", "champagne", "bubbly"]):
                    rec_prefs["wine_type"] = "sparkling"
                elif any(word in message_lower for word in ["natural", "orange", "skin contact"]):
                    rec_prefs["wine_type"] = "natural"
                # "surprise me" or "any" means no type preference

                # Done gathering - clear the flag and proceed with recommendations
                self.context_manager.update_session_context(session, {
                    "gathering_recommendation_prefs": None,
                    "recommendation_prefs": rec_prefs
                })

                # Build description from gathered prefs
                description_parts = []
                if rec_prefs.get("wine_type"):
                    description_parts.append(rec_prefs["wine_type"])
                if rec_prefs.get("food_pairing"):
                    description_parts.append(f"for {rec_prefs['food_pairing']}")
                description = " ".join(description_parts) if description_parts else "wine recommendation"

                return self._handle_recommend(session, description, rec_prefs)

        # Check for pending request clarification response
        if "recommend something new" in message_lower or "new" in message_lower and "recommend" in message_lower:
            pending = self.context_manager.get_pending_request(session)
            if pending:
                # User wants new recommendations - use the original request
                return self._handle_recommend(session, pending["message"], pending.get("entities", {}))

        if "pick from my cellar" in message_lower or ("cellar" in message_lower and ("pick" in message_lower or "my" in message_lower)):
            pending = self.context_manager.get_pending_request(session)
            if pending:
                # User wants to pick from cellar - use the original request
                return self._handle_decide(session, pending["message"], pending.get("entities", {}))

        # Classify intent
        intent_result = self._classify_intent(message, history)

        # Handle low confidence / ambiguity
        if intent_result.confidence < self.CONFIDENCE_THRESHOLD or intent_result.requires_clarification:
            return self._handle_ambiguous(session, message, intent_result)

        # Route to appropriate handler
        response = self._route_to_handler(session, message, intent_result, history)

        return response

    def _classify_intent(
        self,
        message: str,
        history: List[Dict[str, str]]
    ) -> IntentResult:
        """
        Classify the user's intent using GPT-4o-mini.

        Args:
            message: User's message
            history: Conversation history

        Returns:
            IntentResult with intent, confidence, and extracted entities
        """
        # Build context from history
        history_text = ""
        if history:
            recent = history[-6:]  # Last 6 messages for context
            history_text = "\n".join([
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in recent
            ])

        # Classify intent
        intent_prompt = f"""Previous conversation:
{history_text}

Current user message: {message}

{INTENT_CLASSIFICATION_PROMPT}"""

        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an intent classifier. Respond only with JSON."},
                    {"role": "user", "content": intent_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )

            content = response.choices[0].message.content.strip()
            intent_data = self._parse_json(content)

            intent = intent_data.get("intent", "unknown")
            confidence = intent_data.get("confidence", 0.5)
            requires_clarification = intent_data.get("requires_clarification", False)
            clarification_reason = intent_data.get("clarification_reason")

        except Exception as e:
            print(f"Intent classification error: {e}")
            intent = "unknown"
            confidence = 0.3
            requires_clarification = True
            clarification_reason = "Could not understand the request"

        # Extract entities for relevant intents
        entities = {}
        if intent in ["recommend", "cellar_query", "decide"]:
            entities = self._extract_entities(message)

        return IntentResult(
            intent=intent,
            confidence=confidence,
            requires_clarification=requires_clarification,
            clarification_reason=clarification_reason,
            entities=entities
        )

    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """
        Extract wine-related entities from the message.

        Args:
            message: User's message

        Returns:
            Dict of extracted entities
        """
        prompt = f"""User message: {message}

{ENTITY_EXTRACTION_PROMPT}"""

        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "Extract entities. Respond only with JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )

            content = response.choices[0].message.content.strip()
            entities = self._parse_json(content)

            # Clean up null values
            return {k: v for k, v in entities.items() if v is not None}

        except Exception as e:
            print(f"Entity extraction error: {e}")
            return {}

    def _route_to_handler(
        self,
        session: ChatSession,
        message: str,
        intent_result: IntentResult,
        history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Route to the appropriate handler based on intent.

        Args:
            session: Chat session
            message: User's message
            intent_result: Classified intent
            history: Conversation history

        Returns:
            Response dict
        """
        intent = intent_result.intent
        entities = intent_result.entities

        if intent == "greeting":
            return self._handle_greeting(session, message)

        elif intent == "recommend":
            return self._handle_recommend(session, message, entities)

        elif intent == "educate_general":
            return self._handle_education_general(session, message)

        elif intent == "educate_specific":
            return self._handle_education_specific(session, message, history)

        elif intent == "cellar_query":
            return self._handle_cellar_query(session, message, entities)

        elif intent == "cellar_add":
            return self._handle_cellar_add(session, message, history)

        elif intent == "cellar_remove":
            return self._handle_cellar_remove(session, message, history)

        elif intent == "rate":
            return self._handle_rate(session, message, history)

        elif intent == "decide":
            return self._handle_decide(session, message, entities)

        elif intent == "correct":
            return self._handle_correct(session, message, history)

        else:
            return self._handle_unknown(session, message)

    def _handle_greeting(
        self,
        session: ChatSession,
        message: str
    ) -> Dict[str, Any]:
        """Handle greeting messages."""
        is_returning = self.context_manager.is_returning_user(session)

        prompt = GREETING_RESPONSE_PROMPT.format(
            message=message,
            is_returning=is_returning
        )

        response_text = self._generate_response(prompt)

        self.context_manager.add_message(session, "assistant", response_text)

        return self._build_response(
            session=session,
            response=response_text,
            intent="greeting"
        )

    def _handle_recommend(
        self,
        session: ChatSession,
        message: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle wine recommendation requests."""
        # Check if this is a vague request that needs more info
        has_price = entities.get("price_min") or entities.get("price_max")
        has_food = entities.get("food_pairing")
        has_type = entities.get("wine_type")
        has_characteristics = entities.get("characteristics")
        has_occasion = entities.get("occasion")

        # Check for stored preferences from follow-up questions
        session_context = session.context or {}
        stored_prefs = session_context.get("recommendation_prefs", {})

        # Merge stored prefs with current entities
        if stored_prefs:
            if not has_price and stored_prefs.get("price_max"):
                entities["price_max"] = stored_prefs["price_max"]
                has_price = True
            if not has_food and stored_prefs.get("food_pairing"):
                entities["food_pairing"] = stored_prefs["food_pairing"]
                has_food = True
            if not has_type and stored_prefs.get("wine_type"):
                entities["wine_type"] = stored_prefs["wine_type"]
                has_type = True
            # Clear stored prefs after using them
            self.context_manager.update_session_context(session, {"recommendation_prefs": None})

        # If request is too vague, ask clarifying questions
        is_vague = not has_price and not has_food and not has_type and not has_characteristics and not has_occasion
        message_lower = message.lower()
        is_generic = any(phrase in message_lower for phrase in [
            "find a wine", "find me a wine", "recommend", "help me find",
            "suggest a wine", "wine recommendation", "what wine"
        ]) and len(message.split()) < 8

        if is_vague and is_generic:
            response_text = "I'd love to help you find the perfect wine! Let me ask a few questions:\n\n**What's your budget?**"
            self.context_manager.add_message(session, "assistant", response_text)

            # Store that we're in recommendation gathering mode
            self.context_manager.update_session_context(session, {
                "gathering_recommendation_prefs": True,
                "recommendation_prefs": {}
            })

            return self._build_response(
                session=session,
                response=response_text,
                intent="recommend",
                actions=[
                    {"type": "budget_under_20", "label": "Under $20"},
                    {"type": "budget_20_40", "label": "$20-40"},
                    {"type": "budget_40_plus", "label": "$40+"},
                    {"type": "budget_any", "label": "No budget"},
                ]
            )

        # Import here to avoid circular imports
        from app import _get_recommender

        get_recommendations, UserPreferences = _get_recommender()

        # Extract explicit filters for post-filtering
        filter_varietal = entities.get("varietal")
        filter_region = entities.get("region")
        filter_country = entities.get("country")
        filter_wine_type = entities.get("wine_type")
        has_explicit_filters = any([filter_varietal, filter_region, filter_country, filter_wine_type])

        # Build preferences from entities
        user_prefs = UserPreferences(
            description=message,
            budget_min=entities.get("price_min", 10.0),
            budget_max=entities.get("price_max", 200.0),
            food_pairing=entities.get("food_pairing"),
            wine_type_pref=filter_wine_type
        )

        try:
            # Get more recommendations if we need to filter
            fetch_count = 15 if has_explicit_filters else 3
            recommendations = get_recommendations(user_prefs, top_n=fetch_count)
        except Exception as e:
            print(f"Recommendation error: {e}")
            return self._build_response(
                session=session,
                response="I'm having trouble finding wines right now. Could you try rephrasing your request?",
                intent="recommend",
                error=str(e)
            )

        # Helper to determine if a wine is sparkling (handles Champagne, Prosecco, etc.)
        def is_sparkling_wine(wine) -> bool:
            # Check explicit wine_type
            if (wine.wine_type or "").lower() == "sparkling":
                return True

            # Sparkling wine regions
            sparkling_regions = [
                "champagne", "prosecco", "cava", "franciacorta", "crémant", "cremant",
                "lambrusco", "asti", "trento", "alto adige"
            ]
            # Sparkling wine terms (in name or description)
            sparkling_terms = [
                "champagne", "prosecco", "cava", "brut", "sparkling", "spumante",
                "crémant", "cremant", "lambrusco", "sekt", "espumante", "espumoso",
                "asti", "moscato d'asti", "frizzante", "pétillant", "petillant",
                "méthode traditionnelle", "methode traditionnelle", "cap classique",
                "blanc de blancs", "blanc de noirs", "extra brut", "demi-sec"
            ]

            region_lower = (wine.region or "").lower()
            if any(r in region_lower for r in sparkling_regions):
                return True

            name_lower = (wine.name or "").lower()
            if any(s in name_lower for s in sparkling_terms):
                return True

            return False

        # Apply explicit filters if specified
        if has_explicit_filters and recommendations:
            filtered_recs = []
            for rec in recommendations:
                wine = rec.wine

                # Check wine type (with special handling for sparkling)
                if filter_wine_type:
                    filter_type_lower = filter_wine_type.lower()
                    wine_type_lower = (wine.wine_type or "").lower()
                    if filter_type_lower == "sparkling":
                        # Use smart sparkling detection
                        if not is_sparkling_wine(wine):
                            continue
                    elif filter_type_lower not in wine_type_lower:
                        continue

                # Check varietal (case-insensitive partial match)
                if filter_varietal:
                    wine_varietal = (wine.varietal or "").lower()
                    if filter_varietal.lower() not in wine_varietal:
                        continue

                # Check region (case-insensitive partial match)
                if filter_region:
                    wine_region = (wine.region or "").lower()
                    if filter_region.lower() not in wine_region:
                        continue

                # Check country (also check region for US states)
                if filter_country:
                    filter_lower = filter_country.lower()
                    wine_country = (wine.country or "").lower()
                    wine_region = (wine.region or "").lower()
                    if filter_lower not in wine_country and filter_lower not in wine_region:
                        continue

                filtered_recs.append(rec)
                if len(filtered_recs) >= 3:
                    break

            recommendations = filtered_recs

        if not recommendations:
            # Build helpful message based on what filters were applied
            filter_parts = []
            if filter_varietal:
                filter_parts.append(filter_varietal)
            if filter_region:
                filter_parts.append(f"from {filter_region}")
            if filter_country:
                filter_parts.append(f"from {filter_country}")

            if filter_parts:
                filter_desc = " ".join(filter_parts)
                response_text = f"I couldn't find any {filter_desc} wines matching your criteria. Try broadening your search or checking a different region or varietal?"
            else:
                response_text = "I couldn't find wines matching those exact criteria. Try broadening your search - maybe a wider price range or different style?"

            self.context_manager.add_message(session, "assistant", response_text)
            return self._build_response(
                session=session,
                response=response_text,
                intent="recommend"
            )

        # Build response with wine cards - describe what we found
        filter_parts = []
        if filter_varietal:
            filter_parts.append(filter_varietal)
        if filter_wine_type and not filter_varietal:
            filter_parts.append(filter_wine_type)
        if filter_region:
            filter_parts.append(f"from {filter_region}")
        elif filter_country:
            filter_parts.append(f"from {filter_country}")

        if filter_parts:
            filter_desc = " ".join(filter_parts)
            response_text = f"Here are {len(recommendations)} {filter_desc} wines I'd recommend:"
        else:
            response_text = f"I found {len(recommendations)} wines that should work well:"

        # Get user's saved/cellar wine IDs
        saved_ids, cellar_ids = self._get_user_wine_ids()

        cards = []
        rec_metadata = []
        for rec in recommendations:
            wine = rec.wine
            card = {
                "type": "wine",
                "wine_id": wine.id,
                "wine_name": wine.name,
                "producer": wine.producer,
                "vintage": wine.vintage,
                "wine_type": wine.wine_type,
                "varietal": wine.varietal,
                "region": wine.region,
                "country": wine.country,
                "price_usd": wine.price_usd,
                "explanation": rec.explanation,
                "relevance_score": rec.relevance_score,
                "is_saved": wine.id in saved_ids,
                "is_in_cellar": wine.id in cellar_ids,
            }
            cards.append(card)
            rec_metadata.append({
                "wine_id": wine.id,
                "wine_name": wine.name,
                "producer": wine.producer
            })

        # Build actions
        actions = [
            {"type": "save", "label": "Save"},
            {"type": "add_cellar", "label": "Add to cellar"},
            {"type": "tell_more", "label": "Tell me more"}
        ]

        # Store recommendations in message metadata
        self.context_manager.add_message(
            session, "assistant", response_text,
            metadata={"recommendations": rec_metadata}
        )

        return self._build_response(
            session=session,
            response=response_text,
            intent="recommend",
            cards=cards,
            actions=actions
        )

    def _handle_education_general(
        self,
        session: ChatSession,
        message: str
    ) -> Dict[str, Any]:
        """Handle general wine education questions."""
        # Check if this is a general "learn about wine" request vs a specific question
        message_lower = message.lower()
        is_general_learning = any(phrase in message_lower for phrase in [
            "learn about wine", "teach me", "wine education", "learn wine",
            "want to learn", "like to learn", "new to wine", "wine basics"
        ])

        # Search WSET knowledge base
        try:
            knowledge_chunks = search_wset_knowledge(message, top_k=3)
            knowledge_context = "\n\n".join([
                f"**{chunk['heading']}**\n{chunk['text']}"
                for chunk in knowledge_chunks
            ])
        except Exception as e:
            print(f"WSET search error: {e}")
            knowledge_context = ""

        prompt = EDUCATION_GENERAL_PROMPT.format(
            knowledge_context=knowledge_context or "No specific knowledge found.",
            question=message
        )

        response_text = self._generate_response(prompt)

        self.context_manager.add_message(session, "assistant", response_text)

        # Add educational topic suggestions for general learning requests
        actions = None
        if is_general_learning:
            actions = [
                {"type": "learn_topic", "label": "Red vs White"},
                {"type": "learn_topic", "label": "How to Taste Wine"},
                {"type": "learn_topic", "label": "Food Pairings"},
                {"type": "learn_topic", "label": "Wine Regions"},
                {"type": "learn_topic", "label": "Reading a Label"},
            ]

        return self._build_response(
            session=session,
            response=response_text,
            intent="educate_general",
            actions=actions
        )

    def _handle_education_specific(
        self,
        session: ChatSession,
        message: str,
        history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Handle questions about a specific wine."""
        # Get recent wine references
        wine_refs = self.context_manager.get_recent_wine_references(session)

        wine = None
        wine_ref = None

        # First try recent wine references
        if wine_refs:
            wine_ref = wine_refs[0]
            if wine_ref.get("wine_id"):
                wine = self.db.query(Wine).filter(Wine.id == wine_ref["wine_id"]).first()

        # If no recent reference, try to find the wine by searching the message
        if not wine:
            # Search for wines matching words in the message
            # Look for wines where the name appears in the message
            all_wines = self.db.query(Wine).all()
            message_lower = message.lower()

            best_match = None
            best_score = 0

            for w in all_wines:
                wine_name_lower = w.name.lower()
                # Check if significant parts of the wine name appear in the message
                name_words = [word for word in wine_name_lower.split() if len(word) > 3]
                if name_words:
                    matches = sum(1 for word in name_words if word in message_lower)
                    score = matches / len(name_words)
                    if score > best_score and score >= 0.5:  # At least 50% of words match
                        best_score = score
                        best_match = w

            if best_match:
                wine = best_match
                wine_ref = {"wine_id": wine.id, "wine_name": wine.name}

        if not wine and not wine_ref:
            return self._build_response(
                session=session,
                response="I couldn't find that wine in my database. Could you tell me more about it, or try a different wine?",
                intent="educate_specific"
            )

        if wine:
            wine_details = f"""
Name: {wine.name}
Producer: {wine.producer}
Vintage: {wine.vintage}
Type: {wine.wine_type}
Varietal: {wine.varietal}
Region: {wine.region}, {wine.country}
Price: ${wine.price_usd}
"""
            metadata = wine.wine_metadata or {}
            if metadata:
                wine_details += f"""
Body: {metadata.get('body', 'N/A')}
Characteristics: {', '.join(metadata.get('characteristics', []))}
Flavor Notes: {', '.join(metadata.get('flavor_notes', []))}
"""
        else:
            # Build details from wine reference (e.g., from photo scan)
            details_parts = [f"Name: {wine_ref.get('wine_name', 'Unknown')}"]
            if wine_ref.get('producer'):
                details_parts.append(f"Producer: {wine_ref['producer']}")
            if wine_ref.get('vintage'):
                details_parts.append(f"Vintage: {wine_ref['vintage']}")
            if wine_ref.get('wine_type'):
                details_parts.append(f"Type: {wine_ref['wine_type']}")
            if wine_ref.get('varietal'):
                details_parts.append(f"Varietal: {wine_ref['varietal']}")
            if wine_ref.get('region') or wine_ref.get('country'):
                location = ', '.join(filter(None, [wine_ref.get('region'), wine_ref.get('country')]))
                details_parts.append(f"Region: {location}")

            wine_details = '\n'.join(details_parts)

        prompt = f"""You are Pip, a wine expert. The user is asking about a specific wine.

Wine Details:
{wine_details}

User Question: {message}

Provide helpful information about this wine. Be conversational and informative."""

        response_text = self._generate_response(prompt)

        self.context_manager.add_message(session, "assistant", response_text)

        return self._build_response(
            session=session,
            response=response_text,
            intent="educate_specific"
        )

    def _handle_cellar_query(
        self,
        session: ChatSession,
        message: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle cellar query requests."""
        if not self.user:
            return self._build_response(
                session=session,
                response="Sign in to view your cellar. Once you do, I can help you manage your wine collection!",
                intent="cellar_query",
                requires_auth=True
            )

        # Check if user is asking about wines they want to try
        message_lower = message.lower()
        is_saved_query = any(phrase in message_lower for phrase in ['saved', 'want to try', 'to try', 'wines to try', 'try list'])

        # Get status from entities or infer from message
        status = entities.get("status")
        if status is None and is_saved_query:
            status = "saved"

        # Query SavedBottle table for saved wines
        if status == "saved":
            saved_bottles = self.db.query(SavedBottle).filter(
                SavedBottle.user_id == self.user.id
            ).order_by(SavedBottle.saved_at.desc()).limit(10).all()

            if not saved_bottles:
                response_text = "You haven't added any wines to try yet. When I recommend wines, you can add the ones you'd like to try!"
                self.context_manager.add_message(session, "assistant", response_text)
                return self._build_response(
                    session=session,
                    response=response_text,
                    intent="cellar_query",
                    actions=[{"type": "recommend", "label": "Find wines to try"}]
                )

            response_text = f"Here are {len(saved_bottles)} wine{'s' if len(saved_bottles) > 1 else ''} you want to try:"

            cards = []
            for saved in saved_bottles[:5]:
                card = self._saved_bottle_to_card(saved)
                cards.append(card)

            self.context_manager.add_message(session, "assistant", response_text)

            return self._build_response(
                session=session,
                response=response_text,
                intent="cellar_query",
                cards=cards
            )

        # Use CellarAgent for flexible, LLM-based query parsing
        cellar_agent = CellarAgent(self.db, self.user)
        result = cellar_agent.query_cellar(query=message, limit=10)

        if not result["bottles"]:
            response_text = "No wines found matching that criteria. Want to find some wines to add?"
            self.context_manager.add_message(session, "assistant", response_text)
            return self._build_response(
                session=session,
                response=response_text,
                intent="cellar_query",
                actions=[{"type": "recommend", "label": "Find wines"}]
            )

        # Build response text based on filters applied
        filters = result.get("filters_applied", {})
        count = result["count"]

        # Generate a natural response based on what was queried
        # Build wine descriptor (varietal, type, origin)
        wine_desc_parts = []
        if filters.get("varietal"):
            wine_desc_parts.append(filters["varietal"])
        if filters.get("wine_type") and not filters.get("varietal"):
            wine_desc_parts.append(filters["wine_type"])
        if filters.get("region"):
            wine_desc_parts.append(f"from {filters['region']}")
        elif filters.get("country"):
            wine_desc_parts.append(f"from {filters['country']}")

        wine_desc = " ".join(wine_desc_parts) if wine_desc_parts else ""

        # Build rating descriptor
        rating_desc = ""
        if filters.get("min_rating"):
            rating_desc = "you've enjoyed"
        elif filters.get("max_rating"):
            rating_desc = "you weren't a fan of"

        # Build status descriptor
        status_desc = ""
        if filters.get("status") == "tried":
            status_desc = "tried"
        elif filters.get("status") == "owned":
            status_desc = "own"

        # Construct natural response
        if wine_desc and rating_desc:
            response_text = f"Here are the {wine_desc} wines {rating_desc}:"
        elif wine_desc and status_desc:
            response_text = f"Here are the {wine_desc} wines you've {status_desc}:"
        elif rating_desc:
            response_text = f"Here are the wines {rating_desc}:"
        elif status_desc:
            response_text = f"Here are the wines you've {status_desc}:"
        elif wine_desc:
            response_text = f"Here are your {wine_desc} wines:"
        else:
            response_text = f"Here are your wines:"

        # Convert results to cards
        cards = []
        for bottle_data in result["bottles"][:5]:
            # Query the actual bottle to use _bottle_to_card
            bottle = self.db.query(CellarBottle).filter(
                CellarBottle.id == bottle_data["bottle_id"]
            ).first()
            if bottle:
                card = self._bottle_to_card(bottle)
                cards.append(card)

        self.context_manager.add_message(session, "assistant", response_text)

        return self._build_response(
            session=session,
            response=response_text,
            intent="cellar_query",
            cards=cards
        )

    def _handle_cellar_add(
        self,
        session: ChatSession,
        message: str,
        history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Handle adding wine to cellar."""
        if not self.user:
            return self._build_response(
                session=session,
                response="Sign in to add wines to your cellar!",
                intent="cellar_add",
                requires_auth=True
            )

        wine_ref = None
        wine_id = None

        # First, try to find wine name mentioned in the message
        message_lower = message.lower()
        search_text = re.sub(r"['\"\-]", " ", message_lower)

        # Search in saved wines first
        saved_bottles = self.db.query(SavedBottle).filter(
            SavedBottle.user_id == self.user.id
        ).all()

        best_match_score = 0
        best_match_wine = None

        for saved in saved_bottles:
            wine = saved.wine
            if wine:
                name_lower = wine.name.lower()
                name_clean = re.sub(r"['\"\-]", " ", name_lower)
                name_words = [w for w in name_clean.split() if len(w) > 2]
                if name_words:
                    matches = sum(1 for word in name_words if word in search_text)
                    match_score = matches / len(name_words)
                    if match_score >= 0.5 and matches > best_match_score:
                        best_match_score = matches
                        best_match_wine = wine

        # Also search all wines in database if no saved match
        if not best_match_wine:
            all_wines = self.db.query(Wine).all()
            for wine in all_wines:
                name_lower = wine.name.lower()
                name_clean = re.sub(r"['\"\-]", " ", name_lower)
                name_words = [w for w in name_clean.split() if len(w) > 2]
                if name_words:
                    matches = sum(1 for word in name_words if word in search_text)
                    match_score = matches / len(name_words)
                    if match_score >= 0.5 and matches > best_match_score:
                        best_match_score = matches
                        best_match_wine = wine

        if best_match_wine:
            wine_ref = {
                "wine_id": best_match_wine.id,
                "wine_name": best_match_wine.name,
                "producer": best_match_wine.producer
            }
            wine_id = best_match_wine.id

        # Fall back to recent wine references from session
        if not wine_ref:
            wine_refs = self.context_manager.get_recent_wine_references(session)
            if wine_refs:
                wine_ref = wine_refs[0]
                wine_id = wine_ref.get("wine_id")

        if not wine_ref:
            return self._build_response(
                session=session,
                response="Which wine would you like to add? Tell me the name or let's find one first.",
                intent="cellar_add"
            )

        if wine_id:
            # Check if already in cellar
            existing = self.db.query(CellarBottle).filter(
                CellarBottle.user_id == self.user.id,
                CellarBottle.wine_id == wine_id
            ).first()

            if existing:
                existing.quantity += 1
                self.db.commit()
                response_text = f"Added another bottle of {wine_ref.get('wine_name')} to your cellar. You now have {existing.quantity}."
            else:
                # Add to cellar
                cellar_bottle = CellarBottle(
                    user_id=self.user.id,
                    wine_id=wine_id,
                    status="owned",
                    quantity=1
                )
                self.db.add(cellar_bottle)
                self.db.commit()
                self.db.refresh(cellar_bottle)

                # Track for undo
                self.context_manager.track_action(session, "cellar_add", {
                    "cellar_bottle_id": str(cellar_bottle.id),
                    "wine_id": wine_id,
                    "wine_name": wine_ref.get("wine_name")
                })

                response_text = f"Added {wine_ref.get('wine_name')} to your cellar!"
        else:
            # Custom wine entry - save all available details
            cellar_bottle = CellarBottle(
                user_id=self.user.id,
                custom_wine_name=wine_ref.get("wine_name"),
                custom_wine_producer=wine_ref.get("producer"),
                custom_wine_vintage=wine_ref.get("vintage"),
                custom_wine_type=wine_ref.get("wine_type"),
                custom_wine_varietal=wine_ref.get("varietal"),
                custom_wine_region=wine_ref.get("region"),
                custom_wine_country=wine_ref.get("country"),
                status="owned",
                quantity=1
            )
            self.db.add(cellar_bottle)
            self.db.commit()
            self.db.refresh(cellar_bottle)

            self.context_manager.track_action(session, "cellar_add", {
                "cellar_bottle_id": str(cellar_bottle.id),
                "wine_name": wine_ref.get("wine_name")
            })

            response_text = f"Added {wine_ref.get('wine_name')} to your cellar!"

        self.context_manager.add_message(session, "assistant", response_text)

        return self._build_response(
            session=session,
            response=response_text,
            intent="cellar_add",
            actions=[
                {"type": "view_cellar", "label": "View cellar"},
                {"type": "undo", "label": "Undo"}
            ]
        )

    def _handle_cellar_remove(
        self,
        session: ChatSession,
        message: str,
        history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Handle removing wine from cellar (with confirmation)."""
        if not self.user:
            return self._build_response(
                session=session,
                response="Sign in to manage your cellar.",
                intent="cellar_remove",
                requires_auth=True
            )

        # Check if this is a confirmation
        session_context = session.context or {}
        pending_delete = session_context.get("pending_delete")

        message_lower = message.lower()
        is_confirmation = any(word in message_lower for word in ["yes", "confirm", "remove", "delete"])
        if pending_delete and is_confirmation:
            # Execute the delete
            bottle_id_str = pending_delete.get("bottle_id")
            try:
                bottle_id = uuid.UUID(bottle_id_str)
            except (ValueError, TypeError):
                bottle_id = None

            bottle = self.db.query(CellarBottle).filter(
                CellarBottle.id == bottle_id,
                CellarBottle.user_id == self.user.id
            ).first() if bottle_id else None

            if bottle:
                wine_name = bottle.wine.name if bottle.wine else bottle.custom_wine_name
                self.db.delete(bottle)
                self.db.commit()

                # Clear pending delete
                self.context_manager.update_session_context(session, {"pending_delete": None})

                response_text = f"Removed {wine_name} from your cellar."
                self.context_manager.add_message(session, "assistant", response_text)

                return self._build_response(
                    session=session,
                    response=response_text,
                    intent="cellar_remove"
                )

        # First, try to find the wine name in the user's message
        # Get all bottles in cellar to match against
        all_bottles = self.db.query(CellarBottle).filter(
            CellarBottle.user_id == self.user.id
        ).all()

        bottle = None
        message_lower = message.lower()

        # Try to match wine name from message against cellar bottles
        for b in all_bottles:
            wine_name = b.wine.name if b.wine else b.custom_wine_name
            if wine_name:
                # Check if wine name appears in the message
                wine_name_lower = wine_name.lower()
                name_words = [w for w in wine_name_lower.split() if len(w) > 2]
                if name_words:
                    matches = sum(1 for word in name_words if word in message_lower)
                    if matches >= len(name_words) * 0.5:  # At least 50% match
                        bottle = b
                        break

        # If no match from message, fall back to recent wine references
        if not bottle:
            wine_refs = self.context_manager.get_recent_wine_references(session)

            if not wine_refs:
                return self._build_response(
                    session=session,
                    response="Which wine would you like to remove from your cellar?",
                    intent="cellar_remove"
                )

            wine_ref = wine_refs[0]
            wine_id = wine_ref.get("wine_id")

            # Find in cellar
            query = self.db.query(CellarBottle).filter(
                CellarBottle.user_id == self.user.id
            )
            if wine_id:
                query = query.filter(CellarBottle.wine_id == wine_id)
            else:
                query = query.filter(
                    CellarBottle.custom_wine_name.ilike(f"%{wine_ref.get('wine_name', '')}%")
                )

            bottle = query.first()

        if not bottle:
            return self._build_response(
                session=session,
                response="I couldn't find that wine in your cellar.",
                intent="cellar_remove"
            )

        wine_name = bottle.wine.name if bottle.wine else bottle.custom_wine_name

        # Store pending delete and ask for confirmation
        self.context_manager.update_session_context(session, {
            "pending_delete": {
                "bottle_id": str(bottle.id),
                "wine_name": wine_name
            }
        })

        response_text = f"Remove {wine_name} from your cellar? Say 'yes' to confirm."
        self.context_manager.add_message(session, "assistant", response_text)

        return self._build_response(
            session=session,
            response=response_text,
            intent="cellar_remove",
            confirmation_required=True,
            actions=[
                {"type": "confirm", "label": "Yes, remove"},
                {"type": "cancel", "label": "Cancel"}
            ]
        )

    def _handle_rate(
        self,
        session: ChatSession,
        message: str,
        history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Handle rating a wine."""
        if not self.user:
            return self._build_response(
                session=session,
                response="Sign in to rate wines and track your preferences!",
                intent="rate",
                requires_auth=True
            )

        # First, try to find the wine name in recent conversation (including current message)
        cellar_bottle = None
        wine_name = None
        wine_id = None

        # Get all bottles in cellar to match against
        all_bottles = self.db.query(CellarBottle).filter(
            CellarBottle.user_id == self.user.id
        ).all()

        # Also get all wines from the database
        all_wines = self.db.query(Wine).all()

        # Build search text from recent history
        search_text = message.lower()
        for msg in history[-4:]:  # Check last 4 messages
            search_text += " " + msg.get("content", "").lower()
        # Clean up special characters for better matching
        search_text = re.sub(r"['\"\-]", " ", search_text)

        # Try to match against cellar bottles first - find BEST match, not first
        best_match_score = 0
        best_match_bottle = None
        best_match_name = None

        for b in all_bottles:
            bottle_wine_name = b.wine.name if b.wine else b.custom_wine_name
            if bottle_wine_name:
                name_lower = bottle_wine_name.lower()
                # Clean up special characters for matching
                name_clean = re.sub(r"['\"\-]", " ", name_lower)
                name_words = [w for w in name_clean.split() if len(w) > 2]
                if name_words:
                    matches = sum(1 for word in name_words if word in search_text)
                    match_score = matches / len(name_words)
                    # Must be at least 40% match and better than previous best
                    if match_score >= 0.4 and matches > best_match_score:
                        best_match_score = matches
                        best_match_bottle = b
                        best_match_name = bottle_wine_name

        if best_match_bottle:
            cellar_bottle = best_match_bottle
            wine_name = best_match_name

        # If no cellar match, try to match against all wines in database
        if not cellar_bottle:
            best_match_score = 0
            for w in all_wines:
                name_lower = w.name.lower()
                name_clean = re.sub(r"['\"\-]", " ", name_lower)
                name_words = [word for word in name_clean.split() if len(word) > 2]
                if name_words:
                    matches = sum(1 for word in name_words if word in search_text)
                    match_score = matches / len(name_words)
                    if match_score >= 0.4 and matches > best_match_score:
                        best_match_score = matches
                        wine_id = w.id
                        wine_name = w.name

        # Fall back to recent wine from session context first
        if not cellar_bottle and not wine_id:
            session_context = session.context or {}
            recent_wine = session_context.get("recent_wine")
            if recent_wine:
                wine_id = recent_wine.get("wine_id")
                wine_name = recent_wine.get("wine_name")
                bottle_id_str = recent_wine.get("bottle_id")

                # Try to find by bottle_id first (most accurate)
                if bottle_id_str:
                    try:
                        bottle_id = uuid.UUID(bottle_id_str)
                        cellar_bottle = self.db.query(CellarBottle).filter(
                            CellarBottle.id == bottle_id,
                            CellarBottle.user_id == self.user.id
                        ).first()
                    except (ValueError, TypeError):
                        pass

                # Fall back to wine_id
                if not cellar_bottle and wine_id:
                    cellar_bottle = self.db.query(CellarBottle).filter(
                        CellarBottle.user_id == self.user.id,
                        CellarBottle.wine_id == wine_id
                    ).first()

        # Fall back to message metadata references
        if not cellar_bottle and not wine_id:
            wine_refs = self.context_manager.get_recent_wine_references(session)
            if wine_refs:
                wine_ref = wine_refs[0]
                wine_id = wine_ref.get("wine_id")
                wine_name = wine_ref.get("wine_name")

                if wine_id:
                    cellar_bottle = self.db.query(CellarBottle).filter(
                        CellarBottle.user_id == self.user.id,
                        CellarBottle.wine_id == wine_id
                    ).first()

        if not cellar_bottle and not wine_id and not wine_name:
            return self._build_response(
                session=session,
                response="Which wine would you like to rate?",
                intent="rate"
            )

        # Extract rating from message
        rating = self._extract_rating(message)

        # Check if user indicated they drank/tried the wine
        message_lower = message.lower()
        consumed_indicators = ["i drank", "i tried", "i had", "i finished", "just drank", "just tried", "just had"]
        user_consumed = any(indicator in message_lower for indicator in consumed_indicators)

        # Find or create cellar entry
        if not cellar_bottle and wine_id:
            cellar_bottle = self.db.query(CellarBottle).filter(
                CellarBottle.user_id == self.user.id,
                CellarBottle.wine_id == wine_id
            ).first()

        # If user consumed wine but no rating yet, ask for rating (don't move to tried yet)
        if user_consumed and rating is None:
            if cellar_bottle:
                # Store wine reference and mark that user consumed it
                self.context_manager.update_session_context(session, {
                    "recent_wine": {
                        "wine_id": str(cellar_bottle.wine_id) if cellar_bottle.wine_id else None,
                        "wine_name": wine_name,
                        "bottle_id": str(cellar_bottle.id),
                        "user_consumed": True
                    }
                })

                response_text = f"Nice! How would you rate {wine_name} out of 5?"
            else:
                # Wine not in cellar, create entry but keep as "owned" until they confirm
                cellar_bottle = CellarBottle(
                    user_id=self.user.id,
                    wine_id=wine_id,
                    custom_wine_name=wine_name if not wine_id else None,
                    status="owned",
                    quantity=1
                )
                self.db.add(cellar_bottle)
                self.db.commit()

                self.context_manager.update_session_context(session, {
                    "recent_wine": {
                        "wine_id": str(wine_id) if wine_id else None,
                        "wine_name": wine_name,
                        "bottle_id": str(cellar_bottle.id),
                        "user_consumed": True
                    }
                })

                response_text = f"Added {wine_name} to your cellar! How would you rate it out of 5?"

            self.context_manager.add_message(session, "assistant", response_text)
            return self._build_response(
                session=session,
                response=response_text,
                intent="rate"
            )

        # If no rating provided at all, ask for one
        if rating is None:
            self.context_manager.update_session_context(session, {
                "recent_wine": {
                    "wine_id": str(wine_id) if wine_id else None,
                    "wine_name": wine_name
                }
            })
            return self._build_response(
                session=session,
                response=f"How would you rate {wine_name or 'this wine'} out of 5?",
                intent="rate"
            )

        # We have a rating - save it
        was_owned = False
        if not cellar_bottle:
            # Create a "tried" entry (new wine, not owned)
            cellar_bottle = CellarBottle(
                user_id=self.user.id,
                wine_id=wine_id,
                custom_wine_name=wine_name if not wine_id else None,
                status="tried",
                quantity=0,
                rating=rating
            )
            self.db.add(cellar_bottle)
        else:
            cellar_bottle.rating = rating
            was_owned = cellar_bottle.status == "owned"
            # Don't automatically move to tried - ask first

        self.db.commit()

        wine_name = wine_name or "this wine"

        # If this was an owned bottle, ask if they want to move to tried
        if was_owned:
            response_text = f"Got it! Rated {wine_name} {rating}/5. Are you finished with this bottle? Shall I move it to the tried section?"

            # Store pending move for confirmation
            self.context_manager.update_session_context(session, {
                "pending_move_to_tried": {
                    "bottle_id": str(cellar_bottle.id),
                    "wine_name": wine_name
                }
            })

            self.context_manager.add_message(session, "assistant", response_text)

            return self._build_response(
                session=session,
                response=response_text,
                intent="rate",
                actions=[
                    {"type": "confirm_tried", "label": "Yes, move to tried"},
                    {"type": "keep_owned", "label": "No, keep in cellar"},
                ]
            )

        response_text = f"Got it! Rated {wine_name} {rating}/5."

        self.context_manager.add_message(session, "assistant", response_text)

        return self._build_response(
            session=session,
            response=response_text,
            intent="rate"
        )

    def _handle_decide(
        self,
        session: ChatSession,
        message: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle 'what should I drink' requests."""
        if not self.user:
            return self._build_response(
                session=session,
                response="Sign in and I can help you pick from your cellar!",
                intent="decide",
                requires_auth=True
            )

        # Get user's owned bottles
        bottles = self.db.query(CellarBottle).filter(
            CellarBottle.user_id == self.user.id,
            CellarBottle.status == "owned",
            CellarBottle.quantity > 0
        ).all()

        if not bottles:
            return self._build_response(
                session=session,
                response="Your cellar is empty! Let's find some wines to add.",
                intent="decide",
                actions=[{"type": "recommend", "label": "Find wines"}]
            )

        # Build context for decision
        food_pairing = entities.get("food_pairing")
        occasion = entities.get("occasion")

        # Build bottle info with names for matching later
        bottle_info = []
        for b in bottles[:10]:
            wine_name = b.wine.name if b.wine else b.custom_wine_name
            wine_type = (b.wine.wine_type if b.wine else b.custom_wine_type) or "wine"
            bottle_info.append({
                "bottle": b,
                "name": wine_name,
                "type": wine_type
            })

        bottles_text = [f"- {info['name']} ({info['type']})" for info in bottle_info]

        prompt = f"""You are Pip, helping pick a wine from the user's cellar.

User's owned wines:
{chr(10).join(bottles_text)}

User's request: {message}
{"Food pairing: " + food_pairing if food_pairing else ""}
{"Occasion: " + occasion if occasion else ""}

Recommend 1-2 specific wines from their cellar and explain why they'd be good choices.
Be conversational and helpful. Do not use emojis."""

        response_text = self._generate_response(prompt)

        # Find which wines were mentioned in the response
        # Match by checking if significant parts of wine names appear in response
        response_lower = response_text.lower()
        recommended_bottles = []

        for info in bottle_info:
            wine_name = info['name']
            # Check if key parts of the wine name appear in the response
            # Split into words and check for matches (excluding short common words)
            name_words = [w.lower() for w in wine_name.split() if len(w) > 3]
            if name_words:
                matches = sum(1 for word in name_words if word in response_lower)
                # If more than half the significant words match, it's likely mentioned
                if matches >= len(name_words) * 0.5:
                    recommended_bottles.append(info['bottle'])

        # Only include cards for wines actually recommended (max 2)
        cards = [self._bottle_to_card(b) for b in recommended_bottles[:2]]

        self.context_manager.add_message(session, "assistant", response_text)

        return self._build_response(
            session=session,
            response=response_text,
            intent="decide",
            cards=cards
        )

    def _handle_correct(
        self,
        session: ChatSession,
        message: str,
        history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Handle corrections and undo requests."""
        message_lower = message.lower()

        # Check for undo
        if "undo" in message_lower:
            last_action = self.context_manager.pop_last_action(session)

            if not last_action:
                return self._build_response(
                    session=session,
                    response="Nothing to undo right now.",
                    intent="correct"
                )

            # Reverse the action
            if last_action["type"] == "cellar_add":
                bottle_id = last_action["data"].get("cellar_bottle_id")
                if bottle_id:
                    bottle = self.db.query(CellarBottle).filter(
                        CellarBottle.id == bottle_id
                    ).first()
                    if bottle:
                        self.db.delete(bottle)
                        self.db.commit()

                wine_name = last_action["data"].get("wine_name", "that wine")
                response_text = f"Undone! Removed {wine_name} from your cellar."
            else:
                response_text = "Undone!"

            self.context_manager.add_message(session, "assistant", response_text)

            return self._build_response(
                session=session,
                response=response_text,
                intent="correct"
            )

        # Handle filter corrections (e.g., "actually under $30")
        entities = self._extract_entities(message)

        if entities:
            # Re-run recommendation with new filters
            return self._handle_recommend(session, message, entities)

        return self._build_response(
            session=session,
            response="What would you like to change?",
            intent="correct"
        )

    def _handle_image(
        self,
        session: ChatSession,
        message: str,
        image_base64: str
    ) -> Dict[str, Any]:
        """Handle image uploads for wine label recognition."""
        from app import _analyze_wine_image

        result = _analyze_wine_image(image_base64)

        confidence = result.get("confidence", 0)
        wine_name = result.get("name")

        if confidence < 0.3 or not wine_name:
            # Failed to identify
            response_text = """I couldn't identify that wine label clearly. A few tips:
- Make sure the label is well-lit and in focus
- Try to capture the front label with the wine name
- Hold the camera steady

Or you can just tell me the wine name and I'll help from there!"""

            self.context_manager.add_message(session, "assistant", response_text)

            return self._build_response(
                session=session,
                response=response_text,
                intent="photo"
            )

        # Successfully identified - extract all available info
        producer = result.get("producer") or ""
        vintage = result.get("vintage")
        wine_type = result.get("wine_type") or ""
        varietal = result.get("varietal") or ""
        region = result.get("region") or ""
        country = result.get("country") or ""
        additional_info = result.get("additional_info") or ""

        # Build response text
        response_text = f"I found **{wine_name}**"
        if vintage:
            response_text += f" ({vintage})"
        response_text += "! What would you like to do with it?"

        # Store wine reference with all available details
        self.context_manager.add_message(
            session, "assistant", response_text,
            metadata={
                "wine_reference": {
                    "wine_name": wine_name,
                    "producer": producer,
                    "vintage": vintage,
                    "wine_type": wine_type,
                    "varietal": varietal,
                    "region": region,
                    "country": country
                }
            }
        )

        return self._build_response(
            session=session,
            response=response_text,
            intent="photo",
            cards=[{
                "type": "identified_wine",
                "wine_name": wine_name,
                "producer": producer,
                "vintage": vintage,
                "wine_type": wine_type,
                "varietal": varietal,
                "region": region,
                "country": country,
                "confidence": confidence,
                "explanation": additional_info if additional_info else None
            }]
            # No message-level actions - they're rendered on the card itself
        )

    def _handle_ambiguous(
        self,
        session: ChatSession,
        message: str,
        intent_result: IntentResult
    ) -> Dict[str, Any]:
        """Handle ambiguous requests."""
        # Special handling for "new wine or from cellar" ambiguity
        if intent_result.clarification_reason == "new_or_cellar":
            # Check if user has wines in their cellar
            has_cellar_wines = False
            if self.user:
                cellar_count = self.db.query(CellarBottle).filter(
                    CellarBottle.user_id == self.user.id,
                    CellarBottle.status == "owned",
                    CellarBottle.quantity > 0
                ).count()
                has_cellar_wines = cellar_count > 0

            if has_cellar_wines:
                response_text = "Would you like me to recommend something new to try, or help you pick from wines you already have?"

                # Store the original message in session context for follow-up
                self.context_manager.set_pending_request(session, message, intent_result.entities)

                self.context_manager.add_message(session, "assistant", response_text)

                return self._build_response(
                    session=session,
                    response=response_text,
                    intent="clarify_source",
                    requires_clarification=True,
                    actions=[
                        {"type": "recommend_new", "label": "Recommend something new"},
                        {"type": "pick_from_cellar", "label": "Pick from my cellar"}
                    ]
                )
            else:
                # No cellar wines, just recommend new
                return self._handle_recommend(session, message, intent_result.entities)

        # Default ambiguous handling
        prompt = CLARIFICATION_PROMPT.format(
            message=message,
            intent=intent_result.intent,
            reason=intent_result.clarification_reason or "Could not understand the request"
        )

        response_text = self._generate_response(prompt)

        self.context_manager.add_message(session, "assistant", response_text)

        return self._build_response(
            session=session,
            response=response_text,
            intent="ambiguous",
            requires_clarification=True
        )

    def _handle_unknown(
        self,
        session: ChatSession,
        message: str
    ) -> Dict[str, Any]:
        """Handle unknown intents."""
        response_text = """I'm not sure I understood that. I can help you with:
- **Finding wines** - Just describe what you're looking for
- **Wine questions** - Ask me anything about wine
- **Your cellar** - Manage your collection
- **Scanning labels** - Upload a photo of a wine label

What would you like to do?"""

        self.context_manager.add_message(session, "assistant", response_text)

        return self._build_response(
            session=session,
            response=response_text,
            intent="unknown"
        )

    def _generate_response(self, prompt: str) -> str:
        """Generate a response using the LLM."""
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are Pip, a friendly and knowledgeable wine mentor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Response generation error: {e}")
            return "I'm having trouble responding right now. Please try again."

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if json_match:
            text = json_match.group(1)

        # Also try to find raw JSON object
        json_obj_match = re.search(r'\{[\s\S]*\}', text)
        if json_obj_match:
            text = json_obj_match.group()

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {}

    def _extract_rating(self, message: str) -> Optional[float]:
        """Extract a rating from a message."""
        # Look for patterns like "4 stars", "4/5", "4 out of 5", "give it a 4"
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:stars?|/5|out of 5)',
            r'(?:rate|give|score).*?(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:rating)?'
        ]

        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                rating = float(match.group(1))
                if 1 <= rating <= 5:
                    return rating

        return None

    def _get_user_wine_ids(self) -> Tuple[set, set]:
        """Get sets of wine IDs in user's saved and cellar."""
        saved_ids = set()
        cellar_ids = set()

        if self.user:
            saved_bottles = self.db.query(SavedBottle).filter(
                SavedBottle.user_id == self.user.id
            ).all()
            saved_ids = {sb.wine_id for sb in saved_bottles}

            cellar_bottles = self.db.query(CellarBottle).filter(
                CellarBottle.user_id == self.user.id
            ).all()
            cellar_ids = {cb.wine_id for cb in cellar_bottles if cb.wine_id}

        return saved_ids, cellar_ids

    def _bottle_to_card(self, bottle: CellarBottle) -> Dict[str, Any]:
        """Convert a CellarBottle to a card dict."""
        if bottle.wine:
            return {
                "type": "cellar",
                "bottle_id": str(bottle.id),
                "wine_id": bottle.wine.id,
                "wine_name": bottle.wine.name,
                "producer": bottle.wine.producer,
                "vintage": bottle.wine.vintage,
                "wine_type": bottle.wine.wine_type,
                "varietal": bottle.wine.varietal,
                "region": bottle.wine.region,
                "price_usd": bottle.wine.price_usd,
                "status": bottle.status,
                "rating": bottle.rating
            }
        else:
            return {
                "type": "cellar",
                "bottle_id": str(bottle.id),
                "wine_name": bottle.custom_wine_name,
                "producer": bottle.custom_wine_producer,
                "vintage": bottle.custom_wine_vintage,
                "wine_type": bottle.custom_wine_type,
                "varietal": bottle.custom_wine_varietal,
                "region": bottle.custom_wine_region,
                "country": bottle.custom_wine_country,
                "status": bottle.status,
                "rating": bottle.rating
            }

    def _saved_bottle_to_card(self, saved: SavedBottle) -> Dict[str, Any]:
        """Convert a SavedBottle to a card dict."""
        wine = saved.wine
        return {
            "type": "saved",
            "saved_id": str(saved.id),
            "wine_id": wine.id,
            "wine_name": wine.name,
            "producer": wine.producer,
            "vintage": wine.vintage,
            "wine_type": wine.wine_type,
            "varietal": wine.varietal,
            "region": wine.region,
            "country": wine.country,
            "price_usd": wine.price_usd,
            "saved_at": saved.saved_at.isoformat() if saved.saved_at else None,
            "notes": saved.notes,
        }

    def _build_response(
        self,
        session: ChatSession,
        response: str,
        intent: str,
        cards: Optional[List[Dict]] = None,
        actions: Optional[List[Dict]] = None,
        requires_auth: bool = False,
        requires_clarification: bool = False,
        confirmation_required: bool = False,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build the standard response format."""
        return {
            "response": response,
            "intent": intent,
            "session_id": str(session.id),
            "cards": cards or [],
            "actions": actions or [],
            "requires_auth": requires_auth,
            "requires_clarification": requires_clarification,
            "confirmation_required": confirmation_required,
            "error": error
        }
