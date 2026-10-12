import os
import json
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai

genai.configure(api_key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))
model_name = 'gemini-3.5-flash-lite'
m = genai.GenerativeModel(model_name, generation_config={'response_mime_type': 'application/json'})

test_items = [
    {"reviewId": "r1", "score": 1, "content": "Location stuck for 30 min, ETA jumping from 5 to 30 min"},
    {"reviewId": "r2", "score": 1, "content": "Unable to login, OTP not received on mobile"},
    {"reviewId": "r3", "score": 1, "content": "App crashes immediately upon opening"}
]

prompt = f"""Classify these reviews for MoveInSync into themes: LOCATION_ETA, LOGIN_OTP, APP_CRASH_OPEN.
Schema:
[
  {{"reviewId": "...", "primary_theme": "...", "themes": ["..."]}}
]
Reviews:
{json.dumps(test_items)}
"""

res = m.generate_content(prompt)
print(f"Model {model_name} response:")
print(res.text)
