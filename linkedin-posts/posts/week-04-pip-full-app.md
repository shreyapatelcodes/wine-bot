# Week 4: Pip - Full Wine App

**Posted:** ~3 months ago  
**Impressions:** 1,450  
**Project:** Pip - complete AI sommelier with cellar tracking

---

If you'd asked me on Wednesday, I would've said week 4 of my experiment to ship something with AI every week in 2026 was a complete failure.

Spoiler: it wasn't.

Try Pip, an AI sommelier designed to make drinking, buying, and learning about wine easy: https://lnkd.in/gtBM3jqF

Rewinding a bit, I started the week with a simple goal: add image recognition. Take a photo of a bottle, get instant context.

I finished in under an hour.

So I kept going. Claude made it too easy to keep bolting things on:
- a cellar to save bottles
- ratings
- wine detail pages

By midweek, I'd built something technically impressive and genuinely unpleasant to use.

Looking at my vague soup of disconnected features, I realized something embarrassing: I'm a product manager, and I hadn't written a single line of a product spec.

So I stopped. I had Claude interview me to clarify user journeys and jobs to be done, then turned that into a real PRD (linked in the comments if you're curious). We worked through error states, edge cases, and agent orchestration, and then wrote an RFC. Only after that did we go back to building.

What came out of that process was Pip - a single chat interface that lets you:
- get wine recommendations in plain English ("cheap red for taco night")
- ask what to drink from your own collection
- track bottles from wishlist → cellar → tried
- actually learn something (it's trained on real wine education content)

My biggest takeaway from Week 4 is that AI makes it dangerously easy to build garbage fast. Taste is what makes the result worth using.

If you try Pip, I'd love feedback - especially what felt confusing or what you wish it did.

🍷🤖

And thank you Tristan Streichenberger for hosting my database as well as Matt Cummings and Sebastian Solorzano for the feature requests. Thanks also to everyone else who's tried out the stuff I'm building or given feedback!
