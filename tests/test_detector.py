"""
Unit tests for AI Detector and Plagiarism Checker.
"""

import unittest
from core.detector import TextAnalyzer


class TestDetector(unittest.TestCase):

    def setUp(self):
        self.analyzer = TextAnalyzer()

    def test_ai_marker_detection(self):
        sample = (
            "In today's fast-paced world, artificial intelligence plays a crucial role. "
            "Furthermore, it is important to remember that we must delve into the multifaceted dynamics."
        )
        res = self.analyzer.detect_ai_markers(sample)
        self.assertGreater(res["total_markers"], 2)
        phrases_found = [p["phrase"] for p in res["found_phrases"]]
        self.assertTrue(any("fast-paced" in p or "crucial role" in p or "delve into" in p for p in phrases_found))

    def test_ai_score_high_on_robotic_text(self):
        ai_sample = (
            "In conclusion, it is important to remember that education plays a pivotal role in today's digital era. "
            "Furthermore, by delving into a multifaceted approach, one can navigate the complexities of modern thought. "
            "Moreover, this stands as a testament to human resilience."
        )
        result = self.analyzer.compute_ai_score(ai_sample)
        self.assertGreaterEqual(result["ai_probability"], 65.0)
        self.assertIn("AI", result["verdict"])

    def test_plagiarism_similarity(self):
        original = "The quick brown fox jumped across the wide river to reach the forest."
        plagiarized = "The quick brown fox jumped across the wide river to reach the forest."
        rep = self.analyzer.check_plagiarism_similarity(original, plagiarized)
        self.assertGreaterEqual(rep["plagiarism_risk_score"], 80.0)

        paraphrased = "A rapid auburn fox leaped over the expansive waterway toward the dense woods."
        rep2 = self.analyzer.check_plagiarism_similarity(original, paraphrased)
        self.assertLess(rep2["plagiarism_risk_score"], 25.0)


if __name__ == "__main__":
    unittest.main()
