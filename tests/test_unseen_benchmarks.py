"""
Unit and Regression Test Suite for Unseen Real-World Benchmark Texts.
Verifies that arbitrary real-world texts in academic, clinical, and environmental domains
achieve < 5.0% plagiarism risk (> 95% uniqueness) and single-digit AI detection (< 5.0%)
across Turnitin, GPTZero, CopyLeaks, ZeroGPT, and Sapling.
"""

import unittest
from core.humanizer import TextHumanizer


class TestUnseenBenchmarks(unittest.TestCase):
    def setUp(self):
        self.humanizer = TextHumanizer()

    def test_social_media_unseen_benchmark(self):
        text = (
            "The rapid expansion of social media platforms has transformed contemporary communication, "
            "enabling individuals to connect across geographical boundaries. However, research suggests "
            "that excessive screen time is associated with heightened anxiety and depressive symptoms among "
            "adolescents. Addressing these mental health challenges requires concerted interventions from "
            "educators, policymakers, and technology companies."
        )
        res = self.humanizer.process(text, mode="beast")
        metrics = res["metrics"]
        radar = res["radar_after"]

        # Plagiarism risk must be strictly below 5.0%
        self.assertLess(metrics["plagiarism_risk"], 5.0)
        self.assertGreaterEqual(metrics["uniqueness_score"], 95.0)
        # AI score must be <= 5.0%
        self.assertLessEqual(metrics["ai_score_after"], 5.0)
        # Turnitin radar match must be < 5.0% and status must be 'pass'
        self.assertEqual(radar["detectors"]["turnitin"]["status"], "pass")
        self.assertLess(radar["detectors"]["turnitin"]["score"], 5.0)
        # Protected terms must not be butchered
        self.assertIn("social media", res["humanized_text"].lower())
        self.assertIn("mental health", res["humanized_text"].lower())
        self.assertIn("screen time", res["humanized_text"].lower())

    def test_climate_change_unseen_benchmark(self):
        text = (
            "Climate change remains one of the most pressing global challenges of our time. "
            "Rising temperatures and extreme weather events threaten ecosystems and human "
            "livelihoods across the globe. Transitioning to renewable energy sources such as "
            "solar and wind power is essential to mitigate carbon emissions."
        )
        res = self.humanizer.process(text, mode="beast")
        metrics = res["metrics"]
        radar = res["radar_after"]

        self.assertLess(metrics["plagiarism_risk"], 5.0)
        self.assertGreaterEqual(metrics["uniqueness_score"], 95.0)
        self.assertLessEqual(metrics["ai_score_after"], 5.0)
        self.assertEqual(radar["detectors"]["turnitin"]["status"], "pass")
        self.assertLess(radar["detectors"]["turnitin"]["score"], 5.0)
        # Collocations protected
        self.assertIn("climate change", res["humanized_text"].lower())
        self.assertIn("wind power", res["humanized_text"].lower())
        self.assertIn("carbon emissions", res["humanized_text"].lower())

    def test_ai_healthcare_unseen_benchmark(self):
        text = (
            "Artificial intelligence is transforming healthcare by analyzing complex medical data to "
            "improve patient outcomes. Machine learning models assist clinicians in diagnosing rare "
            "diseases and predicting treatment responses. However, data privacy concerns and algorithmic "
            "bias remain significant obstacles to widespread clinical adoption."
        )
        res = self.humanizer.process(text, mode="beast")
        metrics = res["metrics"]
        radar = res["radar_after"]

        self.assertLess(metrics["plagiarism_risk"], 5.0)
        self.assertGreaterEqual(metrics["uniqueness_score"], 95.0)
        self.assertLessEqual(metrics["ai_score_after"], 5.0)
        self.assertEqual(radar["detectors"]["turnitin"]["status"], "pass")
        self.assertLess(radar["detectors"]["turnitin"]["score"], 5.0)
        # Collocations protected
        self.assertIn("data privacy", res["humanized_text"].lower())
        self.assertIn("algorithmic bias", res["humanized_text"].lower())
        self.assertIn("patient outcomes", res["humanized_text"].lower())


if __name__ == "__main__":
    unittest.main()
