"""
Unit tests for TextHumanizer pipeline.
"""

import unittest
from core.humanizer import TextHumanizer


class TestHumanizer(unittest.TestCase):

    def setUp(self):
        self.humanizer = TextHumanizer()

    def test_humanize_reduces_ai_score(self):
        ai_input = (
            "In today's fast-paced digital era, cloud computing plays a crucial role in modern IT architecture. "
            "Furthermore, it is important to remember that companies delve into big data analytics to improve operational efficiency. "
            "In conclusion, cloud infrastructure stands as a testament to technical innovation."
        )
        res = self.humanizer.process(ai_input, tone="academic", intensity=0.55)

        self.assertIn("humanized_text", res)
        self.assertGreater(len(res["humanized_text"]), 20)
        self.assertGreater(res["metrics"]["ai_reduction"], 35.0)
        self.assertGreaterEqual(res["metrics"]["uniqueness_score"], 65.0)

        # Clichés should be eradicated
        humanized_lower = res["humanized_text"].lower()
        self.assertNotIn("in today's fast-paced", humanized_lower)
        self.assertNotIn("delve into", humanized_lower)
        self.assertNotIn("stands as a testament", humanized_lower)

    def test_preserve_keywords(self):
        text = "The machine learning algorithm uses deep neural pathways to improve classification accuracy."
        keywords = ["deep neural pathways", "classification accuracy"]
        res = self.humanizer.process(text, preserve_keywords=keywords)
        self.assertIn("deep neural pathways", res["humanized_text"].lower())


if __name__ == "__main__":
    unittest.main()
