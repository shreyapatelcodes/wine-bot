# Week 1: AI Sommelier Introduction

**Posted:** ~4 months ago  
**Impressions:** 1,418  
**Project:** Winebot - AI wine educator

---

Have you ever walked into a wine shop and felt immediately overwhelmed?

What does dry actually mean?
How do wine pairings work?
Why does a French Cabernet taste different from a Chilean one?

To help myself answer these questions, I built an AI sommelier 🍷 

Try it here: https://lnkd.in/gc3UHxXv

I'm running a new experiment: every weekend, I build and ship something with AI.

With new AI startups popping up constantly and tools like Claude Code getting absurdly good, I want to understand how this shift is actually playing out as a builder, not a spectator.

This weekend's project:
A first-draft AI wine expert trained on industry insiders' knowledge of wine. It answers questions about grapes, regions, climate, and winemaking, grounded in real domain knowledge.

How it works (very high level):
- Domain knowledge is chunked and embedded
- Embeddings are stored in a vector DB (Pinecone)
- Relevant context is retrieved at query time
- GPT-4o-mini generates grounded answers
- Everything is wrapped in a simple front-end

Key takeaway: you don't need to fine-tune models or train anything from scratch. RAG lets you give LLMs expert knowledge on demand.

Cost & scope:
- Embed a 165-page textbook: ~$0.02
- Per question: ~$0.002
- Hosting: free
- Build time: ~5 hours

What surprised me:
- Chunking strategy matters more than expected
- The hardest part wasn't the tech, it was curating a clean, high-quality knowledge source

Potential next iterations:
- Bottle recommendations by taste, pairing, and budget
- Conversation memory
- Upload a wine label → instant context

More builds coming next weekend 🍷🤖
