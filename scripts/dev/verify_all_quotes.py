import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import re

df = pd.read_csv('data/processed/analyzed_reviews.csv')
contents = df['content'].dropna().tolist()

quotes_to_verify = [
    ("LOGIN_OTP 1", "After the recent update, Whenever I try to login for checking the cab details the text box entering the otp doesn't appear. Instead I get a error stating \"Empty response body\"... we had to clear the data of the app every we login.", True),
    ("LOGIN_OTP 2", "This app is the worst. Not able to login via phone/email as the OTP is not received. The most disgusting thing is, it won't give any message whether the user's mobile/email is registered or not.", True),
    ("APP_CRASH_OPEN 1", "The app frequently crashes or hangs while booking cabs, which makes it really frustrating, especially when I'm in a hurry...", True),
    ("APP_CRASH_OPEN 2", "While doing the booking tried to open app, it crashes... shows disabled screen for parking selection...", True),
    ("LOCATION_ETA 1", "The GPS system of the app needs serious improvement. The cab icon often stays at the same point for over 10 minutes, even though the driver has clearly already left that location. This makes the live tracking feature unreliable and misleading...", True),
    ("LOCATION_ETA 2", "The map never updates the cab location on time, If you're working late in the night and your location is outside main city then you can be left stranded... because map is not updated in time and you must be waiting for a cab that has already left...", True),
    ("SLOW_PERFORMANCE 1", "The app takes so much time to just open that it feels like it is performing some rocket science computations in the background.", True),
    ("SLOW_PERFORMANCE 2", "most of the time app keeps loading even in good internet connectivity.", False),
    ("BOOKING 1", "Unable to view the schedule for the whole month even though the schedule is done a month prior. Only the following / next schedule is shown. Reinstalled app multiple times!", False),
    ("BOOKING 2", "Your app is very inconvenient. Accepting booking from wait-list a minute before the trip but not allowing you to cancel anymore. Then you will mark it as no show...", True),
    ("UI_REDESIGN 1", "The recent updates in the UI have made the app very difficult to use. Booking a shuttle is now a 2 step process previously it used to be 1... Another bad thing is even though I am in 1 cab but I can see all the ones available for that time.", True),
    ("UI_REDESIGN 2", "Under Bookings \"Login and logouts\" interface are very confusing... Under a date it's \"Logout and Login\" which makes users very confusing which will impact to \"No Show\".", True),
    ("SUPPORT 1", "Customer support is useless—the representative who attended my call was rude, unprofessional, and did not attempt to resolve the issue... Nothing about the service feels trustworthy.", True),
    ("SUPPORT 2", "The physical experience is extremely poor... The customer care is worst. The app has basic UX issues. For eg. to edit a booking you first have to cancel it.", True),
    ("ROUTING_STOPS 1", "Worst app for planning the route and clubbing... Always gives wrong route. Gives drop to the person nearest last and farthest person gets first drop.", True),
    ("ROUTING_STOPS 2", "Recently, many nodal points have been removed from the list... walking 1 km daily just to reach the cab is quite difficult.", True),
    ("RATING_FEEDBACK 1", "it's asking for feedback after every trip and doesn't let you skip. it's so annoying as we are in a hurry to scan but you have to rate first.", True),
    ("RATING_FEEDBACK 2", "I am forced to rate every trip which is twice a day. There should be an option to skip the step", False),
    ("DRIVER_CONTACT 1", "Could not call the bus driver at critical time, as if I click on the call button, it says like The company policy is not allowed to call. Because of this functionality, I have missed the bus...", True),
    ("DRIVER_CONTACT 2", "When we try to contact the driver no response the auto reply comes (looks like the driver is not responding)... there should be a chat box for me and the driver to connect...", True),
    ("NO_SHOW 1", "The cab was shown at a different location due to a glitch in the app, but the driver reached the correct location and left without picking me up... The lack of cooperation and poor customer service was very frustrating.", True),
    ("NO_SHOW 2", "The timing for my schedule was changed without any prior information. As a result, I was marked as a “no show” even though I had reached the location and my cab had arrived...", True)
]

def normalize_apostrophes(s):
    return s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"').replace('—', '--').replace('–', '-')

print("=" * 80)
print("VERIFYING ALL 22 QUOTES AGAINST analyzed_reviews.csv")
print("Rule: only ellipses (...) and case changes allowed. Shortened quotes marked (lightly shortened).")
print("=" * 80)

all_passed = True
for label, quote, is_shortened in quotes_to_verify:
    parts = [p.strip() for p in quote.split('...') if len(p.strip()) > 0]
    matched = False
    matching_review = None
    
    for c in contents:
        norm_c = normalize_apostrophes(c.lower())
        idx = 0
        parts_match = True
        for part in parts:
            norm_part = normalize_apostrophes(part.lower())
            pos = norm_c.find(norm_part, idx)
            if pos == -1:
                parts_match = False
                break
            idx = pos + len(norm_part)
        if parts_match:
            matched = True
            matching_review = c
            break
            
    if matched:
        short_label = "(lightly shortened)" if is_shortened else "(full quote)"
        print(f"[VERIFIED] {label} {short_label}")
    else:
        print(f"[FAILED]   {label} NOT FOUND IN DATASET!")
        all_passed = False

print("=" * 80)
if all_passed:
    print("ALL 22 QUOTES STRICTLY VERIFIED AGAINST analyzed_reviews.csv!")
else:
    print("FAILURES DETECTED!")
