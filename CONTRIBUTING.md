# Contributing to MoveInSync Reviews Intelligence

Thank you for contributing to the MoveInSync Reviews Intelligence platform. Follow these engineering guidelines to maintain data integrity, validation accuracy, and zero-PII security.

---

## 🛠️ Development Workflow

1. **Clone and Create a Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Setup Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables:**
   Create a local `.env` file with `GEMINI_API_KEY`. Never commit `.env` or raw API keys.

---

## 🏷️ Adding or Modifying a Taxonomy Theme

To introduce a new classification category:
1. **Declare Theme in `config.py`:**
   Add the uppercase snake_case theme name to `KNOWN_THEMES`.
2. **Define Prompt Guidelines in `analyze_reviews.py`:**
   Add category definitions and disambiguation rules in `analyze_llm_batch()`.
3. **Calibrate with Seed Examples:**
   Add 2–3 representative few-shot examples in `data/seed_reviews.txt`.
4. **Run Calibration Validation:**
   ```bash
   python validate_seeds.py
   ```
   Ensure Macro F1 remains above **70.0%** and match rate above **95.0%**.

---

## 🧪 Testing & Validation Standards

Before submitting changes, all automated test suites must pass:
```bash
# 1. Dataset schema and integrity
python test_data_integrity.py

# 2. Taxonomy cleaning unit tests
python test_theme_taxonomy.py

# 3. Statistical drop calculations
python test_version_drops.py

# 4. Near-duplicate text detection
python test_near_duplicates.py

# 5. End-to-end integration outputs
python test_pipeline_e2e.py

# 6. Gate 4 Number Consistency Verification
python verify_numbers.py
```

---

## 🔒 Security & Privacy Rules

- **Zero PII Policy:** Never add code or scripts that log, display, or store personal user data (names, email addresses, phone numbers).
- **Git Ignore Protection:** Verify that `.env`, `data/raw/`, and `data/processed/review_tags_cache.json` remain uncommitted via `git status`.
