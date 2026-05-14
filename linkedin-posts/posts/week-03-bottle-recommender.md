# Week 3: Bottle Recommendation Engine

**Posted:** ~3 months ago  
**Impressions:** 3,243  
**Project:** Two-agent wine recommendation system

---

Week 3 of my goal to build and ship something new with AI every week, and I'm excited about how my AI sommelier has progressed.

Try it here: https://lnkd.in/gjzr-NZM

Last week, I decided to build a bottle recommendation engine. The goal: describe what I want in plain English ("easy-drinking red for pizza night") and get real bottles back. I also wanted it to actually look nice.

I ran into a problem quickly: free-form text + LLMs are great at sounding smart, but terrible at reliably recommending specific things. So I split the system into two agents.

Agent 1: Preference Interpreter 
- takes natural language input ("bold red for steak, under $40")
- pulls in relevant wine knowledge from my education corpus
- translates vibes into structured intent (body, tannin, acidity, style)
- outputs a constrained, machine-readable query

Agent 2: Wine Searcher
- embeds that structured query
- searches a real wine catalog (Kaggle dataset)
- filters by price and wine type
- returns the top 3 matches with a clear why this works explanation

Without this separation, the model either hallucinated recommendations or produced vague "you might like…" answers with no grounding.

The UI was its own lesson.
I wanted the tool to feel refined but cozy, like my favorite wine bars in SF. I pulled visual references (colors, typefaces, layouts), fed them into Stitch (Google's AI design tool), and iterated until I had solid mocks.

My first attempt to implement them failed badly. The framework I'd been using (Streamlit) couldn't support the level of styling I wanted. With Claude Code, I refactored to a different framework in ~20 minutes and shipped something much more polished. 

This week, I spent:
- $0.11 embedding ~1,000 real wines into a searchable vector DB
- $7 hosting the demo
- ~6 hours building and testing

Before I move on to the next project, there's one more feature I want to ship.
Matt Cummings asked early on to be able to take a picture of a bottle and get instant context, no typing required. I'm going to build that next.

More next weekend 🍷🤖
