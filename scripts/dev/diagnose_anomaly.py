import pandas as pd
import numpy as np
import ast
from pathlib import Path
from datetime import datetime, timedelta

def main():
    df = pd.read_csv('data/raw/employee_reviews.csv')
    hist_df = pd.read_csv('data/processed/rating_history.csv')
    
    # Latest histogram
    latest = hist_df.iloc[-1]
    hist_list = ast.literal_eval(latest['histogram']) # [1-star, 2-star, 3-star, 4-star, 5-star]
    hist_map = {star: count for star, count in enumerate(hist_list, 1)}
    
    print("=" * 80)
    print("STAGE A FIX 1: INVESTIGATION OF 2-STAR ANOMALY & ALL SCORE COVERAGE")
    print("=" * 80)
    
    # Check 1: Did score filter return mixed scores?
    print("\n--- Check 1: Review Score Integrity ---")
    print("Scores present in CSV:", sorted(df['score'].unique()))
    for s in sorted(df['score'].unique()):
        print(f"Count of score == {s}: {(df['score'] == s).sum()}")
        
    # Check 2: Dates and 24-month cutoff
    # Cutoff reference date: 2026-10-11 minus 24 months (~2024-10-11)
    df['dt'] = pd.to_datetime(df['at'])
    cutoff_24m = pd.Timestamp("2024-10-11")
    df['is_legacy'] = df['dt'] < cutoff_24m
    
    print("\n--- Check 2: Lifetime vs Last 24 Months Breakdown ---")
    print(f"24-Month Cutoff Date: {cutoff_24m.strftime('%Y-%m-%d')}")
    print(f"Total reviews in dataset: {len(df)}")
    print(f"Reviews in last 24 months (>= 2024-10-11): {(~df['is_legacy']).sum():,} ({((~df['is_legacy']).sum()/len(df))*100:.1f}%)")
    print(f"Legacy reviews older than 24 months (< 2024-10-11): {df['is_legacy'].sum():,} ({(df['is_legacy'].sum()/len(df))*100:.1f}%)")

    # Check 3: Detailed comparison per star rating
    print("\n--- Check 3: Coverage Matrix (CSV vs Histogram) ---")
    print(f"{'Star':<5} | {'Hist Ratings':<12} | {'CSV Total':<10} | {'CSV Lifetime Cov':<16} | {'CSV Last 24M':<12} | {'CSV Legacy (<24M)'}")
    print("-" * 80)
    for star in range(1, 6):
        h_cnt = hist_map[star]
        c_tot = (df['score'] == star).sum()
        c_24m = ((df['score'] == star) & (~df['is_legacy'])).sum()
        c_leg = ((df['score'] == star) & (df['is_legacy'])).sum()
        cov_tot = (c_tot / h_cnt) * 100
        print(f"Star {star} | {h_cnt:<12,} | {c_tot:<10,} | {cov_tot:<15.1f}% | {c_24m:<12,} | {c_leg:,}")

    # Check 4: Duplicate review content / exact text matches in 2-star reviews
    two_star_df = df[df['score'] == 2]
    print("\n--- Check 4: 2-Star Review Content & Duplication Analysis ---")
    print(f"Total 2-star rows: {len(two_star_df)}")
    print(f"Unique reviewId count: {two_star_df['reviewId'].nunique()}")
    print(f"Unique content count: {two_star_df['content'].nunique()}")
    dup_content_count = len(two_star_df) - two_star_df['content'].nunique()
    print(f"Duplicate content count (exact same text): {dup_content_count}")
    
    # Check 5: Yearly distribution of 2-star reviews
    two_star_df['year'] = two_star_df['dt'].dt.year
    year_dist = two_star_df['year'].value_counts().sort_index()
    print("\n2-Star Reviews Year-by-Year Distribution:")
    for yr, cnt in year_dist.items():
        print(f"  {yr}: {cnt} reviews")
        
    # Check 6: Computed Analysis & Hypotheses
    two_star_tot = len(two_star_df)
    two_star_recent = ((df['score'] == 2) & (~df['is_legacy'])).sum()
    two_star_legacy = ((df['score'] == 2) & (df['is_legacy'])).sum()
    pct_legacy = (two_star_legacy / two_star_tot) * 100 if two_star_tot > 0 else 0
    pct_recent = (two_star_recent / two_star_tot) * 100 if two_star_tot > 0 else 0
    h_2star = hist_map.get(2, 0)
    cov_recent = (two_star_recent / h_2star) * 100 if h_2star > 0 else 0
    cov_lifetime = (two_star_tot / h_2star) * 100 if h_2star > 0 else 0

    print("\n--- Check 6: Computed Root-Cause Hypotheses ---")
    print(f"Data Facts (Directly Computed):")
    print(f"- Total 2-star text reviews scraped across all time: {two_star_tot:,}")
    print(f"- 2-star reviews created before {cutoff_24m.strftime('%B %Y')} (legacy): {two_star_legacy:,} ({pct_legacy:.1f}%)")
    print(f"- 2-star reviews created in the last 24 months: {two_star_recent:,} ({pct_recent:.1f}%)")
    print(f"- Current Play Store snapshot 2-star rating histogram count: {h_2star:,}")
    print(f"- Recent 24M coverage of current histogram: {two_star_recent:,} / {h_2star:,} = {cov_recent:.1f}%")
    print(f"- Lifetime coverage ratio: {two_star_tot:,} / {h_2star:,} = {cov_lifetime:.1f}%")

    print("\nExplaining the Gap (Hypotheses, Not Verified):")
    print(f"1. [PROVEN FACT] Lifetime vs. Window Discrepancy: The CSV scraper retrieved {two_star_tot:,} reviews")
    print(f"   accumulated across the entire 12-year lifespan of the app (earliest 2-star: {two_star_df['at'].min()[:10]}).")
    print(f"   Within the last 24 months, there are only {two_star_recent:,} reviews, which represents {cov_recent:.1f}%")
    print(f"   of the current {h_2star:,} Play Store rating count.")
    print(f"2. [HYPOTHESIS, NOT VERIFIED] Recency-Weighted / Rolling Window in Play Store Public Histogram:")
    print(f"   Google Play documentation states that public rating distributions prioritize recent ratings by region")
    print(f"   rather than a lifetime sum. If Google Play's public histogram reflects a rolling calculation window")
    print(f"   or regional cohort (India), historical 2-star ratings from 2014-2024 would not be included in the {h_2star:,}")
    print(f"   histogram count, whereas the review scraper returns the full historical text archive.")
    print(f"3. [HYPOTHESIS, NOT VERIFIED] Geographic or Device Scope Mismatch:")
    print(f"   The Google Play scraper endpoint for public app metadata (`app()`) may report ratings filtered to a")
    print(f"   specific country/device cluster, whereas the reviews feed (`reviews_all()`) can return written reviews")
    print(f"   originating from multiple locales where the app was installed.")

if __name__ == "__main__":
    main()
