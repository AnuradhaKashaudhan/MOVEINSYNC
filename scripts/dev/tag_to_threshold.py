import os
import json
import time
import re
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from config import PROCESSED_DIR, KNOWN_THEMES

CACHE_FILE = PROCESSED_DIR / "review_tags_cache.json"
CSV_FILE = PROCESSED_DIR / "analyzed_reviews.csv"

MODEL_NAME = "gemini-3.5-flash-lite"
BATCH_SIZE = 50
TARGET_1_2_MIN = 1200
TARGET_3_5_MIN = 500

import google.generativeai as genai
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    MODEL_NAME,
    generation_config={"response_mime_type": "application/json"}
)

def load_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
    return {}

def save_cache(cache):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

def call_llm(batch):
    theme_guide = ", ".join(KNOWN_THEMES)
    prompt = f"""You are an expert product analyst for MoveInSync, an employee commute mobile app.
Analyze each review and classify into the standardized themes.

Allowed themes:
{theme_guide}
If an issue clearly does not fit any allowed theme, use "OTHER:<short_label>".

Return a valid JSON array of objects with the exact schema for each review:
[
  {{
    "reviewId": "string",
    "themes": ["THEME_1", "THEME_2"],
    "primary_theme": "THEME_1",
    "sentiment": "positive" | "neutral" | "negative",
    "severity": 1 to 5,
    "is_feature_request": true | false,
    "one_line_summary": "concise 5-10 word summary"
  }}
]

Reviews:
{json.dumps([{'reviewId': item['reviewId'], 'score': item['score'], 'content': item['content']} for item in batch], ensure_ascii=False)}
"""
    for attempt in range(2):
        try:
            res = model.generate_content(prompt, request_options={"timeout": 60})
            clean = res.text.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = re.sub(r',\s*([\]\}])', r'\1', clean)
            parsed = json.loads(clean)
            return {p['reviewId']: p for p in parsed if 'reviewId' in p}
        except Exception as e:
            err = str(e).lower()
            if "quota" in err or "429" in err or "resourceexhausted" in err:
                print(f"[QUOTA LIMIT REACHED]: {e}")
                return "QUOTA"
            time.sleep(2)
    return None

def main():
    df = pd.read_csv(CSV_FILE)
    cache = load_cache()
    
    current_1_2 = len(df[(df['sample_group'] == 'all_1_2_star') & (df['tag_method'] == 'llm')])
    current_3_5 = len(df[(df['sample_group'] == 'random_3_5_star') & (df['tag_method'] == 'llm')])
    print(f"Current LLM-tagged rows: 1-2 star = {current_1_2}, 3-5 star = {current_3_5}")
    
    # Prioritize 1-2 stars to reach >= 1200
    needed_1_2 = max(0, TARGET_1_2_MIN - current_1_2)
    needed_3_5 = max(0, TARGET_3_5_MIN - current_3_5)
    print(f"Needed to reach gate threshold: 1-2 star = {needed_1_2}, 3-5 star = {needed_3_5}")
    
    # Get remaining keyword rows for 1-2 stars (shuffled randomly with fixed seed)
    rem_1_2_idx = df[(df['sample_group'] == 'all_1_2_star') & (df['tag_method'] == 'keyword')].index.tolist()
    np.random.seed(42)
    np.random.shuffle(rem_1_2_idx)
    
    items_to_tag = []
    # Pick enough to exceed 1200 (e.g. needed_1_2 + 50)
    for idx in rem_1_2_idx[:needed_1_2 + 50]:
        r = df.loc[idx]
        items_to_tag.append({
            'idx': idx,
            'reviewId': r['reviewId'],
            'score': int(r['score']),
            'content': str(r['content'])
        })
        
    print(f"Processing {len(items_to_tag)} reviews in batches of {BATCH_SIZE}...")
    
    newly_tagged = 0
    quota_hit = False
    
    for i in range(0, len(items_to_tag), BATCH_SIZE):
        batch = items_to_tag[i:i+BATCH_SIZE]
        print(f"Batch {i//BATCH_SIZE + 1} ({len(batch)} reviews)...")
        res = call_llm(batch)
        if res == "QUOTA":
            quota_hit = True
            break
        elif res and isinstance(res, dict):
            for item in batch:
                r_id = item['reviewId']
                r_idx = item['idx']
                if r_id in res:
                    info = res[r_id]
                    info['tag_method'] = 'llm'
                    cache[r_id] = info
                    
                    df.loc[r_idx, 'tag_method'] = 'llm'
                    df.loc[r_idx, 'primary_theme'] = info.get('primary_theme', 'OTHER:Unknown')
                    df.loc[r_idx, 'themes'] = json.dumps(info.get('themes', []))
                    df.loc[r_idx, 'sentiment'] = info.get('sentiment', 'neutral')
                    df.loc[r_idx, 'severity'] = info.get('severity', 3)
                    df.loc[r_idx, 'is_feature_request'] = info.get('is_feature_request', False)
                    df.loc[r_idx, 'summary'] = info.get('one_line_summary', '')
                    newly_tagged += 1
            save_cache(cache)
            time.sleep(1)
        else:
            print("Batch parse issue, continuing...")
            
    df.to_csv(CSV_FILE, index=False)
    save_cache(cache)
    
    final_1_2 = len(df[(df['sample_group'] == 'all_1_2_star') & (df['tag_method'] == 'llm')])
    final_3_5 = len(df[(df['sample_group'] == 'random_3_5_star') & (df['tag_method'] == 'llm')])
    print(f"\nFinal LLM-tagged counts: 1-2 star = {final_1_2}, 3-5 star = {final_3_5}")
    print(f"Threshold status: 1-2 star (>=1200): {final_1_2 >= TARGET_1_2_MIN}, 3-5 star (>=500): {final_3_5 >= TARGET_3_5_MIN}")
    print("\nUpdated sample_group x tag_method:")
    print(pd.crosstab(df['sample_group'], df['tag_method'], margins=True))

if __name__ == "__main__":
    main()
