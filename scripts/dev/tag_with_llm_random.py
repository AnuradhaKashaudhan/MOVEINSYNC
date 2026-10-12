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

# Model selection: gemini-3.5-flash-lite for higher throughput and active separate quota
MODEL_NAME = "gemini-3.5-flash-lite"
BATCH_SIZE = 50
RANDOM_SEED = 42

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

def call_llm_batch(batch_items):
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

Reviews to analyze:
{json.dumps([{'reviewId': item['reviewId'], 'score': item['score'], 'content': item['content']} for item in batch_items], ensure_ascii=False)}
"""
    try:
        response = model.generate_content(prompt, request_options={"timeout": 60})
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        # Clean trailing commas
        clean_text = re.sub(r',\s*([\]\}])', r'\1', clean_text)
        parsed = json.loads(clean_text)
        return {item['reviewId']: item for item in parsed if 'reviewId' in item}
    except Exception as e:
        err_msg = str(e).lower()
        if "quota" in err_msg or "429" in err_msg or "resourceexhausted" in err_msg:
            print(f"\n[QUOTA REACHED] Gemini API quota reached: {e}")
            return "QUOTA_EXHAUSTED"
        print(f"LLM error: {e}")
        return None

def main():
    print("=" * 80)
    print(f"RESUMING LLM TAGGING (MODEL: {MODEL_NAME}, BATCH SIZE: {BATCH_SIZE})")
    print("=" * 80)
    
    if not CSV_FILE.exists():
        print(f"Error: {CSV_FILE} not found.")
        return
        
    df = pd.read_csv(CSV_FILE)
    cache = load_cache()
    print(f"Loaded {len(df)} rows from {CSV_FILE.name}")
    print(f"Current tag_method counts:\n{df['tag_method'].value_counts()}")
    
    # Identify rows needing LLM tagging
    needs_tagging_idx = df[df['tag_method'] == 'keyword'].index.tolist()
    print(f"\nRows with tag_method == 'keyword' needing LLM tagging: {len(needs_tagging_idx)}")
    
    if not needs_tagging_idx:
        print("All rows are already tagged with LLM!")
        print("\nFinal sample_group x tag_method:")
        print(pd.crosstab(df['sample_group'], df['tag_method'], margins=True))
        return

    # Shuffle indexes with fixed random seed so partial result is an unbiased sample
    np.random.seed(RANDOM_SEED)
    shuffled_idx = np.random.permutation(needs_tagging_idx)
    
    items_to_process = []
    for idx in shuffled_idx:
        row = df.loc[idx]
        items_to_process.append({
            'idx': idx,
            'reviewId': row['reviewId'],
            'score': int(row['score']),
            'content': str(row['content'])
        })
        
    total_batches = (len(items_to_process) + BATCH_SIZE - 1) // BATCH_SIZE
    tagged_in_run = 0
    quota_stopped = False
    
    for b_num in range(0, len(items_to_process), BATCH_SIZE):
        batch = items_to_process[b_num:b_num+BATCH_SIZE]
        curr_b = (b_num // BATCH_SIZE) + 1
        print(f"Processing Batch {curr_b}/{total_batches} ({len(batch)} reviews)...")
        
        result = call_llm_batch(batch)
        if result == "QUOTA_EXHAUSTED":
            quota_stopped = True
            break
        elif result and isinstance(result, dict):
            for item in batch:
                r_id = item['reviewId']
                row_idx = item['idx']
                if r_id in result:
                    tag_info = result[r_id]
                    tag_info['tag_method'] = 'llm'
                    cache[r_id] = tag_info
                    
                    # Update dataframe
                    df.loc[row_idx, 'tag_method'] = 'llm'
                    df.loc[row_idx, 'primary_theme'] = tag_info.get('primary_theme', 'OTHER:Unknown')
                    df.loc[row_idx, 'themes'] = json.dumps(tag_info.get('themes', []))
                    df.loc[row_idx, 'sentiment'] = tag_info.get('sentiment', 'neutral')
                    df.loc[row_idx, 'severity'] = tag_info.get('severity', 3)
                    df.loc[row_idx, 'is_feature_request'] = tag_info.get('is_feature_request', False)
                    df.loc[row_idx, 'summary'] = tag_info.get('one_line_summary', '')
                    tagged_in_run += 1
            save_cache(cache)
            time.sleep(1) # respectful pacing
        else:
            print(f"Batch {curr_b} could not be parsed. Continuing to next batch...")
            continue
            
    # Save updated dataframe
    df.to_csv(CSV_FILE, index=False)
    save_cache(cache)
    
    print("\n" + "=" * 80)
    print("TAGGING RUN COMPLETED / PAUSED")
    print("=" * 80)
    print(f"Rows newly tagged by LLM in this run: {tagged_in_run}")
    if quota_stopped:
        print("[STOPPED] Quota ran out during run. Keyword fallback was NOT used.")
    print("\nCurrent sample_group x tag_method distribution:")
    crosstab = pd.crosstab(df['sample_group'], df['tag_method'], margins=True)
    print(crosstab)
    print("=" * 80)

if __name__ == "__main__":
    main()
