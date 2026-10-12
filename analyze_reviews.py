import os
import json
import time
import re
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from config import RAW_DIR, PROCESSED_DIR, TARGET_APP, KNOWN_THEMES, BATCH_SIZE, LLM_MODEL

CACHE_FILE = PROCESSED_DIR / "review_tags_cache.json"

# Setup Gemini API
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
HAS_GEMINI = False
model = None

if API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(
            model_name=LLM_MODEL,
            generation_config={"response_mime_type": "application/json"}
        )
        HAS_GEMINI = True
    except Exception as e:
        print(f"Failed to initialize Gemini: {e}")

# Keyword rules for all 17 themes
KEYWORD_RULES = [
    ("LOCATION_ETA", [
        r"location", r"eta", r"tracking", r"track", r"gps", r"map", r"live\s*location",
        r"cab\s*location", r"van\s*location", r"wrong\s*location", r"stuck", r"jumping"
    ]),
    ("APP_CRASH_OPEN", [
        r"crash", r"not\s*opening", r"won'?t\s*open", r"closes", r"blank\s*screen",
        r"black\s*screen", r"stopped\s*working", r"not\s*working", r"force\s*close",
        r"app\s*error", r"not\s*installed\s*from\s*play\s*store", r"reinstall"
    ]),
    ("SLOW_PERFORMANCE", [
        r"slow", r"lag", r"hang", r"loading", r"latency", r"takes\s*forever",
        r"freez", r"terribly\s*slow", r"loads\s*info\s*slow"
    ]),
    ("SUPPORT", [
        r"support", r"helpdesk", r"customer\s*care", r"unresponsive", r"no\s*response",
        r"canned", r"ticket", r"helpline", r"transport\s*team", r"escalat"
    ]),
    ("NO_SHOW", [
        r"no\s*show", r"noshow", r"marked\s*no\s*show", r"salary\s*deduction",
        r"penalty", r"did\s*not\s*turn\s*up", r"never\s*came", r"check-in"
    ]),
    ("LOGIN_OTP", [
        r"otp", r"login", r"log\s*in", r"sign\s*in", r"auto\s*logout", r"logged\s*out",
        r"verification\s*code", r"password", r"register", r"session"
    ]),
    ("BOOKING", [
        r"book", r"schedule", r"roster", r"cancel", r"shift", r"slot",
        r"adhoc", r"waitlist", r"drop\s*off", r"pick\s*up\s*time"
    ]),
    ("NOTIFICATIONS", [
        r"notification", r"pop-?up", r"alert", r"spam", r"delay\s*pop", r"remind"
    ]),
    ("UI_REDESIGN", [
        r"ui", r"redesign", r"new\s*update", r"interface", r"layout", r"look",
        r"old\s*version", r"update\s*made\s*it\s*worse", r"confusing"
    ]),
    ("DRIVER_CONTACT", [
        r"driver\s*contact", r"driver\s*number", r"call\s*driver", r"driver\s*calling",
        r"chat", r"connect\s*with\s*driver", r"message\s*driver"
    ]),
    ("PERMISSIONS", [
        r"permission", r"microphone", r"bluetooth", r"mandatory\s*access"
    ]),
    ("ROUTING_STOPS", [
        r"rout", r"circuit", r"detour", r"wrong\s*way", r"roundabout",
        r"took\s*\d+\s*hours", r"pilgrimage", r"drop\s*order"
    ]),
    ("PARKING_SEAT", [
        r"parking", r"seat", r"desk", r"floor", r"seat\s*number", r"cubicle"
    ]),
    ("RATING_FEEDBACK", [
        r"rate\s*the\s*trip", r"force.*rating", r"skip\s*rating", r"feedback\s*option",
        r"star\s*prompt", r"give\s*rating"
    ]),
    ("OTHER_DRIVER_BEHAVIOUR", [
        r"driver\s*rude", r"rash\s*driv", r"misbehav", r"abusive", r"driver\s*behavior",
        r"unprofessional\s*driver", r"driver\s*refused", r"speeding"
    ]),
    ("FEATURE_REQUEST", [
        r"feature\s*request", r"please\s*add", r"would\s*be\s*great\s*if",
        r"suggestion", r"can\s*you\s*add", r"option\s*to\s*search", r"need\s*an\s*option"
    ]),
    ("POSITIVE", [
        r"good", r"great", r"excellent", r"awesome", r"smooth", r"best",
        r"safe", r"helpful", r"love", r"nice", r"superb", r"convenient", r"user\s*friendly"
    ])
]

def fallback_tagging(content, score=None):
    text = str(content).lower()
    matched = []
    
    for theme, patterns in KEYWORD_RULES:
        for p in patterns:
            if re.search(p, text):
                matched.append(theme)
                break
                
    # Score-based heuristics
    if not matched:
        if score and score >= 4:
            matched = ["POSITIVE"]
        elif score and score <= 2:
            matched = ["OTHER:GeneralDissatisfaction"]
        else:
            matched = ["OTHER:NeutralFeedback"]
            
    # If positive word was matched in 1-2 star review (e.g. 'not good' or sarcastic), remove POSITIVE if other themes exist
    if score and score <= 2 and "POSITIVE" in matched and len(matched) > 1:
        matched.remove("POSITIVE")
        
    primary = matched[0]
    sentiment = "negative" if (score and score <= 2) else ("positive" if (score and score >= 4) else "neutral")
    severity = 5 if ("crash" in text or "sos" in text or "deduction" in text) else (4 if (score and score <= 2) else (1 if sentiment == "positive" else 2))
    is_fr = "FEATURE_REQUEST" in matched
    
    return {
        "themes": matched,
        "primary_theme": primary,
        "sentiment": sentiment,
        "severity": severity,
        "is_feature_request": is_fr,
        "one_line_summary": content[:60] if content else ""
    }

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

QUOTA_EXHAUSTED = False

def analyze_llm_batch(batch_items):
    """
    batch_items: list of dicts [{'reviewId': ..., 'content': ..., 'score': ...}]
    """
    global QUOTA_EXHAUSTED
    if QUOTA_EXHAUSTED or not HAS_GEMINI or model is None:
        return None
        
    theme_guide = ", ".join(KNOWN_THEMES)
    prompt = f"""You are an expert product analyst for MoveInSync, an employee commute and office transport mobile app.
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
    "severity": 1 to 5 (5 is blocker/safety/money deduction, 1 is positive/trivial),
    "is_feature_request": true | false,
    "one_line_summary": "concise 5-10 word summary"
  }}
]

Reviews to analyze:
{json.dumps([{'reviewId': item['reviewId'], 'score': item['score'], 'content': item['content']} for item in batch_items], ensure_ascii=False)}
"""

    for attempt in range(2):
        try:
            response = model.generate_content(prompt, request_options={"timeout": 30})
            clean_text = response.text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            parsed = json.loads(clean_text)
            
            # Index by reviewId
            result_map = {item['reviewId']: item for item in parsed if 'reviewId' in item}
            return result_map
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "429" in err_str or "resourceexhausted" in err_str:
                print(f"API Quota exhausted (429). Falling back to keyword tagger for remaining reviews (tag_method='keyword').")
                QUOTA_EXHAUSTED = True
                return None
            wait_time = (2 ** attempt) + 1
            print(f"LLM attempt {attempt+1} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            
    return None

def tag_dataset(df_sample):
    cache = load_cache()
    print(f"Loaded {len(cache)} existing cached tags.")
    
    to_query = []
    for _, row in df_sample.iterrows():
        r_id = row['reviewId']
        if r_id not in cache:
            to_query.append({
                'reviewId': r_id,
                'content': str(row['content']),
                'score': int(row['score'])
            })
            
    print(f"Reviews requiring tagging: {len(to_query)}")
    
    # Process in batches
    batch_size = BATCH_SIZE
    total_batches = (len(to_query) + batch_size - 1) // batch_size if to_query else 0
    
    for b_idx in range(0, len(to_query), batch_size):
        batch = to_query[b_idx:b_idx+batch_size]
        curr_b = (b_idx // batch_size) + 1
        print(f"Processing batch {curr_b}/{total_batches} ({len(batch)} reviews)...")
        
        llm_results = None
        if HAS_GEMINI:
            llm_results = analyze_llm_batch(batch)
            
        if llm_results:
            for item in batch:
                r_id = item['reviewId']
                if r_id in llm_results:
                    tag_info = llm_results[r_id]
                    tag_info['tag_method'] = 'llm'
                    cache[r_id] = tag_info
                else:
                    # Fallback for missing item in batch
                    fb = fallback_tagging(item['content'], item['score'])
                    fb['reviewId'] = r_id
                    fb['tag_method'] = 'keyword'
                    cache[r_id] = fb
        else:
            print(f"Using keyword fallback for batch {curr_b}...")
            for item in batch:
                r_id = item['reviewId']
                fb = fallback_tagging(item['content'], item['score'])
                fb['reviewId'] = r_id
                fb['tag_method'] = 'keyword'
                cache[r_id] = fb
                
        # Save cache every 5 batches
        if curr_b % 5 == 0 or curr_b == total_batches:
            save_cache(cache)
            time.sleep(0.5)

    save_cache(cache)
    
    # Apply tags back to df_sample
    for idx, row in df_sample.iterrows():
        r_id = row['reviewId']
        tag_info = cache.get(r_id, fallback_tagging(row['content'], row['score']))
        df_sample.loc[idx, 'tag_method'] = tag_info.get('tag_method', 'keyword')
        df_sample.loc[idx, 'primary_theme'] = tag_info.get('primary_theme', 'OTHER:Unknown')
        df_sample.loc[idx, 'themes'] = json.dumps(tag_info.get('themes', [tag_info.get('primary_theme', 'OTHER:Unknown')]))
        df_sample.loc[idx, 'sentiment'] = tag_info.get('sentiment', 'neutral')
        df_sample.loc[idx, 'severity'] = tag_info.get('severity', 3)
        df_sample.loc[idx, 'is_feature_request'] = tag_info.get('is_feature_request', False)
        df_sample.loc[idx, 'summary'] = tag_info.get('one_line_summary', '')
        
    return df_sample

def prepare_sampling():
    raw_path = RAW_DIR / f"{TARGET_APP}_reviews.csv"
    df = pd.read_csv(raw_path)
    
    # Filter to non-legacy (last 24 months)
    if 'is_legacy' in df.columns:
        df_recent = df[~df['is_legacy']].copy()
    else:
        df['at_dt'] = pd.to_datetime(df['at'])
        cutoff = df['at_dt'].max() - pd.DateOffset(months=24)
        df_recent = df[df['at_dt'] >= cutoff].copy()
        
    # Group 1: ALL 1-2 star reviews in last 24 months
    g_1_2 = df_recent[df_recent['score'] <= 2].copy()
    g_1_2['sample_group'] = 'all_1_2_star'
    
    # Group 2: Random sample of at least 1,500 from 3-5 stars (fixed seed 42)
    g_3_5_all = df_recent[df_recent['score'] >= 3].copy()
    sample_size = min(1500, len(g_3_5_all))
    g_3_5 = g_3_5_all.sample(n=sample_size, random_state=42).copy()
    g_3_5['sample_group'] = 'random_3_5_star'
    
    combined = pd.concat([g_1_2, g_3_5]).reset_index(drop=True)
    return combined, len(g_1_2), len(g_3_5)

if __name__ == "__main__":
    combined_sample, n_1_2, n_3_5 = prepare_sampling()
    print("=" * 80)
    print("STAGE B: SAMPLING & ESTIMATION")
    print("=" * 80)
    print(f"Sample Group 1 ('all_1_2_star'):   {n_1_2:,} reviews (100% of 1-2 stars in last 24m)")
    print(f"Sample Group 2 ('random_3_5_star'): {n_3_5:,} reviews (random sample with fixed seed 42)")
    print(f"Total Sample Size to Tag:           {len(combined_sample):,} reviews")
    
    batch_size = BATCH_SIZE
    est_calls = (len(combined_sample) + batch_size - 1) // batch_size
    est_tokens_in = len(combined_sample) * 120 + est_calls * 300
    est_tokens_out = len(combined_sample) * 60
    # Gemini 3.8 / 2.5 Flash pricing: $0.15 / 1M input, $0.60 / 1M output
    est_cost = (est_tokens_in / 1_000_000) * 0.15 + (est_tokens_out / 1_000_000) * 0.60
    print(f"Configured Model:                   {LLM_MODEL}")
    print(f"Batch Size:                         {batch_size} reviews/call")
    print(f"Estimated API Calls:                {est_calls}")
    print(f"Estimated Tokens:                   ~{est_tokens_in:,} input, ~{est_tokens_out:,} output")
    print("=" * 80)
    
    print("\nStarting Tagging Process...")
    df_tagged = tag_dataset(combined_sample)
    
    # Save tagged dataset
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "analyzed_reviews.csv"
    df_tagged.to_csv(out_path, index=False)
    print(f"\nSaved {len(df_tagged)} tagged reviews to {out_path}")
    
    # Separate theme analysis for all_1_2_star vs random_3_5_star
    print("\n" + "=" * 80)
    print("THEME FREQUENCY: ALL 1-2 STAR REVIEWS (LAST 24 MONTHS)")
    print("=" * 80)
    df_1_2 = df_tagged[df_tagged['sample_group'] == 'all_1_2_star']
    t_1_2 = df_1_2['primary_theme'].value_counts()
    print(f"{'Rank':<5} | {'Theme':<28} | {'Count':<8} | {'Share of 1-2 Stars (%)'}")
    print("-" * 65)
    for rank, (theme, cnt) in enumerate(t_1_2.items(), 1):
        pct = (cnt / len(df_1_2)) * 100
        print(f"{rank:<5} | {theme:<28} | {cnt:<8} | {pct:.2f}%")
        
    print("\n" + "=" * 80)
    print("THEME FREQUENCY: RANDOM 3-5 STAR SAMPLE (LAST 24 MONTHS)")
    print("=" * 80)
    df_3_5 = df_tagged[df_tagged['sample_group'] == 'random_3_5_star']
    t_3_5 = df_3_5['primary_theme'].value_counts()
    print(f"{'Rank':<5} | {'Theme':<28} | {'Count':<8} | {'Share of 3-5 Stars (%)'}")
    print("-" * 65)
    for rank, (theme, cnt) in enumerate(t_3_5.items(), 1):
        pct = (cnt / len(df_3_5)) * 100
        print(f"{rank:<5} | {theme:<28} | {cnt:<8} | {pct:.2f}%")
    print("=" * 80)
