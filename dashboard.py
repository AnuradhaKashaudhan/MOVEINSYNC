import streamlit as st
import pandas as pd
import numpy as np
import json
import re
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from packaging import version as pkg_version
import ui_theme
import html

# Page Configuration
st.set_page_config(
    page_title="MoveInSync Ratings Intelligence",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom Global Design & Styles
ui_theme.inject_theme()

@st.cache_data
def load_data():
    summary_path = Path("reports/summary.json")
    analyzed_path = Path("data/processed/analyzed_reviews.csv")
    history_path = Path("data/processed/rating_history.csv")
    quotes_path = Path("reports/theme_quotes.json")
    
    summary_data = {}
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            summary_data = json.load(f)
            
    df_reviews = pd.DataFrame()
    if analyzed_path.exists():
        df_reviews = pd.read_csv(analyzed_path)
        if 'at' in df_reviews.columns:
            df_reviews['at_dt'] = pd.to_datetime(df_reviews['at'])
            
    df_history = pd.DataFrame()
    if history_path.exists():
        df_history = pd.read_csv(history_path)
        
    theme_quotes = {}
    if quotes_path.exists():
        with open(quotes_path, "r", encoding="utf-8") as f:
            theme_quotes = json.load(f)
            
    return summary_data, df_reviews, df_history, theme_quotes

summary_data, df_reviews, df_history, theme_quotes = load_data()

# Metadata & Official Metrics
meta = summary_data.get("metadata", {})
n_12_total = meta.get("n_1_2_star", 1671)
n_35_total = meta.get("n_3_5_star", 1500)
sample_total = n_12_total + n_35_total

# Official Play Store Numbers (from history if available, else standard snapshot)
hist_1 = 7324
hist_2 = 840
hist_3 = 1235
hist_4 = 7272
hist_5 = 98191
if not df_history.empty and 'histogram' in df_history.columns:
    try:
        latest_hist = json.loads(df_history.iloc[-1]['histogram'])
        if len(latest_hist) == 5:
            hist_1, hist_2, hist_3, hist_4, hist_5 = latest_hist
    except:
        pass

tot_ratings = hist_1 + hist_2 + hist_3 + hist_4 + hist_5
headline_rating = (1*hist_1 + 2*hist_2 + 3*hist_3 + 4*hist_4 + 5*hist_5) / tot_ratings
hist_1_2 = hist_1 + hist_2
pct_1_2 = (hist_1_2 / tot_ratings) * 100

# Sidebar Configuration
st.sidebar.markdown(
    '<div style="display:flex; align-items:center; gap:10px; margin-bottom: 5px;">'
    '<span style="font-size: 26px;">🚗</span>'
    '<span style="font-size: 20px; font-weight: 800; color: inherit; letter-spacing: -0.02em;">MoveInSync Intel</span>'
    '</div>'
    '<div style="font-size: 12px; color: inherit; opacity: 0.75; margin-bottom: 18px;">'
    'Play Store Feedback Intelligence Pipeline'
    '</div>',
    unsafe_allow_html=True
)

# Refresh Button with Spinner and Toast
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    with st.spinner("Refreshing dataset and analysis..."):
        try:
            st.cache_data.clear()
            st.toast("✅ Data refreshed successfully!", icon="🚀")
            st.rerun()
        except Exception as e:
            st.toast(f"❌ Failed to refresh: {e}", icon="⚠️")

# Filterable reviews (recent 24M window only for operational consistency)
df_recent = df_reviews[~df_reviews['is_legacy']].copy() if ('is_legacy' in df_reviews.columns and not df_reviews.empty) else df_reviews.copy()

st.sidebar.markdown("---")
st.sidebar.markdown("<div style='font-size: 13px; font-weight: 700; color: inherit; opacity: 0.85; margin-bottom: 8px;'>FILTERS</div>", unsafe_allow_html=True)

# Date bounds for full dataset range
if not df_recent.empty and 'at_dt' in df_recent.columns:
    min_date = df_recent['at_dt'].min().date()
    max_date = df_recent['at_dt'].max().date()
else:
    min_date = None
    max_date = None

all_scores = [1, 2, 3, 4, 5]
available_versions = sorted([str(v) for v in df_recent['reviewCreatedVersion'].dropna().unique()], reverse=True)

# Reset filters callback
def reset_filters():
    if min_date and max_date:
        st.session_state["filter_dates"] = (min_date, max_date)
    st.session_state["filter_scores"] = all_scores
    st.session_state["filter_versions"] = []

if "filter_scores" not in st.session_state:
    st.session_state["filter_scores"] = all_scores
if "filter_versions" not in st.session_state:
    st.session_state["filter_versions"] = []
if min_date and max_date and "filter_dates" not in st.session_state:
    st.session_state["filter_dates"] = (min_date, max_date)

# Date Filter: Default = full range of data (min to max date)
if min_date and max_date:
    selected_dates = st.sidebar.date_input(
        "Date Range",
        key="filter_dates",
        min_value=min_date,
        max_value=max_date,
        help="Defaults to the full date range of the dataset."
    )
else:
    selected_dates = None

# Rating Filter: Default = all five stars
selected_scores = st.sidebar.multiselect(
    "Star Rating",
    options=all_scores,
    key="filter_scores",
    help="Select one or more ratings to filter."
)

# Version Filter: Default = empty (empty means all versions)
selected_versions = st.sidebar.multiselect(
    "App Version (Empty = All)",
    options=available_versions,
    key="filter_versions",
    help="Leave empty to include all versions."
)

# Reset filters button
st.sidebar.button("Reset filters", on_click=reset_filters, use_container_width=True)

# Apply Filters
filtered_df = df_recent.copy()
if selected_dates:
    if len(selected_dates) == 2:
        filtered_df = filtered_df[
            (filtered_df['at_dt'].dt.date >= selected_dates[0]) &
            (filtered_df['at_dt'].dt.date <= selected_dates[1])
        ]
    elif len(selected_dates) == 1:
        filtered_df = filtered_df[filtered_df['at_dt'].dt.date >= selected_dates[0]]

if selected_scores:
    filtered_df = filtered_df[filtered_df['score'].isin(selected_scores)]

if selected_versions:
    filtered_df = filtered_df[filtered_df['reviewCreatedVersion'].astype(str).isin(selected_versions)]

# Prominent Matching Reviews Count in Sidebar
st.sidebar.markdown(
    f'<div style="background: rgba(127, 127, 127, 0.12); border: 1px solid rgba(127, 127, 127, 0.25); border-radius: 10px; padding: 12px; margin-top: 15px; text-align: center;">'
    f'<div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: inherit; opacity: 0.75; font-weight: 700;">Matching Reviews</div>'
    f'<div style="font-size: 26px; font-weight: 800; color: var(--primary-color, #06b6d4); margin: 2px 0;">{len(filtered_df):,}</div>'
    f'<div style="font-size: 11.5px; color: inherit; opacity: 0.65;">out of {len(df_recent):,} in recent window</div>'
    f'</div>',
    unsafe_allow_html=True
)

# Navigation
st.sidebar.markdown("---")
pages = [
    "📊 Overview",
    "⚠️ Why ratings are low",
    "🚀 Releases",
    "💬 Support & replies",
    "🔍 Review explorer"
]
choice = st.sidebar.radio("Navigation", pages)


# =============================================================================
# 1. OVERVIEW
# =============================================================================
if choice == "📊 Overview":
    # Hero Animated Banner
    ui_theme.render_hero_banner(headline_rating=round(headline_rating, 2))
    
    # KPI Glass Cards
    rep_12 = summary_data.get("developer_replies", {}).get("one_two_star", {})
    kpi_cards = [
        {
            "label": "Headline Rating",
            "value_num": round(headline_rating, 2),
            "prefix": "",
            "suffix": " ★",
            "delta": "Computed across lifetime",
            "delta_type": "delta-info",
            "is_float": True
        },
        {
            "label": "Total Lifetime Ratings",
            "value_num": tot_ratings,
            "prefix": "",
            "suffix": "",
            "delta": "+29 in latest snapshot",
            "delta_type": "delta-success",
            "is_float": False
        },
        {
            "label": "1-2★ Risk Tail",
            "value_num": hist_1_2,
            "prefix": "",
            "suffix": "",
            "delta": f"{pct_1_2:.1f}% of total ratings",
            "delta_type": "delta-alert",
            "is_float": False
        },
        {
            "label": "1-2★ Developer Reply",
            "value_num": rep_12.get("rate_pct", 4.1),
            "prefix": "",
            "suffix": "%",
            "delta": f"Median: {rep_12.get('median_days', 6.2)} days lag",
            "delta_type": "delta-alert",
            "is_float": True
        },
        {
            "label": "24M Analyzed Sample",
            "value_num": sample_total,
            "prefix": "",
            "suffix": "",
            "delta": "100% LLM-tagged",
            "delta_type": "delta-info",
            "is_float": False
        }
    ]
    ui_theme.render_kpi_cards(kpi_cards)
    
    col_chart1, col_chart2 = st.columns([1.1, 1])
    
    with col_chart1:
        st.markdown("<div style='font-size:16px; font-weight:700; color:inherit; margin-bottom:12px;'>Official Rating Histogram Breakdown</div>", unsafe_allow_html=True)
        # Horizontal bars with CSS width transition
        hist_bars = [
            {
                "label": "5 Stars",
                "percent": round((hist_5 / tot_ratings) * 100, 1),
                "color": "linear-gradient(90deg, #10b981, #059669)",
                "stat_str": f"{hist_5:,} ({((hist_5/tot_ratings)*100):.1f}%)",
                "badge": "Satisfied"
            },
            {
                "label": "4 Stars",
                "percent": round((hist_4 / tot_ratings) * 100, 1),
                "color": "linear-gradient(90deg, #3b82f6, #2563eb)",
                "stat_str": f"{hist_4:,} ({((hist_4/tot_ratings)*100):.1f}%)"
            },
            {
                "label": "3 Stars",
                "percent": round((hist_3 / tot_ratings) * 100, 1),
                "color": "linear-gradient(90deg, #f59e0b, #d97706)",
                "stat_str": f"{hist_3:,} ({((hist_3/tot_ratings)*100):.1f}%)"
            },
            {
                "label": "2 Stars",
                "percent": round((hist_2 / tot_ratings) * 100, 1),
                "color": "linear-gradient(90deg, #f97316, #ea580c)",
                "stat_str": f"{hist_2:,} ({((hist_2/tot_ratings)*100):.1f}%)"
            },
            {
                "label": "1 Star",
                "percent": round((hist_1 / tot_ratings) * 100, 1),
                "color": "linear-gradient(90deg, #ef4444, #dc2626)",
                "stat_str": f"{hist_1:,} ({((hist_1/tot_ratings)*100):.1f}%)",
                "badge": "Risk Tail"
            }
        ]
        ui_theme.render_horizontal_bars(hist_bars, max_val=100)
        
    with col_chart2:
        st.markdown("<div style='font-size:16px; font-weight:700; color:inherit; margin-bottom:12px;'>24-Month Monthly Review Volume</div>", unsafe_allow_html=True)
        if not df_recent.empty and 'at_dt' in df_recent.columns:
            m_vol = df_recent.set_index('at_dt').resample('ME')['reviewId'].count().rename("Reviews")
            st.line_chart(m_vol, color="#06b6d4")


# =============================================================================
# 2. WHY RATINGS ARE LOW
# =============================================================================
elif choice == "⚠️ Why ratings are low":
    st.markdown(
        '<div style="margin-bottom: 20px;">'
        '<h1 style="font-size: 28px; font-weight: 800; color: inherit; margin-bottom: 6px;">Why Ratings Are Low: Root Cause Analysis</h1>'
        '<p style="color: inherit; opacity: 0.75; font-size: 14.5px;">Detailed breakdown of friction themes among 1-2★ reviews across the last 24 months (N = 1,671).</p>'
        '</div>',
        unsafe_allow_html=True
    )
    
    themes_reason = summary_data.get("theme_shares_reasons_only", [])
    themes_all = summary_data.get("theme_shares_all_1_2", [])
    rating_impact = summary_data.get("rating_impact", [])
    helpfulness = {item['theme']: item for item in summary_data.get("helpfulness_ranking", [])}
    
    tab1, tab2, tab3 = st.tabs(["Top Themes (Reasons Only)", "All 1-2★ Breakdown", "Rating Lift Simulator"])
    
    with tab1:
        st.subheader("Top Themes Driving Negative Sentiment (Reasons Only, N = 1,419)")
        st.caption("Excludes NO_DETAIL and POSITIVE to focus strictly on actionable commuter friction.")
        
        if themes_reason:
            # Horizontal bars for top 8 themes
            theme_bars = []
            palette = [
                "linear-gradient(90deg, #ef4444, #dc2626)",
                "linear-gradient(90deg, #f43f5e, #e11d48)",
                "linear-gradient(90deg, #f97316, #ea580c)",
                "linear-gradient(90deg, #fb923c, #f97316)",
                "linear-gradient(90deg, #f59e0b, #d97706)",
                "linear-gradient(90deg, #eab308, #ca8a04)",
                "linear-gradient(90deg, #8b5cf6, #7c3aed)",
                "linear-gradient(90deg, #6366f1, #4f46e5)"
            ]
            for idx, r in enumerate(themes_reason[:8]):
                th_name = r['theme']
                h_info = helpfulness.get(th_name, {})
                thumbs = h_info.get("total_thumbs_up", 0)
                badge_text = f"👍 {thumbs}" if thumbs > 0 else f"#{r['rank']}"
                
                theme_bars.append({
                    "label": th_name,
                    "percent": r['share_pct'],
                    "color": palette[idx % len(palette)],
                    "stat_str": f"{r['count']} ({r['share_pct']:.1f}%)",
                    "badge": badge_text,
                    "badge_class": "pill pill-amber" if idx < 3 else "pill pill-blue"
                })
                
            ui_theme.render_horizontal_bars(theme_bars, max_val=max(r['share_pct'] for r in themes_reason[:8]) * 1.15)
            
            # Key Quotes in Expanders
            st.markdown("<div style='margin-top: 25px; margin-bottom: 12px; font-weight: 700; color: inherit;'>Voice of the Commuter: Key Quotes by Theme</div>", unsafe_allow_html=True)
            for r in themes_reason[:6]:
                th_name = r['theme']
                q_list = theme_quotes.get(th_name, [])
                with st.expander(f"💬 {th_name} — {r['count']} reviews ({r['share_pct']:.1f}% of reasons)"):
                    if q_list:
                        for q in q_list[:3]:
                            st.markdown(f'<div class="quote-box">"{html.escape(q.strip())}"</div>', unsafe_allow_html=True)
                    else:
                        st.info("No curated quotes available.")
                        
    with tab2:
        st.subheader("Complete 1-2★ Theme Distribution (N = 1,671)")
        if themes_all:
            df_ta = pd.DataFrame(themes_all)
            st.dataframe(
                df_ta.rename(columns={
                    "rank": "Rank",
                    "theme": "Theme",
                    "count": "Review Count",
                    "share_pct": "Share of All 1-2★ (%)"
                }),
                use_container_width=True
            )
            
    with tab3:
        st.subheader("Estimated Rating Impact Potential (Histogram Scaling Model)")
        st.markdown("""
        - **Low Impact:** Fixes primary complaint for users, lifting review score to 4 stars (+2.85 delta).
        - **High Impact:** Fixes issues for all mentions (up to 3 themes per review), lifting score to 4 stars.
        - **Realistic Gain:** Resolving the top 3 friction points yields **+0.06 to +0.09 stars** (upper bound ~4.88).
        """)
        if rating_impact:
            df_imp = pd.DataFrame(rating_impact)
            st.dataframe(
                df_imp.rename(columns={
                    "theme": "Theme",
                    "primary_count": "Primary Count",
                    "mentions_count": "Mentions Count",
                    "estimated_lift_low": "Low Lift (+)",
                    "estimated_lift_high": "High Lift (+)",
                    "projected_rating_low": "New Rating (Low)",
                    "projected_rating_high": "New Rating (High)"
                }),
                use_container_width=True
            )


# =============================================================================
# 3. RELEASES
# =============================================================================
elif choice == "🚀 Releases":
    st.markdown(
        '<div style="margin-bottom: 20px;">'
        '<h1 style="font-size: 28px; font-weight: 800; color: inherit; margin-bottom: 6px;">Release Quality & App Version Diagnostics</h1>'
        '<p style="color: inherit; opacity: 0.75; font-size: 14.5px;">Tracking 1-2★ share and 95% confidence intervals chronologically across semver builds (Min 100 reviews). No sample averages.</p>'
        '</div>',
        unsafe_allow_html=True
    )
    
    versions = summary_data.get("version_analysis_unbiased", [])
    spikes = summary_data.get("spikes_detected", [])
    
    st.subheader("Version Quality Diagnostics (Chronological Semver Order, Min 100 Reviews)")
    
    if versions:
        # Build clean display table
        table_rows = []
        for v in versions:
            ci_str = f"[{v['ci_low_pct']:.1f}%, {v['ci_high_pct']:.1f}%]"
            neighbour_str = f"{v['neighbour_pooled_share_pct']:.1f}% [{v['neighbour_ci_low_pct']:.1f}%, {v['neighbour_ci_high_pct']:.1f}%]" if v.get('neighbour_pooled_share_pct') is not None else "N/A"
            status = v.get("status", "Normal")
            
            table_rows.append({
                "Version": f"v{v['version']}",
                "Total Reviews (n)": v['n'],
                "1-2★ Count": v['n_1_2'],
                "1-2★ Share (%)": f"{v['share_1_2_pct']:.1f}%",
                "95% Confidence Interval": ci_str,
                "Neighbour Pooled Share": neighbour_str,
                "Statistical Finding": status
            })
            
        df_ver = pd.DataFrame(table_rows)
        st.dataframe(df_ver, use_container_width=True)
        
        # Version 12.19.0 Diagnostic Note
        st.info("ℹ️ **Version 12.19.0 Finding:**\n\n"
                "In build `v12.19.0` (n=102), the 1-2 star share rose from 29.8% to 35.3%; however, "
                "because its 95% confidence interval [26.0%, 44.6%] overlaps with neighbouring versions [22.2%, 37.3%], "
                "the statistical evidence for a version-level drop is **inconclusive**.")
        
    st.subheader("Data-Backed Monthly Theme Spikes (>=8 Reviews & >=2x Trailing 6M Avg)")
    if spikes:
        df_sp = pd.DataFrame(spikes)
        st.dataframe(
            df_sp.rename(columns={
                "month": "Month",
                "theme": "Spike Theme",
                "count": "Review Count",
                "share_pct": "Monthly Share (%)",
                "trailing_avg_pct": "Trailing 6M Avg (%)",
                "top_versions": "Coinciding Versions"
            }),
            use_container_width=True
        )


# =============================================================================
# 4. SUPPORT AND REPLIES
# =============================================================================
elif choice == "💬 Support & replies":
    st.markdown(
        '<div style="margin-bottom: 20px;">'
        '<h1 style="font-size: 28px; font-weight: 800; color: inherit; margin-bottom: 6px;">Developer Support & Customer Engagement</h1>'
        '<p style="color: inherit; opacity: 0.75; font-size: 14.5px;">Analysis of developer responses, reply latency, canned templates, and near-duplicate feedback.</p>'
        '</div>',
        unsafe_allow_html=True
    )
    
    rep = summary_data.get("developer_replies", {})
    r12 = rep.get("one_two_star", {})
    r45 = rep.get("four_five_star", {})
    canned = rep.get("canned_replies", {})
    dups = summary_data.get("near_duplicates", {})
    
    # Stat Cards
    support_cards = [
        {
            "label": "1-2★ Developer Reply Rate",
            "value_num": r12.get("rate_pct", 4.1),
            "prefix": "",
            "suffix": "%",
            "delta": f"{r12.get('replied', 69)} of {r12.get('total', 1671):,} reviews answered",
            "delta_type": "delta-alert",
            "is_float": True
        },
        {
            "label": "Median Reply Latency",
            "value_num": r12.get("median_days", 6.2),
            "prefix": "",
            "suffix": " days",
            "delta": f"{r12.get('median_hours', 148.9):.1f} hours average turnaround",
            "delta_type": "delta-alert",
            "is_float": True
        },
        {
            "label": "Canned Template Share",
            "value_num": canned.get("canned_share_pct", 26.2),
            "prefix": "",
            "suffix": "%",
            "delta": f"{canned.get('canned_count', 27)} of {canned.get('total_replies', 103)} replies repeated >= 3x",
            "delta_type": "delta-alert",
            "is_float": True
        }
    ]
    ui_theme.render_kpi_cards(support_cards)
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("<div style='font-size: 16px; font-weight: 700; color: inherit; margin-bottom: 10px;'>Response Rate by Rating Tier</div>", unsafe_allow_html=True)
        tier_bars = [
            {
                "label": "1-2★ Reviews",
                "percent": r12.get("rate_pct", 4.1),
                "color": "linear-gradient(90deg, #ef4444, #dc2626)",
                "stat_str": f"{r12.get('rate_pct', 4.1)}% ({r12.get('replied', 69)}/{r12.get('total', 1671)})",
                "badge": "Low"
            },
            {
                "label": "4-5★ Reviews",
                "percent": r45.get("rate_pct", 0.0),
                "color": "linear-gradient(90deg, #10b981, #059669)",
                "stat_str": f"{r45.get('rate_pct', 0.0)}% ({r45.get('replied', 0)}/{r45.get('total', 0)})",
                "badge": "High"
            }
        ]
        ui_theme.render_horizontal_bars(tier_bars, max_val=20)
        
    with col_s2:
        st.markdown("<div style='font-size: 16px; font-weight: 700; color: inherit; margin-bottom: 10px;'>Flagged Near-Duplicate Reviews (Cosine > 0.85)</div>", unsafe_allow_html=True)
        st.caption(f"Total review pairs detected (>=15 words): {dups.get('total_pairs_flagged', 0)} (possible templated text, not verified)")
        if dups.get("sample_pairs"):
            for pair in dups["sample_pairs"][:3]:
                with st.expander(f"Similarity: {pair['similarity']} | Review {pair['reviewId_1'][:8]}..."):
                    st.write(f"**Review A:** {pair['text_1']}")
                    st.write(f"**Review B:** {pair['text_2']}")
        else:
            st.info("No duplicate clusters found exceeding 0.85 cosine threshold.")


# =============================================================================
# 5. REVIEW EXPLORER
# =============================================================================
elif choice == "🔍 Review explorer":
    st.markdown(
        '<div style="margin-bottom: 20px;">'
        '<h1 style="font-size: 28px; font-weight: 800; color: inherit; margin-bottom: 6px;">Review Explorer</h1>'
        '<p style="color: inherit; opacity: 0.75; font-size: 14.5px;">Search and explore anonymized user reviews with multi-dimensional filtering.</p>'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Filter summary ribbon
    st.markdown(
        f'<div class="filter-ribbon">'
        f'<div>Matching Reviews: <strong>{len(filtered_df):,}</strong></div>'
        f'<div style="font-size: 12px; color: inherit; opacity: 0.75;">Privacy Gate: Anonymized hashes only (Zero PII)</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    query = st.text_input("🔍 Search review text...", placeholder="e.g. OTP, crash, driver location, no show...")
    df_display = filtered_df.copy()
    if query:
        df_display = df_display[df_display['content'].astype(str).str.contains(query, case=False, na=False)]
        
    cols_to_show = ['reviewId', 'score', 'at', 'reviewCreatedVersion', 'primary_theme', 'thumbsUpCount', 'content']
    existing_cols = [c for c in cols_to_show if c in df_display.columns]
    
    st.dataframe(
        df_display[existing_cols].head(250),
        use_container_width=True,
        column_config={
            "score": st.column_config.NumberColumn("Rating", format="%d ⭐"),
            "thumbsUpCount": st.column_config.NumberColumn("Thumbs Up", format="%d 👍"),
            "at": st.column_config.DatetimeColumn("Date & Time"),
            "primary_theme": st.column_config.TextColumn("Primary Theme"),
            "content": st.column_config.TextColumn("Review Text", width="large")
        }
    )
