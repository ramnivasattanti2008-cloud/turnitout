"""
Tests for Beast Mode Engine and Stealth Adversarial Transformations.
Verifies 0% verbatim plagiarism and single-digit/zero AI detection across domains.
"""

import unittest
from core.beast_engine import BeastEngine
from core.detector import TextAnalyzer


class TestBeastEngine(unittest.TestCase):
    def setUp(self):
        self.beast = BeastEngine()
        self.analyzer = TextAnalyzer()

    def test_beast_mode_eradicates_ai_and_plagiarism(self):
        text = (
            "Furthermore, it is crucial to recognize that artificial intelligence plays a "
            "multifaceted and pivotal role in modern society. Moreover, it is important to remember "
            "that machine learning algorithms serve as a testament to human innovation."
        )
        res = self.beast.execute_beast_mode(text)
        self.assertIn("humanized_text", res)
        self.assertIn("metrics", res)
        
        metrics = res["metrics"]
        self.assertLessEqual(metrics["ai_score_after"], 5.0)
        self.assertEqual(metrics["plagiarism_risk_score"], 0.0)
        self.assertEqual(metrics["uniqueness_score"], 100.0)
        self.assertEqual(metrics["verbatim_overlap"], 0)
        
        # Verify radar clearance
        radar = res["radar_after"]
        self.assertEqual(radar["detectors"]["turnitin"]["score"], 0.0)
        self.assertEqual(radar["detectors"]["copyleaks"]["score"], 0.0)
        self.assertEqual(radar["detectors"]["turnitin"]["status"], "pass")
        self.assertEqual(radar["detectors"]["gptzero"]["status"], "pass")

    def test_sentence_alternatives_generation(self):
        sentence = "Artificial intelligence plays a pivotal role in modern society."
        alts = self.beast.generate_sentence_alternatives(sentence)
        self.assertEqual(len(alts), 3)
        for alt in alts:
            self.assertIn("style", alt)
            self.assertIn("text", alt)
            self.assertTrue(len(alt["text"]) > 10)


if __name__ == "__main__":
    unittest.main()
