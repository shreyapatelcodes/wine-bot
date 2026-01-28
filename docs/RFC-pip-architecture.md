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
6. **Explanation attribution bug:** Agent 2 attributes system-inferred category knowledge to user preferences ("Based on your preference for bold fruit..." when user just said "California red")

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

### 2b. Honest Explanation Generation (Fix)

**Problem:** Currently, Agent 2 conflates what the user asked for with what the system inferred about a wine category.

```
User: "California red wine"
Agent 1: Queries WSET → "California reds are bold, oaky, ripe tannins..."
Agent 2: "Based on your preference for bold fruit and oak..." ← WRONG
User: "I never said that!"
```

**Root cause:** `create_agent2_explanation_prompt` receives both:
- `user_preferences`: What the user said ("California red wine")
- `search_query`: The enriched query from Agent 1 ("bold, oaky, ripe tannins...")

The LLM conflates these, attributing system inferences to the user.

**Fix:** Separate user constraints from category knowledge in the data flow.

**Change 1: Extend SearchQuery to include category knowledge**

```python
class SearchQuery(BaseModel):
    query_text: str                    # For vector search
    category_knowledge: str            # NEW: What we learned about the category
    user_request: str                  # NEW: Original user request (preserved)
    price_range: tuple[float, float]
    wine_type_filter: str | None
    region_filter: str | None
    # ... other filters
```

**Change 2: Agent 1 returns both query and knowledge separately**

```python
class PreferenceInterpreter:
    def interpret(self, user_prefs: UserPreferences) -> SearchQuery:
        # Query WSET knowledge
        wset_chunks = search_wset_knowledge(user_prefs.description)
        category_knowledge = self._summarize_category(wset_chunks)

        # Generate search query
        query_text = self._generate_search_query(user_prefs.description, wset_chunks)

        return SearchQuery(
            query_text=query_text,
            category_knowledge=category_knowledge,  # What we learned
            user_request=user_prefs.description,    # What user said
            # ... filters
        )
```

**Change 3: New explanation prompt that maintains honesty**

```python
def create_agent2_explanation_prompt(
    user_request: str,           # What user actually said
    category_knowledge: str,     # What we know about that category
    wine: Wine
) -> str:
    return f"""Generate a 1-2 sentence explanation for why this wine is a good match.

CRITICAL: The user asked for "{user_request}". Only attribute preferences they explicitly stated.

Category context (for your understanding, not to attribute to user): {category_knowledge}

Wine: {wine.name} ({wine.varietal}, {wine.region})
Characteristics: {", ".join(wine.characteristics)}
Flavor notes: {", ".join(wine.flavor_notes)}

Rules:
- Reference what the user actually asked for
- You may briefly educate about the category ("California reds are known for...")
- Connect this wine to both the request and category
- NEVER say "based on your preference for X" unless user explicitly said X

Good: "You asked for a California red — this Napa Cab delivers the bold fruit and soft tannins the region is known for."
Bad: "Based on your preference for bold fruit and oak..." (user never said this)

Explanation:"""
```

**Example transformation:**

| Before | After |
|--------|-------|
| "Based on your preference for bold, oaky wines, this Napa Cab is perfect with its rich tannins." | "You asked for a California red — this Napa Cab is a classic example, with the bold fruit and soft oak the region is known for." |
| "This matches your love of earthy, full-bodied reds." | "You wanted something earthy — this Barolo delivers, with the truffle and leather notes Nebbiolo is famous for." |

**Key principle:** Be honest about what's user preference vs. system knowledge. Educate, don't fabricate.

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
@jwt_required(optional=True)  # Allow anonymous for recommendations, require auth for cellar ops
def chat():
    user_id = get_jwt_identity()  # May be None for anonymous
    data = request.json

    message = data.get("message", "")
    attachments = data.get("attachments", [])  # Base64 images
    conversation_history = data.get("history", [])  # Last N messages for context

    orchestrator = ChatOrchestrator()
    response = orchestrator.process(
        message=message,
        user_id=user_id,
        attachments=attachments,
        history=conversation_history  # For multi-turn context
    )

    return jsonify({
        "message": response.message,
        "cards": [card.to_dict() for card in response.cards],
        "actions": response.suggested_actions,
        "requires_auth": response.requires_auth,  # True if action needs login
        "confirmation": response.confirmation,  # For destructive actions
    })
```

**Request:**
```json
{
    "message": "Tell me more about the second one",
    "attachments": [],
    "history": [
        {"role": "user", "content": "Red wine under $40 for steak"},
        {"role": "assistant", "content": "Here are two great options...", "cards": [{"id": "wine-1", ...}, {"id": "wine-2", ...}]}
    ]
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
    "actions": ["Save to cellar", "Find more options"],
    "requires_auth": false,
    "confirmation": null
}
```

**Response requiring confirmation:**
```json
{
    "message": "Remove the 2019 Malbec from your cellar?",
    "cards": [],
    "actions": ["Yes, remove it", "No, keep it"],
    "requires_auth": true,
    "confirmation": {
        "action": "cellar_remove",
        "target_id": "bottle-123",
        "destructive": true
    }
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

## Conversation UX Implementation

### 1. Multi-Turn Context

**Frontend responsibility:** Send last N messages with each request.

```typescript
const MAX_HISTORY_MESSAGES = 10;

function sendMessage(message: string) {
  const history = messages.slice(-MAX_HISTORY_MESSAGES).map(m => ({
    role: m.role,
    content: m.content,
    cards: m.cards?.map(c => ({ id: c.data.id, type: c.type, name: c.data.name }))
  }));

  return api.post('/chat', { message, history, attachments });
}
```

**Backend responsibility:** Use history for context resolution.

```python
class ChatOrchestrator:
    def process(self, message: str, user_id: str, attachments: list, history: list) -> ChatResponse:
        # Include history in intent classification for context
        intent = self.intent_classifier.classify(
            message=message,
            attachments=attachments,
            history=history  # Helps resolve "the second one", "that wine", etc.
        )

        # If intent references previous items, resolve them
        if intent.has_reference:
            intent.resolved_items = self._resolve_references(intent, history)

        # Route to agent with full context
        return self._route_to_agent(intent, user_id, history)
```

**Reference resolution examples:**

| User says | History contains | Resolved to |
|-----------|------------------|-------------|
| "the second one" | 2 wine cards | wine cards[1] |
| "that Malbec" | 1 Malbec in cards | that specific wine |
| "add it" | 1 wine discussed | that wine |
| "both of them" | 2 wines shown | both wines |

### 2. Ambiguity Handling

**Intent classifier returns confidence + ambiguity flag:**

```python
class IntentClassification(BaseModel):
    type: str  # recommend, rate, cellar_add, etc.
    confidence: float  # 0-1
    is_ambiguous: bool
    ambiguity_reason: str | None  # "multiple_wines", "unclear_target", etc.
    clarifying_question: str | None  # Pre-generated question to ask

INTENT_CLASSIFICATION_PROMPT = """
Classify the user's intent. If the intent is unclear or could apply to multiple items, mark as ambiguous.

Return JSON:
{
    "type": "...",
    "confidence": 0.0-1.0,
    "is_ambiguous": true/false,
    "ambiguity_reason": "multiple_wines" | "unclear_rating" | "vague_criteria" | null,
    "clarifying_question": "Which wine..." | null,
    "extracted_entities": {...}
}

User message: {message}
Conversation history: {history}
"""
```

**Orchestrator handles ambiguity:**

```python
def process(self, message, user_id, attachments, history):
    intent = self.intent_classifier.classify(message, attachments, history)

    if intent.is_ambiguous:
        return ChatResponse(
            message=intent.clarifying_question,
            cards=[],
            actions=self._generate_disambiguation_options(intent, history)
        )

    # Proceed with clear intent
    return self._route_to_agent(intent, user_id, history)
```

### 3. Undo and Correction

**Pattern matching for corrections:**

```python
CORRECTION_PATTERNS = [
    r"actually[,]? (?:make that|change that to|I meant)",
    r"no[,]? (?:I meant|not that|the other)",
    r"nevermind|never mind|cancel that",
    r"undo|remove that|take that back",
]

class IntentClassifier:
    def classify(self, message, attachments, history):
        # Check for correction intent first
        if self._is_correction(message):
            return self._classify_correction(message, history)

        # Normal classification
        ...

    def _classify_correction(self, message, history):
        # Find the last action taken
        last_action = self._find_last_action(history)

        return IntentClassification(
            type="correction",
            correction_target=last_action,
            correction_type=self._parse_correction_type(message),  # "change_value", "undo", "switch_target"
        )
```

**Correction agent:**

```python
class CorrectionAgent:
    def handle(self, intent: IntentClassification, user_id: str) -> ChatResponse:
        match intent.correction_type:
            case "undo":
                return self._undo_last_action(intent.correction_target, user_id)
            case "change_value":
                return self._update_value(intent.correction_target, intent.new_value, user_id)
            case "switch_target":
                return self._switch_target(intent.correction_target, intent.new_target, user_id)
```

### 4. Typing/Thinking Indicator

**Frontend implementation:**

```typescript
function ChatContainer() {
  const [isLoading, setIsLoading] = useState(false);

  async function sendMessage(message: string) {
    setIsLoading(true);  // Show indicator immediately

    try {
      const response = await api.post('/chat', { message, history });
      addMessage({ role: 'assistant', ...response });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div>
      <MessageList messages={messages} />
      {isLoading && <TypingIndicator />}  {/* "Pip is thinking..." */}
      <InputArea onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 text-gray-500 p-4">
      <div className="typing-dots">  {/* Animated dots */}
        <span /><span /><span />
      </div>
      <span>Pip is thinking...</span>
    </div>
  );
}
```

### 5. First-Run Experience

**Backend: Check if user is new:**

```python
@app.route("/api/v1/chat", methods=["POST"])
def chat():
    user_id = get_jwt_identity()
    data = request.json

    # Check if this is first message (no history, new or anonymous user)
    is_first_message = not data.get("history") and not data.get("message")

    if is_first_message:
        return jsonify({
            "message": get_welcome_message(user_id),
            "cards": [],
            "actions": ["Recommend something", "I have a question", "Show me how this works"],
            "is_onboarding": True
        })

    # Normal flow
    ...

def get_welcome_message(user_id: str | None) -> str:
    if user_id:
        user = User.query.get(user_id)
        if user and user.profile and user.profile.total_ratings > 0:
            return f"Welcome back! Ready to explore more wines?"

    return """Hey! I'm Pip, your personal wine guide.

I can help you discover wines you'll love, remember what you've tried, and learn as you go.

What sounds good right now?"""
```

**Frontend: Render quick action buttons:**

```typescript
function QuickActions({ actions, onSelect }: { actions: string[], onSelect: (action: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2 p-4">
      {actions.map(action => (
        <button
          key={action}
          onClick={() => onSelect(action)}
          className="px-4 py-2 bg-purple-100 text-purple-700 rounded-full hover:bg-purple-200"
        >
          {action}
        </button>
      ))}
    </div>
  );
}
```

### 6. Confirmation for Destructive Actions

**Backend returns confirmation request:**

```python
class CellarAgent:
    def remove(self, intent: Intent, user_id: str) -> ChatResponse:
        bottle = self._resolve_bottle(intent, user_id)

        # Don't execute yet - ask for confirmation
        return ChatResponse(
            message=f"Remove {bottle.wine.name} from your cellar? This can't be undone.",
            cards=[CellarCard(bottle)],
            actions=["Yes, remove it", "No, keep it"],
            confirmation=ConfirmationRequest(
                action="cellar_remove",
                target_id=str(bottle.id),
                destructive=True
            )
        )

    def confirm_remove(self, bottle_id: str, user_id: str) -> ChatResponse:
        # Actually execute the removal
        bottle = CellarBottle.query.get(bottle_id)
        db.session.delete(bottle)
        db.session.commit()

        return ChatResponse(
            message=f"Done — {bottle.wine.name} has been removed from your cellar.",
            cards=[]
        )
```

**Frontend handles confirmation:**

```typescript
function handleResponse(response: ChatResponse) {
  if (response.confirmation?.destructive) {
    // Store pending confirmation
    setPendingConfirmation(response.confirmation);
  }

  addMessage({ role: 'assistant', ...response });
}

function handleQuickAction(action: string) {
  if (pendingConfirmation && action === "Yes, remove it") {
    // Send confirmation
    api.post('/chat', {
      message: action,
      confirmation: pendingConfirmation
    });
    setPendingConfirmation(null);
  } else {
    // Normal message
    sendMessage(action);
  }
}
```

### 7. Smart Photo Retry

**Vision agent returns guidance on failure:**

```python
class PhotoAgent:
    def handle(self, attachments: list, user_id: str) -> ChatResponse:
        if not attachments:
            return ChatResponse(
                message="I don't see a photo. Tap the camera icon to take one!",
                cards=[]
            )

        analysis = self.vision_service.analyze(attachments[0])

        if analysis.confidence < 0.3:
            return self._suggest_retry(analysis)

        if analysis.confidence < 0.7:
            return self._partial_match(analysis, user_id)

        return self._full_match(analysis, user_id)

    def _suggest_retry(self, analysis: VisionAnalysis) -> ChatResponse:
        # Determine why it failed and give specific guidance
        if analysis.failure_reason == "blurry":
            message = "I can't quite read the label — it's a bit blurry. Try holding your phone steady and getting closer to the label?"
        elif analysis.failure_reason == "wrong_side":
            message = "I can see the back label, but I need the front to identify the wine. Can you flip it around?"
        elif analysis.failure_reason == "not_wine":
            message = "That doesn't look like a wine bottle to me. Were you trying to show me something else?"
        elif analysis.failure_reason == "obscured":
            message = "Part of the label is covered. Can you show me the full front label?"
        else:
            message = "I'm having trouble reading this label. Can you try another photo with better lighting?"

        return ChatResponse(
            message=message,
            cards=[],
            actions=["Try another photo", "Type the wine name instead"]
        )

    def _partial_match(self, analysis: VisionAnalysis, user_id: str) -> ChatResponse:
        # We got some info but not everything
        partial_info = []
        if analysis.vintage:
            partial_info.append(f"a {analysis.vintage}")
        if analysis.wine_type:
            partial_info.append(analysis.wine_type)
        if analysis.country:
            partial_info.append(f"from {analysis.country}")

        info_str = " ".join(partial_info) if partial_info else "a wine"

        return ChatResponse(
            message=f"I can see this is {info_str}, but I can't read the producer name. Do you know what it's called?",
            cards=[],
            actions=["Try another photo"]
        )
```

### 8. Streaming Responses (Should-Have)

**If implemented, use Server-Sent Events:**

```python
@app.route("/api/v1/chat/stream", methods=["POST"])
def chat_stream():
    def generate():
        for chunk in orchestrator.process_streaming(message, user_id, history):
            yield f"data: {json.dumps(chunk)}\n\n"

    return Response(generate(), mimetype='text/event-stream')
```

```typescript
async function sendMessageStreaming(message: string) {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    body: JSON.stringify({ message, history }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let assistantMessage = { role: 'assistant', content: '', cards: [] };
  addMessage(assistantMessage);

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = JSON.parse(decoder.decode(value).replace('data: ', ''));

    if (chunk.type === 'text') {
      assistantMessage.content += chunk.content;
      updateLastMessage(assistantMessage);
    } else if (chunk.type === 'cards') {
      assistantMessage.cards = chunk.cards;
      updateLastMessage(assistantMessage);
    }
  }
}
```

**Note:** Streaming adds complexity. Acceptable to defer for POC and use loading indicator instead.

---

## Migration Path

### Phase 1: Backend Extensions
1. Add ChatOrchestrator with intent classification
2. Add NLP extraction to PreferenceInterpreter
3. Fix explanation attribution (separate user_request from category_knowledge in SearchQuery)
4. Add EducationAgent
5. Add CellarAgent (with confirmation flow for destructive actions)
6. Add ProfileService and ProfileAgent
7. Add DecideAgent
8. Add CorrectionAgent (undo/correction support)
9. Add POST /api/v1/chat endpoint (with history parameter)
10. Add UserProfile table migration
11. Add ambiguity detection to intent classifier
12. Add smart retry logic to PhotoAgent

### Phase 2: Frontend Rebuild
1. Build new ChatContainer with card rendering
2. Build card components (CellarCard, ProfileCard)
3. Build action buttons and photo capture
4. Add typing/thinking indicator
5. Add first-run experience with quick actions
6. Add confirmation dialog handling for destructive actions
7. Implement conversation history management (last N messages)
8. Remove old pages (CellarPage, WineDetailPage, SavedPage)
9. Update routing to single ChatPage

### Phase 3: Integration & Polish
1. Connect frontend to new /chat endpoint
2. Test all 9 capabilities
3. Test conversation UX flows (multi-turn, ambiguity, correction, confirmation)
4. Refine intent classification prompts
5. Refine ambiguity detection and clarifying questions
6. Add error handling for edge cases
7. Polish card UI and transitions
8. (Optional) Add streaming responses

---

## Open Technical Questions

1. **LLM choice for intent classification:** Use same model as recommendations (GPT-4) or faster/cheaper model for classification step?

2. ~~**Conversation context:** How much history to include in each request? Full session or last N messages?~~ **Decided:** Last 10 messages.

3. **Card rendering:** Should cards be embedded in messages or rendered separately in a fixed area?

4. **Offline/optimistic updates:** Should "add to cellar" update UI immediately or wait for server confirmation? (Suggest: optimistic update with rollback on failure)

5. **Correction scope:** How far back can user correct? Just the last action, or any action in history?

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Intent classification errors | Include "unclear" intent with clarifying question fallback; ambiguity detection |
| LLM latency for every message | Consider classification-only for simple intents, skip LLM for direct commands; typing indicator provides feedback |
| Profile building takes time | Set expectations in UI ("I'm still learning your taste") |
| Scope creep | Strict POC scope — defer streaming, persistence, notifications |
| Multi-turn context bloat | Limit to last 10 messages; summarize cards to IDs only |
| Correction complexity | Start with last-action-only corrections; expand scope later if needed |
| Photo retry frustration | Specific guidance based on failure reason; offer "type name instead" escape hatch |
| Confirmation fatigue | Only confirm destructive actions; non-destructive actions (add, rate) are immediate with undo option |

---

## Success Criteria

### Core Capabilities
1. User can complete all 9 capabilities without leaving chat
2. "Under $40 California red" returns wines matching those filters
3. Rating a wine updates profile (visible when asking "what do I like?")
4. Empty states are handled gracefully
5. Off-topic questions redirect politely
6. Explanations only attribute preferences user actually expressed (no fabricated preferences)

### Conversation UX
7. Multi-turn context works: "tell me about the second one" resolves correctly
8. Ambiguous requests trigger clarifying questions, not wrong actions
9. User can undo/correct: "actually, make that 3 stars" works
10. Typing indicator appears immediately when user sends a message
11. First-time users see welcome message with quick action buttons
12. Destructive actions (remove from cellar) require confirmation
13. Failed photo analysis provides actionable guidance for retry
