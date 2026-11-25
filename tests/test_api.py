"""
Unit tests for Flask API endpoints.
"""

import json
import unittest
from web.app import app


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_page(self):
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Turnitout", resp.data)

    def test_presets_api(self):
        resp = self.app.get("/api/presets")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("academic", data)
        self.assertIn("essay", data)

    def test_detect_api(self):
        payload = {"text": "In today's fast-paced world, artificial intelligence plays a crucial role."}
        resp = self.app.post("/api/detect", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("ai_probability", data)
        self.assertIn("verdict", data)

    def test_humanize_api(self):
        payload = {
            "text": "Furthermore, it is important to remember that education plays a pivotal role in society.",
            "tone": "standard",
            "intensity": 0.50
        }
        resp = self.app.post("/api/humanize", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("humanized_text", data)
        self.assertIn("metrics", data)
        self.assertGreater(data["metrics"]["uniqueness_score"], 60.0)

    def test_model_status_api(self):
        resp = self.app.get("/api/model/status")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("model_version", data)


if __name__ == "__main__":
    unittest.main()
