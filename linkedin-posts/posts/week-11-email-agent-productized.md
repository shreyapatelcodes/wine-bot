# Week 11: Email Agent Productized

**Posted:** ~1 month ago  
**Impressions:** 2,085  
**Project:** Making the email agent usable by others

---

I built an email agent for my nonprofit last week. It worked perfectly. This week, I tried to make something that anyone can use. When I sent it to a friend, I got a text 10 minutes later: "nothing is happening." 

She'd pasted the command across two lines. The terminal just sat there. 10 minutes of debugging later: one line break. 

That's when I realized my project wasn't a product. It was a set of scripts that happened to work on my laptop. 

So this week I did the unglamorous work: 

1. Built a setup wizard. It walks you through Google sign-in, asks your name and preferences, and writes the Claude Desktop config for you. No JSON editing. 

2. Fixed the errors nobody sees coming. My spam filter used substring matching, so typing "co" as a blocked sender would trash every .com email. A missing credentials file threw a raw Python traceback instead of "hey, run the setup wizard first." 

3. Wrote the README for the person who's never touched a terminal. Step-by-step Google Cloud setup, what to do when OAuth says "access denied," the works. 

https://lnkd.in/gPa7WdAj

Clone it. Run one command. Sign into Google. You have an AI email assistant inside Claude Desktop. 

Week 11 of building and shipping with AI. Turns out the hard part isn't getting it to work. It's getting it to work on someone else's laptop!
