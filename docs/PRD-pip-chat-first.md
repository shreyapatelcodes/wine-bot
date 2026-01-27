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

### Out of scope (POC)
- Proactive follow-up questions from Pip
- Periodic check-ins ("You've tried 5 wines this month...")
- Conversation memory beyond preferences
- Social features (sharing, friends)
- Multiple purchase integrations (just Vivino for now)
- Push notifications
- Advanced inventory tracking (drink windows, storage location)

---

## Open Questions

1. **Onboarding:** Should Pip ask preference questions upfront, or learn purely through usage?
2. **Conversation persistence:** Should users see past conversations, or just current session?
3. **Cellar view:** Is the in-chat card view sufficient, or do some users need a dedicated browse view?

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
