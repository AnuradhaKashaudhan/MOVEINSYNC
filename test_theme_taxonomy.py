import unittest
from compute_stage_d_analysis import clean_theme

class TestThemeTaxonomyCleaning(unittest.TestCase):
    def test_spelling_normalization(self):
        self.assertEqual(clean_theme("other_driver_behavior"), "OTHER_DRIVER_BEHAVIOUR")
        self.assertEqual(clean_theme("other_driver_behaviour"), "OTHER_DRIVER_BEHAVIOUR")
        self.assertEqual(clean_theme("ui_red_esign"), "UI_REDESIGN")
        self.assertEqual(clean_theme("slow_permissions"), "PERMISSIONS")

    def test_generic_negatives_mapped_to_no_detail(self):
        generics = [
            "waste", "poor_quality", "app_frustration", "generic_negative",
            "useless_app", "general_poor", "confusing_ui", "imposing_policies"
        ]
        for g in generics:
            self.assertEqual(clean_theme(g), "NO_DETAIL", f"Expected '{g}' to map to NO_DETAIL")

    def test_null_or_empty_mapped_to_no_detail(self):
        self.assertEqual(clean_theme(None), "NO_DETAIL")
        self.assertEqual(clean_theme(float("nan")), "NO_DETAIL")

    def test_standard_themes_preserved(self):
        standard = ["LOGIN_OTP", "APP_CRASH_OPEN", "LOCATION_ETA", "SLOW_PERFORMANCE", "BOOKING"]
        for s in standard:
            self.assertEqual(clean_theme(s), s, f"Expected '{s}' to be preserved")

if __name__ == "__main__":
    unittest.main()
