"""
Comprehensive Unit & Integration Tests for Word (.docx) Format-Preserving Humanizer.
Tests in-place style preservation, font/color fidelity, table handling,
0% AI score achievement, 0% plagiarism score achievement, and Flask API endpoints.
"""

import io
import unittest
from pathlib import Path
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from core.document_parser import DocumentParser
from core.humanizer import TextHumanizer
from web.app import app


class TestDocxHumanizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.humanizer = TextHumanizer()
        cls.client = app.test_client()

    def _create_sample_styled_docx(self) -> io.BytesIO:
        """Creates an in-memory .docx with custom styles, fonts, alignments, bullets, and tables."""
        doc = docx.Document()

        # 1. Title / Heading
        h = doc.add_heading("1. Introduction", level=1)
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 2. Rich-styled paragraph with AI-generated text
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.25
        run = p.add_run(
            "In today's fast-paced digital world, artificial intelligence plays a crucial role "
            "in revolutionizing higher education pedagogy. Furthermore, it is important to remember "
            "that deep learning algorithms delve into massive datasets to extract valuable insights. "
            "A multifaceted approach is imperative to navigate the complexities of algorithmic bias. "
            "In conclusion, modern neural architectures stand as a testament to the power of human ingenuity."
        )
        run.font.name = "Georgia"
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.italic = False
        run.font.color.rgb = RGBColor(10, 40, 90)

        # 3. Bullet points
        b1 = doc.add_paragraph("First key breakthrough in automated systems.", style="List Bullet")
        b2 = doc.add_paragraph("Second key advancement in natural language processing.", style="List Bullet")

        # 4. Table with content
        table = doc.add_table(rows=2, cols=2)
        table.rows[0].cells[0].text = "Category"
        table.rows[0].cells[1].text = "Description"
        table.rows[1].cells[0].text = "Machine Learning"
        p_cell = table.rows[1].cells[1].paragraphs[0]
        c_run = p_cell.add_run(
            "It goes without saying that deep learning algorithms weave a rich tapestry of data representations."
        )
        c_run.font.name = "Arial"
        c_run.font.size = Pt(10)
        c_run.font.color.rgb = RGBColor(50, 50, 50)

        stream = io.BytesIO()
        doc.save(stream)
        stream.seek(0)
        return stream

    def test_paragraph_formatting_preservation(self):
        """Verifies that replace_paragraph_text_preserving_formatting keeps fonts, sizes, colors, and alignments."""
        doc = docx.Document()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run("Original text with custom styling.")
        r.font.name = "Times New Roman"
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.italic = True
        r.font.color.rgb = RGBColor(128, 0, 0)

        new_text = "Completely overhauled phrasing that replaces the previous content entirely."
        DocumentParser.replace_paragraph_text_preserving_formatting(p, new_text)

        # Assertions
        self.assertEqual(p.text, new_text)
        self.assertEqual(p.alignment, WD_ALIGN_PARAGRAPH.JUSTIFY)
        self.assertEqual(p.runs[0].font.name, "Times New Roman")
        self.assertEqual(p.runs[0].font.size, Pt(14))
        self.assertTrue(p.runs[0].font.bold)
        self.assertTrue(p.runs[0].font.italic)
        self.assertEqual(p.runs[0].font.color.rgb, RGBColor(128, 0, 0))

    def test_is_structural_heading(self):
        """Verifies detection of outline headings to avoid altering standard structural labels."""
        self.assertTrue(DocumentParser.is_structural_heading("1. Introduction", "Heading 1"))
        self.assertTrue(DocumentParser.is_structural_heading("Abstract", "Normal"))
        self.assertTrue(DocumentParser.is_structural_heading("2.3 Methodology", "Heading 2"))
        self.assertTrue(DocumentParser.is_structural_heading("References", "Normal"))
        self.assertTrue(DocumentParser.is_structural_heading("Conclusion", "Normal"))

        # Non-headings
        self.assertFalse(DocumentParser.is_structural_heading(
            "In today's fast-paced world, artificial intelligence plays a crucial role in modern science.",
            "Normal"
        ))

    def test_humanize_docx_document_end_to_end(self):
        """
        Tests end-to-end format-preserving document humanization.
        Asserts layout preservation, 0% AI detection, and 0% plagiarism.
        """
        source_stream = self._create_sample_styled_docx()

        out_stream, summary = DocumentParser.humanize_docx_document(
            docx_source=source_stream,
            humanizer=self.humanizer,
            mode="beast",
            intensity=0.85
        )

        self.assertIsInstance(out_stream, io.BytesIO)
        self.assertGreater(len(out_stream.getvalue()), 1000)

        # Check metrics
        metrics = summary["metrics"]
        self.assertGreaterEqual(metrics["ai_score_before"], 60.0)
        self.assertLessEqual(metrics["ai_score_after"], 5.0)  # Near 0% AI
        self.assertLessEqual(metrics["plagiarism_risk"], 5.0)    # Near 0.0% plagiarism
        self.assertGreaterEqual(metrics["uniqueness_score"], 95.0)  # >= 95% unique

        # Verify radar passes Turnitin, GPTZero, CopyLeaks, ZeroGPT, Sapling
        radar = summary["radar_after"]["detectors"]
        for det_name, info in radar.items():
            self.assertEqual(info["status"], "pass", f"Detector {det_name} failed: {info}")

        # Re-parse output docx to check formatting preservation
        out_stream.seek(0)
        reloaded_doc = docx.Document(out_stream)

        # 1. Verify heading preserved
        h0 = reloaded_doc.paragraphs[0]
        self.assertEqual(h0.text.strip(), "1. Introduction")
        self.assertEqual(h0.alignment, WD_ALIGN_PARAGRAPH.CENTER)

        # 2. Verify styled paragraph preserved its font name, size, bold, color, and alignment
        p1 = reloaded_doc.paragraphs[1]
        self.assertNotEqual(p1.text.strip(), "")
        self.assertNotIn("delve into massive datasets", p1.text)
        self.assertNotIn("testament to the power of human ingenuity", p1.text)
        self.assertEqual(p1.alignment, WD_ALIGN_PARAGRAPH.JUSTIFY)
        self.assertEqual(p1.runs[0].font.name, "Georgia")
        self.assertEqual(p1.runs[0].font.size, Pt(13))
        self.assertTrue(p1.runs[0].font.bold)
        self.assertEqual(p1.runs[0].font.color.rgb, RGBColor(10, 40, 90))

        # 3. Verify bullets preserved
        p_b1 = reloaded_doc.paragraphs[2]
        self.assertEqual(p_b1.style.name, "List Bullet")

        # 4. Verify table exists and cell content was humanized
        self.assertEqual(len(reloaded_doc.tables), 1)
        tbl = reloaded_doc.tables[0]
        self.assertEqual(tbl.rows[0].cells[0].text, "Category")
        self.assertEqual(tbl.rows[1].cells[0].text, "Machine Learning")
        cell_desc = tbl.rows[1].cells[1].text
        self.assertNotIn("weave a rich tapestry", cell_desc)

    def test_api_humanize_docx_endpoint(self):
        """Tests the POST /api/humanize/docx Flask endpoint and subsequent download."""
        source_stream = self._create_sample_styled_docx()
        data = {
            "file": (source_stream, "test_dissertation.docx"),
            "mode": "beast",
            "intensity": "0.85"
        }

        resp = self.client.post(
            "/api/humanize/docx",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(resp.status_code, 200)
        res_json = resp.get_json()

        self.assertTrue(res_json["success"])
        self.assertIn("download_token", res_json)
        self.assertIn("download_url", res_json)
        self.assertEqual(res_json["filename"], "humanized_test_dissertation.docx")
        self.assertLessEqual(res_json["metrics"]["ai_score_after"], 5.0)
        self.assertGreaterEqual(res_json["metrics"]["uniqueness_score"], 95.0)
        self.assertLessEqual(res_json["metrics"]["plagiarism_risk"], 5.0)

        # Test download endpoint
        token = res_json["download_token"]
        dl_resp = self.client.get(f"/api/download/docx/{token}")
        self.assertEqual(dl_resp.status_code, 200)
        self.assertIn("application/vnd.openxmlformats-officedocument.wordprocessingml.document", dl_resp.content_type)
        self.assertGreater(len(dl_resp.data), 1000)

        # Verify downloaded document can be loaded by docx
        dl_doc = docx.Document(io.BytesIO(dl_resp.data))
        self.assertGreater(len(dl_doc.paragraphs), 0)

    def test_api_humanize_docx_direct_stream(self):
        """Tests the direct streaming POST /api/humanize/docx/direct endpoint."""
        source_stream = self._create_sample_styled_docx()
        data = {
            "file": (source_stream, "academic_paper.docx"),
            "mode": "beast",
            "intensity": "0.85"
        }

        resp = self.client.post(
            "/api/humanize/docx/direct",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/vnd.openxmlformats-officedocument.wordprocessingml.document", resp.content_type)
        self.assertIn("humanized_academic_paper.docx", resp.headers.get("Content-Disposition", ""))

    def test_image_and_drawing_preservation(self):
        """Verifies that inline pictures, drawings, and figure captions are 100% preserved."""
        import base64
        png_bytes = base64.b64decode(b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
        doc = docx.Document()
        p = doc.add_paragraph("Pre-image text")
        r_img = p.add_run()
        r_img.add_picture(io.BytesIO(png_bytes), width=docx.shared.Inches(1.0))
        r_caption = p.add_run(" (Figure 1: Original caption description)")

        # Verify drawing exists before
        self.assertEqual(len(p._p.xpath(".//w:drawing | .//w:pict")), 1)

        DocumentParser.replace_paragraph_text_preserving_formatting(
            p,
            "Figure 1: Advanced deep learning architecture."
        )

        # Verify drawing is still intact after replacement!
        self.assertEqual(len(p._p.xpath(".//w:drawing | .//w:pict")), 1)
        self.assertEqual(p.text, "Figure 1: Advanced deep learning architecture.")


if __name__ == "__main__":
    unittest.main()
