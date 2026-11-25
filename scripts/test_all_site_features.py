"""
Comprehensive End-to-End Test Suite for TextHumanizer Pro Web Application.
Tests every API endpoint, edge case, file upload format, and error handling.
"""

import io
import docx
import requests
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE_URL = "http://127.0.0.1:5000"

def test_endpoint(name, func):
    try:
        func()
        print(f"  [PASS] {name}")
        return True
    except Exception as e:
        print(f"  [FAIL] {name}: {str(e)}")
        return False

def run_all_tests():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE SITE & API VERIFICATION")
    print("=" * 60)
    results = []

    # 1. Main Page
    def t_main_page():
        r = requests.get(f"{BASE_URL}/")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert "Turnitout" in r.text
        assert "TextHumanizer" in r.text
        assert "BEAST MODE" in r.text
        assert "Turnitin AI" in r.text
        assert "Commercial AI Detector Radar" in r.text
    results.append(test_endpoint("GET / (Main Page HTML & Elements)", t_main_page))

    # 2. Static CSS & JS
    def t_static_assets():
        r_css = requests.get(f"{BASE_URL}/static/css/style.css")
        assert r_css.status_code == 200
        assert "var(--bg-primary)" in r_css.text

        r_js = requests.get(f"{BASE_URL}/static/js/app.js")
        assert r_js.status_code == 200
        assert "DOMContentLoaded" in r_js.text
    results.append(test_endpoint("Static Assets (/static/css, /static/js)", t_static_assets))

    # 3. Presets
    def t_presets():
        r = requests.get(f"{BASE_URL}/api/presets")
        assert r.status_code == 200
        d = r.json()
        assert "academic" in d and "essay" in d and "business" in d
        assert len(d["academic"]) > 50
    results.append(test_endpoint("GET /api/presets", t_presets))

    # 4. Model Status
    def t_model_status():
        r = requests.get(f"{BASE_URL}/api/model/status")
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") == "ready"
        assert "calibration" in d
    results.append(test_endpoint("GET /api/model/status", t_model_status))

    # 5. Detect Endpoint (Normal + Empty error handling)
    def t_detect():
        # Empty
        r_empty = requests.post(f"{BASE_URL}/api/detect", json={"text": ""})
        assert r_empty.status_code == 400
        assert "error" in r_empty.json()

        # Valid text
        text = (
            "In today's fast-paced digital landscape, artificial intelligence plays a crucial role. "
            "Furthermore, it is important to remember that deep learning algorithms delve into massive datasets."
        )
        r = requests.post(f"{BASE_URL}/api/detect", json={"text": text})
        assert r.status_code == 200
        d = r.json()
        assert "ai_probability" in d
        assert "radar" in d
        assert "detectors" in d["radar"]
        assert "sentence_analysis" in d
        assert len(d["sentence_analysis"]["sentences"]) >= 2
    results.append(test_endpoint("POST /api/detect (AI & Plagiarism Scan)", t_detect))

    # 6. Humanize Endpoint (Standard & Beast modes)
    def t_humanize():
        # Empty
        r_empty = requests.post(f"{BASE_URL}/api/humanize", json={"text": ""})
        assert r_empty.status_code == 400

        # Standard
        text = "Artificial intelligence models delve into massive datasets to extract valuable insights."
        r_std = requests.post(f"{BASE_URL}/api/humanize", json={"text": text, "mode": "standard"})
        assert r_std.status_code == 200
        assert len(r_std.json()["humanized_text"]) > 10

        # Beast
        r_beast = requests.post(f"{BASE_URL}/api/humanize", json={"text": text, "mode": "beast", "intensity": 0.85})
        assert r_beast.status_code == 200
        d_beast = r_beast.json()
        assert d_beast["metrics"]["ai_score_after"] <= 5.0
        assert d_beast["metrics"]["uniqueness_score"] >= 80.0
    results.append(test_endpoint("POST /api/humanize (Standard & Beast Modes)", t_humanize))

    # 7. Beast Direct Endpoint
    def t_beast_direct():
        text = "Furthermore, it is imperative to utilize deep learning algorithms to enhance productivity."
        r = requests.post(f"{BASE_URL}/api/beast", json={"text": text, "intensity": 0.75})
        assert r.status_code == 200
        d = r.json()
        assert "humanized_text" in d
        assert "delve" not in d["humanized_text"].lower()
    results.append(test_endpoint("POST /api/beast (Direct Beast API)", t_beast_direct))

    # 8. Sentence Alternatives
    def t_alternatives():
        sentence = "Deep learning algorithms analyze complex datasets."
        r = requests.post(f"{BASE_URL}/api/alternatives", json={"sentence": sentence, "tone": "academic"})
        assert r.status_code == 200
        d = r.json()
        assert len(d["alternatives"]) == 3
        styles = [a["style"] for a in d["alternatives"]]
        assert "Direct & Punchy" in styles
        assert "Scholarly & Analytical" in styles
    results.append(test_endpoint("POST /api/alternatives (3 Instant Variations)", t_alternatives))

    # 9. File Upload (.txt and .docx)
    def t_file_upload():
        # Plain text
        txt_bytes = b"Sample text content for parsing and testing."
        files_txt = {"file": ("test.txt", txt_bytes, "text/plain")}
        r_txt = requests.post(f"{BASE_URL}/api/upload", files=files_txt)
        assert r_txt.status_code == 200
        assert "Sample text content" in r_txt.json()["text"]

        # Docx
        doc = docx.Document()
        doc.add_paragraph("Docx upload paragraph for parsing verification.")
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        files_docx = {"file": ("sample.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        r_docx = requests.post(f"{BASE_URL}/api/upload", files=files_docx)
        assert r_docx.status_code == 200
        assert "Docx upload paragraph" in r_docx.json()["text"]
    results.append(test_endpoint("POST /api/upload (.txt & .docx parsing)", t_file_upload))

    # 10. Word Export Endpoint
    def t_export_docx():
        r = requests.post(f"{BASE_URL}/api/export/docx", json={"text": "Humanized export paragraph."})
        assert r.status_code == 200
        assert len(r.content) > 500
        doc = docx.Document(io.BytesIO(r.content))
        assert any("Humanized export paragraph." in p.text for p in doc.paragraphs)
    results.append(test_endpoint("POST /api/export/docx (Downloadable Word Document)", t_export_docx))

    # 11. Word Format-Preserving Humanization Endpoint
    def t_humanize_docx():
        doc = docx.Document()
        h = doc.add_heading("1. Background Study", level=1)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run("In today's fast-paced digital world, machine learning models delve into massive corporate datasets.")
        r.font.name = "Georgia"
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(10, 40, 90)

        doc.add_paragraph("First key point on neural network architectures.", style="List Bullet")

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)

        files = {"file": ("paper.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        r = requests.post(f"{BASE_URL}/api/humanize/docx", files=files, data={"mode": "beast", "intensity": 0.85})
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["metrics"]["ai_score_after"] <= 5.0
        assert "download_url" in d
        assert "download_token" in d

        # Test clean download
        dl_url = f"{BASE_URL}{d['download_url']}"
        r_dl = requests.get(dl_url)
        assert r_dl.status_code == 200
        assert len(r_dl.content) > 1000

        # Test annotated diff download
        assert "annotated_download_url" in d
        r_ann = requests.get(f"{BASE_URL}{d['annotated_download_url']}")
        assert r_ann.status_code == 200
        assert len(r_ann.content) > 1000

        # Verify formatting
        dl_doc = docx.Document(io.BytesIO(r_dl.content))
        assert dl_doc.paragraphs[0].text == "1. Background Study"
        assert dl_doc.paragraphs[1].runs[0].font.name == "Georgia"
        assert dl_doc.paragraphs[2].style.name == "List Bullet"
    results.append(test_endpoint("POST /api/humanize/docx & GET /api/download/docx/<token>", t_humanize_docx))

    # 12. Direct Docx Streaming Endpoint
    def t_humanize_docx_direct():
        doc = docx.Document()
        doc.add_paragraph("Direct streaming word document test paragraph.")
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        files = {"file": ("direct.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        r = requests.post(f"{BASE_URL}/api/humanize/docx/direct", files=files, data={"mode": "beast", "intensity": 0.85})
        assert r.status_code == 200
        assert len(r.content) > 500
        doc_res = docx.Document(io.BytesIO(r.content))
        assert len(doc_res.paragraphs) >= 1
    results.append(test_endpoint("POST /api/humanize/docx/direct (Single-Request Streaming)", t_humanize_docx_direct))

    # 13. Download Invalid Token 404 Handling
    def t_invalid_download_token():
        r = requests.get(f"{BASE_URL}/api/download/docx/non-existent-token-12345")
        assert r.status_code == 404
        assert "error" in r.json()
    results.append(test_endpoint("GET /api/download/docx/<invalid-token> (404 Error Handling)", t_invalid_download_token))

    # 14. Sample Word Doc Endpoint
    def t_sample_docx():
        r = requests.get(f"{BASE_URL}/api/sample/docx")
        assert r.status_code == 200
        assert "officedocument" in r.headers.get("Content-Type", "")
        doc = docx.Document(io.BytesIO(r.content))
        assert len(doc.paragraphs) >= 4
        assert "Executive Overview" in doc.paragraphs[0].text
        assert len(doc.tables) >= 1
    results.append(test_endpoint("GET /api/sample/docx (Rich Styled Sample Word Document)", t_sample_docx))

    # 15. Code Comment Humanizer
    def t_code_humanize():
        code_sample = """# This function initializes the database connection
def connect_db():
    # Loop through the list of servers
    for s in servers:
        pass
"""
        r = requests.post(f"{BASE_URL}/api/code/humanize", json={"code": code_sample, "language": "python", "persona": "intermediate"})
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True
        assert d.get("comments_modified", 0) >= 1
        assert "connect_db" in d["code"]
    results.append(test_endpoint("POST /api/code/humanize (Code Comment Humanizer)", t_code_humanize))

    # 16. Auto-Citation Generator
    def t_citations_generate():
        r = requests.post(f"{BASE_URL}/api/citations/generate", json={"discipline": "computer_science", "count": 2})
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True
        assert "@article{" in d.get("bibtex", "")
        assert len(d.get("latex_cite_keys", [])) == 2
    results.append(test_endpoint("POST /api/citations/generate (BibTeX/LaTeX Citation Generator)", t_citations_generate))

    # 17. Watermark & Zero-Width Scrubber
    def t_watermark_scrub():
        dirty_text = "Standard\u200B text with invisible\u200C zero-width\uFEFF watermarks."
        r = requests.post(f"{BASE_URL}/api/scrub/watermarks", json={"text": dirty_text})
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True
        assert d.get("zero_width_purged", 0) >= 3
        assert "\u200B" not in d["clean_text"]
    results.append(test_endpoint("POST /api/scrub/watermarks (Zero-Width Threat Erasure)", t_watermark_scrub))

    print("=" * 60)
    passed = sum(1 for res in results if res)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed ({round(passed/total*100, 1)}%)")
    print("=" * 60)
    assert passed == total, f"Some tests failed! {total - passed} failure(s)."

if __name__ == "__main__":
    run_all_tests()
