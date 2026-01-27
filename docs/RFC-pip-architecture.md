# RFC: Pip Chat-First Architecture

**Version:** 1.0
**Date:** 2026-01-27
**Status:** Draft
**Related:** PRD-pip-chat-first.md

---

## Summary

This RFC describes the technical architecture for rebuilding wine-app as a chat-first experience. We're keeping the existing backend foundation (auth, database, Pinecone integration) and extending it with new capabilities while replacing the multi-page frontend with a single chat interface.

---

## Goals

1. Single chat interface replaces all pages
2. Pip can understand intent and route to appropriate capability
3. Natural language extraction for price, region, type, occasion
4. Pip can take actions (add to cellar, rate, query cellar)
5. Profile builds implicitly from ratings
6. Maintain existing auth, database, and wine catalog infrastructure

## Non-Goals (POC)

- Streaming responses
- Conversation persistence beyond current session
- Complex multi-turn context management
- Real-time inventory sync with external systems

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ ChatPage │  │CellarPage│  │DetailPage│  │SavedPage │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │           │
│       └─────────────┴─────────────┴─────────────┘           │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTP
┌──────────────────────────┼───────────────────────────────────┐
│                     wine-app/api                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │  Auth   │  │ Cellar  │  │ Vision  │  │  Recs   │        │
│  │Endpoints│  │Endpoints│  │Endpoints│  │Endpoint │        │
│  └─────────┘  └─────────┘  └─────────┘  └────┬────┘        │
│                                              │              │
└──────────────────────────────────────────────┼──────────────┘
                                               │ HTTP
┌──────────────────────────────────────────────┼──────────────┐
│                  wine-recommender                            │
│  ┌────────────────────┐    ┌────────────────────┐           │
│  │PreferenceInterpreter│───▶│   WineSearcher    │           │
│  │     (Agent 1)       │    │    (Agent 2)      │           │
│  └────────────────────┘    └────────────────────┘           │
│                                     │                        │
│                              ┌──────┴──────┐                │
│                              │  Pinecone   │                │
│                              └─────────────┘                │
└──────────────────────────────────────────────────────────────┘
```

**Problems with current architecture:**
1. Frontend has multiple disconnected pages
2. Recommendation endpoint only recommends — can't educate, take actions, or query cellar
3. PreferenceInterpreter doesn't extract filters from natural language (just passes through)
4. No intent classification — everything goes to recommendations
5. No profile synthesis capability

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │                   ChatInterface                     │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐           │     │
│  │  │MessageList│ │CardViews │ │InputArea │           │     │
│  │  └──────────┘ └──────────┘ └──────────┘           │     │
│  └────────────────────────────────────────────────────┘     │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTP POST /api/v1/chat
┌──────────────────────────┼───────────────────────────────────┐
│                     wine-app/api                             │
│                          │                                   │
│               ┌──────────▼──────────┐                       │
│               │   Chat Orchestrator  │                       │
│               │  (Intent Classifier) │                       │
│               └──────────┬──────────┘                        │
│                          │                                   │
│    ┌─────────┬───────────┼───────────┬─────────┬─────────┐  │
│    ▼         ▼           ▼           ▼         ▼         ▼  │
│ ┌─────┐ ┌────────┐ ┌──────────┐ ┌────────┐ ┌──────┐ ┌─────┐│
│ │Recs │ │Educate │ │CellarOps │ │Profile │ │Decide│ │Photo││
│ │Agent│ │ Agent  │ │  Agent   │ │ Agent  │ │Agent │ │Agent││
│ └──┬──┘ └───┬────┘ └────┬─────┘ └───┬────┘ └──┬───┘ └──┬──┘│
│    │        │           │           │         │        │    │
│    │    ┌───┴───┐   ┌───┴───┐   ┌───┴───┐    │    ┌───┴───┐│
│    │    │Wine   │   │Cellar │   │Profile│    │    │Vision ││
│    │    │Educator│  │  DB   │   │  DB   │    │    │  API  ││
│    │    └───────┘   └───────┘   └───────┘    │    └───────┘│
│    │                                         │              │
└────┼─────────────────────────────────────────┼──────────────┘
     │ HTTP                                    │
┌────┼─────────────────────────────────────────┼──────────────┐
│    │            wine-recommender             │              │
│    ▼                                         ▼              │
│  ┌────────────────────┐    ┌────────────────────┐          │
│  │PreferenceInterpreter│───▶│   WineSearcher    │          │
│  │  + NLP Extraction   │    │ + Profile Boost   │          │
│  └────────────────────┘    └────────────────────┘          │
│                                     │                       │
│                              ┌──────┴──────┐               │
│                              │  Pinecone   │               │
│                              └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Chat Orchestrator (New)

**Location:** `wine-app/api/agents/orchestrator.py`

**Responsibility:** Receives user message, classifies intent, routes to appropriate agent, formats response.

```python
class ChatOrchestrator:
    def process(self, message: str, user_id: str, attachments: list[Attachment]) -> ChatResponse:
        # 1. Classify intent
        intent = self.intent_classifier.classify(message, attachments)

        # 2. Route to appropriate agent
        match intent.type:
            case "recommend":
                return self.recommendation_agent.handle(intent, user_id)
            case "educate_general":
                return self.education_agent.handle_general(intent)
            case "educate_specific":
                return self.education_agent.handle_specific(intent, user_id)
            case "cellar_add":
                return self.cellar_agent.add(intent, user_id)
            case "cellar_query":
                return self.cellar_agent.query(intent, user_id)
            case "rate":
                return self.cellar_agent.rate(intent, user_id)
            case "profile_query":
                return self.profile_agent.query(user_id)
            case "decide":
                return self.decide_agent.handle(intent, user_id)
            case "analyze_photo":
                return self.photo_agent.handle(attachments, user_id)
            case "off_topic":
                return self.handle_off_topic()
            case "unclear":
                return self.handle_clarification(intent)
```

**Intent Classification (LLM-based):**

```python
INTENT_CLASSIFICATION_PROMPT = """
Classify the user's intent. Return JSON with:
- type: one of [recommend, educate_general, educate_specific, cellar_add, cellar_query, rate, profile_query, decide, analyze_photo, off_topic, unclear]
- extracted_entities: relevant extracted info

User message: {message}
Has photo attachment: {has_photo}
"""
```

---

### 2. Enhanced PreferenceInterpreter

**Location:** `wine-recommender/agents/preference_interpreter.py`

**Changes:** Add NLP extraction for price, region, type, occasion.

```python
class PreferenceInterpreter:
    def interpret(self, user_description: str, user_prefs: UserPreferences) -> SearchQuery:
        # NEW: Extract filters from natural language
        extracted = self._extract_filters(user_description)

        # Merge extracted with explicit preferences (extracted takes precedence)
        price_range = extracted.price_range or (user_prefs.budget_min, user_prefs.budget_max)
        wine_type = extracted.wine_type or user_prefs.wine_type_pref
        region = extracted.region  # NEW
        occasion = extracted.occasion  # NEW

        # Generate semantic search query
        query_text = self._generate_query(user_description, self.wine_knowledge)

        return SearchQuery(
            query_text=query_text,
            price_range=price_range,
            wine_type_filter=wine_type,
            region_filter=region,  # NEW
            occasion=occasion,  # NEW
        )

    def _extract_filters(self, description: str) -> ExtractedFilters:
        """Use LLM to extract structured filters from natural language."""
        prompt = f"""
        Extract wine search filters from this request. Return JSON:
        {{
            "price_min": number or null,
            "price_max": number or null,
            "wine_type": "red" | "white" | "rosé" | "sparkling" | null,
            "region": string or null,
            "country": string or null,
            "occasion": string or null,
            "food_pairing": string or null
        }}

        Examples:
        - "under $40" → {{"price_max": 40}}
        - "affordable red" → {{"price_max": 25, "wine_type": "red"}}
        - "California Pinot" → {{"region": "California", "varietal": "Pinot Noir"}}
        - "something for steak" → {{"food_pairing": "steak"}}

        User request: {description}
        """
        return self.llm.extract(prompt, ExtractedFilters)
```

---

### 3. Education Agent (New)

**Location:** `wine-app/api/agents/education_agent.py`

**Responsibility:** Answer wine questions without recommending.

```python
class EducationAgent:
    def __init__(self, wine_educator: WineEducator):
        self.wine_educator = wine_educator  # Existing WSET knowledge base

    def handle_general(self, intent: Intent) -> ChatResponse:
        """Answer general wine questions."""
        # Query wine educator knowledge base
        context = self.wine_educator.query(intent.question)

        # Generate educational response (no recommendations)
        response = self.llm.generate(
            prompt=EDUCATION_PROMPT,
            context=context,
            question=intent.question
        )

        return ChatResponse(
            message=response,
            cards=[]  # No wine cards for education
        )

    def handle_specific(self, intent: Intent, wine: Wine) -> ChatResponse:
        """Tell user about a specific bottle."""
        # Generate bottle-specific education
        response = self.llm.generate(
            prompt=BOTTLE_EDUCATION_PROMPT,
            wine=wine,
            question=intent.question  # e.g., "what should I pair this with?"
        )

        return ChatResponse(
            message=response,
            cards=[WineCard(wine)]  # Show the wine being discussed
        )
```

---

### 4. Cellar Agent (New)

**Location:** `wine-app/api/agents/cellar_agent.py`

**Responsibility:** Handle cellar operations through conversation.

```python
class CellarAgent:
    def add(self, intent: Intent, user_id: str) -> ChatResponse:
        """Add wine to cellar."""
        wine = intent.resolved_wine  # Resolved by orchestrator
        status = intent.extracted_status or "owned"

        bottle = CellarBottle(
            user_id=user_id,
            wine_id=wine.id,
            status=status,
            quantity=intent.extracted_quantity or 1
        )
        db.session.add(bottle)
        db.session.commit()

        return ChatResponse(
            message=f"Added {wine.name} to your cellar!",
            cards=[CellarCard(bottle)]
        )

    def query(self, intent: Intent, user_id: str) -> ChatResponse:
        """Query cellar with natural language filters."""
        filters = intent.extracted_filters  # e.g., {"wine_type": "white", "status": "owned"}

        bottles = CellarBottle.query.filter_by(user_id=user_id)
        if filters.wine_type:
            bottles = bottles.join(Wine).filter(Wine.wine_type == filters.wine_type)
        if filters.status:
            bottles = bottles.filter(CellarBottle.status == filters.status)

        bottles = bottles.all()

        if not bottles:
            return ChatResponse(
                message="You haven't added any bottles yet. Send me a photo of a bottle or ask for recommendations to get started!",
                cards=[]
            )

        # Generate natural language summary
        summary = self._generate_summary(bottles, intent.question)

        return ChatResponse(
            message=summary,
            cards=[CellarCard(b) for b in bottles[:10]]  # Limit cards shown
        )

    def rate(self, intent: Intent, user_id: str) -> ChatResponse:
        """Rate a wine and extract preference signals."""
        bottle = self._resolve_bottle(intent, user_id)

        bottle.rating = intent.extracted_rating
        bottle.tasting_notes = intent.extracted_notes
        bottle.tried_date = datetime.utcnow()
        bottle.status = "tried"

        # Extract preference signals for profile
        signals = self._extract_preference_signals(bottle, intent)
        self.profile_service.update(user_id, signals)

        db.session.commit()

        confirmation = f"Got it — you gave {bottle.wine.name} {intent.extracted_rating} stars."
        if intent.extracted_notes:
            confirmation += f" I'll remember you liked the {intent.extracted_notes}."

        return ChatResponse(message=confirmation, cards=[])
```

---

### 5. Profile Agent (New)

**Location:** `wine-app/api/agents/profile_agent.py`

**Responsibility:** Build and surface user taste profile.

```python
class ProfileAgent:
    def query(self, user_id: str) -> ChatResponse:
        """Describe user's taste profile."""
        profile = self.profile_service.get(user_id)

        if not profile.has_data:
            return ChatResponse(
                message="I'm still getting to know your taste! Rate a few bottles and I'll start building your profile.",
                cards=[]
            )

        description = self._generate_profile_description(profile)
        return ChatResponse(message=description, cards=[])

    def _generate_profile_description(self, profile: UserProfile) -> str:
        """Generate natural language profile description."""
        parts = []

        if profile.preferred_styles:
            parts.append(f"You tend to prefer {', '.join(profile.preferred_styles)} wines.")

        if profile.preferred_attributes:
            parts.append(f"You like wines that are {', '.join(profile.preferred_attributes)}.")

        if profile.avoided_attributes:
            parts.append(f"You've mentioned you don't love {', '.join(profile.avoided_attributes)}.")

        if profile.explored_varietals:
            parts.append(f"You've been exploring {', '.join(profile.explored_varietals)} lately.")

        if profile.price_comfort:
            parts.append(f"You usually spend around ${profile.price_comfort[0]}-${profile.price_comfort[1]}.")

        return " ".join(parts)


class ProfileService:
    def update(self, user_id: str, signals: PreferenceSignals):
        """Update user profile with new preference signals."""
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)

        # Merge new signals with existing profile
        # High ratings (4-5) → add wine attributes to "preferred"
        # Low ratings (1-2) → add wine attributes to "avoided"
        # Explicit notes → extract and prioritize

        profile.merge_signals(signals)
        db.session.commit()

    def _extract_signals_from_rating(self, bottle: CellarBottle, rating: int, notes: str) -> PreferenceSignals:
        """Infer preferences from rating + wine attributes."""
        wine = bottle.wine
        signals = PreferenceSignals()

        if rating >= 4:
            signals.preferred.extend([wine.body, wine.sweetness])
            signals.preferred.extend(wine.characteristics)
        elif rating <= 2:
            signals.avoided.extend([wine.body, wine.sweetness])
            if wine.tannin:
                signals.avoided.append(f"{wine.tannin}-tannin")

        # Extract explicit signals from notes using LLM
        if notes:
            explicit = self._extract_from_notes(notes)
            signals.merge(explicit)  # Explicit overrides inferred

        return signals
```

---

### 6. Decide Agent (New)

**Location:** `wine-app/api/agents/decide_agent.py`

**Responsibility:** Pick a wine from user's cellar for tonight.

```python
class DecideAgent:
    def handle(self, intent: Intent, user_id: str) -> ChatResponse:
        """Pick ONE wine from cellar with explanation."""
        owned_bottles = CellarBottle.query.filter_by(
            user_id=user_id,
            status="owned"
        ).all()

        if not owned_bottles:
            return ChatResponse(
                message="Your cellar is empty! Want me to recommend something to start your collection?",
                cards=[]
            )

        # Get user profile for preference matching
        profile = self.profile_service.get(user_id)

        # Score bottles against occasion/pairing
        occasion = intent.extracted_occasion  # e.g., "pasta", "salmon"
        scored = self._score_bottles(owned_bottles, occasion, profile)

        if not scored:
            # No good match - be honest
            best_available = owned_bottles[0]
            return ChatResponse(
                message=f"None of your bottles are ideal for {occasion}, but {best_available.wine.name} would work in a pinch. Want me to find a better match to buy?",
                cards=[CellarCard(best_available)]
            )

        winner = scored[0]
        explanation = self._generate_explanation(winner, occasion)

        return ChatResponse(
            message=f"I'd go with your {winner.wine.name} — {explanation}",
            cards=[CellarCard(winner)]
        )
```

---

## Data Model Changes

### New: UserProfile Table

```python
class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), unique=True, nullable=False)

    # Preference vectors (stored as JSONB)
    preferred_attributes = Column(JSONB, default=list)  # ["earthy", "full-bodied", "dry"]
    avoided_attributes = Column(JSONB, default=list)    # ["sweet", "high-tannin"]
    explored_varietals = Column(JSONB, default=list)    # ["Pinot Noir", "Barolo"]
    price_comfort = Column(JSONB, default=list)         # [20, 50] (min, max)

    # Metadata
    total_ratings = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="profile")
```

### Extended: SearchQuery Schema

```python
class SearchQuery(BaseModel):
    query_text: str
    price_range: tuple[float | None, float | None] = (None, None)
    wine_type_filter: str | None = None
    region_filter: str | None = None      # NEW
    country_filter: str | None = None     # NEW
    varietal_filter: str | None = None    # NEW
    occasion: str | None = None           # NEW
    food_pairing: str | None = None       # NEW
```

---

## API Changes

### New Endpoint: POST /api/v1/chat

Replaces direct calls to /recommendations, /cellar, etc. with a unified chat endpoint.

```python
@app.route("/api/v1/chat", methods=["POST"])
@jwt_required()
def chat():
    user_id = get_jwt_identity()
    data = request.json

    message = data.get("message", "")
    attachments = data.get("attachments", [])  # Base64 images

    orchestrator = ChatOrchestrator()
    response = orchestrator.process(message, user_id, attachments)

    return jsonify({
        "message": response.message,
        "cards": [card.to_dict() for card in response.cards],
        "actions": response.suggested_actions,  # e.g., ["Save to cellar", "Tell me more"]
    })
```

**Request:**
```json
{
    "message": "Red wine under $40 for steak",
    "attachments": []
}
```

**Response:**
```json
{
    "message": "Here's a great option for steak night...",
    "cards": [
        {
            "type": "wine",
            "wine": { "id": "...", "name": "...", "price": 35, ... },
            "explanation": "This Malbec has bold fruit and soft tannins..."
        }
    ],
    "actions": ["Save to cellar", "Find more options"]
}
```

### Existing Endpoints (Kept)

These remain for direct operations but are now secondary to /chat:
- GET/POST/PATCH/DELETE `/api/v1/cellar/*` — Direct cellar operations
- POST `/api/v1/vision/analyze` — Used internally by photo agent
- GET `/api/v1/wines/search` — Used internally by recommendation agent

---

## Frontend Changes

### Replace Multi-Page with Single Chat Interface

**Current structure (remove):**
```
pages/
  ChatPage.tsx      ← Keep, but expand significantly
  CellarPage.tsx    ← Remove
  WineDetailPage.tsx ← Remove
  SavedPage.tsx     ← Remove
```

**New structure:**
```
components/
  chat/
    ChatContainer.tsx       ← Main container
    MessageList.tsx         ← Message history
    MessageBubble.tsx       ← Individual messages
    InputArea.tsx           ← Text input + photo button

  cards/
    WineCard.tsx            ← Recommendation card (keep)
    CellarCard.tsx          ← Cellar bottle card (new)
    ProfileCard.tsx         ← Profile summary card (new)
    CardGrid.tsx            ← Grid view for "show my cellar"

  actions/
    QuickActions.tsx        ← Suggested action buttons
    PhotoCapture.tsx        ← Camera/upload interface

pages/
  ChatPage.tsx              ← The only page
```

### Chat State Management

```typescript
interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  cards?: Card[];
  actions?: string[];
  timestamp: Date;
}

interface Card {
  type: "wine" | "cellar" | "profile";
  data: WineCardData | CellarCardData | ProfileCardData;
}
```

---

## Migration Path

### Phase 1: Backend Extensions
1. Add ChatOrchestrator with intent classification
2. Add NLP extraction to PreferenceInterpreter
3. Add EducationAgent
4. Add CellarAgent
5. Add ProfileService and ProfileAgent
6. Add DecideAgent
7. Add POST /api/v1/chat endpoint
8. Add UserProfile table migration

### Phase 2: Frontend Rebuild
1. Build new ChatContainer with card rendering
2. Build card components (CellarCard, ProfileCard)
3. Build action buttons and photo capture
4. Remove old pages (CellarPage, WineDetailPage, SavedPage)
5. Update routing to single ChatPage

### Phase 3: Integration & Polish
1. Connect frontend to new /chat endpoint
2. Test all 9 capabilities
3. Refine intent classification prompts
4. Add error handling for edge cases
5. Polish card UI and transitions

---

## Open Technical Questions

1. **LLM choice for intent classification:** Use same model as recommendations (GPT-4) or faster/cheaper model for classification step?

2. **Conversation context:** How much history to include in each request? Full session or last N messages?

3. **Card rendering:** Should cards be embedded in messages or rendered separately in a fixed area?

4. **Offline/optimistic updates:** Should "add to cellar" update UI immediately or wait for server confirmation?

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Intent classification errors | Include "unclear" intent with clarifying question fallback |
| LLM latency for every message | Consider classification-only for simple intents, skip LLM for direct commands |
| Profile building takes time | Set expectations in UI ("I'm still learning your taste") |
| Scope creep | Strict POC scope — defer streaming, persistence, notifications |

---

## Success Criteria

1. User can complete all 9 capabilities without leaving chat
2. "Under $40 California red" returns wines matching those filters
3. Rating a wine updates profile (visible when asking "what do I like?")
4. Empty states are handled gracefully
5. Off-topic questions redirect politely
