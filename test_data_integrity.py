import unittest
import pandas as pd
from pathlib import Path

class TestDataIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_path = Path("data/processed/analyzed_reviews.csv")
        cls.history_path = Path("data/processed/rating_history.csv")
        assert cls.data_path.exists(), "analyzed_reviews.csv not found!"
        cls.df = pd.read_csv(cls.data_path)

    def test_active_sample_size(self):
        df_active = self.df[~self.df['is_legacy']] if 'is_legacy' in self.df.columns else self.df
        self.assertEqual(len(df_active), 3171, "Active sample size must equal exactly 3,171 reviews")

    def test_required_columns(self):
        expected_cols = [
            'reviewId', 'score', 'content', 'at', 'sample_group', 
            'tag_method', 'primary_theme', 'themes', 'sentiment', 'severity'
        ]
        for col in expected_cols:
            self.assertIn(col, self.df.columns, f"Missing required column: {col}")

    def test_score_range(self):
        scores = self.df['score'].dropna()
        self.assertTrue((scores >= 1).all() and (scores <= 5).all(), "Scores must be integers between 1 and 5")

    def test_sentiment_values(self):
        valid_sentiments = {'negative', 'neutral', 'positive', 'mixed'}
        sentiments = set(self.df['sentiment'].dropna().unique())
        self.assertTrue(sentiments.issubset(valid_sentiments), f"Invalid sentiments found: {sentiments - valid_sentiments}")

    def test_severity_range(self):
        severities = self.df['severity'].dropna()
        self.assertTrue((severities >= 1.0).all() and (severities <= 5.0).all(), "Severity must be between 1.0 and 5.0")

if __name__ == "__main__":
    unittest.main()
