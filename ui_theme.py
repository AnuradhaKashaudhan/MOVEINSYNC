import streamlit as st
import streamlit.components.v1 as components
import json
import html

# Core CSS for styling and animations
GLOBAL_CSS = """
<style>
    /* Google Font fallback */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Keyframes */
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(16px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes barExpand {
        from { width: 0%; }
        to { width: var(--target-width); }
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(-45deg, #091e2b, #0f2c3f, #1e1b4b, #0d3840);
        background-size: 300% 300%;
        animation: gradientBG 14s ease infinite;
        border-radius: 16px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(20, 184, 166, 0.25);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), 0 0 20px 0 rgba(6, 182, 212, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1.5rem;
    }

    .hero-content {
        flex: 1;
        min-width: 280px;
    }

    .hero-badge {
        display: inline-block;
        padding: 4px 12px;
        background: rgba(6, 182, 212, 0.15);
        border: 1px solid rgba(6, 182, 212, 0.35);
        color: #38bdf8;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        border-radius: 9999px;
        margin-bottom: 0.75rem;
    }

    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0 0 0.5rem 0;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }

    .hero-insight {
        font-size: 1.05rem;
        color: #cbd5e1;
        margin: 0;
        font-weight: 500;
    }

    .hero-insight strong {
        color: #f87171;
    }

    .hero-score-box {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.2rem 1.8rem;
        text-align: center;
        min-width: 170px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }

    .hero-score-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.05em;
    }

    .hero-score-val {
        font-size: 2.8rem;
        font-weight: 800;
        color: #ffffff;
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
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 1.2rem;
        margin-bottom: 2rem;
    }

    .glass-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.4rem;
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.3s ease;
        animation: fadeInUp 0.6s ease forwards;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }

    .glass-card:hover {
        transform: translateY(-4px);
        border-color: rgba(6, 182, 212, 0.35);
        box-shadow: 0 12px 28px -6px rgba(0, 0, 0, 0.5), 0 0 15px rgba(6, 182, 212, 0.15);
    }

    .glass-card-title {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }

    .glass-card-value {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.3rem;
        line-height: 1.1;
    }

    .glass-card-delta {
        font-size: 0.82rem;
        color: #64748b;
        font-weight: 500;
    }

    .delta-alert {
        color: #f87171;
    }

    .delta-success {
        color: #34d399;
    }

    .delta-info {
        color: #38bdf8;
    }

    /* Staggered Delays */
    .delay-1 { animation-delay: 0.05s; }
    .delay-2 { animation-delay: 0.12s; }
    .delay-3 { animation-delay: 0.19s; }
    .delay-4 { animation-delay: 0.26s; }
    .delay-5 { animation-delay: 0.33s; }

    /* Custom Horizontal Bar System */
    .bar-row {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.85rem;
    }

    .bar-label {
        width: 140px;
        font-size: 0.88rem;
        font-weight: 600;
        color: #e2e8f0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .bar-track {
        flex: 1;
        height: 24px;
        background: rgba(15, 23, 42, 0.7);
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.05);
        position: relative;
    }

    .bar-fill {
        height: 100%;
        border-radius: 6px;
        transition: width 0.7s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 8px;
    }

    .bar-stat {
        width: 110px;
        text-align: right;
        font-family: monospace;
        font-size: 0.85rem;
        color: #94a3b8;
    }

    /* Badges */
    .pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }

    .pill-red {
        background: rgba(239, 68, 68, 0.18);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }

    .pill-amber {
        background: rgba(245, 158, 11, 0.18);
        color: #fde68a;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }

    .pill-blue {
        background: rgba(59, 130, 246, 0.18);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.35);
    }

    .pill-teal {
        background: rgba(20, 184, 166, 0.18);
        color: #5eead4;
        border: 1px solid rgba(20, 184, 166, 0.35);
    }

    /* Filter status ribbon */
    .filter-ribbon {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(6, 182, 212, 0.3);
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin-bottom: 1.5rem;
        font-size: 0.9rem;
        color: #cbd5e1;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .filter-ribbon strong {
        color: #38bdf8;
    }

    /* Quote card in expander */
    .quote-box {
        background: rgba(15, 23, 42, 0.6);
        border-left: 3px solid #8b5cf6;
        padding: 0.85rem 1.1rem;
        border-radius: 0 8px 8px 0;
        font-style: italic;
        color: #e2e8f0;
        font-size: 0.9rem;
        margin: 0.5rem 0;
        line-height: 1.5;
    }

    /* Prefernces: reduced motion */
    @media (prefers-reduced-motion: reduce) {
        *, .hero-banner, .glass-card, .bar-fill {
            animation: none !important;
            transition: none !important;
        }
    }

    /* Mobile adjustments */
    @media (max-width: 768px) {
        .hero-banner {
            padding: 1.5rem;
        }
        .hero-title {
            font-size: 1.6rem;
        }
        .hero-score-box {
            width: 100%;
        }
        .bar-label {
            width: 100px;
            font-size: 0.8rem;
        }
        .bar-stat {
            width: 80px;
            font-size: 0.78rem;
        }
    }
</style>
"""

def inject_theme():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

def render_hero_banner(headline_rating=4.64, delta_ratings=29):
    """
    Renders an animated hero banner with count-up on the 4.64 rating.
    """
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        {GLOBAL_CSS}
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
        }}
    </style>
    </head>
    <body>
    <div class="hero-banner">
        <div class="hero-content">
            <span class="hero-badge">Verified Play Store Intelligence</span>
            <h1 class="hero-title">MoveInSync Play Store Intelligence</h1>
            <p class="hero-insight">Key Discovery: <strong>The problem is the 1-2 star tail</strong> (8,164 acute ratings), not 3-star mediocrity.</p>
        </div>
        <div class="hero-score-box">
            <div class="hero-score-label">Headline Rating</div>
            <div class="hero-score-val"><span id="count-rating">0.00</span> <span class="hero-score-star">★</span></div>
            <div class="glass-card-delta delta-info">across 114,862 lifetime ratings</div>
        </div>
    </div>
    <script>
        (function() {{
            const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            const target = {headline_rating};
            const el = document.getElementById('count-rating');
            if (prefersReduced) {{
                el.textContent = target.toFixed(2);
                return;
            }}
            const duration = 650;
            const startTime = performance.now();
            function update(now) {{
                const elapsed = now - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // easeOutQuad
                const ease = 1 - (1 - progress) * (1 - progress);
                const current = (ease * target).toFixed(2);
                el.textContent = current;
                if (progress < 1) {{
                    requestAnimationFrame(update);
                }} else {{
                    el.textContent = target.toFixed(2);
                }}
            }}
            requestAnimationFrame(update);
        }})();
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=195, scrolling=False)

def render_kpi_cards(cards):
    """
    Renders a row of animated glassmorphic cards with count-ups.
    cards: list of dicts with keys: 'label', 'value_num', 'prefix', 'suffix', 'delta', 'delta_type', 'is_float'
    """
    cards_json = json.dumps(cards)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        {GLOBAL_CSS}
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
        }}
    </style>
    </head>
    <body>
    <div class="glass-grid" id="kpi-container"></div>
    <script>
        (function() {{
            const cards = {cards_json};
            const container = document.getElementById('kpi-container');
            const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            
            cards.forEach((c, idx) => {{
                const cardDiv = document.createElement('div');
                cardDiv.className = 'glass-card delay-' + ((idx % 5) + 1);
                
                const titleDiv = document.createElement('div');
                titleDiv.className = 'glass-card-title';
                titleDiv.textContent = c.label;
                
                const valDiv = document.createElement('div');
                valDiv.className = 'glass-card-value';
                const spanId = 'kpi-val-' + idx;
                valDiv.innerHTML = '<span id="' + spanId + '">' + (c.prefix || '') + '0' + (c.suffix || '') + '</span>';
                
                const deltaDiv = document.createElement('div');
                deltaDiv.className = 'glass-card-delta ' + (c.delta_type || '');
                deltaDiv.textContent = c.delta;
                
                cardDiv.appendChild(titleDiv);
                cardDiv.appendChild(valDiv);
                cardDiv.appendChild(deltaDiv);
                container.appendChild(cardDiv);
                
                const el = document.getElementById(spanId);
                const target = c.value_num;
                const isFloat = c.is_float;
                const prefix = c.prefix || '';
                const suffix = c.suffix || '';
                
                if (prefersReduced) {{
                    el.textContent = prefix + (isFloat ? target.toFixed(2) : target.toLocaleString()) + suffix;
                    return;
                }}
                
                const duration = 600 + (idx * 60);
                const startTime = performance.now();
                function update(now) {{
                    const elapsed = now - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    const ease = 1 - Math.pow(1 - progress, 3);
                    const current = ease * target;
                    const displayVal = isFloat ? current.toFixed(1) : Math.round(current).toLocaleString();
                    el.textContent = prefix + displayVal + suffix;
                    if (progress < 1) {{
                        requestAnimationFrame(update);
                    }} else {{
                        el.textContent = prefix + (isFloat ? target.toFixed(1) : target.toLocaleString()) + suffix;
                    }}
                }}
                requestAnimationFrame(update);
            }});
        }})();
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=135, scrolling=False)

def render_horizontal_bars(bars, max_val=None):
    """
    bars: list of dicts: {'label': str, 'value': num, 'percent': float, 'color': str, 'stat_str': str, 'badge': str}
    """
    bars_json = json.dumps(bars)
    calc_max = max(b.get('percent', b.get('value', 1)) for b in bars) if not max_val and bars else (max_val or 100)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        {GLOBAL_CSS}
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
        }}
    </style>
    </head>
    <body>
    <div id="bar-container"></div>
    <script>
        (function() {{
            const bars = {bars_json};
            const maxVal = {calc_max};
            const container = document.getElementById('bar-container');
            const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

            bars.forEach((b, idx) => {{
                const row = document.createElement('div');
                row.className = 'bar-row';
                
                const label = document.createElement('div');
                label.className = 'bar-label';
                label.title = b.label;
                label.innerHTML = (b.badge ? '<span class="' + (b.badge_class || 'pill pill-teal') + '" style="margin-right:6px;">' + b.badge + '</span>' : '') + b.label;
                
                const track = document.createElement('div');
                track.className = 'bar-track';
                
                const fill = document.createElement('div');
                fill.className = 'bar-fill';
                fill.style.background = b.color || 'linear-gradient(90deg, #06b6d4, #0891b2)';
                
                const targetPct = Math.min((b.percent / maxVal) * 100, 100);
                
                if (prefersReduced) {{
                    fill.style.width = targetPct + '%';
                }} else {{
                    fill.style.width = '0%';
                    setTimeout(() => {{
                        fill.style.width = targetPct + '%';
                    }}, 40 + idx * 30);
                }}
                
                track.appendChild(fill);
                
                const stat = document.createElement('div');
                stat.className = 'bar-stat';
                stat.textContent = b.stat_str;
                
                row.appendChild(label);
                row.appendChild(track);
                row.appendChild(stat);
                container.appendChild(row);
            }});
        }})();
    </script>
    </body>
    </html>
    """
    height = max(len(bars) * 44 + 10, 60)
    components.html(html_code, height=height, scrolling=False)
