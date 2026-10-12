import os
import re
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from config import DATA_DIR, KNOWN_THEMES, LLM_MODEL
from analyze_reviews import fallback_tagging, HAS_GEMINI

def parse_seed_file(file_path):
    if not file_path.exists():
        print(f"Error: Seed file {file_path} not found.")
        return []
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    records = []
    
    # Check if format has [R...] blocks
    if re.search(r'\[R\d+\]', content):
        blocks = re.split(r'(?=\[R\d+\])', content)
        for b in blocks:
            b = b.strip()
            if not b.startswith('['):
                continue
            r_match = re.match(r'\[(R\d+)\]', b)
            r_id = r_match.group(1) if r_match else "R_unknown"
            
            # Extract fields
            date_m = re.search(r'Date:\s*(.*)', b, re.IGNORECASE)
            stars_m = re.search(r'Stars:\s*(\d+)', b, re.IGNORECASE)
            helpful_m = re.search(r'Helpful:\s*(\d+)', b, re.IGNORECASE)
            themes_m = re.search(r'Themes:\s*(.*)', b, re.IGNORECASE)
            sentiment_m = re.search(r'Sentiment:\s*(.*)', b, re.IGNORECASE)
            
            # Text can be multi-line until Reply: or end of block
            text_m = re.search(r'Text:\s*(.*?)(?=(?:Reply:|$))', b, re.DOTALL | re.IGNORECASE)
            reply_m = re.search(r'Reply:\s*(.*)', b, re.DOTALL | re.IGNORECASE)
            
            raw_themes = themes_m.group(1).strip() if themes_m else ""
            themes_list = [t.strip().upper() for t in re.split(r'[,|;]', raw_themes) if t.strip()]
            
            score_val = int(stars_m.group(1)) if stars_m else 1
            text_val = text_m.group(1).strip() if text_m else ""
            
            records.append({
                'id': r_id,
                'score': score_val,
                'themes': themes_list,
                'text': text_val,
                'reply': reply_m.group(1).strip() if reply_m else None
            })
    return records

def call_gemini_batch(batch_records, train_examples):
    import google.generativeai as genai
    import config
    api_key = config.GEMINI_API_KEY
    if api_key:
        genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.5-flash-lite", generation_config={"response_mime_type": "application/json"})
    
    # Use few-shot examples from train set only
    few_shot_str = "\n".join([
        f"Review: \"{ex['text'][:120]}\" -> Themes: {ex['themes']}"
        for ex in train_examples[:8]
    ])
    
    prompt = f"""You are an expert product analyst classifying mobile app user reviews for MoveInSync.
Classify each review into 1 to 3 relevant themes from this predefined list:
{', '.join(KNOWN_THEMES)}

Examples from training data:
{few_shot_str}

Output JSON array of objects with schema:
[
  {{
    "reviewId": "string",
    "primary_theme": "THEME_NAME",
    "themes": ["THEME_NAME_1", "THEME_NAME_2"],
    "sentiment": "positive|neutral|negative"
  }}
]

Reviews to classify:
{json.dumps([{'reviewId': r['id'], 'score': r['score'], 'content': r['text']} for r in batch_records])}
"""
    for attempt in range(3):
        try:
            res = model.generate_content(prompt)
            clean = res.text.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            clean = re.sub(r',\s*([\]\}])', r'\1', clean)
            parsed = json.loads(clean)
            return {item['reviewId']: item for item in parsed if 'reviewId' in item}
        except Exception as e:
            time.sleep(2 * (attempt + 1))
            if attempt == 2:
                print(f"LLM call failed after 3 attempts: {e}")
                return {}

def evaluate_tagger(held_out_records, train_records):
    print(f"\n--- EVALUATION: LLM Tagger ON {len(held_out_records)} HELD-OUT REVIEWS (gemini-3.5-flash-lite) ---")
    
    llm_map = {}
    batch_size = 25
    for i in range(0, len(held_out_records), batch_size):
        chunk = held_out_records[i:i + batch_size]
        print(f"Classifying batch {i//batch_size + 1}/{(len(held_out_records)-1)//batch_size + 1} ({len(chunk)} reviews)...")
        chunk_map = call_gemini_batch(chunk, train_records)
        llm_map.update(chunk_map)
        time.sleep(1)
        
    predictions = []
    print("\n--- PER-REVIEW LLM EXECUTION LOG (Model: gemini-3.5-flash-lite) ---")
    for r in held_out_records:
        r_id = r['id']
        if r_id in llm_map:
            p = llm_map[r_id]
            pred_themes = p.get('themes', [p.get('primary_theme', '')])
            primary = p.get('primary_theme', '')
            method = "llm"
            raw_out = json.dumps(p)
        else:
            fb = fallback_tagging(r['text'], r['score'])
            pred_themes = fb.get('themes', [fb.get('primary_theme', '')])
            primary = fb.get('primary_theme', '')
            method = "fallback"
            raw_out = json.dumps(fb)
            
        print(f"[{r_id}] Model: gemini-3.5-flash-lite | Raw Output: {raw_out}")
        predictions.append({
            'id': r['id'],
            'text': r['text'],
            'expected_themes': r['themes'],
            'predicted_themes': pred_themes,
            'predicted_primary': primary,
            'method': method,
            'raw_out': raw_out
        })
        
    at_least_one = 0
    theme_stats = {t: {'tp': 0, 'fp': 0, 'fn': 0} for t in KNOWN_THEMES}
    disagreement_items = []
    
    for item in predictions:
        exp_set = set(t.upper() for t in item['expected_themes'])
        pred_set = set(t.upper() for t in item['predicted_themes'])
        if item['predicted_primary']:
            pred_set.add(item['predicted_primary'].upper())
            
        inter = len(exp_set.intersection(pred_set))
        union = len(exp_set.union(pred_set)) if exp_set.union(pred_set) else 1

        if inter > 0:
            at_least_one += 1
            
        if inter == 0:
            disagreement_items.append((2.0, item))
        elif exp_set != pred_set:
            severity = 1.0 - (inter / union)
            disagreement_items.append((severity, item))
            
        for t in KNOWN_THEMES:
            t_upper = t.upper()
            in_exp = t_upper in exp_set
            in_pred = t_upper in pred_set
            if in_exp and in_pred:
                theme_stats[t]['tp'] += 1
            elif not in_exp and in_pred:
                theme_stats[t]['fp'] += 1
            elif in_exp and not in_pred:
                theme_stats[t]['fn'] += 1

    match_rate = (at_least_one / len(predictions)) * 100 if predictions else 0
    print(f"\n================================================================================")
    print(f"VALIDATION METRICS SUMMARY (N = {len(predictions)} HELD-OUT REVIEWS)")
    print(f"================================================================================")
    print(f"Overall 'At least one theme matches' Rate: {at_least_one}/{len(predictions)} ({match_rate:.1f}%)")
    
    print(f"\n{'Theme':<25} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Precision':<10} | {'Recall':<10} | {'F1-Score'}")
    print("-" * 75)
    f1s = []
    for t, s in theme_stats.items():
        tp, fp, fn = s['tp'], s['fp'], s['fn']
        if tp == 0 and fp == 0 and fn == 0:
            continue
        prec = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0.0
        rec = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        f1s.append(f1)
        print(f"{t:<25} | {tp:<4} | {fp:<4} | {fn:<4} | {prec:<9.1f}% | {rec:<9.1f}% | {f1:.1f}%")
        
    macro_f1 = np.mean(f1s) if f1s else 0.0
    print(f"\nMacro Average F1 across active themes: {macro_f1:.1f}%")
    
    disagreement_items.sort(key=lambda x: x[0], reverse=True)
    top_10 = [x[1] for x in disagreement_items[:10]]
    
    print(f"\n--- TOP 10 BIGGEST DISAGREEMENTS ({len(disagreement_items)} total differences) ---")
    if top_10:
        print(f"{'Rank':<5} | {'ID':<6} | {'My Tags (Ground Truth)':<30} | {'Model Tags':<30} | {'Text'}")
        print("-" * 115)
        for idx, d in enumerate(top_10, 1):
            exp_s = ", ".join(d['expected_themes'])
            pred_s = ", ".join(d['predicted_themes'])
            txt_s = d['text'][:60].replace('\n', ' ') + "..." if len(d['text']) > 60 else d['text'].replace('\n', ' ')
            print(f"{idx:<5} | {d['id']:<6} | {exp_s:<30} | {pred_s:<30} | {txt_s}")
    else:
        print("Zero disagreements! 100% agreement on all held-out reviews.")
        
    return match_rate, macro_f1, disagreement_items


def main():
    seed_file = DATA_DIR / "seed_reviews.txt"
    file_size = seed_file.stat().st_size
    with open(seed_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    first_line = lines[0] if lines else ""
    last_line = lines[-1] if lines else ""
    
    records = parse_seed_file(seed_file)
    print("=" * 80)
    print("GATE 1: SEED REVIEW PARSING & HELD-OUT VALIDATION (N = 110)")
    print("=" * 80)
    print(f"File Path: {seed_file}")
    print(f"File Size: {file_size:,} bytes")
    print(f"First Line: {first_line}")
    print(f"Last Line: {last_line}")
    print(f"Total [R###] blocks parsed: {len(records)}")
    
    # Split train vs held-out with fixed seed
    np.random.seed(42)
    indices = np.random.permutation(len(records))
    
    train_idx = indices[:40]
    test_idx = indices[40:110]
        
    train_set = [records[i] for i in train_idx]
    held_out_set = [records[i] for i in test_idx]
    
    print(f"Training / Few-Shot Examples (Allowed in prompt): {len(train_set)}")
    print(f"Held-Out Validation Set (NEVER shown to model): {len(held_out_set)}")
    
    evaluate_tagger(held_out_set, train_set)
    print("=" * 80)

if __name__ == "__main__":
    main()
