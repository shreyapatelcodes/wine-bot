# Week 16: CareConnect Overnight Agents

**Posted:** ~2 weeks ago  
**Impressions:** 1,948  
**Project:** CareConnect - family communication portal for senior care

---

This week I tried something I hadn't done before. Instead of sitting with Claude and building turn by turn, I described what I wanted, went to sleep, and let agents work through the night. I woke up to 18 routes, a working Claude-powered chat, a staff dashboard, a marketing page, and a live deployment!

The product is CareConnect, a family communication portal for senior care facilities. The idea: care staff are doing the hard work of keeping people safe, comfortable, and connected, but families still go home and worry. AI can be a bridge, or at least help build one. I've been thinking about this problem for a few weeks. 

Try it out here: https://lnkd.in/g-MwC7nB

This felt like a good way to pressure-test it fast. 

Two things I learned: 

1. Parallel agents are genuinely different from sequential ones. When you work turn by turn with a single agent, you're always bottlenecked by the last step. Seven agents building simultaneously produces a different kind of output. Architectural decisions that one agent makes don't cascade into another agent's work the way they would in a single long thread. 

2. Sonnet is good enough. I used claude-sonnet-4-6 for everything - the chat responses, the weekly digest, the streaming API. I never once felt like I needed Opus. The quality bar for a demo like this is "convincing and fast," and Sonnet clears that easily. If you're building and defaulting to the most powerful model out of habit, worth reconsidering.

3. I'm not 100% convinced by this idea. While AI can summarize information well and be a competent chatbot, I worry that it doesn't really have the human touch inherent in speaking to the people looking after your loved ones. I also worry that it may add more work to care teams' plates. Beyond that HIPPA violations and hallucinations pose major risks.

This was my 16th week building and shipping weekly with AI! Excited to keep experimenting in this space!
