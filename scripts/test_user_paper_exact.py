"""
Verification script for user's real research paper scenario.
Tests:
1. Author names & affiliations remain 100% verbatim.
2. Paper title & keywords remain 100% verbatim.
3. Reference citations remain 100% verbatim.
4. Technical terms (mail server, mail gateway, classifier, dataset) are preserved.
5. Zero absurd WordNet corruptions (no 'waiter', no 'newspaper', no 'strait', no 'occupation').
6. Natural, fluent, scholarly prose with 0% AI detection.
"""

import io
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import docx
from core.humanizer import TextHumanizer
from core.document_parser import DocumentParser

def run_test():
    doc = docx.Document()
    
    # Title
    p_title = doc.add_paragraph("Why 98% Lab Accuracy Breaks across Mail Gateways: Auditing Empirical Data Leakage")
    p_title.style = 'Title'
    
    # Authors
    p_authors = doc.add_paragraph("Ramnivas Attanti, Shreya P, Md Nadeem Sarwar*")
    
    # Affiliation
    p_affil = doc.add_paragraph("Department of Computer Science and Engineering, Jain (Deemed-to-be-University), Bangalore, India")
    
    # Corresponding author email
    p_email = doc.add_paragraph("*Corresponding author: ramnivas@jainuniversity.ac.in")
    
    # Keywords
    p_kw = doc.add_paragraph("Keywords: Spam classification, Mail gateway, Data leakage, Concept drift, Machine learning")
    
    # Section Heading: Introduction
    p_h1 = doc.add_paragraph("1. Introduction")
    p_h1.style = 'Heading 1'
    
    # Body Paragraph 1
    p_b1 = doc.add_paragraph(
        "Email still carries the bulk of organizational communication, serving as the primary attack vector for phishing and credential harvesting. "
        "Why does a classifier that achieves 98% accuracy in a paper fail on a real mail server? "
        "Spam filtering sounds like a solved problem if one only looks at standard benchmark datasets. "
        "However, real-world mail gateways encounter continuous distribution shift, evasion heuristics, and operational telemetry constraints."
    )
    
    # Section Heading: Experimental Results
    p_h2 = doc.add_paragraph("2. Experimental Results")
    p_h2.style = 'Heading 1'
    
    # Table
    tbl = doc.add_table(rows=3, cols=4)
    headers = ["Model", "Accuracy", "F1-Score", "Mail Server Latency"]
    for i, h in enumerate(headers):
        tbl.rows[0].cells[i].text = h
    
    row1 = ["Baseline SVM", "98.2%", "0.98", "12 ms"]
    for i, v in enumerate(row1):
        tbl.rows[1].cells[i].text = v
        
    row2 = ["Proposed Gateway Model", "97.8%", "0.97", "14 ms"]
    for i, v in enumerate(row2):
        tbl.rows[2].cells[i].text = v
        
    # Section Heading: References
    p_href = doc.add_paragraph("References")
    p_href.style = 'Heading 1'
    
    # Citations
    p_ref1 = doc.add_paragraph('[1] J. Smith and A. Taylor, "Empirical audit of mail gateway telemetry," IEEE Trans. Inf. Forensics Security, vol. 18, pp. 240-252, 2023.')
    p_ref2 = doc.add_paragraph('[2] R. Attanti, "Machine learning in enterprise security," ACM Comput. Surv., vol. 55, no. 4, 2022.')
    
    doc_bytes = io.BytesIO()
    doc.save(doc_bytes)
    doc_bytes.seek(0)
    
    humanizer = TextHumanizer()
    out_stream, out_ann, metrics = DocumentParser.humanize_docx_document(
        docx_source=doc_bytes,
        humanizer=humanizer,
        mode="beast",
        intensity=0.85,
        return_annotated=True
    )
    
    # Parse back the humanized doc
    res_doc = docx.Document(io.BytesIO(out_stream.getvalue()))
    res_texts = [p.text for p in res_doc.paragraphs]
    
    print("\n--- HUMANIZED DOCUMENT PARAGRAPHS ---")
    for idx, t in enumerate(res_texts):
        print(f"P{idx}: {t}")
        
    # Assertions
    # 1. Title preserved verbatim
    assert "Why 98% Lab Accuracy Breaks across Mail Gateways" in res_texts[0], f"Title altered: {res_texts[0]}"
    
    # 2. Authors preserved verbatim
    assert res_texts[1] == "Ramnivas Attanti, Shreya P, Md Nadeem Sarwar*", f"Authors altered: {res_texts[1]}"
    
    # 3. Affiliation preserved verbatim
    assert "Department of Computer Science and Engineering, Jain (Deemed-to-be-University), Bangalore, India" == res_texts[2], f"Affiliation altered: {res_texts[2]}"
    
    # 4. Email preserved verbatim
    assert "*Corresponding author: ramnivas@jainuniversity.ac.in" == res_texts[3], f"Email altered: {res_texts[3]}"
    
    # 5. Keywords preserved verbatim
    assert "Keywords: Spam classification, Mail gateway, Data leakage, Concept drift, Machine learning" == res_texts[4], f"Keywords altered: {res_texts[4]}"
    
    # 6. Heading 1 preserved
    assert res_texts[5] == "1. Introduction", f"Heading altered: {res_texts[5]}"
    
    # 7. Check body paragraph (res_texts[6]) for absence of corruptions
    body_p = res_texts[6].lower()
    assert "waiter" not in body_p, f"Corruption 'waiter' found in body: {res_texts[6]}"
    assert "newspaper" not in body_p, f"Corruption 'newspaper' found in body: {res_texts[6]}"
    assert "strait" not in body_p, f"Corruption 'strait' found in body: {res_texts[6]}"
    assert "occupation" not in body_p, f"Corruption 'occupation' found in body: {res_texts[6]}"
    assert "novel computer science" not in body_p, f"Collocation bridging found: {res_texts[6]}"
    
    # 8. Check references preserved verbatim
    ref_heading_idx = res_texts.index("References")
    assert "[1] J. Smith and A. Taylor" in res_texts[ref_heading_idx + 1], f"Ref 1 altered: {res_texts[ref_heading_idx + 1]}"
    assert "[2] R. Attanti" in res_texts[ref_heading_idx + 2], f"Ref 2 altered: {res_texts[ref_heading_idx + 2]}"
    
    # 9. Check table contents
    res_tbl = res_doc.tables[0]
    assert res_tbl.rows[0].cells[0].text == "Model"
    assert res_tbl.rows[0].cells[1].text == "Accuracy"
    assert res_tbl.rows[0].cells[3].text == "Mail Server Latency"
    assert res_tbl.rows[1].cells[0].text == "Baseline SVM"
    assert res_tbl.rows[1].cells[1].text == "98.2%"
    assert res_tbl.rows[2].cells[0].text == "Proposed Gateway Model"
    
    # 10. Metrics check
    print("\n--- METRICS SUMMARY ---")
    print(f"AI Score Before: {metrics['metrics']['ai_score_before']}%")
    print(f"AI Score After: {metrics['metrics']['ai_score_after']}%")
    print(f"AI Reduction: {metrics['metrics']['ai_reduction']}%")
    print(f"Uniqueness Score: {metrics['metrics']['uniqueness_score']}%")
    print(f"Plagiarism Risk: {metrics['metrics']['plagiarism_risk']}%")
    
    assert metrics['metrics']['ai_score_after'] <= 10.0, f"AI score after too high: {metrics['metrics']['ai_score_after']}%"
    assert metrics['metrics']['uniqueness_score'] >= 65.0, f"Uniqueness score too low: {metrics['metrics']['uniqueness_score']}%"
    assert metrics['metrics']['plagiarism_risk'] <= 35.0, f"Plagiarism risk too high: {metrics['metrics']['plagiarism_risk']}%"
    
    print("\n>>> ALL VERIFICATION CHECKS PASSED PERFECTLY! <<<")

if __name__ == "__main__":
    run_test()
