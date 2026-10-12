# MoveInSync Play Store Reviews Intelligence: Submission Notes

---

## 🛠️ How I Got There and Tools Used (Methodology Note)

To build this Play Store reviews intelligence pipeline, I used **Python 3.13**, **pandas**, and **google-play-scraper** to collect 15,019 MoveInSync reviews, pairing them with official Play Store rating snapshots (114,862 lifetime ratings). Early verification uncovered a critical data nuance: 83.7% of 2-star reviews stemmed from pre-October 2024 legacy archives. I isolated the active 24-month window (5,814 reviews) and enforced strict sample separation, analyzing 1,671 low-star (1-2★) reviews and 1,500 random high-star (3-5★) reviews without mixing distributions.

Using **Antigravity** and Google's **Gemini 3.5 Flash Lite** API, I classified all 3,171 reviews across 16 domain themes, completely eliminating heuristic keyword fallbacks. Validation against n=70 held-out reviews verified a 98.6% match rate and an honest 77.5% macro F1 score. Finally, I built an automated executive HTML reporting engine, an interactive **Streamlit** dashboard, and a GitHub Actions workflow delivering reproducible, verified product intelligence.

*(Word count: 147 words)*

---

## 🎥 2-Minute Demo Video Script

### Video Goal
Deliver a crisp, executive-ready walkthrough of the MoveInSync Reviews Intelligence Platform, demonstrating how raw customer sentiment converts into an actionable engineering roadmap.

---

### [0:00 – 0:25] Introduction & The 1-Star Tail Insight
- **Visual:** Browser showing `reports/ratings_report.html` header and KPI cards.
- **Narrator:**
  > *"Hello everyone. Today I'm presenting the MoveInSync Play Store Ratings Intelligence Pipeline.
  > If you look at our Play Store listing, our aggregate headline score looks healthy at 4.64 stars across 114,000 ratings. But when you inspect the histogram, a critical reality emerges: 85.5% of commuters award 5 stars for routine, uninterrupted rides, but ratings do not drift into mild 3-star reviews. Instead, acute operational failures push commuters directly into our 8,164-review 1-to-2 star tail. When an employee is stranded late at night or locked out during a shift cutoff, they give 1 star."*

---

### [0:25 – 0:50] Root Causes & Voice of the Commuter
- **Visual:** Switch to Streamlit Dashboard -> **Why ratings are low** tab.
- **Narrator:**
  > *"Using Gemini 3.5 Flash Lite, we classified over 3,100 reviews with zero keyword fallbacks, validated at a 77.5% macro F1 across n=70 held-out reviews.
  > When we filter down to reviews giving specific reasons, three acute friction points account for nearly 40% of all negative sentiment:
  > First, **Login and OTP failures** at 17.3%, where auto-logout loops and missing OTP input boxes lock commuters out of tracking.
  > Second, **Launch crashes** at 10.4%, including 'app not installed' errors following auto-updates.
  > And third, **Live location and ETA drift** at 10.2%, which holds the highest community agreement with 128 thumbs-up."*

---

### [0:50 – 1:15] Release Diagnostics & Spike Detection
- **Visual:** Navigate to **Releases** tab in Streamlit; hover over version chart and spike table.
- **Narrator:**
  > *"Our pipeline tracks releases chronologically. In our version quality analysis, version 12.19.0 saw its 1-2 star share rise to 35.3%, but confidence intervals overlap with neighbours, making the version drop inconclusive.
  > Instead, our automated monthly spike detection flags actionable spikes: in September 2026, launch crashes surged to 19.1% of reviews, and in August to 13.0%, pinpointing exact moments of commuter friction."*

---

### [1:15 – 1:40] Support Gap & Review Explorer
- **Visual:** Navigate to **Support & replies** and **Review explorer** tabs.
- **Narrator:**
  > *"Turning to support operations, we found that our developer reply rate on 1-2 star reviews is only 4.1%, with a 6.2-day median delay, and over 26% of replies are identical canned templates.
  > In the Review Explorer, team members can search and filter reviews dynamically while guaranteeing complete user privacy—all usernames and personal identifiable information have been completely stripped from the database."*

---

### [1:40 – 2:00] The Action Plan & One-Command Automation
- **Visual:** Show `RECOMMENDATIONS.md` prioritized fix table, then terminal running `python run_all.py`.
- **Narrator:**
  > *"In our RECOMMENDATIONS document, we outline quick wins for tomorrow: extending login token lifetimes, fixing dynamic split bundles, and enforcing geofenced proof before drivers can mark a commuter as No-Show. Resolving the top 3 themes yields a realistic rating lift of +0.06 to +0.09 stars.
  > The entire pipeline runs via a single command—`python run_all.py`—and schedules automatically every week via GitHub Actions. Thank you!"*
