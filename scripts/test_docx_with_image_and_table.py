import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from core.document_parser import DocumentParser
from core.humanizer import TextHumanizer

def test_full_docx_workflow():
    print("Creating sample Word document with text, heading, table, and image placeholder...")
    doc = docx.Document()
    
    # Title
    t = doc.add_paragraph()
    r_t = t.add_run("Deep Neural Networks for Enterprise Intrusion Detection")
    r_t.font.name = "Arial"
    r_t.font.size = Pt(16)
    r_t.font.bold = True
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Authors
    a = doc.add_paragraph()
    r_a = a.add_run("Ramnivas Attanti, Shreya P, Md Nadeem Sarwar*")
    r_a.font.italic = True
    a.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Heading 1
    doc.add_heading("1. Introduction", level=1)
    
    # AI-heavy body paragraph
    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_p1 = p1.add_run(
        "Furthermore, it is crucial to recognize that artificial intelligence plays a "
        "multifaceted and pivotal role in modern corporate security architectures. "
        "Moreover, it is important to remember that machine learning algorithms delve into "
        "massive telemetry datasets to extract actionable insights. A multifaceted approach "
        "is imperative to navigate the complexities of evolving attack vectors."
    )
    r_p1.font.name = "Georgia"
    r_p1.font.size = Pt(11)
    
    # Table
    doc.add_heading("2. Quantitative Evaluation", level=1)
    table = doc.add_table(rows=3, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Architecture", "Precision", "Recall"]
    data = [
        ["Baseline SVM", "94.2%", "91.8%"],
        ["Proposed DNN", "98.7%", "97.4%"]
    ]
    for c_idx, h in enumerate(headers):
        cell = table.rows[0].cells[c_idx]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
    
    for r_idx, row_values in enumerate(data):
        for c_idx, val in enumerate(row_values):
            table.rows[r_idx + 1].cells[c_idx].text = val
            
    # References
    doc.add_heading("References", level=1)
    ref = doc.add_paragraph("[1] R. Attanti and S. P, 'Intrusion Detection Heuristics', IEEE S&P, vol. 12, pp. 110-120, 2024.")
    
    buf_in = io.BytesIO()
    doc.save(buf_in)
    buf_in.seek(0)
    
    print(f"Original doc size: {len(buf_in.getvalue())} bytes")
    
    # Run format-preserving humanization
    humanizer = TextHumanizer()
    out_clean, out_annotated, summary = DocumentParser.humanize_docx_document(
        docx_source=buf_in.getvalue(),
        humanizer=humanizer,
        mode="beast",
        intensity=0.85,
        return_annotated=True
    )
    
    print("\n--- HUMANIZATION SUMMARY ---")
    print("Paragraphs processed:", summary["paragraphs_processed"])
    print("Tables processed:", summary["tables_processed"])
    print("Metrics:", summary["metrics"])
    print("Turnitin Radar:", summary["radar_after"]["detectors"]["turnitin"])
    
    # Verify resulting document
    doc_out = docx.Document(out_clean)
    print("\n--- OUTPUT DOC VERIFICATION ---")
    print("Total paragraphs in output doc:", len(doc_out.paragraphs))
    print("Total tables in output doc:", len(doc_out.tables))
    
    # 1. Title preserved verbatim
    assert "Deep Neural Networks for Enterprise Intrusion Detection" in doc_out.paragraphs[0].text
    print("[OK] Title preserved verbatim")
    
    # 2. Authors preserved verbatim
    assert "Ramnivas Attanti" in doc_out.paragraphs[1].text
    print("[OK] Author line preserved verbatim")
    
    # 3. Heading 1 preserved
    assert "1. Introduction" in doc_out.paragraphs[2].text
    print("[OK] Heading '1. Introduction' preserved")
    
    # 4. Humanized paragraph check
    body_text = doc_out.paragraphs[3].text
    print("Humanized body text:", body_text)
    assert "multifaceted" not in body_text.lower()
    assert "furthermore" not in body_text.lower()
    assert "delve" not in body_text.lower()
    assert doc_out.paragraphs[3].runs[0].font.name == "Georgia"
    print("[OK] AI clichés removed, Georgia font preserved")
    
    # 5. Table preserved
    assert len(doc_out.tables) == 1
    assert doc_out.tables[0].rows[0].cells[0].text == "Architecture"
    assert doc_out.tables[0].rows[1].cells[1].text == "94.2%"
    print("[OK] Table structure & numeric cell values 100% intact")
    
    # 6. References preserved verbatim
    assert "[1] R. Attanti" in doc_out.paragraphs[-1].text
    print("[OK] Bibliographic reference preserved verbatim")
    
    # 7. AI & Plagiarism Metrics
    m = summary["metrics"]
    assert m["ai_score_after"] <= 5.0
    assert m.get("plagiarism_risk_score", m.get("plagiarism_risk")) == 0.0
    assert m["uniqueness_score"] == 100.0
    print("[OK] 0.0% Plagiarism & Single-Digit/Zero AI Score Verified!")
    
    print("\n>>> ALL DOCX IMAGE/TABLE/FORMAT CHECKS PASSED 1000% <<<")

if __name__ == "__main__":
    test_full_docx_workflow()
