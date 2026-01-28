"""
Chat Orchestrator for Pip wine assistant.
Classifies user intent and routes to appropriate handlers.
"""

import json
import re
from typing import Optional, Dict, Any, List, Tuple
from openai import OpenAI
from sqlalchemy.orm import Session

from config import Config
from models.database import User, ChatSession, Wine, CellarBottle, SavedBottle
from agents.context_manager import ContextManager
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

        # Check for pending request clarification response
        message_lower = message.lower()
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
        # Import here to avoid circular imports
        from app import _get_recommender

        get_recommendations, UserPreferences = _get_recommender()

        # Build preferences from entities
        user_prefs = UserPreferences(
            description=message,
            budget_min=entities.get("price_min", 10.0),
            budget_max=entities.get("price_max", 200.0),
            food_pairing=entities.get("food_pairing"),
            wine_type_pref=entities.get("wine_type")
        )

        try:
            recommendations = get_recommendations(user_prefs, top_n=3)
        except Exception as e:
            print(f"Recommendation error: {e}")
            return self._build_response(
                session=session,
                response="I'm having trouble finding wines right now. Could you try rephrasing your request?",
                intent="recommend",
                error=str(e)
            )

        if not recommendations:
            response_text = "I couldn't find wines matching those exact criteria. Try broadening your search - maybe a wider price range or different style?"
            self.context_manager.add_message(session, "assistant", response_text)
            return self._build_response(
                session=session,
                response=response_text,
                intent="recommend"
            )

        # Build response with wine cards
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

        return self._build_response(
            session=session,
            response=response_text,
            intent="educate_general"
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
            wine_details = f"Wine: {wine_ref.get('wine_name', 'Unknown')}"

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

        # Check if user is asking about saved/wishlist wines
        message_lower = message.lower()
        is_saved_query = any(word in message_lower for word in ['saved', 'wishlist', 'want to try', 'to try'])

        # Get status from entities or infer from message
        status = entities.get("status")
        if status is None:
            if is_saved_query:
                status = "saved"
            else:
                status = "owned"

        # Query SavedBottle table for saved/wishlist wines
        if status == "saved":
            saved_bottles = self.db.query(SavedBottle).filter(
                SavedBottle.user_id == self.user.id
            ).order_by(SavedBottle.saved_at.desc()).limit(10).all()

            if not saved_bottles:
                response_text = "You haven't saved any wines yet. When I recommend wines, you can save the ones you want to try!"
                self.context_manager.add_message(session, "assistant", response_text)
                return self._build_response(
                    session=session,
                    response=response_text,
                    intent="cellar_query",
                    actions=[{"type": "recommend", "label": "Find wines to save"}]
                )

            response_text = f"You have {len(saved_bottles)} saved wine{'s' if len(saved_bottles) > 1 else ''}:"

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

        # Build query filters for CellarBottle
        query = self.db.query(CellarBottle).filter(
            CellarBottle.user_id == self.user.id
        )

        # Apply filters from entities
        wine_type = entities.get("wine_type")
        price_max = entities.get("price_max")

        if status:
            query = query.filter(CellarBottle.status == status)

        bottles = query.order_by(CellarBottle.added_at.desc()).limit(10).all()

        # Filter by wine type and price in Python (since some are custom entries)
        filtered_bottles = []
        for bottle in bottles:
            # Get wine type
            bottle_type = None
            bottle_price = None
            if bottle.wine:
                bottle_type = bottle.wine.wine_type
                bottle_price = bottle.wine.price_usd
            elif bottle.custom_wine_type:
                bottle_type = bottle.custom_wine_type
                bottle_price = bottle.purchase_price

            # Apply filters
            if wine_type and bottle_type and bottle_type.lower() != wine_type.lower():
                continue
            if price_max and bottle_price and bottle_price > price_max:
                continue

            filtered_bottles.append(bottle)

        if not filtered_bottles:
            response_text = "Your cellar is empty for those criteria. Want to find some wines to add?"
            self.context_manager.add_message(session, "assistant", response_text)
            return self._build_response(
                session=session,
                response=response_text,
                intent="cellar_query",
                actions=[{"type": "recommend", "label": "Find wines"}]
            )

        response_text = f"You have {len(filtered_bottles)} wine{'s' if len(filtered_bottles) > 1 else ''} matching that:"

        cards = []
        for bottle in filtered_bottles[:5]:
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

        # Get recent wine references
        wine_refs = self.context_manager.get_recent_wine_references(session)

        if not wine_refs:
            return self._build_response(
                session=session,
                response="Which wine would you like to add? Tell me the name or let's find one first.",
                intent="cellar_add"
            )

        wine_ref = wine_refs[0]
        wine_id = wine_ref.get("wine_id")

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

        if pending_delete and message.lower() in ["yes", "confirm", "remove it", "delete it"]:
            # Execute the delete
            bottle_id = pending_delete.get("bottle_id")
            bottle = self.db.query(CellarBottle).filter(
                CellarBottle.id == bottle_id,
                CellarBottle.user_id == self.user.id
            ).first()

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

        # Get wine reference to remove
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
                response=f"I couldn't find {wine_ref.get('wine_name')} in your cellar.",
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

        # Extract rating from message
        rating = self._extract_rating(message)

        if rating is None:
            return self._build_response(
                session=session,
                response="How would you rate this wine? You can say something like '4 stars' or 'I'd give it a 3.5'.",
                intent="rate"
            )

        # Get wine reference
        wine_refs = self.context_manager.get_recent_wine_references(session)

        if not wine_refs:
            return self._build_response(
                session=session,
                response="Which wine would you like to rate?",
                intent="rate"
            )

        wine_ref = wine_refs[0]
        wine_id = wine_ref.get("wine_id")

        # Find in cellar or create tried entry
        cellar_bottle = None
        if wine_id:
            cellar_bottle = self.db.query(CellarBottle).filter(
                CellarBottle.user_id == self.user.id,
                CellarBottle.wine_id == wine_id
            ).first()

        if not cellar_bottle:
            # Create a "tried" entry
            cellar_bottle = CellarBottle(
                user_id=self.user.id,
                wine_id=wine_id,
                custom_wine_name=wine_ref.get("wine_name") if not wine_id else None,
                status="tried",
                quantity=0,
                rating=rating
            )
            self.db.add(cellar_bottle)
        else:
            cellar_bottle.rating = rating
            if cellar_bottle.status == "owned":
                cellar_bottle.status = "tried"

        self.db.commit()

        wine_name = wine_ref.get("wine_name", "this wine")
        response_text = f"Got it! Rated {wine_name} {rating}/5. Would you like to add any tasting notes?"

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

        # Store wine reference
        self.context_manager.add_message(
            session, "assistant", response_text,
            metadata={
                "wine_reference": {
                    "wine_name": wine_name,
                    "producer": producer,
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
                "quantity": bottle.quantity,
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
                "status": bottle.status,
                "quantity": bottle.quantity,
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
