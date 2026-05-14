# Week 10: Email Agent for Nonprofit

**Posted:** ~1 month ago  
**Impressions:** 2,140  
**Project:** AI email assistant for Letters Against Isolation

---

I run a volunteer-run nonprofit that sends letters to isolated seniors around the world. It's one of the most meaningful things in my life. But managing the inbox on top of a full-time job can be overwhelming. 

This week, I decided built an AI agent that handles them for me. Here's exactly how I did it in Claude Code (no engineering background required):

Step 1: I gave it access to my inbox.
Set up Gmail API credentials (~10 min in Google Cloud Console). One Python script handles fetch, trash, archive, and send.

Step 2: I taught it what I know.
Claude perused all of the emails I'd sent over the past few months, categorized them into buckets and broke down the information we share when we respond. I also dropped our FAQ, important links into a folder of markdown files with those responses. That's the knowledge base. No database. No fancy setup. Just .md files.

Step 3: I taught it how I sound.
This was the fun part! I exported past emails from my & my team's inboxes and had Claude analyze them for patterns: how we greet people, how we sign off, common phrases, and the overall warmth level. It turned that into a tone guide and a set of reply templates. Then I refined them, adding details like "never use em dashes" and "always CC Suzy for group event questions." The result is an agent that actually sounds like me, not a corporate chatbot.

Step 4: I said "process emails."
Claude trashed 420 spam emails, surfaced the real ones, and drafted replies in my voice. I reviewed each one, made small edits, and hit approve. The replies went out from my actual inbox.

One volunteer had been waiting for a week to hear if she could include poetry in her letters. The agent drafted a perfect response. I tweaked one line, approved it, and it was sent.

The thing that surprised me most: I didn't need a custom web app, or a separate tool. The conversation IS the interface. Claude reads my knowledge base, drafts the reply, I approve it right there, and it sends. That's it.

If you're a PM, nonprofit leader, or anyone drowning in repetitive emails: you can build this. The entire project is a few Python scripts and a folder of markdown files!

Week 10 of building with AI. This one actually changed my day-to-day!
