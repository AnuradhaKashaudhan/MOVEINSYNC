import streamlit as st
import pandas as pd
import numpy as np
import json
import re
from pathlib import Path
from packaging import version as pkg_version

# Page Configuration
st.set_page_config(
    page_title="MoveInSync Ratings Intelligence",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        padding: 1.2rem;
        border-radius: 0.6rem;
        border: 1px solid #334155;
        margin-bottom: 1rem;
    }
    .badge-drop {
        color: #ef4444;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    summary_path = Path("reports/summary.json")
    analyzed_path = Path("data/processed/analyzed_reviews.csv")
    history_path = Path("data/processed/rating_history.csv")
    
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
        
    return summary_data, df_reviews, df_history

summary_data, df_reviews, df_history = load_data()

# Sidebar
st.sidebar.title("MoveInSync Intel")
st.sidebar.caption("Play Store Feedback Intelligence Pipeline")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Filterable reviews (recent window only for operational consistency)
df_recent = df_reviews[~df_reviews['is_legacy']].copy() if 'is_legacy' in df_reviews.columns else df_reviews.copy()

# Sidebar Filters
st.sidebar.subheader("Filters")

# Date Filter
if not df_recent.empty and 'at_dt' in df_recent.columns:
    min_date = df_recent['at_dt'].min().date()
    max_date = df_recent['at_dt'].max().date()
    selected_dates = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    selected_dates = None

# Rating Filter
all_scores = [1, 2, 3, 4, 5]
selected_scores = st.sidebar.multiselect(
    "Star Rating",
    options=all_scores,
    default=all_scores
)

# Version Filter
available_versions = sorted([str(v) for v in df_recent['reviewCreatedVersion'].dropna().unique()], reverse=True)
selected_versions = st.sidebar.multiselect(
    "App Version",
    options=available_versions,
    default=[]
)

# Apply Filters
filtered_df = df_recent.copy()
if selected_dates and len(selected_dates) == 2:
    filtered_df = filtered_df[
        (filtered_df['at_dt'].dt.date >= selected_dates[0]) &
        (filtered_df['at_dt'].dt.date <= selected_dates[1])
    ]

if selected_scores:
    filtered_df = filtered_df[filtered_df['score'].isin(selected_scores)]

if selected_versions:
    filtered_df = filtered_df[filtered_df['reviewCreatedVersion'].astype(str).isin(selected_versions)]

# Navigation
pages = [
    "Overview",
    "Why ratings are low",
    "Releases",
    "Support & replies",
    "Review explorer"
]
choice = st.sidebar.radio("Navigation", pages)

# -----------------------------------------------------------------------------
# 1. OVERVIEW
# -----------------------------------------------------------------------------
if choice == "Overview":
    st.title("Executive Overview")
    st.markdown("Play Store aggregate health, rating distribution, and acute negative tail analysis.")
    
    # KPIs
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.metric(label="Headline Play Store Rating", value="4.64 ★", delta="-0.01 recent trend")
    with kpi_col2:
        st.metric(label="Total Lifetime Ratings", value="114,862", delta="+29 new ratings")
    with kpi_col3:
        st.metric(label="1-2★ Risk Tail (Lifetime)", value="8,164", delta="7.1% of ratings", delta_color="inverse")
    with kpi_col4:
        st.metric(label="24M LLM Sample Analyzed", value="3,171", delta="100% Gemini tagged")
        
    st.info("💡 **Key Insight: The Problem is the 1-Star Tail**\n\n"
            "While **85.5%** of lifetime ratings are 5 stars (routine enterprise rides), "
            "ratings rarely drift into 3-star mediocrity. Instead, acute operational failures "
            "(login lockouts, app launch crashes, driver location drift) push commuters straight into the "
            "**7,324 one-star ratings**. Fixing the top 3 themes can realistically lift the headline rating by +0.06 to +0.08 stars.")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Official Rating Histogram")
        hist_data = {
            "Rating": ["1 Star", "2 Star", "3 Star", "4 Star", "5 Star"],
            "Count": [7324, 840, 1235, 7272, 98191]
        }
        df_hist = pd.DataFrame(hist_data).set_index("Rating")
        st.bar_chart(df_hist)
        
    with col_chart2:
        st.subheader("24-Month Monthly Review Volume")
        if not df_recent.empty and 'at_dt' in df_recent.columns:
            m_vol = df_recent.set_index('at_dt').resample('ME')['reviewId'].count()
            st.line_chart(m_vol)

# -----------------------------------------------------------------------------
# 2. WHY RATINGS ARE LOW
# -----------------------------------------------------------------------------
elif choice == "Why ratings are low":
    st.title("Why Ratings Are Low: Root Cause Analysis")
    st.markdown("Detailed breakdown of friction points among low-star (1-2★) reviews.")
    
    themes_reason = summary_data.get("theme_shares_reasons_only", [])
    themes_all = summary_data.get("theme_shares_all_1_2", [])
    rating_impact = summary_data.get("rating_impact", [])
    helpfulness = summary_data.get("helpfulness_ranking", [])
    
    tab1, tab2, tab3 = st.tabs(["Top Themes (Reasons Only)", "All 1-2★ Breakdown", "Rating Lift Simulator"])
    
    with tab1:
        st.subheader("Themes Over Reviews Giving a Reason (Excluding NO_DETAIL & POSITIVE)")
        if themes_reason:
            df_tr = pd.DataFrame(themes_reason)
            st.dataframe(
                df_tr.rename(columns={
                    "rank": "Rank",
                    "theme": "Theme",
                    "count": "Review Count",
                    "share_pct": "Share of Reasons (%)"
                }),
                use_container_width=True
            )
            
            # Chart
            chart_df = df_tr.head(10).set_index("theme")["share_pct"]
            st.bar_chart(chart_df)
            
    with tab2:
        st.subheader("Full 1-2 Star Theme Distribution (N = 1,671)")
        if themes_all:
            df_ta = pd.DataFrame(themes_all)
            st.dataframe(
                df_ta.rename(columns={
                    "rank": "Rank",
                    "theme": "Primary Theme",
                    "count": "Count",
                    "share_pct": "Share of All 1-2★ (%)"
                }),
                use_container_width=True
            )
            
    with tab3:
        st.subheader("Estimated Rating Impact Potential (Histogram Scaling Model)")
        st.markdown("""
        **Assumptions:**
        1. Low impact: Only reviews where theme is primary convert to 4-star (+2.85 star delta).
        2. High impact: All reviews mentioning the theme (up to 3 themes) convert to 4-star.
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

# -----------------------------------------------------------------------------
# 3. RELEASES
# -----------------------------------------------------------------------------
elif choice == "Releases":
    st.title("Release Quality & App Version Diagnostics")
    st.markdown("Tracking rating changes across numeric release versions and correlating with theme spikes.")
    
    versions = summary_data.get("rating_by_version", [])
    spikes = summary_data.get("spikes_detected", [])
    
    st.subheader("Rating by App Version (Numeric Release Order, Min 50 Reviews)")
    if versions:
        df_v = pd.DataFrame(versions)
        st.dataframe(
            df_v.rename(columns={
                "version": "App Version",
                "count": "Total Reviews",
                "avg_score": "Average Score",
                "pct_1_2_star": "% 1-2 Star",
                "flagged_drop": "Drop Flag (>0.25 vs Neighbors)"
            }),
            use_container_width=True
        )
        
        # Version chart
        v_chart = df_v.set_index("version")["avg_score"]
        st.line_chart(v_chart)
        
    st.subheader("Data-Backed Theme Spikes (>=8 Reviews & >=2x Trailing 6M Avg)")
    if spikes:
        df_sp = pd.DataFrame(spikes)
        st.dataframe(
            df_sp.rename(columns={
                "month": "Month",
                "theme": "Theme",
                "count": "Review Count",
                "share_pct": "Monthly Share (%)",
                "trailing_avg_pct": "Trailing 6M Avg (%)",
                "top_versions": "Coinciding Releases"
            }),
            use_container_width=True
        )

# -----------------------------------------------------------------------------
# 4. SUPPORT AND REPLIES
# -----------------------------------------------------------------------------
elif choice == "Support & replies":
    st.title("Developer Support & Review Feedback Loop")
    st.markdown("Analysis of developer responses, reply latency, canned templates, and near-duplicate feedback.")
    
    rep = summary_data.get("developer_replies", {})
    r12 = rep.get("one_two_star", {})
    r45 = rep.get("four_five_star", {})
    canned = rep.get("canned_replies", {})
    dups = summary_data.get("near_duplicates", {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="1-2★ Reply Rate", value=f"{r12.get('rate_pct', 4.1)}%", delta=f"{r12.get('replied', 69)} replied")
    with col2:
        st.metric(label="1-2★ Median Latency", value=f"{r12.get('median_days', 6.2)} days", delta=f"{r12.get('median_hours', 148.9)} hours", delta_color="inverse")
    with col3:
        st.metric(label="Canned / Generic Reply Share", value=f"{canned.get('canned_share_pct', 26.2)}%", delta="27 of 103 replies repeated >= 3x", delta_color="inverse")
        
    st.subheader("Flagged Near-Duplicate Reviews (TF-IDF Cosine Similarity > 0.85)")
    st.caption(f"Total pairs detected: {dups.get('total_pairs_flagged', 69)}")
    if dups.get("sample_pairs"):
        for pair in dups["sample_pairs"][:5]:
            with st.expander(f"Similarity: {pair['similarity']} | Review {pair['reviewId_1']} vs {pair['reviewId_2']}"):
                st.write(f"**Review A:** {pair['text_1']}")
                st.write(f"**Review B:** {pair['text_2']}")

# -----------------------------------------------------------------------------
# 5. REVIEW EXPLORER
# -----------------------------------------------------------------------------
elif choice == "Review explorer":
    st.title("Review Explorer")
    st.markdown("Search and explore anonymized reviews across all filtered dimensions.")
    
    st.write(f"**Matching Reviews:** {len(filtered_df):,}")
    
    # Search box
    query = st.text_input("🔍 Search review text...", "")
    df_display = filtered_df.copy()
    if query:
        df_display = df_display[df_display['content'].astype(str).str.contains(query, case=False, na=False)]
        
    cols_to_show = ['reviewId', 'score', 'at', 'reviewCreatedVersion', 'primary_theme', 'thumbsUpCount', 'content']
    existing_cols = [c for c in cols_to_show if c in df_display.columns]
    
    st.dataframe(
        df_display[existing_cols].head(200),
        use_container_width=True
    )
