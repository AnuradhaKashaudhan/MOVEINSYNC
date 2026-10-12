import json
import re
from pathlib import Path

def main():
    print("=" * 70)
    print("GATE 4: NUMBER CONSISTENCY VERIFICATION")
    print("=" * 70)
    
    summary_path = Path("reports/summary.json")
    rec_path = Path("RECOMMENDATIONS.md")
    html_path = Path("reports/ratings_report.html")
    
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
        
    with open(rec_path, "r", encoding="utf-8") as f:
        rec_text = f.read()
        
    with open(html_path, "r", encoding="utf-8") as f:
        html_text = f.read()
        
    mismatches = []
    
    def check_value(doc_name, text, pattern, expected_val, label):
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            found = match.group(1).replace(",", "").strip()
            try:
                if abs(float(found) - float(expected_val)) < 0.05:
                    print(f"[PASS] {label}: found {found} matches expected {expected_val} in {doc_name}")
                else:
                    mismatches.append(f"{doc_name} {label}: found {found} != expected {expected_val}")
                    print(f"[FAIL] {label}: found {found} != expected {expected_val} in {doc_name}")
            except:
                if found == str(expected_val):
                    print(f"[PASS] {label}: found {found} matches expected {expected_val} in {doc_name}")
                else:
                    mismatches.append(f"{doc_name} {label}: found {found} != expected {expected_val}")
                    print(f"[FAIL] {label}: found {found} != expected {expected_val} in {doc_name}")
        else:
            mismatches.append(f"{doc_name} {label}: pattern NOT found")
            print(f"[FAIL] {label}: pattern NOT found in {doc_name}")

    meta = summary['metadata']
    reasons = {x['theme']: x for x in summary['theme_shares_reasons_only']}
    rep_12 = summary['developer_replies']['one_two_star']
    canned = summary['developer_replies']['canned_replies']
    dups = summary['near_duplicates']['total_pairs_flagged']

    # 1. Check Sample sizes in RECOMMENDATIONS.md
    check_value("RECOMMENDATIONS.md", rec_text, r'N\s*=\s*([0-9,]+)\s*one- and two-star', meta['n_1_2_star'], "1-2 Star Sample Size")
    check_value("RECOMMENDATIONS.md", rec_text, r'articulating an actionable reason \(N\s*=\s*([0-9,]+)', 1419, "Reasons Sample Size")

    # 2. Check Top Themes in RECOMMENDATIONS.md (Anchored to section headers)
    for th in ['LOGIN_OTP', 'APP_CRASH_OPEN', 'LOCATION_ETA', 'SLOW_PERFORMANCE', 'BOOKING', 'UI_REDESIGN', 'SUPPORT', 'ROUTING_STOPS', 'RATING_FEEDBACK', 'DRIVER_CONTACT', 'NO_SHOW']:
        exp_cnt = reasons[th]['count']
        exp_pct = reasons[th]['share_pct']
        th_header_pattern = rf'###\s*[0-9]+\.\s*{th}.*?Count & Share:\*\*\s*([0-9,]+)\s*reviews\s*\(\s*([0-9\.]+)%'
        match = re.search(th_header_pattern, rec_text, re.DOTALL)
        if match:
            found_cnt = match.group(1).replace(",", "").strip()
            found_pct = match.group(2).strip()
            if abs(float(found_cnt) - float(exp_cnt)) < 0.05:
                print(f"[PASS] {th} Count: found {found_cnt} matches expected {exp_cnt}")
            else:
                mismatches.append(f"{th} Count: found {found_cnt} != expected {exp_cnt}")
                print(f"[FAIL] {th} Count: found {found_cnt} != expected {exp_cnt}")
            if abs(float(found_pct) - float(exp_pct)) < 0.05:
                print(f"[PASS] {th} Share %: found {found_pct} matches expected {exp_pct}")
            else:
                mismatches.append(f"{th} Share %: found {found_pct} != expected {exp_pct}")
                print(f"[FAIL] {th} Share %: found {found_pct} != expected {exp_pct}")
        else:
            mismatches.append(f"{th}: Header block NOT found")
            print(f"[FAIL] {th}: Header block NOT found")

    # 3. Check Support Metrics in RECOMMENDATIONS.md
    check_value("RECOMMENDATIONS.md", rec_text, r'reply rate on 1-2 star reviews is only\s*\**([0-9\.]+)%', rep_12['rate_pct'], "1-2 Star Reply Rate")
    check_value("RECOMMENDATIONS.md", rec_text, r'([0-9\.]+)-day\s*\(148\.9\s*hours\)', rep_12['median_days'], "Median Reply Delay")
    check_value("RECOMMENDATIONS.md", rec_text, r'and\s*\**([0-9\.]+)%\**\s*of responses are near-identical canned', canned['canned_share_pct'], "Canned Reply Share")
    check_value("RECOMMENDATIONS.md", rec_text, r'identified\s*([0-9]+)\s*review pairs with similarity > 0.85', dups, "Near-Duplicate Pairs")

    # 4. Check HTML Report values
    check_value("HTML Report", html_text, r'Evaluated on\s*([0-9,]+)\s*low-star', meta['n_1_2_star'], "HTML 1-2 Star Sample")
    check_value("HTML Report", html_text, r'([0-9,]+)\s*high-star', meta['n_3_5_star'], "HTML 3-5 Star Sample")
    check_value("HTML Report", html_text, r'Headline Play Store Rating</div>\s*<div class="kpi-value">\s*([0-9\.]+)', 4.64, "HTML Headline Rating")
    check_value("HTML Report", html_text, r'Developer Reply Rate.*?<div class="kpi-value"[^>]*>\s*([0-9\.]+)%', rep_12['rate_pct'], "HTML Reply Rate")

    print("\n" + "=" * 70)
    if mismatches:
        print(f"VERIFICATION FAILED: {len(mismatches)} mismatches detected!")
        for m in mismatches:
            print(f"- {m}")
        exit(1)
    else:
        print("VERIFICATION PASSED: All quoted numbers strictly match reports/summary.json!")
        print("=" * 70)

if __name__ == "__main__":
    main()
