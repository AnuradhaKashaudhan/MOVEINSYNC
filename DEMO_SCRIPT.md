# MoveInSync Ratings Intelligence - Demo Video Script
**Target Duration:** 2 minutes

**(0:00 - 0:15) Intro: The Problem**
*(Visual: Screen recording of MoveInSync Play Store page showing 4.6 rating, zooming in on recent 1-star reviews)*
"MoveInSync handles commutes for 1.5 million employees, but our Play Store rating has a persistent 1-star tail dragging down our otherwise great score. The question isn't just 'what's our rating?' but 'exactly what's breaking for our users today?'"

**(0:15 - 0:40) The Solution: One Command**
*(Visual: Terminal window. Type `python run_all.py` and hit enter)*
"To solve this, I built a reusable Python pipeline. With a single command, `run_all.py` connects to the Play Store via `google-play-scraper`, pulls the latest thousands of reviews, deduplicates them, and feeds them into an analyzer script."

**(0:40 - 1:10) Analysis & Tagging**
"The pipeline categorizes every review into known operational themes—like 'ETA inaccurate' or 'App crashes'. It uses Gemini 3.5 Flash Lite LLM tagging, with zero keyword fallbacks in our analyzed dataset. Validation against n=70 held-out reviews verified a 98.6% match rate and an honest 77.5% macro F1 score."

**(1:10 - 1:40) The Deliverables: Dashboard & Report**
*(Visual: Switch to Streamlit dashboard in browser. Click through the 'Why Ratings are Low' tab, then open `ratings_report.html`)*
"The output isn't just a spreadsheet. The pipeline auto-generates a clean Streamlit dashboard and a standalone HTML report. Product managers can instantly see that launch crashes, OTP login issues, and inaccurate ETAs are driving the most 1-star reviews, complete with real, anonymized user quotes."

**(1:40 - 2:00) The Outcome**
*(Visual: Open `RECOMMENDATIONS.md` showing the prioritized table)*
"Finally, it powers our actionable recommendations document. We go from raw Play Store noise to a prioritized Jira backlog for Engineering and Product teams. A reusable tool that turns complaints into clear next steps."
