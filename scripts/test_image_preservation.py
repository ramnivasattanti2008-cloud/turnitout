import io
import docx
import base64

# Minimal valid 1x1 transparent PNG in base64
TINY_PNG_B64 = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
png_bytes = base64.b64decode(TINY_PNG_B64)
img_buf = io.BytesIO(png_bytes)

doc = docx.Document()
p1 = doc.add_paragraph("Intro paragraph with some text.")
p_img = doc.add_paragraph()
r_img = p_img.add_run()
r_img.add_picture(img_buf, width=docx.shared.Inches(1.5))
r_txt = p_img.add_run(" (Figure 1: Architecture diagram)")

p_caption = doc.add_paragraph("Figure 1: Overview of our system architecture.")

print(f"Total paragraphs: {len(doc.paragraphs)}")
for idx, p in enumerate(doc.paragraphs):
    drawings = p._p.xpath(".//w:drawing | .//w:pict")
    print(f"P{idx}: text='{p.text}', drawings={len(drawings)}, runs={len(p.runs)}")
    for r_idx, r in enumerate(p.runs):
        r_drawings = r._r.xpath(".//w:drawing | .//w:pict")
        print(f"   Run {r_idx}: text='{r.text}', drawings={len(r_drawings)}")
