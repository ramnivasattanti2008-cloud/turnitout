"""
Tests for Advanced AI and Plagiarism Detection Subsystem.
Verifies:
- Sentence-by-sentence AI probability breakdown & interactive HTML heatmap
- Corpus & Web plagiarism search against 4,000+ reference texts
- Verbatim n-gram sequence matching & visual highlight markup
- Full forensic detection API payload structure
- Flask REST API endpoints (/api/detect and /api/plagiarism)
"""

import json
import unittest

from core.detector import CorpusPlagiarismIndex, TextAnalyzer
from web.app import app


class TestDetectorAdvanced(unittest.TestCase):
    def setUp(self):
        self.analyzer = TextAnalyzer()
        self.app = app.test_client()
        self.sample_ai = (
            "In today's fast-paced academic landscape, artificial intelligence plays a crucial role "
            "in higher education pedagogy. Furthermore, it is important to remember that deep learning "
            "algorithms delve into massive datasets to extract valuable insights. A multifaceted approach "
            "is imperative to navigate the complexities of algorithmic bias. In conclusion, machine learning "
            "stands as a testament to the power of human ingenuity."
        )
        self.sample_human = (
            "Old barns hold the scent of dry cedar and dusty hay. Sunlight cuts through the timber slats "
            "in sharp white bars across the floorboards. A swallow darts from the rafters out toward the pasture."
        )

    def test_sentence_level_ai_breakdown(self):
        """Sentence breakdown should correctly analyze every sentence with individual scores and HTML markup."""
        res = self.analyzer.analyze_sentence_ai(self.sample_ai)
        self.assertGreater(res["total_sentences"], 1)
        self.assertGreater(res["high_risk_count"], 0)
        self.assertIn("highlighted_html", res)
        self.assertIn("ai-sentence", res["highlighted_html"])
        self.assertIn("ai-risk-high", res["highlighted_html"])

        # Check human sample
        human_res = self.analyzer.analyze_sentence_ai(self.sample_human)
        self.assertGreater(human_res["human_count"], 0)
        self.assertEqual(human_res["high_risk_count"], 0)

    def test_corpus_plagiarism_scan(self):
        """Corpus search should execute cleanly against indexed reference texts."""
        res = self.analyzer.check_corpus_plagiarism(self.sample_ai)
        self.assertIn("plagiarism_risk_score", res)
        self.assertIn("uniqueness_score", res)
        self.assertIn("verdict", res)
        self.assertIn("risk_badge", res)
        self.assertIn("matched_sources", res)
        self.assertGreaterEqual(res["uniqueness_score"], 0.0)
        self.assertLessEqual(res["uniqueness_score"], 100.0)

    def test_verbatim_plagiarism_highlighting(self):
        """Comparative plagiarism should detect exact matching sequences and produce mark tags."""
        orig = "Machine learning algorithms delve into massive datasets to extract valuable insights."
        rewritten = "Deep learning algorithms delve into massive datasets to extract valuable insights."

        sim = self.analyzer.check_plagiarism_similarity(orig, rewritten)
        self.assertGreater(sim["plagiarism_risk_score"], 50.0)
        self.assertLess(sim["uniqueness_score"], 50.0)
        self.assertGreater(len(sim["matching_sequences"]), 0)
        self.assertIn("plag-match", sim["highlighted_plagiarism_html"])

    def test_full_forensic_detection_payload(self):
        """full_forensic_detection should return all unified diagnostic sections."""
        res = self.analyzer.full_forensic_detection(self.sample_ai)

        # AI Likelihood
        self.assertIn("ai_probability", res)
        self.assertGreater(res["ai_probability"], 70.0)
        self.assertIn("verdict", res)

        # Plagiarism
        self.assertIn("plagiarism_risk_score", res)
        self.assertIn("uniqueness_score", res)
        self.assertIn("plagiarism", res)

        # Commercial 5-Engine Radar
        self.assertIn("radar", res)
        detectors = res["radar"]["detectors"]
        for d in ["turnitin", "gptzero", "copyleaks", "zerogpt", "sapling"]:
            self.assertIn(d, detectors)
            self.assertIn("score", detectors[d])
            self.assertIn("status", detectors[d])

        # Sentence Heatmap
        self.assertIn("sentence_analysis", res)
        self.assertEqual(res["sentence_analysis"]["total_sentences"], 4)

    def test_api_detect_endpoint(self):
        """POST /api/detect should return full forensic diagnostics for both AI and plagiarism."""
        response = self.app.post(
            "/api/detect",
            data=json.dumps({"text": self.sample_ai}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertIn("ai_probability", data)
        self.assertIn("plagiarism_risk_score", data)
        self.assertIn("uniqueness_score", data)
        self.assertIn("radar", data)
        self.assertIn("sentence_analysis", data)

    def test_api_plagiarism_endpoint(self):
        """POST /api/plagiarism should return plagiarism scores against corpus or reference text."""
        response = self.app.post(
            "/api/plagiarism",
            data=json.dumps({
                "text": "Machine learning algorithms delve into massive datasets to extract valuable insights.",
                "reference_text": "Deep learning algorithms delve into massive datasets to extract valuable insights."
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertIn("plagiarism_risk_score", data)
        self.assertIn("uniqueness_score", data)
        self.assertIn("ngram_4_overlap", data)


if __name__ == "__main__":
    unittest.main()
