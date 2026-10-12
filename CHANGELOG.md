# Changelog

All notable changes to the MoveInSync Play Store Reviews Intelligence Pipeline are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] - 2026-10-12

### Added
- Comprehensive technical implementation manual (`IMPLEMENTATION.md`).
- Automated data integrity test suite (`test_data_integrity.py`).
- Automated taxonomy cleaning unit tests (`test_theme_taxonomy.py`).
- Pipeline latency benchmark tool (`scripts/dev/benchmark_pipeline.py`).
- Automated Gate 4 verification step in GitHub Actions weekly workflow.

### Fixed
- Streamlit dual-theme compatibility: removed hardcoded `theme.base = "dark"` in favor of native System / Light / Dark settings menu.
- Replaced `st.components.v1.html` iframes with pure `st.markdown` to eliminate iframe boundaries, clipped cards, and serif font fallbacks.
- Enforced zero indentation on HTML blocks in `ui_theme.py` and `dashboard.py` to prevent Markdown parsing HTML as preformatted code blocks.
- Configured default sidebar filters: App Version defaults to empty (`[]`), date range spans full dataset, star ratings default to all five stars (matching review count = 3,171 on first load).
- Added interactive "Reset filters" button.

---

## [1.2.0] - 2026-10-11

### Added
- Rigorous statistical modeling engine (`compute_stage_d_analysis.py`).
- Wilson score 95% confidence intervals on version analysis with neighbour-pooled non-overlapping drop test.
- Trailing 6-month spike detector (`count >= 8` and `monthly_share >= 2x trailing_avg`).
- Cosine similarity near-duplicate review clustering with TF-IDF vectorizer (threshold: 0.85).
- Histogram scaling model for projected rating lift simulation (+0.06 to +0.09 stars for top 3 themes).
- Standalone self-contained HTML executive report compiler (`build_report.py`).
- Automated Gate 4 number verification suite (`verify_numbers.py`).

---

## [1.1.0] - 2026-10-10

### Added
- LLM semantic classification engine (`analyze_reviews.py`) powered by Google `gemini-3.5-flash-lite`.
- 110-review curated ground-truth seed dataset (`data/seed_reviews.txt`).
- Seed calibration script (`validate_seeds.py`) achieving 98.6% match rate and 77.5% Macro F1 on held-out reviews.
- Local disk classification caching (`data/processed/review_tags_cache.json`) for idempotency and zero redundant API costs.
- Privacy Gate stripping all personal identifiable information (usernames, emails) from reviews.

---

## [1.0.0] - 2026-10-09

### Added
- Initial Play Store scraper (`collect_reviews.py`) targeting `com.moveinsync.ets`.
- Raw review ingestion and official rating histogram snapshot capture (`rating_history.csv`).
- 24-month temporal boundary separating pre-Oct 2024 legacy records from the active operational window.
- Isolated sample separation: `all_1_2_star` (N=1,671) and `random_3_5_star` (N=1,500).
