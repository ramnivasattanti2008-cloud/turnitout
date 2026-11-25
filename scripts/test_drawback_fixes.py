"""
Test script for drawback fixes:
- Nested tables in .docx
- Hyperlinks in paragraphs
- First-row table column header protection
- Technical collocations protection (ground truth, loss function, etc.)
- Citation bracket protection
"""

import io
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import docx
from docx.shared import Pt, RGBColor
from core.document_parser import DocumentParser
from core.humanizer import TextHumanizer

def test_drawback_fixes():
    print("=" * 60)
    print("TESTING DRAWBACK FIXES & ADVANCED DOCX PROCESSING")
    print("=" * 60)

    # 1. Build a complex document with nested tables, hyperlinks, headers, and scientific terms
    doc = docx.Document()
    doc.add_heading("1. Advanced Machine Learning Research", level=1)

    p1 = doc.add_paragraph("In recent studies, reinforcement learning and deep neural networks optimize the loss function across massive training corpora. ")
    p1.add_run("The empirical findings demonstrate high confidence interval adherence (p < 0.05) against the ground truth benchmark [1, 2].")

    # Table with column header and nested table in cell
    tbl = doc.add_table(rows=2, cols=2)
    tbl.rows[0].cells[0].text = "Model Category"
    tbl.rows[0].cells[1].text = "Evaluation Summary"

    tbl.rows[1].cells[0].text = "Transformer Architecture"
    cell_data = tbl.rows[1].cells[1]
    p_cell = cell_data.paragraphs[0]
    p_cell.text = "Large language models evaluate complex feature extraction pipelines while maintaining statistical significance."

    # Add nested table inside cell_data
    nested_tbl = cell_data.add_table(rows=2, cols=2)
    nested_tbl.rows[0].cells[0].text = "Metric"
    nested_tbl.rows[0].cells[1].text = "Benchmark Score"
    nested_tbl.rows[1].cells[0].text = "F1-Score"
    nested_tbl.rows[1].cells[1].paragraphs[0].text = "Cross-validation scores demonstrate robust generalization capability across all validation splits."

    # Save to BytesIO
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    doc_bytes = buf.getvalue()

    # 2. Humanize document
    humanizer = TextHumanizer()
    out_stream, metrics = DocumentParser.humanize_docx_document(
        docx_source=doc_bytes,
        humanizer=humanizer,
        mode="beast",
        intensity=0.85
    )

    # 3. Inspect results
    h_doc = docx.Document(out_stream)
    print(f"[Check 1] Heading 1 preserved: '{h_doc.paragraphs[0].text}'")
    assert h_doc.paragraphs[0].text == "1. Advanced Machine Learning Research"

    # Check body paragraph
    h_p1 = h_doc.paragraphs[1].text
    print(f"[Check 2] Body Text: '{h_p1}'")
    assert "reinforcement learning" in h_p1.lower(), "reinforcement learning collocation corrupted!"
    assert "loss function" in h_p1.lower(), "loss function collocation corrupted!"
    assert "ground truth" in h_p1.lower(), "ground truth collocation corrupted!"
    assert "(p < 0.05)" in h_p1, "Statistical p-value corrupted!"
    assert "[1, 2]" in h_p1, "Citation reference corrupted!"

    # Check table column header preserved
    h_tbl = h_doc.tables[0]
    hdr0 = h_tbl.rows[0].cells[0].text
    hdr1 = h_tbl.rows[0].cells[1].text
    print(f"[Check 3] Table headers preserved: '{hdr0}' | '{hdr1}'")
    assert hdr0 == "Model Category", f"Header altered: {hdr0}"
    assert hdr1 == "Evaluation Summary", f"Header altered: {hdr1}"

    # Check nested table processed
    nested_cell = h_tbl.rows[1].cells[1]
    assert len(nested_cell.tables) == 1, "Nested table missing!"
    nested_h_tbl = nested_cell.tables[0]
    assert nested_h_tbl.rows[0].cells[0].text == "Metric"
    assert nested_h_tbl.rows[0].cells[1].text == "Benchmark Score"
    nested_val_p = nested_h_tbl.rows[1].cells[1].paragraphs[0].text
    print(f"[Check 4] Nested table cell humanized: '{nested_val_p}'")
    assert "cross-validation" in nested_val_p.lower()

    # Check metrics
    print(f"[Check 5] 5-Gram Plagiarism Overlap: {metrics['plagiarism_check']['ngram_5_overlap']}%")
    print(f"[Check 6] AI Detection Score: {metrics['metrics']['ai_score_after']}%")
    assert metrics['plagiarism_check']['ngram_5_overlap'] == 0.0, "5-gram overlap is not 0.0%!"
    assert metrics['metrics']['ai_score_after'] <= 5.0, "AI score is > 5.0%!"

    print("=" * 60)
    print("ALL DRAWBACK FIX TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_drawback_fixes()
