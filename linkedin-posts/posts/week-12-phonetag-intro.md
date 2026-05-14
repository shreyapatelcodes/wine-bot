# Week 12: PhoneTag - Voice Agent

**Posted:** ~1 month ago  
**Impressions:** 6,504 ⭐ TOP PERFORMER  
**Project:** AI agent that makes phone calls for you

---

Last week, I needed a plumber. He called during a meeting. I called back - he was busy. He called again - I was on another call. It took four rounds of phone tag for a conversation that took 30 seconds: "I'm free Thursday at 10." "Done." 

So this week I built PhoneTag - an AI agent that makes phone calls for you. I give it a number, explain the context ("plumber, drain clog, I'm free Tuesday after 2pm and all day Thursday"), and it does the rest. It calls, introduces itself, negotiates a time, and reports back with what happened. 

Here's what's under the hood: 
- Claude parses my request into structured intent (who to call, why, and when I'm free)
- Vapi makes the actual phone call with a voice AI agent that has a real conversation 
- Twilio handles the telephon-y layer

My biggest takeaway was surprising: so much of the work was proving I'm a real person. Toll-free numbers need regulatory verification. Local numbers need carrier registration. There are layers of checks between "I want to make a call" and actually connecting. In a world where AI is everywhere, it's honestly a little heartening - there's still someone making sure a real person is at the other end of the line! 

Right now PhoneTag does a very specific job, and I have to boot up a local app every time I want to use it. Next, I want to make it something I can just text and have it work - and make the results easier to see and act on. 

Week 12 of building and shipping with AI! Stay tuned for more!
