import streamlit as st
import html

# Core CSS for styling and animations (dual theme compatible: light & dark)
GLOBAL_CSS = """
<style>
/* Design Tokens & Theme Variables */
:root {
    --mis-card-bg: rgba(127, 127, 127, 0.12);
    --mis-card-border: rgba(127, 127, 127, 0.25);
    --mis-accent: var(--primary-color, #06b6d4);
    --mis-card-radius: 12px;
}

/* Global font & text inheritance */
html, body, [class*="css"], .hero-banner, .glass-card, .bar-row, .filter-ribbon, .quote-box {
    font-family: inherit;
}

/* Subtle Keyframes */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Hero Banner: dual-theme compatible */
.hero-banner {
    background: rgba(127, 127, 127, 0.12);
    border: 1px solid rgba(127, 127, 127, 0.25);
    border-radius: 14px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 1.8rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1.5rem;
    color: inherit;
    animation: fadeInUp 0.4s ease forwards;
}

.hero-content {
    flex: 1;
    min-width: 280px;
}

.hero-badge {
    display: inline-block;
    padding: 4px 12px;
    background: rgba(127, 127, 127, 0.12);
    border: 1px solid rgba(127, 127, 127, 0.25);
    color: var(--primary-color, #06b6d4);
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-radius: 9999px;
    margin-bottom: 0.75rem;
}

.hero-title {
    font-size: 2rem;
    font-weight: 800;
    color: inherit;
    margin: 0 0 0.5rem 0;
    line-height: 1.2;
    letter-spacing: -0.02em;
}

.hero-insight {
    font-size: 1.02rem;
    color: inherit;
    opacity: 0.85;
    margin: 0;
    font-weight: 500;
}

.hero-insight strong {
    color: #ef4444;
}

.hero-score-box {
    background: rgba(127, 127, 127, 0.12);
    border: 1px solid rgba(127, 127, 127, 0.25);
    border-radius: 14px;
    padding: 1.2rem 1.8rem;
    text-align: center;
    min-width: 170px;
    color: inherit;
}

.hero-score-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    color: inherit;
    opacity: 0.75;
    font-weight: 600;
    letter-spacing: 0.05em;
}

.hero-score-val {
    font-size: 2.6rem;
    font-weight: 800;
    color: inherit;
    line-height: 1.1;
    margin: 0.2rem 0;
}

.hero-score-star {
    color: #f59e0b;
    font-size: 1.8rem;
}

/* Glass KPI Cards */
.glass-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.1rem;
    margin-bottom: 1.8rem;
}

.glass-card {
    background: rgba(127, 127, 127, 0.12);
    border: 1px solid rgba(127, 127, 127, 0.25);
    border-radius: 12px;
    padding: 1.3rem;
    color: inherit;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    animation: fadeInUp 0.4s ease forwards;
}

.glass-card:hover {
    transform: translateY(-3px);
    border-color: var(--primary-color, #06b6d4);
    box-shadow: 0 6px 18px rgba(127, 127, 127, 0.15);
}

.glass-card-title {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: inherit;
    opacity: 0.75;
    font-weight: 600;
    margin-bottom: 0.4rem;
}

.glass-card-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: inherit;
    margin-bottom: 0.3rem;
    line-height: 1.1;
}

.glass-card-delta {
    font-size: 0.82rem;
    color: inherit;
    opacity: 0.75;
    font-weight: 500;
}

.delta-alert {
    color: #ef4444;
    opacity: 1;
    font-weight: 600;
}

.delta-success {
    color: #10b981;
    opacity: 1;
    font-weight: 600;
}

.delta-info {
    color: var(--primary-color, #06b6d4);
    opacity: 1;
    font-weight: 600;
}

/* Staggered Delays for subtle feel */
.delay-1 { animation-delay: 0.04s; }
.delay-2 { animation-delay: 0.08s; }
.delay-3 { animation-delay: 0.12s; }
.delay-4 { animation-delay: 0.16s; }
.delay-5 { animation-delay: 0.20s; }

/* Horizontal Bar System */
.bar-container {
    margin-bottom: 1rem;
}

.bar-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.75rem;
    color: inherit;
}

.bar-label {
    width: 140px;
    font-size: 0.88rem;
    font-weight: 600;
    color: inherit;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: flex;
    align-items: center;
}

.bar-track {
    flex: 1;
    height: 22px;
    background: rgba(127, 127, 127, 0.18);
    border: 1px solid rgba(127, 127, 127, 0.25);
    border-radius: 6px;
    overflow: hidden;
    position: relative;
}

.bar-fill {
    height: 100%;
    border-radius: 5px;
    transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.bar-stat {
    width: 120px;
    text-align: right;
    font-family: inherit;
    font-size: 0.85rem;
    color: inherit;
    opacity: 0.8;
}

/* Badges / Pills */
.pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}

.pill-red {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.pill-amber {
    background: rgba(245, 158, 11, 0.15);
    color: #d97706;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.pill-blue {
    background: rgba(59, 130, 246, 0.15);
    color: #2563eb;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

.pill-teal {
    background: rgba(20, 184, 166, 0.15);
    color: #0d9488;
    border: 1px solid rgba(20, 184, 166, 0.3);
}

/* Filter status ribbon */
.filter-ribbon {
    background: rgba(127, 127, 127, 0.12);
    border: 1px solid rgba(127, 127, 127, 0.25);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
    color: inherit;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.filter-ribbon strong {
    color: var(--primary-color, #06b6d4);
}

/* Quote box */
.quote-box {
    background: rgba(127, 127, 127, 0.12);
    border: 1px solid rgba(127, 127, 127, 0.25);
    border-left: 4px solid var(--primary-color, #06b6d4);
    padding: 0.85rem 1.1rem;
    border-radius: 0 8px 8px 0;
    font-style: italic;
    color: inherit;
    font-size: 0.9rem;
    margin: 0.5rem 0;
    line-height: 1.5;
}

/* Respect prefers-reduced-motion */
@media (prefers-reduced-motion: reduce) {
    *, .hero-banner, .glass-card, .bar-fill {
        animation: none !important;
        transition: none !important;
    }
}

/* Mobile adjustments */
@media (max-width: 768px) {
    .hero-banner {
        padding: 1.4rem;
    }
    .hero-title {
        font-size: 1.5rem;
    }
    .hero-score-box {
        width: 100%;
    }
    .bar-label {
        width: 100px;
        font-size: 0.8rem;
    }
    .bar-stat {
        width: 90px;
        font-size: 0.78rem;
    }
}
</style>
"""

def inject_theme():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

def render_hero_banner(headline_rating=4.64, delta_ratings=29):
    """
    Renders the hero banner using pure st.markdown.
    Zero indentation to avoid markdown code block parsing.
    """
    html_code = (
        f'<div class="hero-banner">'
        f'<div class="hero-content">'
        f'<span class="hero-badge">Verified Play Store Intelligence</span>'
        f'<h1 class="hero-title">MoveInSync Play Store Intelligence</h1>'
        f'<p class="hero-insight">Key Discovery: <strong>The problem is the 1-2 star tail</strong> (8,164 acute ratings), not 3-star mediocrity.</p>'
        f'</div>'
        f'<div class="hero-score-box">'
        f'<div class="hero-score-label">Headline Rating</div>'
        f'<div class="hero-score-val">{headline_rating:.2f} <span class="hero-score-star">★</span></div>'
        f'<div class="glass-card-delta delta-info">across 114,862 lifetime ratings</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html_code, unsafe_allow_html=True)

def render_kpi_cards(cards):
    """
    Renders glassmorphic KPI cards using pure st.markdown.
    Zero indentation to avoid markdown code block parsing.
    """
    card_elements = []
    for idx, c in enumerate(cards):
        delay_class = f"delay-{(idx % 5) + 1}"
        prefix = c.get('prefix', '')
        suffix = c.get('suffix', '')
        target = c.get('value_num', 0)
        is_float = c.get('is_float', False)
        val_str = f"{prefix}{target:.1f}{suffix}" if is_float else f"{prefix}{target:,}{suffix}"
        delta_type = c.get('delta_type', '')
        delta_text = c.get('delta', '')
        label = c.get('label', '')
        
        card_html = (
            f'<div class="glass-card {delay_class}">'
            f'<div class="glass-card-title">{html.escape(label)}</div>'
            f'<div class="glass-card-value">{val_str}</div>'
            f'<div class="glass-card-delta {delta_type}">{html.escape(str(delta_text))}</div>'
            f'</div>'
        )
        card_elements.append(card_html)
    
    html_code = f'<div class="glass-grid">{"".join(card_elements)}</div>'
    st.markdown(html_code, unsafe_allow_html=True)

def render_horizontal_bars(bars, max_val=None):
    """
    Renders horizontal bars using pure st.markdown.
    Zero indentation to avoid markdown code block parsing.
    """
    calc_max = max(b.get('percent', b.get('value', 1)) for b in bars) if not max_val and bars else (max_val or 100)
    rows = []
    for idx, b in enumerate(bars):
        pct = b.get('percent', 0)
        target_pct = min(max((pct / calc_max) * 100, 0), 100)
        color = b.get('color', 'var(--primary-color, #06b6d4)')
        badge_class = b.get('badge_class', 'pill pill-teal')
        badge_html = f'<span class="{badge_class}" style="margin-right:6px;">{html.escape(str(b["badge"]))}</span>' if b.get('badge') else ''
        stat_str = b.get('stat_str', '')
        label = b.get('label', '')
        
        row_html = (
            f'<div class="bar-row">'
            f'<div class="bar-label" title="{html.escape(str(label))}">{badge_html}{html.escape(str(label))}</div>'
            f'<div class="bar-track">'
            f'<div class="bar-fill" style="width: {target_pct:.1f}%; background: {color};"></div>'
            f'</div>'
            f'<div class="bar-stat">{html.escape(str(stat_str))}</div>'
            f'</div>'
        )
        rows.append(row_html)
        
    html_code = f'<div class="bar-container">{"".join(rows)}</div>'
    st.markdown(html_code, unsafe_allow_html=True)
