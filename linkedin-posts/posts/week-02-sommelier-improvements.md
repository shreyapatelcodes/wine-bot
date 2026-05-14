# Week 2: Sommelier Improvements

**Posted:** ~3 months ago  
**Impressions:** 1,418  
**Project:** Winebot - conciseness and follow-ups

---

I love wine, but it is really easy to feel intimidated by the jargon-heavy way people talk about it. That's why I'm working on building an AI sommelier. 

This is week 2/52 of a personal experiment: every weekend, I build and ship something with AI.

Last weekend, I shared a demo. It worked, but when using it, 2 problems jumped out immediately:
- It used way too much wine jargon
- It was too verbose

Fixing the wine-snob energy was easy: I added guidance to speak like a friend and explain any jargon.

Making it concise was harder. Just telling the model to "write less" didn't work. To get answers down from a mini thesis to a single paragraph, I had to:
1. explicitly cap response length
2. show examples of what a good answer looked like
3. limit the max tokens
4. turn down the model temperature (lower = more predictable, less rambling)

That helped a lot, but I worried that shorter answers would block people who did want to go deeper.

My solution was follow-ups. I had Winebot ask a question at the end of each response to invite exploration. At first it sounded like a study guide ("which climate factors matter most?"), but after some iteration, it started asking questions that actually felt natural. That was a fun unlock.

You can try the improved experience here:
https://lnkd.in/gc3UHxXv

Behind the scenes, I also started building the next big feature: real bottle recommendations.

I originally planned to scrape a wine retailer's website and even built a script with Claude Code. Most major retailers aggressively block bots, sending me back to the drawing board. I pivoted to a Kaggle dataset of real wines and used GPT to translate messy product descriptions into structured assumptions about acidity, tannins, body, and style.

Next step: shipping the full bottle recommender with a real catalog and real links.

More next weekend 🍷🤖
