import pandas as pd
import numpy as np
import json
from pathlib import Path

def main():
    analyzed_path = Path("data/processed/analyzed_reviews.csv")
    raw_path = Path("data/raw/employee_reviews.csv")
    
    df_analyzed = pd.read_csv(analyzed_path)
    df_raw = pd.read_csv(raw_path)
    
    # Merge timestamp 'at' if not present in analyzed
    if 'at' not in df_analyzed.columns:
        df_analyzed = df_analyzed.merge(df_raw[['reviewId', 'at']], on='reviewId', how='left')
        
    df_analyzed['at_dt'] = pd.to_datetime(df_analyzed['at'])
    df_analyzed['year_month'] = df_analyzed['at_dt'].dt.to_period('M').astype(str)
    
    # Standardize theme names: Rename OTHER:GeneralDissatisfaction and variations to NO_DETAIL
    def clean_theme(t):
        if pd.isna(t):
            return "NO_DETAIL"
        t_str = str(t).strip()
        if t_str.startswith("OTHER:GeneralDissatisfaction") or t_str.startswith("OTHER:GENERAL_DISSATISFACTION") or t_str == "OTHER:GENERIC_NEGATIVE" or t_str == "OTHER:GENERAL_NEGATIVE":
            return "NO_DETAIL"
        return t_str
        
    df_analyzed['primary_theme_clean'] = df_analyzed['primary_theme'].apply(clean_theme)
    
    print("=" * 80)
    print("1. INSPECTION OF 10 RANDOM 'POSITIVE' REVIEWS IN 1-2 STAR GROUP")
    print("=" * 80)
    pos_12 = df_analyzed[(df_analyzed['sample_group'] == 'all_1_2_star') & (df_analyzed['primary_theme'] == 'POSITIVE')]
    print(f"Total POSITIVE reviews in 1-2 star group: {len(pos_12)}")
    sample_pos = pos_12.sample(n=min(10, len(pos_12)), random_state=42)
    for i, (_, row) in enumerate(sample_pos.iterrows(), 1):
        print(f"\n[{i}] Score: {row['score']} Star | ReviewID: {row['reviewId']} | Method: {row['tag_method']}")
        print(f"    Text: {repr(row['content'])}")
        
    print("\n" + "=" * 80)
    print("2. 1-2 STAR THEME REPORTING (ALL vs REASON GIVEN)")
    print("=" * 80)
    df_12 = df_analyzed[df_analyzed['sample_group'] == 'all_1_2_star'].copy()
    
    # (a) Over all 1-2 star reviews
    print("\n(a) Primary Theme Shares: Over ALL 1-2 Star Reviews (N = 1,671)")
    vc_all = df_12['primary_theme_clean'].value_counts()
    print(f"{'Rank':<5} | {'Theme':<25} | {'Count':<8} | {'Share (%)'}")
    print("-" * 55)
    for rank, (th, cnt) in enumerate(vc_all.items(), 1):
        pct = (cnt / len(df_12)) * 100
        print(f"{rank:<5} | {th:<25} | {cnt:<8} | {pct:.2f}%")
        
    # (b) Over only reviews that give a reason (excluding NO_DETAIL and POSITIVE)
    df_reason = df_12[~df_12['primary_theme_clean'].isin(['NO_DETAIL', 'POSITIVE'])].copy()
    print(f"\n(b) Primary Theme Shares: Over Reviews Giving a Reason (N = {len(df_reason)})")
    vc_reason = df_reason['primary_theme_clean'].value_counts()
    print(f"{'Rank':<5} | {'Theme':<25} | {'Count':<8} | {'Share of Reasons (%)'}")
    print("-" * 55)
    for rank, (th, cnt) in enumerate(vc_reason.items(), 1):
        pct = (cnt / len(df_reason)) * 100
        print(f"{rank:<5} | {th:<25} | {cnt:<8} | {pct:.2f}%")

    print("\n" + "=" * 80)
    print("3. THEME MENTIONS (UP TO 3 THEMES PER REVIEW)")
    print("=" * 80)
    # Parse themes json list
    all_mentions = []
    for _, row in df_12.iterrows():
        try:
            th_list = json.loads(row['themes']) if isinstance(row['themes'], str) else [row['primary_theme']]
        except:
            th_list = [row['primary_theme']]
        # Clean themes
        cleaned_list = list(set([clean_theme(t) for t in th_list[:3]]))
        for t in cleaned_list:
            all_mentions.append(t)
            
    mention_series = pd.Series(all_mentions).value_counts()
    print(f"{'Rank':<5} | {'Theme':<25} | {'Mention Count':<15} | {'% of Reviews Mentioning'}")
    print("-" * 65)
    for rank, (th, cnt) in enumerate(mention_series.items(), 1):
        pct = (cnt / len(df_12)) * 100
        print(f"{rank:<5} | {th:<25} | {cnt:<15} | {pct:.2f}%")

    print("\n" + "=" * 80)
    print("4. MONTHLY SHARE OF TOP 8 THEMES (LAST 24 MONTHS) - RECENCY CHECK")
    print("=" * 80)
    # Top 8 actionable themes in 1-2 stars
    top_8_themes = [
        "LOCATION_ETA", "LOGIN_OTP", "APP_CRASH_OPEN", "BOOKING",
        "SLOW_PERFORMANCE", "SUPPORT", "UI_REDESIGN", "NO_SHOW"
    ]
    
    # Filter to last 24 months
    recent_months = sorted(df_12['year_month'].unique())[-24:]
    df_12_recent = df_12[df_12['year_month'].isin(recent_months)].copy()
    
    # Cross tabulation of month x theme
    ct = pd.crosstab(df_12_recent['year_month'], df_12_recent['primary_theme_clean'])
    monthly_totals = df_12_recent['year_month'].value_counts()
    
    # Print table header
    header_str = f"{'Month':<8} | {'Total':<6} | " + " | ".join([f"{t[:10]:<10}" for t in top_8_themes])
    print(header_str)
    print("-" * len(header_str))
    
    for m in recent_months:
        tot = monthly_totals.get(m, 0)
        row_str = f"{m:<8} | {tot:<6} | "
        if tot == 0:
            row_str += " | ".join(["0.0%      " for _ in top_8_themes])
        else:
            pcts = []
            for t in top_8_themes:
                c = ct.loc[m, t] if (m in ct.index and t in ct.columns) else 0
                pct = (c / tot) * 100
                pcts.append(f"{pct:<9.1f}%")
            row_str += " | ".join(pcts)
        print(row_str)
        
    print("=" * 80)

if __name__ == "__main__":
    main()
