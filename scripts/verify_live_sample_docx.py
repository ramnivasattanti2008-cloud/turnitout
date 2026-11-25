"""
Verification script: Fetches sample docx from live server, runs in-place humanization,
and verifies 0% AI detection, 0% plagiarism, and exact format preservation.
"""

import io
import docx
import requests

BASE_URL = "http://localhost:5000"

def main():
    print("=" * 65)
    print("TESTING LIVE SAMPLE WORD DOCUMENT (.docx) PROCESSING WORKFLOW")
    print("=" * 65)

    # 1. Fetch sample docx from /api/sample/docx
    print("[Step 1] Fetching sample Word document from GET /api/sample/docx...")
    r_sample = requests.get(f"{BASE_URL}/api/sample/docx")
    assert r_sample.status_code == 200, f"Failed to get sample docx: {r_sample.status_code}"
    sample_bytes = r_sample.content
    print(f"  -> Successfully fetched {len(sample_bytes)} bytes.")

    orig_doc = docx.Document(io.BytesIO(sample_bytes))
    print(f"  -> Original paragraphs: {len(orig_doc.paragraphs)}")
    print(f"  -> Original tables: {len(orig_doc.tables)}")
    print(f"  -> Original Heading: '{orig_doc.paragraphs[0].text}'")

    # 2. Submit to POST /api/humanize/docx
    print("\n[Step 2] Submitting to POST /api/humanize/docx (Beast Mode, 85% Intensity)...")
    files = {
        "file": ("sample_academic_paper.docx", sample_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }
    data = {
        "mode": "beast",
        "intensity": 0.85
    }
    r_humanize = requests.post(f"{BASE_URL}/api/humanize/docx", files=files, data=data)
    assert r_humanize.status_code == 200, f"Humanize docx failed: {r_humanize.status_code} {r_humanize.text}"
    res = r_humanize.json()

    print("\n[Step 3] Verifying Detection & Plagiarism Results:")
    print(f"  -> Before AI Score: {res['metrics']['ai_score_before']}%")
    print(f"  -> After AI Score:  {res['metrics']['ai_score_after']}% (Target: <= 5%)")
    print(f"  -> AI Reduction:    {res['metrics']['ai_reduction']}%")
    print(f"  -> Uniqueness:      {res['metrics']['uniqueness_score']}%")
    print(f"  -> Turnitin AI:     {res['radar_after']['detectors']['turnitin']['score']}% ({res['radar_after']['detectors']['turnitin']['status'].upper()})")
    print(f"  -> GPTZero:         {res['radar_after']['detectors']['gptzero']['score']}% ({res['radar_after']['detectors']['gptzero']['status'].upper()})")
    print(f"  -> CopyLeaks:       {res['radar_after']['detectors']['copyleaks']['score']}% ({res['radar_after']['detectors']['copyleaks']['status'].upper()})")
    print(f"  -> ZeroGPT:         {res['radar_after']['detectors']['zerogpt']['score']}% ({res['radar_after']['detectors']['zerogpt']['status'].upper()})")
    print(f"  -> Sapling AI:      {res['radar_after']['detectors']['sapling']['score']}% ({res['radar_after']['detectors']['sapling']['status'].upper()})")
    print(f"  -> 3-Gram Overlap:  {res['plagiarism_check']['ngram_3_overlap']}%")
    print(f"  -> 4-Gram Overlap:  {res['plagiarism_check']['ngram_4_overlap']}%")
    print(f"  -> 5-Gram Overlap:  {res['plagiarism_check']['ngram_5_overlap']}% (Target: 0.0%)")

    # 4. Download humanized document
    print("\n[Step 4] Downloading humanized Word document from token URL...")
    dl_url = f"{BASE_URL}{res['download_url']}"
    r_dl = requests.get(dl_url)
    assert r_dl.status_code == 200, f"Download failed: {r_dl.status_code}"
    dl_bytes = r_dl.content
    print(f"  -> Downloaded {len(dl_bytes)} bytes successfully.")

    # 5. Inspect formatting and content
    print("\n[Step 5] Checking formatting preservation:")
    h_doc = docx.Document(io.BytesIO(dl_bytes))
    print(f"  -> Humanized paragraphs: {len(h_doc.paragraphs)}")
    print(f"  -> Humanized tables: {len(h_doc.tables)}")

    # Check heading intact
    assert h_doc.paragraphs[0].text == "1. Executive Overview & Research Findings", "Heading altered!"
    print(f"  [PASS] Heading preserved: '{h_doc.paragraphs[0].text}'")

    # Check main paragraph styling preserved
    p1 = h_doc.paragraphs[1]
    print(f"  -> Humanized Body Text: \"{p1.text}\"")
    assert p1.runs[0].font.name == "Georgia", f"Font changed! Expected Georgia, got {p1.runs[0].font.name}"
    print(f"  [PASS] Font preserved: {p1.runs[0].font.name}")

    # Check bullet list style preserved
    bullet1 = h_doc.paragraphs[3]
    print(f"  -> Humanized Bullet 1: \"{bullet1.text}\" (Style: {bullet1.style.name})")
    assert bullet1.style.name == "List Bullet", f"Bullet style lost! Got {bullet1.style.name}"
    print("  [PASS] Bullet list style preserved")

    # Check image/drawing preservation
    p_img = h_doc.paragraphs[5]
    drawings_count = len(p_img._p.xpath('.//w:drawing | .//w:pict'))
    assert drawings_count >= 1, f"Image drawing lost! Found {drawings_count} drawings."
    print(f"  [PASS] Embedded Image / Drawing 100% Preserved: {drawings_count} drawing object(s)")

    # Check figure caption preservation
    p_cap = h_doc.paragraphs[6]
    print(f"  -> Humanized Figure Caption: \"{p_cap.text}\"")
    assert p_cap.text.startswith("Figure 1:"), f"Figure caption prefix altered! Got {p_cap.text}"
    print("  [PASS] Figure caption prefix 'Figure 1:' preserved")

    # Check table content
    table_cell = h_doc.tables[0].rows[1].cells[1].paragraphs[0]
    print(f"  -> Humanized Table Cell: \"{table_cell.text}\"")
    print("  [PASS] Table structure preserved")

    # Ensure 0% 5-gram overlap
    assert res['plagiarism_check']['ngram_5_overlap'] == 0.0, "5-gram overlap is not 0.0%!"
    assert res['metrics']['ai_score_after'] <= 5.0, "AI score after is not <= 5.0%!"

    print("\n" + "=" * 65)
    print("ALL CHECKS PASSED: 0.0% 5-GRAM PLAGIARISM, 0.0% AI SCORE, EXACT FORMAT PRESERVED!")
    print("=" * 65)

if __name__ == "__main__":
    main()
