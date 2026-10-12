import pandas as pd
import numpy as np
import re
from pathlib import Path
from packaging import version as pkg_version

def parse_semver(v_str):
    if pd.isna(v_str):
        return None
    v_str = str(v_str).strip()
    try:
        # Extract numeric semver components
        clean = re.sub(r'[^0-9\.]', '', v_str)
        if clean.endswith('.'):
            clean = clean[:-1]
        if not clean:
            return None
        return pkg_version.parse(clean)
    except Exception:
        return None

def extract_major_minor(v_str):
    if pd.isna(v_str):
        return "Unknown"
    v_str = str(v_str).strip()
    clean = re.sub(r'[^0-9\.]', '', v_str)
    parts = clean.split('.')
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    elif len(parts) == 1 and parts[0]:
        return f"{parts[0]}.0"
    return "Unknown"

def main():
    raw_path = Path("data/raw/employee_reviews.csv")
    df = pd.read_csv(raw_path)
    print("Initial raw rows:", len(df))
    
    # Fix 2: Drop userName completely
    if 'userName' in df.columns:
        df = df.drop(columns=['userName'])
        print("Dropped 'userName' column. Keeping only reviewId.")
        
    # Fix 3: Drop empty content rows
    is_empty_content = df['content'].isna() | (df['content'].astype(str).str.strip() == '')
    empty_cnt = is_empty_content.sum()
    if empty_cnt > 0:
        df = df[~is_empty_content].copy()
        print(f"Dropped {empty_cnt} row(s) with empty content.")
        
    # Convert timestamps
    df['at_dt'] = pd.to_datetime(df['at'])
    df['repliedAt_dt'] = pd.to_datetime(df['repliedAt'], errors='coerce')
    
    # 24-month cutoff based on dataset max date
    max_date = df['at_dt'].max()
    cutoff_24m = max_date - pd.DateOffset(months=24)
    print(f"Dataset Max Date: {max_date}")
    print(f"24-Month Cutoff Date: {cutoff_24m}")
    
    df['is_legacy'] = df['at_dt'] < cutoff_24m
    print(f"Total reviews: {len(df)}")
    print(f"Recent (last 24m): {(~df['is_legacy']).sum()}")
    print(f"Legacy (> 24m): {df['is_legacy'].sum()}")
    
    # Major-minor version
    df['major_minor'] = df['reviewCreatedVersion'].apply(extract_major_minor)
    
    # Save cleaned raw data back
    cols_to_save = ['reviewId', 'score', 'content', 'thumbsUpCount', 
                    'reviewCreatedVersion', 'at', 'replyContent', 'repliedAt', 'is_legacy']
    df_to_save = df[[c for c in cols_to_save if c in df.columns]]
    df_to_save.to_csv(raw_path, index=False)
    print(f"Saved cleaned data to {raw_path} ({len(df_to_save)} rows)")
    
    # -------------------------------------------------------------------------
    # PRINT REPORT FOR FIX 4: Version Handling (Last 15 versions in release order)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("FIX 4: VERSION HANDLING (RELEASE ORDER - NUMERIC SEMVER)")
    print("=" * 80)
    
    # Filter to recent 24 months with valid version
    df_recent = df[~df['is_legacy']].copy()
    valid_versions = df_recent[df_recent['reviewCreatedVersion'].notna()].copy()
    
    # Parse versions
    valid_versions['parsed_ver'] = valid_versions['reviewCreatedVersion'].apply(parse_semver)
    valid_versions = valid_versions[valid_versions['parsed_ver'].notna()]
    
    # Group by version
    ver_groups = []
    for ver_str, group in valid_versions.groupby('reviewCreatedVersion'):
        p_ver = group['parsed_ver'].iloc[0]
        cnt = len(group)
        avg_score = group['score'].mean()
        low_star_cnt = (group['score'] <= 2).sum()
        pct_low = (low_star_cnt / cnt) * 100
        min_date_ver = group['at_dt'].min()
        max_date_ver = group['at_dt'].max()
        ver_groups.append({
            'version': ver_str,
            'parsed_ver': p_ver,
            'count': cnt,
            'avg_score': avg_score,
            'pct_1_2_star': pct_low,
            'first_seen': min_date_ver,
            'last_seen': max_date_ver
        })
        
    ver_df = pd.DataFrame(ver_groups).sort_values(by='parsed_ver', ascending=True)
    # Get last 15 versions in release order
    last_15 = ver_df.tail(15)
    
    print(f"{'Version':<12} | {'Count':<8} | {'Avg Score':<10} | {'% 1-2 Star':<12} | {'First Seen':<12} | {'Last Seen'}")
    print("-" * 75)
    for _, r in last_15.iterrows():
        print(f"{r['version']:<12} | {r['count']:<8} | {r['avg_score']:<10.2f} | {r['pct_1_2_star']:<11.1f}% | {str(r['first_seen'])[:10]:<12} | {str(r['last_seen'])[:10]}")

    # Major.Minor grouping (Last 24 months)
    print("\n--- Major.Minor Version Aggregates (Last 24 Months) ---")
    mm_agg = df_recent.groupby('major_minor').agg(
        count=('score', 'count'),
        avg_score=('score', 'mean'),
        one_two_star_count=('score', lambda s: (s <= 2).sum())
    ).reset_index()
    mm_agg['pct_1_2_star'] = (mm_agg['one_two_star_count'] / mm_agg['count']) * 100
    mm_agg['parsed'] = mm_agg['major_minor'].apply(parse_semver)
    mm_agg = mm_agg.sort_values(by='parsed', ascending=True)
    print(f"{'Major.Minor':<12} | {'Count':<8} | {'Avg Score':<10} | {'% 1-2 Star'}")
    print("-" * 45)
    for _, r in mm_agg.tail(10).iterrows():
        print(f"{r['major_minor']:<12} | {r['count']:<8} | {r['avg_score']:<10.2f} | {r['pct_1_2_star']:.1f}%")

    # -------------------------------------------------------------------------
    # PRINT REPORT FOR FIX 5: Reply Rate & Median Reply Time
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("FIX 5: DEVELOPER REPLY RATE & MEDIAN REPLY TIME")
    print("=" * 80)
    
    def analyze_replies(subset, label):
        total = len(subset)
        has_reply = subset['replyContent'].notna() & (subset['replyContent'].astype(str).str.strip() != '')
        replied_subset = subset[has_reply].copy()
        reply_rate = (len(replied_subset) / total) * 100 if total > 0 else 0
        
        # Calculate reply duration
        replied_subset['reply_duration_hours'] = (replied_subset['repliedAt_dt'] - replied_subset['at_dt']).dt.total_seconds() / 3600.0
        # Filter valid positive durations
        valid_dur = replied_subset['reply_duration_hours'][replied_subset['reply_duration_hours'] >= 0]
        med_hours = valid_dur.median() if not valid_dur.empty else np.nan
        med_days = med_hours / 24.0 if not np.isnan(med_hours) else np.nan
        
        return {
            'label': label,
            'total': total,
            'replied': len(replied_subset),
            'rate': reply_rate,
            'median_hours': med_hours,
            'median_days': med_days
        }

    # Last 24 months splits
    rep_1_2 = analyze_replies(df_recent[df_recent['score'] <= 2], "1-2 Star Reviews (Last 24M)")
    rep_4_5 = analyze_replies(df_recent[df_recent['score'] >= 4], "4-5 Star Reviews (Last 24M)")
    rep_all = analyze_replies(df_recent, "All Recent Reviews (Last 24M)")
    
    # Lifetime splits
    rep_1_2_life = analyze_replies(df[df['score'] <= 2], "1-2 Star Reviews (Lifetime)")
    rep_4_5_life = analyze_replies(df[df['score'] >= 4], "4-5 Star Reviews (Lifetime)")

    print("\nDeveloper Reply Statistics (Last 24 Months):")
    print(f"{'Group':<30} | {'Total':<7} | {'Replied':<8} | {'Reply Rate':<12} | {'Median Reply Time'}")
    print("-" * 80)
    for st in [rep_1_2, rep_4_5, rep_all]:
        time_str = f"{st['median_days']:.1f} days ({st['median_hours']:.1f} hrs)" if not np.isnan(st['median_days']) else "N/A"
        print(f"{st['label']:<30} | {st['total']:<7} | {st['replied']:<8} | {st['rate']:<11.1f}% | {time_str}")

    print("\nDeveloper Reply Statistics (Lifetime):")
    print(f"{'Group':<30} | {'Total':<7} | {'Replied':<8} | {'Reply Rate':<12} | {'Median Reply Time'}")
    print("-" * 80)
    for st in [rep_1_2_life, rep_4_5_life]:
        time_str = f"{st['median_days']:.1f} days ({st['median_hours']:.1f} hrs)" if not np.isnan(st['median_days']) else "N/A"
        print(f"{st['label']:<30} | {st['total']:<7} | {st['replied']:<8} | {st['rate']:<11.1f}% | {time_str}")

if __name__ == "__main__":
    main()
