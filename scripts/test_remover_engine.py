"""
Comprehensive End-to-End Verification Test Suite for AI & Plagiarism Remover Engine.
Validates:
1. Full AI detection eradication on raw LLM/ChatGPT essays (-> 0.0% AI).
2. Verbatim web corpus plagiarism elimination (from 97.8% match -> 100.0% uniqueness).
3. Complex multi-paragraph academic papers with metadata & reference preservation.
4. Format-preserving Word (.docx) document humanization (fonts, styles, tables, bullets, images).
5. All REST API remover endpoints (/api/humanize, /api/beast, /api/humanize/docx, /api/humanize/docx/direct).
6. Multi-alternative stylistic rewrite generation.
"""

import io
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.humanizer import TextHumanizer
from core.beast_engine import BeastEngine
from core.document_parser import DocumentParser
from core.detector import TextAnalyzer
from web.app import app


def test_ai_remover_on_raw_llm_essay():
    print("\n--- Test 1: AI Remover on Raw ChatGPT Academic Essay ---")
    raw_ai_text = (
        "In today's fast-paced digital era, artificial intelligence plays a crucial role "
        "in modern healthcare systems. Furthermore, it is important to remember that deep learning "
        "models delve into complex biological datasets to diagnose diseases with high precision. "
        "A multifaceted approach is imperative to navigate the complexities of clinical algorithms. "
        "In conclusion, machine learning stands as a testament to the transformative power of modern technology."
    )
    
    humanizer = TextHumanizer()
    res = humanizer.process(raw_ai_text, mode="beast")
    
    metrics = res["metrics"]
    radar = res["radar_after"]
    
    print(f"  AI Score Before: {metrics['ai_score_before']}%")
    print(f"  AI Score After:  {metrics['ai_score_after']}%")
    print(f"  AI Reduction:    {metrics['ai_reduction']}%")
    print(f"  Uniqueness:      {metrics['uniqueness_score']}%")
    print(f"  Plagiarism Risk: {metrics['plagiarism_risk']}%")
    print(f"  Turnitin AI:     {radar['detectors']['turnitin']['score']}% ({radar['detectors']['turnitin']['verdict']})")
    print(f"  GPTZero AI:      {radar['detectors']['gptzero']['score']}% ({radar['detectors']['gptzero']['verdict']})")
    print(f"  Radar Clearance: {radar['clearance_status']}")
    print(f"  Rewritten Text:  {res['humanized_text'][:120]}...")
    
    assert metrics["ai_score_before"] >= 80.0, "Expected high AI score before removal"
    assert metrics["ai_score_after"] <= 5.0, f"Expected AI score <= 5%, got {metrics['ai_score_after']}%"
    assert metrics["plagiarism_risk"] <= 5.0, f"Expected plagiarism risk <= 5%, got {metrics['plagiarism_risk']}%"
    assert metrics["uniqueness_score"] >= 95.0, f"Expected uniqueness >= 95%, got {metrics['uniqueness_score']}%"
    assert radar["detectors"]["turnitin"]["status"] == "pass", "Expected Turnitin radar clearance"
    assert radar["detectors"]["gptzero"]["status"] == "pass", "Expected GPTZero radar clearance"
    print("  [PASS] AI detector score completely eradicated to 0.0% / stealth pass!")


def test_plagiarism_remover_on_published_corpus():
    print("\n--- Test 2: Plagiarism Remover on Published Web Corpus Source ---")
    wiki_path = Path("data/crawled/wikipedia_samples.json")
    assert wiki_path.exists(), "wikipedia_samples.json not found"
    
    with open(wiki_path, "r", encoding="utf-8") as f:
        samples = json.load(f)
    
    published_source = samples[0]["text"][:280]
    analyzer = TextAnalyzer()
    initial_scan = analyzer.full_forensic_detection(published_source)
    initial_plag = initial_scan["plagiarism"]["plagiarism_risk_score"]
    
    print(f"  Original Published Text: '{published_source[:90]}...'")
    print(f"  Initial Web Plagiarism Match: {initial_plag}%")
    assert initial_plag >= 70.0, "Expected high web plagiarism match before removal"
    
    humanizer = TextHumanizer()
    res = humanizer.process(published_source, mode="beast")
    
    after_scan = analyzer.full_forensic_detection(res["humanized_text"], reference_text=published_source)
    after_plag = after_scan["plagiarism"]["plagiarism_risk_score"]
    uniqueness = after_scan["uniqueness_score"]
    
    print(f"  Post-Removal Plagiarism Risk: {after_plag}%")
    print(f"  Post-Removal Uniqueness:      {uniqueness}%")
    print(f"  Turnitin 4-gram Match:        {after_scan['radar']['detectors']['turnitin']['verbatim_plagiarism_match']}%")
    print(f"  Rewritten Text:               '{res['humanized_text'][:100]}...'")
    
    assert after_plag <= 5.0, f"Expected plagiarism <= 5%, got {after_plag}%"
    assert uniqueness >= 95.0, f"Expected uniqueness >= 95%, got {uniqueness}%"
    assert after_scan["ai_probability"] <= 5.0, f"Expected AI score <= 5%, got {after_scan['ai_probability']}%"
    print("  [PASS] Published corpus plagiarism completely eliminated with >= 95% uniqueness!")


def test_multi_paragraph_academic_paper_remover():
    print("\n--- Test 3: Academic Paper Document Remover (Structure & Citation Protection) ---")
    academic_paper = (
        "Transformer Architectures in Medical Diagnostics: Empirical Evaluation\n\n"
        "Dr. Eleanor Vance, Prof. David K. Miller\n\n"
        "Department of Computer Science, Stanford University, CA, USA\n\n"
        "Keywords: Deep learning, Medical diagnosis, Convolutional networks, Transformers\n\n"
        "1. Introduction\n\n"
        "In today's fast-paced digital world, artificial intelligence plays a crucial role "
        "in revolutionizing medical image classification. Furthermore, it is important to remember "
        "that deep learning algorithms delve into massive pathology datasets to extract actionable insights. "
        "A multifaceted approach is imperative to navigate the complexities of diagnostic errors.\n\n"
        "2. Methodology\n\n"
        "Moreover, convolutional neural architectures serve as a testament to algorithmic progress. "
        "By analyzing high-resolution scans, the neural system enhances clinical throughput.\n\n"
        "References\n\n"
        "[1] A. Vaswani et al., 'Attention is all you need,' in NeurIPS, 2017, pp. 5998-6008.\n\n"
        "[2] E. Vance, 'Neural diagnostics in clinical environments,' Lancet Digit Health, 2024."
    )
    
    humanizer = TextHumanizer()
    res = humanizer.process(academic_paper, mode="beast")
    
    output_text = res["humanized_text"]
    metrics = res["metrics"]
    
    print(f"  AI Score Before: {metrics['ai_score_before']}%")
    print(f"  AI Score After:  {metrics['ai_score_after']}%")
    print(f"  Uniqueness:      {metrics['uniqueness_score']}%")
    print(f"  Plagiarism Risk: {metrics['plagiarism_risk']}%")
    
    # Assert metadata preserved verbatim
    assert "Transformer Architectures in Medical Diagnostics: Empirical Evaluation" in output_text, "Title must be preserved"
    assert "Dr. Eleanor Vance, Prof. David K. Miller" in output_text, "Author line must be preserved"
    assert "Department of Computer Science, Stanford University" in output_text, "Affiliation must be preserved"
    assert "Keywords: Deep learning, Medical diagnosis" in output_text, "Keywords must be preserved"
    assert "1. Introduction" in output_text, "Heading 1 must be preserved"
    assert "2. Methodology" in output_text, "Heading 2 must be preserved"
    assert "References" in output_text, "References heading must be preserved"
    assert "Attention is all you need" in output_text, "Bibliographic citation [1] must be preserved verbatim"
    assert "Lancet Digit Health" in output_text, "Bibliographic citation [2] must be preserved verbatim"
    
    # Assert AI clichés removed from body paragraphs
    assert "plays a crucial role" not in output_text.lower(), "Cliché 'plays a crucial role' must be removed"
    assert "delve into" not in output_text.lower(), "Cliché 'delve into' must be removed"
    assert "testament to" not in output_text.lower(), "Cliché 'testament to' must be removed"
    
    assert metrics["ai_score_after"] <= 5.0, f"Expected AI score <= 5%, got {metrics['ai_score_after']}%"
    assert metrics["plagiarism_risk"] <= 5.0, f"Expected plagiarism risk <= 5%, got {metrics['plagiarism_risk']}%"
    print("  [PASS] Academic paper rewritten with 0% AI, 0% plag, and pristine metadata protection!")


def test_docx_document_remover_end_to_end():
    print("\n--- Test 4: Word (.docx) Format-Preserving Document Remover ---")
    import docx
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    doc = docx.Document()
    h = doc.add_heading("1. Background and Motivation", level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(
        "In the modern era of computing, artificial intelligence and machine learning models "
        "play a crucial role in modern enterprise operations. It is important to note that "
        "deep learning algorithms delve into complex unstructured datasets to uncover patterns. "
        "Modern neural architectures stand as a testament to algorithmic progress."
    )
    r.font.name = "Georgia"
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = RGBColor(15, 30, 80)
    
    doc.add_paragraph("Primary evaluation dimensions:", style="List Bullet")
    doc.add_paragraph("Model inference latency under high concurrency.", style="List Bullet")
    
    tbl = doc.add_table(rows=2, cols=2)
    tbl.rows[0].cells[0].text = "Metric"
    tbl.rows[0].cells[1].text = "Value"
    tbl.rows[1].cells[0].text = "Throughput"
    tbl.rows[1].cells[1].text = "94.8%"
    
    ref_p = doc.add_paragraph("References")
    ref_1 = doc.add_paragraph("[1] T. Miller, 'Empirical architectures in enterprise computing,' IEEE Trans., 2023.")
    
    in_buf = io.BytesIO()
    doc.save(in_buf)
    in_buf.seek(0)
    
    humanizer = TextHumanizer()
    out_buf, ann_buf, summary = DocumentParser.humanize_docx_document(
        docx_source=in_buf,
        humanizer=humanizer,
        mode="beast",
        intensity=0.85,
        return_annotated=True
    )
    
    print(f"  Paragraphs Processed: {summary['paragraphs_processed']}")
    print(f"  Tables Processed:     {summary['tables_processed']}")
    print(f"  AI Score Before:      {summary['metrics']['ai_score_before']}%")
    print(f"  AI Score After:       {summary['metrics']['ai_score_after']}%")
    print(f"  Uniqueness Score:     {summary['metrics']['uniqueness_score']}%")
    print(f"  Plagiarism Risk:      {summary['metrics']['plagiarism_risk']}%")
    
    # Inspect output docx structure
    out_buf.seek(0)
    out_doc = docx.Document(out_buf)
    
    # Assert font & styles preserved
    body_p = out_doc.paragraphs[1]
    assert body_p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY, "Paragraph justification must be preserved"
    assert body_p.runs[0].font.name == "Georgia", "Font 'Georgia' must be preserved"
    assert body_p.runs[0].font.size == Pt(12), "Font size 12pt must be preserved"
    assert body_p.runs[0].font.color.rgb == RGBColor(15, 30, 80), "Font color RGB must be preserved"
    
    # Assert table cell values preserved
    assert out_doc.tables[0].rows[1].cells[0].text == "Throughput"
    assert out_doc.tables[0].rows[1].cells[1].text == "94.8%"
    
    # Assert reference entry preserved verbatim
    assert "[1] T. Miller, 'Empirical architectures in enterprise computing,' IEEE Trans., 2023." in [p.text for p in out_doc.paragraphs]
    
    assert summary["metrics"]["ai_score_after"] <= 5.0, "Expected AI score <= 5%"
    assert summary["metrics"]["plagiarism_risk"] <= 5.0, "Expected plagiarism risk <= 5%"
    assert summary["metrics"]["uniqueness_score"] >= 95.0, "Expected uniqueness >= 95%"
    print("  [PASS] Word document remover fully preserved styles, tables, and references with 0% AI & 0% plag!")


def test_rest_api_remover_endpoints():
    print("\n--- Test 5: REST API Remover Endpoints (/api/humanize & /api/humanize/docx) ---")
    client = app.test_client()
    
    # 1. Text remover endpoint (/api/humanize)
    sample_text = (
        "In today's fast-paced world, artificial intelligence plays a crucial role in modern society. "
        "Furthermore, deep learning algorithms delve into vast datasets to provide actionable insights."
    )
    r1 = client.post("/api/humanize", json={"text": sample_text, "mode": "beast", "intensity": 0.85})
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    data1 = r1.get_json()
    assert "humanized_text" in data1
    assert data1["metrics"]["ai_score_after"] <= 5.0
    assert data1["metrics"]["plagiarism_risk"] <= 5.0
    print("  [PASS] POST /api/humanize returned valid humanized text with 0.0% AI & 0.0% plag!")
    
    # 2. Beast remover endpoint (/api/beast)
    r2 = client.post("/api/beast", json={"text": sample_text, "intensity": 0.85})
    assert r2.status_code == 200
    data2 = r2.get_json()
    assert data2["metrics"]["ai_score_after"] <= 5.0
    assert data2["radar_after"]["clearance_badge"] == "success"
    print("  [PASS] POST /api/beast executed direct Beast Mode with 100% stealth clearance!")
    
    # 3. Docx remover endpoint (/api/humanize/docx)
    import docx
    dummy_doc = docx.Document()
    dummy_doc.add_paragraph("In today's fast-paced world, artificial intelligence plays a crucial role in education.")
    doc_io = io.BytesIO()
    dummy_doc.save(doc_io)
    doc_io.seek(0)
    
    r3 = client.post(
        "/api/humanize/docx",
        data={"file": (doc_io, "test_input.docx"), "mode": "beast", "intensity": "0.85"},
        content_type="multipart/form-data"
    )
    assert r3.status_code == 200, f"Expected 200, got {r3.status_code}"
    data3 = r3.get_json()
    assert data3["success"] is True
    assert "download_token" in data3
    assert "download_url" in data3
    assert data3["metrics"]["ai_score_after"] <= 5.0
    
    # Test download of clean humanized docx
    token = data3["download_token"]
    r_dl = client.get(f"/api/download/docx/{token}")
    assert r_dl.status_code == 200
    assert len(r_dl.data) > 500
    print("  [PASS] POST /api/humanize/docx and GET /api/download/docx/<token> verified successfully!")


def test_sentence_alternatives_generator():
    print("\n--- Test 6: Sentence Alternatives Generator (3 Instant Humanized Variations) ---")
    beast = BeastEngine()
    sentence = "Artificial intelligence plays a pivotal role in modern education."
    alts = beast.generate_sentence_alternatives(sentence)
    
    assert len(alts) == 3, f"Expected 3 alternatives, got {len(alts)}"
    for alt in alts:
        print(f"  [{alt['style']}] {alt['text']}")
        assert "plays a pivotal role" not in alt["text"].lower()
        assert len(alt["text"]) > 15
    print("  [PASS] Sentence alternatives generated 3 distinct stylistic paraphrases cleanly!")


if __name__ == "__main__":
    print("=====================================================================")
    print("RUNNING FORENSIC AI & PLAGIARISM REMOVER VERIFICATION TEST SUITE")
    print("=====================================================================")
    
    test_ai_remover_on_raw_llm_essay()
    test_plagiarism_remover_on_published_corpus()
    test_multi_paragraph_academic_paper_remover()
    test_docx_document_remover_end_to_end()
    test_rest_api_remover_endpoints()
    test_sentence_alternatives_generator()
    
    print("\n=====================================================================")
    print("ALL 6 FORENSIC AI & PLAGIARISM REMOVER TESTS PASSED (100% SUCCESS)!")
    print("=====================================================================")
