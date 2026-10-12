import unittest
import json
from pathlib import Path

class TestPipelineEndToEnd(unittest.TestCase):
    def test_summary_json_structure(self):
        summary_path = Path("reports/summary.json")
        self.assertTrue(summary_path.exists(), "reports/summary.json does not exist!")
        self.assertGreater(summary_path.stat().st_size, 1000, "reports/summary.json is too small or empty")
        
        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        required_keys = [
            "metadata", "theme_shares_all_1_2", "theme_shares_reasons_only",
            "monthly_trends", "spikes_detected", "version_analysis_unbiased",
            "rating_impact", "developer_replies", "near_duplicates"
        ]
        for key in required_keys:
            self.assertIn(key, data, f"Missing required top-level key: {key}")

    def test_html_report_integrity(self):
        report_path = Path("reports/ratings_report.html")
        self.assertTrue(report_path.exists(), "reports/ratings_report.html does not exist!")
        self.assertGreater(report_path.stat().st_size, 10000, "Report file is under 10KB")
        
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertTrue(content.strip().startswith("<!DOCTYPE html>"), "Report must begin with <!DOCTYPE html>")
        self.assertIn("MoveInSync", content, "Report content missing 'MoveInSync'")

    def test_rating_history_snapshot(self):
        history_path = Path("data/processed/rating_history.csv")
        self.assertTrue(history_path.exists(), "rating_history.csv not found!")
        with open(history_path, "r", encoding="utf-8") as f:
            header = f.readline()
        self.assertIn("histogram", header, "rating_history.csv missing 'histogram' column")

if __name__ == "__main__":
    unittest.main()
