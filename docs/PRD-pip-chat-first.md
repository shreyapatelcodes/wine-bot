# PRD: Pip — Chat-First Wine Discovery

**Version:** 1.0
**Date:** 2026-01-27
**Status:** Draft

---

## Overview

### Vision

Pip is your personal wine mentor who lives in your pocket. One interface, one relationship, everything through conversation. The app doesn't have separate screens for browsing, managing, or rating — Pip handles all of it conversationally.

### Problem Statement

Wine is intimidating. Walking into a wine shop without knowledge feels overwhelming. Existing wine apps focus on catalog browsing or collection management, but they don't help you *learn* or build a relationship with your evolving taste.

Current state of wine-app:
- Multiple disconnected experiences (Chat, Cellar, Detail pages)
- Agent only recommends — doesn't teach, remember, or take actions
- Rating flow is awkward (separate page, manual navigation)
- Natural language understanding is weak (price/region filtering doesn't work)
- No sense of building a relationship or profile over time

### Core Job to Be Done

> "I don't know much about wine but I want to learn. Help me explore, remember what I've tried, and use that knowledge to make better recommendations over time."

This is a **discovery + learning** app, not a collection management app. The cellar is Pip's memory. Ratings are Pip asking how something was. Recommendations are Pip teaching through doing.

---

## Target User

**Primary persona:** Wine-curious beginner

- Interested in wine but feels overwhelmed by choices
- Wants to develop their palate and learn what they like
- Shops at wine stores or online but doesn't know what to pick
- Values guidance over raw information
- Wants their history and preferences to matter

**Not optimizing for:**
- Wine experts who want detailed tasting note logging
- Collectors managing large cellars with inventory tracking
- Sommeliers or industry professionals

---

## Product Principles

1. **Conversation over navigation** — If the user has to tap through screens, we've failed
2. **Teaching through doing** — Every recommendation is a learning moment
3. **Memory builds trust** — Pip remembers, so the user doesn't have to
4. **Honest over salesy** — If there's no good match, say so
5. **Simple over comprehensive** — Do fewer things exceptionally well

---

## Capabilities

Pip can do 9 things. Everything flows through chat.

### 1. Recommend
**Intent:** "Find me something new"

| Example prompts |
|-----------------|
| "Red wine under $40 for a steak dinner" |
| "Something light and refreshing for summer" |
| "A good starter wine for someone who likes sweet drinks" |

**Behavior:**
- Extracts price, region, type, occasion from natural language
- Returns 1-3 wine recommendations with explanations
- Includes Vivino link to purchase
- "Save to cellar?" action available

**Error states:**
- No matches → "I couldn't find a perfect match for [X]. Want me to relax the price limit?"
- Vague query → Pip asks clarifying question

---

### 2. Educate (General)
**Intent:** "Teach me about wine"

| Example prompts |
|-----------------|
| "Why is Burgundy so expensive?" |
| "What's the difference between Syrah and Shiraz?" |
| "How do I read a wine label?" |

**Behavior:**
- Answers the question directly
- Does NOT recommend a bottle (unless asked)
- Draws from wine education knowledge base (WSET)

**Error states:**
- Not about wine → "I'm your wine guide — I'm not sure about [topic], but I'd love to help with anything wine-related!"

---

### 3. Educate (Specific Bottle)
**Intent:** "Tell me about this bottle"

| Example prompts |
|-----------------|
| "Tell me about this wine" (with photo) |
| "What should I pair with this Barolo?" |
| "Is this wine worth $50?" |

**Behavior:**
- Provides context about the wine (region, style, what to expect)
- Suggests food pairings
- Gives honest assessment ("This is a good value" or "You could find better at this price")
- Responsive to follow-up questions

**Error states:**
- Can't identify bottle → "I can't quite make out the label. Can you try a clearer photo, or tell me the name?"
- Not in catalog → "I don't have info on this specific bottle, but based on [varietal/region], here's what I'd expect..."

---

### 4. Remember (Add to Cellar)
**Intent:** "Save this for me"

| Example prompts |
|-----------------|
| "Add this to my cellar" |
| "Save that recommendation" |
| [Photo] "I just bought this" |

**Behavior:**
- Adds wine to cellar with status (owned/wishlist)
- Confirms: "Added [wine] to your cellar!"
- Can set quantity if mentioned

**Error states:**
- Not logged in → Prompt to sign in
- Ambiguous "this" → "Which wine do you want me to add?"

---

### 5. Recall (Inventory)
**Intent:** "What do I have?"

| Example prompts |
|-----------------|
| "What's in my cellar?" |
| "Do I have any whites?" |
| "Show me my reds under $30" |

**Behavior:**
- Queries cellar with optional filters
- Renders wine cards in chat (secondary card view)
- Can answer aggregate questions ("You have 12 bottles, mostly reds")

**Error states:**
- Cellar empty → "You haven't added any bottles yet. You can send me a photo of a bottle or ask for recommendations to get started."

---

### 6. Recall (Profile)
**Intent:** "What do I like?"

| Example prompts |
|-----------------|
| "What kinds of wine do I like?" |
| "What's my taste profile?" |
| "Have I tried any Pinot Noir?" |

**Behavior:**
- Synthesizes from rating history
- "You tend to prefer earthy, medium-bodied reds. You've mentioned you don't love high tannin wines. You've been exploring a lot of Pinot Noir lately."

**Error states:**
- No ratings yet → "I'm still getting to know your taste! Rate a few bottles and I'll start building your profile."

---

### 7. Rate
**Intent:** "Log an experience"

| Example prompts |
|-----------------|
| "I just had the Barolo — 4 stars, loved the earthiness" |
| "That Riesling was too sweet, 2 stars" |
| "Rate my last bottle 5 stars" |

**Behavior:**
- Updates cellar entry with rating, notes, tried_date
- Extracts qualitative feedback for profile building
- Confirms: "Got it — you gave [wine] 4 stars. I'll remember you liked the earthiness."

**Profile inference:**
- Rating + wine attributes → inferred preference
- 4-5 stars on earthy wine → "prefers: earthy"
- 1-2 stars on sweet wine → "avoids: sweet"
- Qualitative notes override inference

**Error states:**
- Wine not in cellar → "I don't have [wine] in your cellar. Want me to add it?"
- Ambiguous → "Which wine are you rating?"

---

### 8. Decide (From Cellar)
**Intent:** "Help me choose tonight"

| Example prompts |
|-----------------|
| "What should I drink tonight?" |
| "Pick a wine for pasta from my cellar" |
| "I'm having salmon — what do I have that would work?" |

**Behavior:**
- Queries cellar for owned bottles
- Selects ONE bottle with explanation
- "I'd go with your 2019 Chablis — the bright acidity will cut through the richness of the salmon."

**Error states:**
- Cellar empty → "Your cellar is empty! Want me to recommend something to start your collection?"
- No good pairing → "None of your bottles are ideal for [dish], but [bottle] would work in a pinch. Want me to find a better match to buy?"

---

### 9. Analyze (Photo)
**Intent:** "What is this?"

| Example prompts |
|-----------------|
| [Photo] "What is this?" |
| [Photo] "Should I buy this?" |
| [Photo] "What do you think?" |

**Behavior:**
- Identifies wine from label (vision API)
- Provides education (same as Educate Specific)
- Compares to taste profile if available
- Offers to add to cellar

**Error states:**
- Can't read label → "I can't quite make out the label. Can you try a clearer photo, or tell me the name?"

---

## Conversation UX Requirements

For an agentic shopping experience to feel natural, these conversation behaviors are essential.

### Must-Have (POC)

#### 1. Multi-Turn Context
Pip maintains context across multiple messages within a session.

| Conversation | How Pip handles it |
|--------------|-------------------|
| "Recommend something" → "For what occasion?" → "Steak dinner" | Pip remembers the original request and combines with new info |
| "Show me my cellar" → "Any whites?" | Pip understands "whites" refers to filtering the cellar just shown |
| "Tell me about the second one" | Pip knows which wine was "second" in the previous list |

**Implementation:** Include last N messages (suggest N=10) as context in each request.

#### 2. Ambiguity Handling
When unclear, Pip asks instead of guessing wrong.

| Ambiguous input | Pip's response |
|-----------------|----------------|
| "Add this to my cellar" (3 wines shown) | "Which one — the Malbec, the Pinot, or the Cab?" |
| "Rate it 4 stars" (no recent wine context) | "Which wine are you rating?" |
| "Something cheap" (unclear threshold) | "What's your budget? Under $20? $30?" |

**Principle:** A clarifying question is better than a wrong action.

#### 3. Undo and Correction
Users can reverse actions and correct Pip's understanding.

| User says | Pip's response |
|-----------|----------------|
| "Actually, make that 3 stars not 4" | "Updated to 3 stars." |
| "Nevermind, don't add that" | "No problem, I won't add it." |
| "Remove that from my cellar" | "Are you sure you want to remove [wine]?" (confirm destructive action) |
| "No, I meant the Pinot not the Malbec" | "Got it — switching to the Pinot." |

**Principle:** Trust requires reversibility.

#### 4. Typing/Thinking Indicator
User sees feedback that Pip is processing their request.

- Show a typing indicator or "Pip is thinking..." state
- Appears immediately after user sends message
- Disappears when response arrives

**Why it matters:** 3-5 second LLM latency feels broken without feedback.

#### 5. First-Run Experience
New users get guided onboarding, not a blank chat.

```
User opens app for first time
→ Pip: "Hey! I'm Pip, your personal wine guide. I can help you discover
   wines you'll love, remember what you've tried, and learn as you go.

   What sounds good right now?"

   [Recommend something] [I have a question] [Show me how this works]
```

- Quick action buttons lower the barrier to first interaction
- Pip adapts to whatever the user picks
- No mandatory onboarding quiz — learn through conversation

### Should-Have (Polish)

#### 6. Streaming Responses
Text appears progressively as it's generated.

- Reduces perceived latency
- Feels more conversational (like watching someone type)
- Cards can appear after text completes

**Trade-off:** Adds implementation complexity. Acceptable to defer for POC but strongly improves feel.

#### 7. Confirmation for Destructive Actions
Pip confirms before irreversible changes.

| Action | Confirmation |
|--------|--------------|
| Remove from cellar | "Remove [wine] from your cellar? This can't be undone." [Yes] [No] |
| Clear all ratings | "This will clear your taste profile. Are you sure?" [Yes] [No] |
| Delete account | Requires explicit confirmation |

**Non-destructive actions (add, rate) can happen immediately** with ability to undo.

#### 8. Smart Photo Retry
When photo analysis fails, guide the user to success.

| Failure mode | Pip's response |
|--------------|----------------|
| Blurry image | "I can't quite read the label — it's a bit blurry. Try holding your phone steady and getting closer?" |
| Back of bottle | "I can see the back label, but I need the front to identify the wine. Can you flip it around?" |
| Not a wine | "That doesn't look like a wine bottle to me. Were you trying to show me something else?" |
| Partial success | "I can see this is a 2019 red from France, but I can't read the producer. Do you know the name?" |

**Principle:** Failed photo shouldn't be a dead end.

---

## User Flows

### Flow 1: First-time user
```
Opens app → Sees Pip welcome message
→ "I'm Pip, your wine guide. What are you in the mood for?"
→ User: "I don't know anything about wine"
→ Pip: "That's totally fine! Let's start simple..."
→ Asks a few light questions (red or white? sweet or dry?)
→ Makes first recommendation with explanation
→ Prompts to save and sign in
```

### Flow 2: Getting a recommendation
```
User: "Red wine under $40 for a steak dinner"
→ Pip extracts: type=red, price<40, occasion=steak
→ Searches catalog with filters
→ Returns 1-2 options with explanations + Vivino links
→ "Want me to add one to your cellar?"
```

### Flow 3: Rating after drinking
```
User: "Just finished that Malbec, it was amazing"
→ Pip: "Nice! How would you rate it? And what did you love about it?"
→ User: "5 stars, super smooth and fruity"
→ Pip logs rating + notes, infers preference for smooth/fruity
→ "Got it — 5 stars, smooth and fruity. I'll keep that in mind!"
```

### Flow 4: Picking from cellar
```
User: "What should I drink tonight with tacos?"
→ Pip queries cellar for owned bottles
→ Evaluates pairing potential
→ "Your Grenache would be perfect — it's got juicy fruit that'll play great with the spice."
```

### Flow 5: Learning moment
```
User: "Why is that Burgundy you recommended so expensive?"
→ Pip explains terroir, production methods, demand
→ Does NOT try to sell another bottle
→ "Does that make sense? Any other questions about Burgundy?"
```

---

## Success Metrics

### Primary (POC validation)
- Users return to chat multiple times per week
- Users rate bottles through conversation (not through forms)
- Natural language queries successfully extract filters (price, region, type)

### Secondary
- Cellar bottles added via chat > via manual entry
- Users ask "what should I drink" at least once
- Users ask educational questions (not just recommendations)

---

## Scope

### In scope (POC)
- Single chat interface (replace multi-page app)
- All 9 capabilities listed above
- NLP extraction for price, region, type
- Intent classification (recommend vs educate vs action)
- Implicit profile building from ratings
- Vivino links for purchase
- Photo analysis for bottle identification
- **Multi-turn context** (last N messages inform each request)
- **Ambiguity handling** (ask clarifying questions vs. guess wrong)
- **Undo/correction support** ("actually...", "nevermind")
- **Typing/thinking indicator** (feedback during LLM processing)
- **First-run experience** (guided onboarding with quick actions)
- **Confirmation for destructive actions** (remove from cellar, etc.)
- **Smart photo retry** (guide user when photo analysis fails)

### Should-have (if time permits)
- **Streaming responses** (text appears as generated)

### Out of scope (POC)
- Proactive outreach ("Hey, that winery you liked released something new...")
- Periodic check-ins ("You've tried 5 wines this month...")
- Conversation persistence across sessions (beyond preferences)
- Social features (sharing, friends)
- Multiple purchase integrations (just Vivino for now)
- Push notifications
- Advanced inventory tracking (drink windows, storage location)

---

## Open Questions

1. ~~**Onboarding:** Should Pip ask preference questions upfront, or learn purely through usage?~~ **Decided:** First-run experience with guided quick actions, then learn through usage.
2. **Conversation persistence:** Should users see past conversations, or just current session? (Leaning toward: current session only for POC, preferences persist)
3. **Cellar view:** Is the in-chat card view sufficient, or do some users need a dedicated browse view?
4. **Multi-turn context depth:** How many messages to include? (Suggest: 10)

---

## Appendix: Error Handling Summary

| Situation | Pip's Response |
|-----------|----------------|
| Off-topic question | "I'm your wine guide — happy to help with anything wine-related!" |
| No matching wines | "I couldn't find a perfect match. Want me to relax [constraint]?" |
| Empty cellar (decide) | "Your cellar is empty! Want me to recommend something?" |
| Empty cellar (recall) | "You haven't added any bottles yet. Send me a photo or ask for a rec!" |
| No good pairing in cellar | "None are ideal, but [X] would work. Want me to find something better?" |
| Can't identify photo | "I can't make out the label. Try another photo or tell me the name?" |
| No ratings for profile | "I'm still learning your taste! Rate a few bottles first." |
| Ambiguous reference | "Which wine do you mean?" |
