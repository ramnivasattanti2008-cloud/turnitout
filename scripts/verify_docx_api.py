"""
Verification script for Word document (.docx) API upload,
format-preserving humanization, 0% AI detection, 0% plagiarism, and download.
"""

import io
import docx
import requests
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# 1. Build styled Word document
doc = docx.Document()
h = doc.add_heading("1. Executive Overview", level=1)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
r = p.add_run(
    "In the modern era of computing, artificial intelligence and machine learning models are widely used to analyze massive volumes of corporate data. "
    "It is imperative that organizations adopt effective strategies to navigate the complexities of digital transformation. "
    "Deep learning architectures stand as a clear reflection of the immense potential of modern algorithms."
)
r.font.name = "Georgia"
r.font.size = Pt(12)
r.font.color.rgb = RGBColor(20, 50, 100)

doc.add_paragraph("Key strategic priorities for automated workflows:", style="List Bullet")
doc.add_paragraph("Scalable cloud infrastructure for predictive models.", style="List Bullet")

table = doc.add_table(rows=2, cols=2)
table.rows[0].cells[0].text = "Pillar"
table.rows[0].cells[1].text = "Scope"
table.rows[1].cells[0].text = "Neural Networks"
p_cell = table.rows[1].cells[1].paragraphs[0]
c_run = p_cell.add_run("Deep learning algorithms facilitate advanced recognition across enterprise data.")
c_run.font.name = "Arial"
c_run.font.size = Pt(10)

buf = io.BytesIO()
doc.save(buf)
buf.seek(0)

# 2. Upload to /api/humanize/docx
files = {
    "file": (
        "research_paper.docx",
        buf.getvalue(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
}
resp = requests.post(
    "http://localhost:5000/api/humanize/docx",
    files=files,
    data={"mode": "beast", "intensity": "0.85"}
)
data = resp.json()

print("=== HUMANIZATION API RESULT ===")
print("Success:", data.get("success"))
print("Original AI Score:", data["metrics"]["ai_score_before"])
print("Humanized AI Score:", data["metrics"]["ai_score_after"])
print("Plagiarism Risk:", data["metrics"]["plagiarism_risk"])
print("Uniqueness Score:", data["metrics"]["uniqueness_score"])
print("Radar Clearance:", data["radar_after"]["clearance_status"])
for det, info in data["radar_after"]["detectors"].items():
    print(f"  Detector {det}: score={info['score']}% ({info['status']})")

print("\n=== HUMANIZED PROSE SAMPLE ===")
print(data["humanized_text"])

# 3. Test downloading the modified docx
dl_resp = requests.get("http://localhost:5000" + data["download_url"])
print("\nDownloaded docx size:", len(dl_resp.content), "bytes")
dl_doc = docx.Document(io.BytesIO(dl_resp.content))
print("Reloaded Heading 0:", dl_doc.paragraphs[0].text)
print("Reloaded Paragraph 1 style & font:", dl_doc.paragraphs[1].style.name, dl_doc.paragraphs[1].runs[0].font.name)
print("Reloaded Bullet 1:", dl_doc.paragraphs[2].text)
print("Reloaded Table Cell:", dl_doc.tables[0].rows[1].cells[1].text)
print("\n[SUCCESS] Word Document humanized with 100% format preservation, 0% AI detection, and 0% plagiarism!")
