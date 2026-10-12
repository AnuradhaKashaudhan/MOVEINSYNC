import pandas as pd
import numpy as np
import re
from packaging import version as pkg_version

df_raw = pd.read_csv('data/raw/employee_reviews.csv')
recent = df_raw[~df_raw['is_legacy']].copy()
recent = recent[recent['reviewCreatedVersion'].notna()]

def parse_semver(v_str):
    clean = re.sub(r'[^0-9\.]', '', str(v_str).strip())
    if clean.endswith('.'): clean = clean[:-1]
    try: return pkg_version.parse(clean)
    except: return None

recent['semver'] = recent['reviewCreatedVersion'].apply(parse_semver)
recent = recent[recent['semver'].notna()]

v_stats = []
for v, grp in recent.groupby('reviewCreatedVersion'):
    n = len(grp)
    if n < 100: continue
    sem = grp['semver'].iloc[0]
    n_12 = (grp['score'] <= 2).sum()
    p = n_12 / n
    # Wilson score interval or standard normal
    se = np.sqrt(p * (1 - p) / n)
    ci_low = max(0.0, p - 1.96 * se)
    ci_high = min(1.0, p + 1.96 * se)
    v_stats.append({
        'version': v,
        'semver': sem,
        'n': n,
        'n_12': n_12,
        'share_12': p,
        'ci_low': ci_low,
        'ci_high': ci_high
    })

v_df = pd.DataFrame(v_stats).sort_values('semver').reset_index(drop=True)
print(f"Total versions with >= 100 reviews: {len(v_df)}")
print("-" * 115)
print(f"{'Version':<10} | {'n':<5} | {'1-2 Star Share (95% CI)':<30} | {'Neighbour Pooled (95% CI)':<30} | {'Status'}")
print("-" * 115)

for i in range(len(v_df)):
    curr = v_df.iloc[i]
    neighbors = []
    if i > 0: neighbors.append(v_df.iloc[i-1])
    if i < len(v_df) - 1: neighbors.append(v_df.iloc[i+1])
    
    if neighbors:
        n_pool = sum(nb['n'] for nb in neighbors)
        n_12_pool = sum(nb['n_12'] for nb in neighbors)
        p_pool = n_12_pool / n_pool
        se_pool = np.sqrt(p_pool * (1 - p_pool) / n_pool)
        ci_low_pool = max(0.0, p_pool - 1.96 * se_pool)
        ci_high_pool = min(1.0, p_pool + 1.96 * se_pool)
        
        # Test: is curr share higher than pool AND CIs do not overlap?
        is_drop = (curr['share_12'] > p_pool) and (curr['ci_low'] > ci_high_pool)
        if is_drop:
            drop_label = "DROP (Statistically Significant)"
        elif curr['share_12'] > p_pool:
            drop_label = "Higher (CIs overlap)"
        else:
            drop_label = "Normal / Lower"
        pool_str = f"{p_pool*100:5.1f}% [{ci_low_pool*100:4.1f}%, {ci_high_pool*100:4.1f}%]"
    else:
        is_drop = False
        pool_str = "N/A"
        drop_label = "No neighbors"
        
    ci_curr_str = f"{curr['share_12']*100:5.1f}% [{curr['ci_low']*100:4.1f}%, {curr['ci_high']*100:4.1f}%]"
    print(f"v{curr['version']:<9} | {curr['n']:<5} | {ci_curr_str:<30} | {pool_str:<30} | {drop_label}")

# Also check 12.19.0 specifically to see its numbers!
v_12_19 = recent[recent['reviewCreatedVersion'] == '12.19.0']
print("\n" + "=" * 80)
print(f"SPECIFIC CHECK: Version 12.19.0 has n = {len(v_12_19)} reviews.")
if len(v_12_19) > 0:
    n_12_19 = len(v_12_19)
    n_12_19_bad = (v_12_19['score'] <= 2).sum()
    p_12_19 = n_12_19_bad / n_12_19
    se_19 = np.sqrt(p_12_19 * (1 - p_12_19) / n_12_19)
    print(f"v12.19.0: n = {n_12_19}, 1-2 star = {n_12_19_bad} ({p_12_19*100:.1f}%), 95% CI: [{max(0, p_12_19-1.96*se_19)*100:.1f}%, {min(1, p_12_19+1.96*se_19)*100:.1f}%]")
    print(f"Eligible for >= 100 review threshold? {'YES' if n_12_19 >= 100 else 'NO (n < 100)'}")
