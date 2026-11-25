"""
Flask Web Application & REST API for TextHumanizer Pro.
Provides real-time paragraph humanization, AI detection diagnostics,
plagiarism overlap analysis, multi-format file uploads (.docx, .pdf, .txt, .md),
Word export, and model calibration endpoints.
"""

import io
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict
import uuid
from flask import Flask, jsonify, render_template, request, send_file, Response, redirect

from config import (
    HOST, PORT, TONE_MODIFIERS,
    GOOGLE_ADSENSE_ID, GOOGLE_ADSENSE_SLOT_TOP,
    GOOGLE_ADSENSE_SLOT_MIDDLE, GOOGLE_ADSENSE_SLOT_BOTTOM,
    GOOGLE_TAG_ID, MONETIZATION_ENABLED, ADS_TXT_CONTENT
)
from core.citation_generator import CitationEngine
from core.code_humanizer import CodeCommentHumanizer
from core.detector import TextAnalyzer
from core.document_parser import DocumentParser
from core.humanizer import TextHumanizer
from core.monetization import monetization_manager
from core.watermark_scrubber import WatermarkScrubber
from model.trainer import ModelTrainer

BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
    static_url_path="/static"
)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024
humanizer = TextHumanizer()
analyzer = TextAnalyzer()
trainer = ModelTrainer()
code_humanizer = CodeCommentHumanizer()
citation_engine = CitationEngine()
scrubber = WatermarkScrubber()

DOCX_DOWNLOAD_STORE: Dict[str, Dict[str, Any]] = {}
DOCX_STORE_LOCK = threading.Lock()


def clean_old_docx_downloads():
    """Purges expired docx buffers older than 30 minutes."""
    now = time.time()
    with DOCX_STORE_LOCK:
        expired = [token for token, val in DOCX_DOWNLOAD_STORE.items() if now - val.get("created_at", now) > 1800]
        for token in expired:
            DOCX_DOWNLOAD_STORE.pop(token, None)



SAMPLE_PRESETS = {
    "academic": (
        "In today's fast-paced academic landscape, artificial intelligence plays a crucial role "
        "in higher education pedagogy. Furthermore, it is important to remember that deep learning "
        "algorithms delve into massive datasets to extract valuable insights. A multifaceted approach "
        "is imperative to navigate the complexities of algorithmic bias. In conclusion, machine learning "
        "stands as a testament to the power of human ingenuity."
    ),
    "essay": (
        "It goes without saying that literature serves as a beacon of hope in times of societal crisis. "
        "Moreover, great writers weave a rich tapestry of human emotions that resonates deeply with readers. "
        "By delving into the nuances of classic novels, one can foster a deeper sense of empathy. "
        "To sum up, classic literature plays a pivotal role in shaping our shared moral consciousness."
    ),
    "business": (
        "In today's competitive corporate world, digital transformation is a game-changer for enterprise efficiency. "
        "Furthermore, harnessing the power of cloud architecture allows organizations to seamlessly integrate "
        "their workflows. It is crucial to note that leadership must foster a culture of agile innovation. "
        "In summary, modern cloud solutions pave the way for sustainable market dominance."
    )
}


@app.route("/")
def index():
    """Renders main dashboard interface with active ad campaigns & monetization."""
    monetization_manager.record_impression(count=3)
    top_camps = monetization_manager.get_campaigns("top")
    mid_camps = monetization_manager.get_campaigns("middle")
    sticky_camps = monetization_manager.get_campaigns("sticky")
    stats = monetization_manager.get_stats()
    return render_template(
        "index.html",
        tones=TONE_MODIFIERS,
        google_adsense_id=GOOGLE_ADSENSE_ID,
        google_adsense_slot_top=GOOGLE_ADSENSE_SLOT_TOP,
        google_adsense_slot_middle=GOOGLE_ADSENSE_SLOT_MIDDLE,
        google_adsense_slot_bottom=GOOGLE_ADSENSE_SLOT_BOTTOM,
        google_tag_id=GOOGLE_TAG_ID,
        monetization_enabled=MONETIZATION_ENABLED,
        top_campaigns=top_camps,
        middle_campaigns=mid_camps,
        sticky_campaigns=sticky_camps,
        monetization_stats=stats
    )


@app.route("/sitemap.xml")
def sitemap_xml():
    """Generates SEO-boosting XML sitemap for search engines."""
    base = request.host_url.rstrip("/")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base}/privacy</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{base}/terms</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>"""
    return Response(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots_txt():
    """Guides search crawlers to index Turnitout pages and sitemap."""
    base = request.host_url.rstrip("/")
    txt = f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"
    return Response(txt, mimetype="text/plain")


@app.route("/api/referrals/claim", methods=["POST"])
def claim_referral():
    """Tracks viral referral invite link and credits user acquisition value."""
    payload = request.get_json(silent=True) or {}
    ref_code = payload.get("ref_code", "student_invite")
    res = monetization_manager.record_referral(ref_code)
    return jsonify({
        "status": "success",
        "message": "Referral recorded! 1 Month Pro bonus credited to your account.",
        "referral": res,
        "stats": monetization_manager.get_stats()
    })


@app.route("/ads.txt")
def ads_txt():
    """Serves Google AdSense publisher verification file."""
    return Response(ADS_TXT_CONTENT, mimetype="text/plain")


@app.route("/privacy")
@app.route("/privacy-policy")
def privacy_policy():
    """Renders legally compliant privacy policy required by Google AdSense."""
    return render_template("privacy.html", google_adsense_id=GOOGLE_ADSENSE_ID)


@app.route("/terms")
@app.route("/terms-of-service")
def terms_of_service():
    """Renders Terms of Service."""
    return render_template("terms.html")


@app.route("/api/ads/click", methods=["GET", "POST"])
def track_ad_click():
    """Tracks ad click, updates revenue, and redirects/returns target URL."""
    ad_id = request.args.get("ad_id") or (request.get_json(silent=True) or {}).get("ad_id", "")
    target_url = monetization_manager.record_click(ad_id)
    if request.method == "POST" or request.headers.get("Accept") == "application/json":
        return jsonify({
            "status": "success",
            "ad_id": ad_id,
            "target_url": target_url,
            "stats": monetization_manager.get_stats()
        })
    return redirect(target_url or "/")


@app.route("/api/monetization/stats", methods=["GET"])
def get_monetization_stats():
    """Returns real-time earnings, impressions, clicks, and eCPM."""
    return jsonify(monetization_manager.get_stats())


@app.route("/api/pro/checkout", methods=["POST"])
def process_pro_checkout():
    """Processes simulated Pro/Team subscription purchase and updates recurring revenue."""
    payload = request.get_json(silent=True) or {}
    plan = payload.get("plan", "pro")
    monetization_manager.record_subscription_sale(plan)
    return jsonify({
        "status": "success",
        "plan": plan,
        "message": f"Successfully upgraded to TextHumanizer Pro ({plan.upper()})! Unlimited 0% AI generation unlocked.",
        "stats": monetization_manager.get_stats()
    })


@app.route("/api/monetization/status", methods=["GET"])
def get_monetization_status():
    """Returns current Google Ads and monetization readiness status."""
    return jsonify({
        "monetization_enabled": MONETIZATION_ENABLED,
        "google_adsense_connected": bool(GOOGLE_ADSENSE_ID),
        "google_adsense_id": GOOGLE_ADSENSE_ID if GOOGLE_ADSENSE_ID else None,
        "google_tag_connected": bool(GOOGLE_TAG_ID),
        "google_tag_id": GOOGLE_TAG_ID if GOOGLE_TAG_ID else None,
        "ads_txt_ready": True,
        "privacy_policy_ready": True,
        "terms_ready": True,
        "stats": monetization_manager.get_stats(),
        "ad_slots": {
            "top": bool(GOOGLE_ADSENSE_SLOT_TOP),
            "middle": bool(GOOGLE_ADSENSE_SLOT_MIDDLE),
            "bottom": bool(GOOGLE_ADSENSE_SLOT_BOTTOM)
        }
    })


@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Returns sample text presets for instant demonstration."""
    return jsonify(SAMPLE_PRESETS)


@app.route("/api/sample/docx", methods=["GET"])
def get_sample_docx():
    """Generates and returns a rich styled sample Word (.docx) document for testing."""
    import docx
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = docx.Document()
    doc.add_heading("1. Executive Overview & Research Findings", level=1)

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
    doc.add_paragraph("Rigorous validation benchmarks across enterprise datasets.", style="List Bullet")

    # Embedded architecture diagram / figure
    import base64
    from docx.shared import Inches
    png_bytes = base64.b64decode(b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_img = p_img.add_run()
    r_img.add_picture(io.BytesIO(png_bytes), width=Inches(3.0))

    p_cap = doc.add_paragraph("Figure 1: Conceptual architecture of neural adversarial optimization framework.")
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Pillar"
    table.rows[0].cells[1].text = "Scope"
    table.rows[1].cells[0].text = "Neural Networks"
    p_cell = table.rows[1].cells[1].paragraphs[0]
    c_run = p_cell.add_run("Deep learning algorithms facilitate advanced pattern recognition across enterprise data.")
    c_run.font.name = "Arial"
    c_run.font.size = Pt(10)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name="sample_academic_paper.docx"
    )


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Parses uploaded file (.txt, .md, .docx, .pdf) and returns extracted plain text."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400
    try:
        content = file.read()
        extracted = DocumentParser.extract_text(content, filename=file.filename)
        return jsonify({
            "filename": file.filename,
            "text": extracted,
            "word_count": len(extracted.split())
        })
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to parse file: {str(e)}"}), 500


@app.route("/api/export/docx", methods=["POST"])
def export_docx():
    """Exports humanized text into a downloadable Word (.docx) document."""
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided for export."}), 400
    try:
        docx_io = DocumentParser.export_to_docx_bytes(text)
        return send_file(
            docx_io,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,
            download_name="humanized_document.docx"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to export docx: {str(e)}"}), 500


@app.route("/api/humanize/docx", methods=["POST"])
def humanize_docx():
    """
    In-place, format-preserving Word document humanization.
    Uploads a .docx file, removes all AI detection signatures and plagiarism,
    preserves exact styles, headings, fonts, colors, bullet points, tables, and alignments,
    and returns full diagnostics + download URL for the resulting .docx file.
    """
    clean_old_docx_downloads()

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Please upload a .docx document."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    if not file.filename.lower().endswith(".docx"):
        return jsonify({"error": "Invalid format. Only .docx files are supported for format-preserving humanization."}), 400

    mode = request.form.get("mode", "beast")
    if not mode:
        mode = "beast"
    intensity_raw = request.form.get("intensity")
    if intensity_raw is not None:
        try:
            intensity = min(1.0, max(0.20, float(intensity_raw)))
        except (ValueError, TypeError):
            intensity = 0.75
    else:
        intensity = 0.75
    preserve_keywords_raw = request.form.get("preserve_keywords", "")
    if preserve_keywords_raw:
        preserve_keywords = [k.strip() for k in preserve_keywords_raw.split(",") if k.strip()]
    else:
        preserve_keywords = []

    try:
        content = file.read()
        out_stream, annotated_stream, metrics_summary = DocumentParser.humanize_docx_document(
            docx_source=content,
            humanizer=humanizer,
            mode=mode,
            intensity=intensity,
            preserve_keywords=preserve_keywords,
            annotate_changes=False,
            return_annotated=True
        )

        token = str(uuid.uuid4())
        annotated_token = str(uuid.uuid4())
        original_name = Path(file.filename).name
        clean_stem = Path(file.filename).stem
        download_name = f"humanized_{clean_stem}.docx"
        annotated_download_name = f"annotated_diff_{clean_stem}.docx"

        with DOCX_STORE_LOCK:
            DOCX_DOWNLOAD_STORE[token] = {
                "data": out_stream.getvalue(),
                "filename": download_name,
                "created_at": time.time()
            }
            DOCX_DOWNLOAD_STORE[annotated_token] = {
                "data": annotated_stream.getvalue(),
                "filename": annotated_download_name,
                "created_at": time.time()
            }

        return jsonify({
            "success": True,
            "filename": download_name,
            "original_filename": original_name,
            "download_token": token,
            "download_url": f"/api/download/docx/{token}",
            "annotated_download_token": annotated_token,
            "annotated_filename": annotated_download_name,
            "annotated_download_url": f"/api/download/docx/{annotated_token}",
            "paragraphs_processed": metrics_summary.get("paragraphs_processed", 0),
            "tables_processed": metrics_summary.get("tables_processed", 0),
            "original_word_count": metrics_summary.get("original_word_count", 0),
            "humanized_word_count": metrics_summary.get("humanized_word_count", 0),
            "metrics": metrics_summary.get("metrics", {}),
            "before_analysis": metrics_summary.get("before_analysis", {}),
            "after_analysis": metrics_summary.get("after_analysis", {}),
            "radar_before": metrics_summary.get("radar_before", {}),
            "radar_after": metrics_summary.get("radar_after", {}),
            "plagiarism_check": metrics_summary.get("plagiarism_check", {}),
            "sentence_analysis_before": metrics_summary.get("sentence_analysis_before", {}),
            "sentence_analysis_after": metrics_summary.get("sentence_analysis_after", {}),
            "original_text": metrics_summary.get("original_text", ""),
            "humanized_text": metrics_summary.get("humanized_text", "")
        })
    except Exception as e:
        return jsonify({"error": f"Failed to humanize Word document: {str(e)}"}), 500


@app.route("/api/download/docx/<token>", methods=["GET"])
def download_docx(token: str):
    """Downloads previously humanized Word document by session token."""
    clean_old_docx_downloads()
    with DOCX_STORE_LOCK:
        record = DOCX_DOWNLOAD_STORE.get(token)

    if not record:
        return jsonify({"error": "Download token expired or not found. Please re-run humanization."}), 404

    docx_io = io.BytesIO(record["data"])
    docx_io.seek(0)
    return send_file(
        docx_io,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=record["filename"]
    )


@app.route("/api/humanize/docx/direct", methods=["POST"])
def humanize_docx_direct():
    """
    Direct streaming endpoint for programmatic or curl workflows.
    Accepts .docx upload and directly returns the format-preserved humanized .docx file.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Please upload a .docx document."}), 400

    file = request.files["file"]
    if not file or not file.filename.lower().endswith(".docx"):
        return jsonify({"error": "Invalid format. Expected .docx file."}), 400

    mode = request.form.get("mode", "beast")
    if not mode:
        mode = "beast"
    intensity_raw = request.form.get("intensity")
    if intensity_raw is not None:
        try:
            intensity = min(1.0, max(0.20, float(intensity_raw)))
        except (ValueError, TypeError):
            intensity = 0.75
    else:
        intensity = 0.75
    try:
        content = file.read()
        out_stream, _ = DocumentParser.humanize_docx_document(
            docx_source=content,
            humanizer=humanizer,
            mode=mode,
            intensity=intensity
        )
        clean_stem = Path(file.filename).stem
        return send_file(
            out_stream,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,
            download_name=f"humanized_{clean_stem}.docx"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to humanize docx: {str(e)}"}), 500


@app.route("/api/humanize", methods=["POST"])
def humanize_text():
    """
    Transforms text to remove AI signatures and plagiarism patterns.
    Accepts JSON: { text, tone, intensity, preserve_keywords }
    """
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Please provide input text to humanize."}), 400

    tone = data.get("tone", "academic")
    mode = data.get("mode", "beast")
    if not mode:
        mode = "beast"

    intensity_raw = data.get("intensity")
    if intensity_raw is not None:
        try:
            intensity = min(1.0, max(0.20, float(intensity_raw)))
        except (ValueError, TypeError):
            intensity = 0.70
    else:
        intensity = 0.70

    preserve_keywords = data.get("preserve_keywords", [])

    if isinstance(preserve_keywords, str):
        preserve_keywords = [k.strip() for k in preserve_keywords.split(",") if k.strip()]

    result = humanizer.process(
        text=text,
        tone=tone,
        intensity=intensity,
        preserve_keywords=preserve_keywords,
        mode=mode
    )

    return jsonify(result)


@app.route("/api/beast", methods=["POST"])
def beast_mode():
    """Direct Beast Mode endpoint for stealth clearance transformation."""
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Please provide input text to beast-transform."}), 400

    vocabulary_level = data.get("vocabulary_level", "scholar")
    intensity = float(data.get("intensity", 0.65))
    preserve_keywords = data.get("preserve_keywords", [])
    if isinstance(preserve_keywords, str):
        preserve_keywords = [k.strip() for k in preserve_keywords.split(",") if k.strip()]

    result = humanizer.beast.execute_beast_mode(
        text=text,
        vocabulary_level=vocabulary_level,
        intensity=intensity,
        preserve_keywords=preserve_keywords
    )
    return jsonify(result)


@app.route("/api/alternatives", methods=["POST"])
def get_sentence_alternatives():
    """Returns 3 instant rephrasing alternatives for any sentence."""
    data = request.get_json(force=True, silent=True) or {}
    sentence = data.get("sentence", "").strip()
    tone = data.get("tone", "standard")

    if not sentence:
        return jsonify({"error": "No sentence provided."}), 400

    alts = humanizer.get_sentence_alternatives(sentence, tone=tone)
    return jsonify({"sentence": sentence, "alternatives": alts})


@app.route("/api/detect", methods=["POST"])
def detect_ai():
    """
    Analyzes text for AI likelihood, 5-detector radar, sentence-level heatmap,
    and plagiarism overlap (against reference text or web/literature corpus).
    """
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "").strip()
    reference_text = data.get("reference_text", "").strip()

    if not text:
        return jsonify({"error": "No text provided for detection."}), 400

    analysis = analyzer.full_forensic_detection(text, reference_text=reference_text)
    return jsonify(analysis)


@app.route("/api/plagiarism", methods=["POST"])
def detect_plagiarism():
    """
    Dedicated plagiarism scanner checking verbatim sequence overlap
    against reference text or the 4,000+ harvested academic/web corpus.
    """
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "").strip()
    reference_text = data.get("reference_text", "").strip()

    if not text:
        return jsonify({"error": "No text provided for plagiarism check."}), 400

    if reference_text:
        res = analyzer.check_plagiarism_similarity(reference_text, text)
        res["corpus_matches"] = analyzer.check_corpus_plagiarism(text)
    else:
        res = analyzer.check_corpus_plagiarism(text)

    return jsonify(res)



@app.route("/api/train", methods=["POST"])
def trigger_training():
    """Triggers dataset builder and calibration workflow."""
    try:
        calibrated = trainer.train_and_calibrate()
        return jsonify({"success": True, "results": calibrated})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/model/status", methods=["GET"])
def model_status():
    """Returns status of current calibrated model and neural transformer."""
    res = {
        "status": "ready",
        "model_version": "2.5.0-beast",
        "optimal_intensity": 0.50,
        "note": "Ready for continuous training"
    }

    checkpoint_file = trainer.model_dir / "calibrated_weights.json"
    if checkpoint_file.exists():
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            res["calibration"] = json.load(f)

    neural_meta_file = trainer.model_dir / "fine_tuned_t5" / "training_meta.json"
    if neural_meta_file.exists():
        with open(neural_meta_file, "r", encoding="utf-8") as f:
            res["neural_model"] = json.load(f)

    return jsonify(res)


@app.route("/api/code/humanize", methods=["POST"])
def api_code_humanize():
    """Humanizes code comments and docstrings across beginner, intermediate, and expert personas."""
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    language = data.get("language", "python")
    persona = data.get("persona", "intermediate")

    if not code:
        return jsonify({"success": False, "error": "No code provided"}), 400

    result = code_humanizer.process_code(code, language=language, persona=persona)
    return jsonify({"success": True, **result})


@app.route("/api/citations/generate", methods=["POST"])
def api_citations_generate():
    """Generates discipline-specific BibTeX, LaTeX, and structured references."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    discipline = data.get("discipline")
    count = int(data.get("count", 3))

    result = citation_engine.generate_references(discipline=discipline, count=count, text_context=text)
    return jsonify({"success": True, **result})


@app.route("/api/scrub/watermarks", methods=["POST"])
def api_scrub_watermarks():
    """Purges zero-width Unicode characters, C2PA manifests, and SynthID watermarks."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400

    result = scrubber.scrub(text)
    return jsonify({"success": True, **result})


if __name__ == "__main__":
    print(f"Starting TextHumanizer Pro Web Server on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
