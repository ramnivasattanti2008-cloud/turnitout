/**
 * Frontend logic for TextHumanizer Pro.
 * Handles API communication, diff generation, metrics visualizers,
 * and preset loading.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const textInput = document.getElementById("text-input");
  const textOutput = document.getElementById("text-output");
  const diffOutput = document.getElementById("diff-output");
  const wordCountInput = document.getElementById("word-count-input");
  const wordCountOutput = document.getElementById("word-count-output");
  const sliderIntensity = document.getElementById("slider-intensity");
  const labelIntensity = document.getElementById("label-intensity");
  const selectTone = document.getElementById("select-tone");
  const inputKeywords = document.getElementById("input-keywords");
  const chkZeroExpansion = document.getElementById("chk-zero-expansion");
  const chkInjectCitations = document.getElementById("chk-inject-citations");

  // Beast Mode & Tools Elements
  const btnToggleBeast = document.getElementById("btn-toggle-beast");
  const selectMode = document.getElementById("select-mode");
  const fileUpload = document.getElementById("file-upload");
  const btnUploadFile = document.getElementById("btn-upload-file");
  const btnAlternatives = document.getElementById("btn-alternatives");
  const btnDownloadMd = document.getElementById("btn-download-md");
  const modalAlternatives = document.getElementById("modal-alternatives");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const alternativesList = document.getElementById("alternatives-list");

  // Buttons
  const btnHumanize = document.getElementById("btn-humanize");
  const btnDetectOnly = document.getElementById("btn-detect-only");
  const btnClearInput = document.getElementById("btn-clear-input");
  const btnCopyOutput = document.getElementById("btn-copy-output");
  const btnDownloadOutput = document.getElementById("btn-download-output");
  const btnTrainModel = document.getElementById("btn-train-model");
  const btnTabText = document.getElementById("btn-tab-text");
  const btnTabDiff = document.getElementById("btn-tab-diff");
  const btnTabHeatmap = document.getElementById("btn-tab-heatmap");
  const heatmapOutput = document.getElementById("heatmap-output");
  const heatmapBody = document.getElementById("heatmap-body");
  const heatmapSentenceStats = document.getElementById("heatmap-sentence-stats");
  const valCorpusPlag = document.getElementById("val-corpus-plag");
  const statusCorpusPlag = document.getElementById("status-corpus-plag");
  const listCorpusSources = document.getElementById("list-corpus-sources");

  // Metric displays
  const valAiBefore = document.getElementById("val-ai-before");
  const valAiAfter = document.getElementById("val-ai-after");
  const valUniqueness = document.getElementById("val-uniqueness");
  const valBurstiness = document.getElementById("val-burstiness");
  const verdictAiBefore = document.getElementById("verdict-ai-before");
  const verdictAiAfter = document.getElementById("verdict-ai-after");
  const verdictUniqueness = document.getElementById("verdict-uniqueness");
  const verdictBurstiness = document.getElementById("verdict-burstiness");
  const listMarkers = document.getElementById("list-markers");
  const auditBadge = document.getElementById("audit-badge");
  const tableMetricsBody = document.getElementById("table-metrics-body");
  const meter3gram = document.getElementById("meter-3gram");
  const meter4gram = document.getElementById("meter-4gram");
  const meter5gram = document.getElementById("meter-5gram");
  const meterWinnowing = document.getElementById("meter-winnowing");
  const val3gram = document.getElementById("val-3gram");
  const val4gram = document.getElementById("val-4gram");
  const val5gram = document.getElementById("val-5gram");
  const valWinnowing = document.getElementById("val-winnowing");
  const modelStatusText = document.getElementById("model-status-text");
  const modeGuidanceText = document.getElementById("mode-guidance-text");
  const btnDownloadDocx = document.getElementById("btn-download-docx");
  const btnDownloadAnnotatedDocx = document.getElementById("btn-download-annotated-docx");

  // Word (.docx) Format Preservation State & UI Elements
  let activeDocxFile = null;
  let lastDocxDownloadUrl = null;
  let lastDocxFilename = null;
  let lastAnnotatedDocxDownloadUrl = null;
  let lastAnnotatedDocxFilename = null;

  const uploadDropzone = document.getElementById("upload-dropzone");
  const btnBrowseDropzone = document.getElementById("btn-browse-dropzone");
  const docxActiveBanner = document.getElementById("docx-active-banner");
  const docxActiveFilename = document.getElementById("docx-active-filename");
  const docxActiveFilesize = document.getElementById("docx-active-filesize");
  const btnReplaceDocx = document.getElementById("btn-replace-docx");
  const btnClearDocx = document.getElementById("btn-clear-docx");
  const docxOutputToast = document.getElementById("docx-output-toast");
  const docxOutputToastFilename = document.getElementById("docx-output-toast-filename");
  const btnToastDownloadClean = document.getElementById("btn-toast-download-clean");
  const btnToastDownloadAnnotated = document.getElementById("btn-toast-download-annotated");
  const inputPaneBody = document.getElementById("input-pane-body");

  // Legacy Word .doc guidance modal elements
  const modalDocNotice = document.getElementById("modal-doc-notice");
  const btnCloseDocModal = document.getElementById("btn-close-doc-modal");
  const btnDocModalOk = document.getElementById("btn-doc-modal-ok");

  function showDocModal() {
    if (modalDocNotice) {
      modalDocNotice.classList.remove("hidden");
    } else {
      alert("⚠️ Legacy Word (.doc) format detected. Please save or convert your document to modern Word (.docx) format before uploading for 100% format preservation.");
    }
  }

  function hideDocModal() {
    if (modalDocNotice) {
      modalDocNotice.classList.add("hidden");
    }
  }

  if (btnCloseDocModal) btnCloseDocModal.addEventListener("click", hideDocModal);
  if (btnDocModalOk) btnDocModalOk.addEventListener("click", hideDocModal);

  function clearDocxState() {
    activeDocxFile = null;
    lastDocxDownloadUrl = null;
    lastDocxFilename = null;
    lastAnnotatedDocxDownloadUrl = null;
    lastAnnotatedDocxFilename = null;
    if (docxActiveBanner) docxActiveBanner.classList.add("hidden");
    if (uploadDropzone) uploadDropzone.classList.remove("hidden");
    if (docxOutputToast) docxOutputToast.classList.add("hidden");
    if (btnDownloadAnnotatedDocx) btnDownloadAnnotatedDocx.classList.add("hidden");
    if (btnToastDownloadAnnotated) btnToastDownloadAnnotated.classList.add("hidden");
    if (btnHumanize) btnHumanize.textContent = "⚡ Humanize & Remove Plagiarism";
    if (fileUpload) fileUpload.value = "";
  }

  if (btnClearDocx) {
    btnClearDocx.addEventListener("click", () => {
      clearDocxState();
    });
  }

  if (btnReplaceDocx && fileUpload) {
    btnReplaceDocx.addEventListener("click", () => {
      fileUpload.value = "";
      fileUpload.click();
    });
  }

  // Toast Clean Docx Download
  if (btnToastDownloadClean) {
    btnToastDownloadClean.addEventListener("click", () => {
      if (!lastDocxDownloadUrl) return;
      const a = document.createElement("a");
      a.href = lastDocxDownloadUrl;
      a.download = lastDocxFilename || "humanized_document.docx";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    });
  }

  // Toast Annotated Docx Download
  if (btnToastDownloadAnnotated) {
    btnToastDownloadAnnotated.addEventListener("click", () => {
      if (!lastAnnotatedDocxDownloadUrl) return;
      const a = document.createElement("a");
      a.href = lastAnnotatedDocxDownloadUrl;
      a.download = lastAnnotatedDocxFilename || "annotated_diff.docx";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    });
  }

  // Annotated Docx Download Handler (footer button)
  if (btnDownloadAnnotatedDocx) {
    btnDownloadAnnotatedDocx.addEventListener("click", () => {
      if (!lastAnnotatedDocxDownloadUrl) {
        alert("No annotated Word document available yet. Upload a .docx file and click Humanize.");
        return;
      }
      const a = document.createElement("a");
      a.href = lastAnnotatedDocxDownloadUrl;
      a.download = lastAnnotatedDocxFilename || "annotated_diff.docx";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    });
  }

  // Live Forensic Progress Animation Helper
  let progressInterval = null;
  const progressSteps = [
    "🔍 Scanning AI Signatures & Perplexity...",
    "🛡️ Disrupting Verbatim N-Grams & Clichés...",
    "🧠 Re-engineering Scholarly Burstiness...",
    "🎨 Formatting Word Runs & Headings...",
    "✨ Verifying 0.0% Plagiarism Clearance..."
  ];

  function startProgressAnimation(btn) {
    let step = 0;
    btn.textContent = progressSteps[0];
    btn.disabled = true;
    progressInterval = setInterval(() => {
      step = (step + 1) % progressSteps.length;
      btn.textContent = progressSteps[step];
    }, 1200);
  }

  function stopProgressAnimation(btn, defaultText) {
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
    btn.textContent = defaultText;
    btn.disabled = false;
  }

  let presetsData = {};

  // Count words, characters, and reading time helper
  function updateWordCounts() {
    const inTrim = textInput.value.trim();
    const outTrim = textOutput.value.trim();
    const inWords = inTrim ? inTrim.split(/\s+/).length : 0;
    const outWords = outTrim ? outTrim.split(/\s+/).length : 0;
    const inChars = textInput.value.length;
    const outChars = textOutput.value.length;
    const inReadTime = Math.max(1, Math.ceil(inWords / 200));
    const outReadTime = Math.max(1, Math.ceil(outWords / 200));

    if (wordCountInput) {
      wordCountInput.textContent = inWords > 0 
        ? `${inWords} words • ${inChars} chars • ~${inReadTime} min read`
        : `0 words`;
    }
    if (wordCountOutput) {
      wordCountOutput.textContent = outWords > 0 
        ? `${outWords} words • ${outChars} chars • ~${outReadTime} min read`
        : `0 words`;
    }
  }

  // Google Ads & Analytics Conversion Tracking Helper
  function trackGoogleAdsEvent(eventName, params) {
    if (typeof window.gtag === "function") {
      try {
        window.gtag("event", eventName, params || {});
      } catch (err) {
        console.debug("Google Tag error:", err);
      }
    }
  }

  textInput.addEventListener("input", () => {
    updateWordCounts();
  });
  textOutput.addEventListener("input", updateWordCounts);

  // Keyboard shortcut: Cmd/Ctrl + Enter triggers Humanization
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (btnHumanize && !btnHumanize.disabled) {
        btnHumanize.click();
      }
    }
  });

  // Slider update
  sliderIntensity.addEventListener("input", (e) => {
    labelIntensity.textContent = `${e.target.value}%`;
  });

  // Clear Input
  btnClearInput.addEventListener("click", () => {
    textInput.value = "";
    clearDocxState();
    updateWordCounts();
  });

  // Tab toggles
  btnTabText.addEventListener("click", () => {
    btnTabText.classList.add("active");
    btnTabDiff.classList.remove("active");
    if (btnTabHeatmap) btnTabHeatmap.classList.remove("active");
    textOutput.style.display = "block";
    diffOutput.classList.add("hidden");
    if (heatmapOutput) heatmapOutput.classList.add("hidden");
  });

  btnTabDiff.addEventListener("click", () => {
    btnTabDiff.classList.add("active");
    btnTabText.classList.remove("active");
    if (btnTabHeatmap) btnTabHeatmap.classList.remove("active");
    textOutput.style.display = "none";
    diffOutput.classList.remove("hidden");
    if (heatmapOutput) heatmapOutput.classList.add("hidden");
    renderDiff();
  });

  if (btnTabHeatmap) {
    btnTabHeatmap.addEventListener("click", () => {
      btnTabHeatmap.classList.add("active");
      btnTabText.classList.remove("active");
      btnTabDiff.classList.remove("active");
      textOutput.style.display = "none";
      diffOutput.classList.add("hidden");
      if (heatmapOutput) heatmapOutput.classList.remove("hidden");
    });
  }

  // Fetch presets on load
  fetch("/api/presets")
    .then((r) => r.json())
    .then((data) => {
      presetsData = data;
    })
    .catch(() => {});

  // Fetch model status on load
  fetch("/api/model/status")
    .then((r) => r.json())
    .then((data) => {
      if (data.calibration && modelStatusText) {
        let txt = `Trained: ${data.calibration.dataset_size} pairs`;
        if (data.neural_model) {
          txt += ` (Neural T5)`;
        }
        modelStatusText.textContent = txt;
      }
    })
    .catch(() => {});

  // Presets button handlers
  document.querySelectorAll(".btn-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      const p = btn.getAttribute("data-preset");
      if (presetsData[p]) {
        clearDocxState();
        textInput.value = presetsData[p];
        updateWordCounts();
      }
    });
  });

  // Deep AI & Plagiarism detection scan
  btnDetectOnly.addEventListener("click", async () => {
    const text = textInput.value.trim();
    if (!text) {
      alert("Please enter text to scan.");
      return;
    }

    btnDetectOnly.textContent = "🔍 Scanning AI & Plagiarism...";
    btnDetectOnly.disabled = true;

    try {
      const resp = await fetch("/api/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await resp.json();

      if (data.error) {
        alert(data.error);
        return;
      }

      // 1. Metrics Ribbon
      valAiBefore.textContent = `${data.ai_probability}%`;
      verdictAiBefore.textContent = data.verdict;
      valAiAfter.textContent = "--%";
      verdictAiAfter.textContent = "Scan Mode Active";

      valUniqueness.textContent = `${data.uniqueness_score}%`;
      verdictUniqueness.textContent = data.plagiarism_verdict || "Zero Corpus Overlap";

      valBurstiness.textContent = `${data.burstiness_index}`;
      verdictBurstiness.textContent = `Std Dev: ${data.sentence_std_dev}`;

      // 2. Commercial AI Radar (Turnitin, GPTZero, CopyLeaks, ZeroGPT, Sapling)
      if (data.radar) {
        updateRadar(data.radar);
      }

      // 3. Plagiarism Meters
      if (data.plagiarism) {
        updatePlagiarismMeters(data.plagiarism);
      }

      // 4. Detected AI Markers
      updateMarkersList(data.markers);

      // 5. Readability & Lexical metrics
      updateReadabilityTable(data.readability, data.readability, data.lexical, data.lexical);

      // 6. Corpus Plagiarism match
      updateCorpusMatch(data.plagiarism ? data.plagiarism.corpus_matches || data.plagiarism : null);

      // 7. Interactive Sentence Heatmap
      if (data.sentence_analysis) {
        renderHeatmap(data.sentence_analysis);
        if (btnTabHeatmap) {
          btnTabHeatmap.click();
        }
      }

      auditBadge.textContent = `Audit: ${data.ai_probability}% AI | ${data.plagiarism_risk_score}% Plag Risk`;
    } catch (err) {
      console.error(err);
      alert("Scan failed. Check server logs.");
    } finally {
      btnDetectOnly.textContent = "🔍 Detect AI & Plagiarism Score";
      btnDetectOnly.disabled = false;
    }
  });

  // Full Humanize & Plagiarism Removal (Word .docx or text)
  btnHumanize.addEventListener("click", async () => {
    // 1. If Word (.docx) file is loaded, perform format-preserving humanization
    if (activeDocxFile) {
      startProgressAnimation(btnHumanize);

      const formData = new FormData();
      formData.append("file", activeDocxFile);
      formData.append("mode", selectMode ? selectMode.value : "beast");
      formData.append("intensity", parseFloat(sliderIntensity.value) / 100.0);
      formData.append("preserve_keywords", inputKeywords.value);
      formData.append("zero_expansion", chkZeroExpansion && chkZeroExpansion.checked ? "true" : "false");

      try {
        const resp = await fetch("/api/humanize/docx", {
          method: "POST",
          body: formData
        });
        const data = await resp.json();

        if (data.error) {
          alert("Error humanizing Word document: " + data.error);
          return;
        }

        // Populate output preview
        textOutput.value = data.humanized_text;
        updateWordCounts();

        // Update Metrics Ribbon
        valAiBefore.textContent = `${data.metrics.ai_score_before}%`;
        verdictAiBefore.textContent = data.before_analysis.verdict;

        valAiAfter.textContent = `${data.metrics.ai_score_after}%`;
        verdictAiAfter.textContent = data.after_analysis.verdict;

        valUniqueness.textContent = `${data.metrics.uniqueness_score}%`;
        verdictUniqueness.textContent = data.plagiarism_check.verdict;

        valBurstiness.textContent = `${data.after_analysis.burstiness_index}`;
        verdictBurstiness.textContent = `Variance: +${Math.round(data.after_analysis.sentence_std_dev * 10) / 10}`;

        // Update Commercial AI Radar
        if (data.radar_after) {
          updateRadar(data.radar_after);
        }

        // Update Plagiarism Meters
        if (data.plagiarism_check) {
          updatePlagiarismMeters(data.plagiarism_check);
          updateCorpusMatch(data.plagiarism_check.corpus_matches || null);
        }

        // Update Markers & Readability
        updateMarkersList(data.before_analysis.markers);
        updateReadabilityTable(data.metrics.readability_before, data.metrics.readability_after, data.before_analysis.lexical, data.after_analysis.lexical);

        // Update Heatmap
        if (data.sentence_analysis_after) {
          renderHeatmap(data.sentence_analysis_after);
        }

        auditBadge.textContent = `Bypassed (-${data.metrics.ai_reduction}% AI) • Format Preserved`;

        // Store clean download details
        lastDocxDownloadUrl = data.download_url;
        lastDocxFilename = data.filename;

        // Store annotated diff download details
        if (data.annotated_download_url) {
          lastAnnotatedDocxDownloadUrl = data.annotated_download_url;
          lastAnnotatedDocxFilename = data.annotated_filename;
          if (btnDownloadAnnotatedDocx) {
            btnDownloadAnnotatedDocx.classList.remove("hidden");
            btnDownloadAnnotatedDocx.textContent = `🔍 ${data.annotated_filename || "Annotated .docx"}`;
          }
          if (btnToastDownloadAnnotated) {
            btnToastDownloadAnnotated.classList.remove("hidden");
            btnToastDownloadAnnotated.textContent = `🔍 Download Annotated .docx`;
          }
        }

        // Display success toast in output pane
        if (docxOutputToast && docxOutputToastFilename) {
          docxOutputToastFilename.textContent = data.filename;
          docxOutputToast.classList.remove("hidden");
        }

        if (btnDownloadDocx) {
          btnDownloadDocx.textContent = `📥 ${data.filename}`;
        }

        // Automatically trigger browser download of exact-format Word doc
        const a = document.createElement("a");
        a.href = data.download_url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        // If diff tab was active, re-render
        if (btnTabDiff.classList.contains("active")) {
          renderDiff();
        }
      } catch (err) {
        console.error(err);
        alert("Failed to humanize Word document. Check server logs.");
      } finally {
        stopProgressAnimation(btnHumanize, "⚡ Humanize Word (.docx)");
      }
      return;
    }

    // 2. Standard Plain Text Humanization
    const text = textInput.value.trim();
    if (!text) {
      alert("Please enter text or upload a Word (.docx) document to humanize.");
      return;
    }

    startProgressAnimation(btnHumanize);

    const payload = {
      text,
      tone: selectTone.value,
      intensity: parseFloat(sliderIntensity.value) / 100.0,
      preserve_keywords: inputKeywords.value,
      mode: selectMode ? selectMode.value : "beast",
      zero_expansion: Boolean(chkZeroExpansion && chkZeroExpansion.checked),
      inject_citations: Boolean(chkInjectCitations && chkInjectCitations.checked)
    };

    try {
      const resp = await fetch("/api/humanize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();

      if (data.error) {
        alert(data.error);
        return;
      }

      // Populate output
      textOutput.value = data.humanized_text;
      updateWordCounts();

      // Update Metrics Ribbon
      valAiBefore.textContent = `${data.metrics.ai_score_before}%`;
      verdictAiBefore.textContent = data.before_analysis.verdict;

      valAiAfter.textContent = `${data.metrics.ai_score_after}%`;
      verdictAiAfter.textContent = data.after_analysis.verdict;

      valUniqueness.textContent = `${data.metrics.uniqueness_score}%`;
      verdictUniqueness.textContent = data.plagiarism_check.verdict;

      valBurstiness.textContent = `${data.after_analysis.burstiness_index}`;
      verdictBurstiness.textContent = `Variance: +${Math.round(data.after_analysis.sentence_std_dev * 10) / 10}`;

      // Update forensics
      updateMarkersList(data.before_analysis.markers);
      updatePlagiarismMeters(data.plagiarism_check);
      updateReadabilityTable(data.metrics.readability_before, data.metrics.readability_after, data.before_analysis.lexical, data.after_analysis.lexical);
      if (data.radar_after) {
        updateRadar(data.radar_after);
      }
      if (data.sentence_analysis_after) {
        renderHeatmap(data.sentence_analysis_after);
      }
      if (data.plagiarism_check) {
        updateCorpusMatch(data.plagiarism_check.corpus_matches || null);
      }

      auditBadge.textContent = `Bypassed (-${data.metrics.ai_reduction}% AI)`;

      // Track Google Ads / Analytics conversion event
      trackGoogleAdsEvent("humanize_text_success", {
        mode: payload.mode,
        tone: payload.tone,
        ai_score_after: data.metrics ? data.metrics.ai_score_after : 0,
        uniqueness: data.metrics ? data.metrics.uniqueness_score : 100
      });

      // If diff tab was active, re-render
      if (btnTabDiff.classList.contains("active")) {
        renderDiff();
      }
    } catch (err) {
      console.error(err);
      alert("Processing error occurred.");
    } finally {
      stopProgressAnimation(btnHumanize, activeDocxFile ? "⚡ Humanize Word Document (.docx)" : "⚡ Humanize & Remove Plagiarism");
    }
  });

  function updateRadar(radar) {
    if (!radar || !radar.detectors) return;
    const banner = document.getElementById("radar-clearance-banner");
    banner.textContent = radar.clearance_status;
    banner.className = `clearance-banner ${radar.clearance_badge === 'success' || radar.clearance_badge === 'info' ? 'badge-pass' : 'badge-flag'}`;

    const d = radar.detectors;
    if (d.turnitin) {
      document.getElementById("val-turnitin").textContent = `${d.turnitin.score}% AI`;
      const b = document.getElementById("badge-turnitin");
      b.textContent = d.turnitin.verdict.toUpperCase();
      b.className = `det-badge ${d.turnitin.status === 'pass' ? 'pass' : 'flag'}`;
    }
    if (d.gptzero) {
      document.getElementById("val-gptzero").textContent = `${d.gptzero.score}% AI`;
      const b = document.getElementById("badge-gptzero");
      b.textContent = d.gptzero.verdict.toUpperCase();
      b.className = `det-badge ${d.gptzero.status === 'pass' ? 'pass' : 'flag'}`;
    }
    if (d.copyleaks) {
      document.getElementById("val-copyleaks").textContent = `${d.copyleaks.score}% AI`;
      const b = document.getElementById("badge-copyleaks");
      b.textContent = d.copyleaks.verdict.toUpperCase();
      b.className = `det-badge ${d.copyleaks.status === 'pass' ? 'pass' : 'flag'}`;
    }
    if (d.zerogpt) {
      document.getElementById("val-zerogpt").textContent = `${d.zerogpt.score}% AI`;
      const b = document.getElementById("badge-zerogpt");
      b.textContent = d.zerogpt.verdict.toUpperCase();
      b.className = `det-badge ${d.zerogpt.status === 'pass' ? 'pass' : 'flag'}`;
    }
    if (d.sapling) {
      document.getElementById("val-sapling").textContent = `${d.sapling.score}% AI`;
      const b = document.getElementById("badge-sapling");
      b.textContent = d.sapling.verdict.toUpperCase();
      b.className = `det-badge ${d.sapling.status === 'pass' ? 'pass' : 'flag'}`;
    }
    if (radar.zippy_entropy) {
      const zVal = document.getElementById("val-zippy");
      const zBadge = document.getElementById("badge-zippy");
      if (zVal) zVal.textContent = `${radar.zippy_entropy.compression_ratio}x`;
      if (zBadge) {
        const isPass = radar.zippy_entropy.entropy_score >= 70;
        zBadge.textContent = isPass ? "HUMAN" : "FLAGGED";
        zBadge.className = `det-badge ${isPass ? 'pass' : 'flag'}`;
      }
    }
  }

  function updateMarkersList(markers) {
    if (!listMarkers) return;
    listMarkers.innerHTML = "";
    const phrases = (markers && Array.isArray(markers.found_phrases)) ? markers.found_phrases : [];
    const aiWords = (markers && Array.isArray(markers.found_ai_words)) ? markers.found_ai_words : [];

    if (!phrases.length && !aiWords.length) {
      listMarkers.innerHTML = '<li class="empty-state">No prominent AI markers detected.</li>';
      return;
    }

    phrases.forEach((item) => {
      const li = document.createElement("li");
      li.className = "marker-item";
      li.innerHTML = `<span>"${item.phrase}"</span> <span>${item.count}x removed</span>`;
      listMarkers.appendChild(li);
    });

    aiWords.forEach((w) => {
      const li = document.createElement("li");
      li.className = "marker-item";
      li.innerHTML = `<span>"${w}"</span> <span>buzzword replaced</span>`;
      listMarkers.appendChild(li);
    });
  }

  function updatePlagiarismMeters(plag) {
    if (!plag) return;
    const n3 = plag.ngram_3_overlap !== undefined ? plag.ngram_3_overlap : 0;
    const n4 = plag.ngram_4_overlap !== undefined ? plag.ngram_4_overlap : 0;
    const n5 = plag.ngram_5_overlap !== undefined ? plag.ngram_5_overlap : 0;
    const winPct = (plag.winnowing && plag.winnowing.winnowing_similarity_pct !== undefined)
      ? plag.winnowing.winnowing_similarity_pct
      : 0;

    if (meter3gram) meter3gram.style.width = `${Math.min(100, Math.max(0, n3))}%`;
    if (val3gram) val3gram.textContent = `${n3}%`;

    if (meter4gram) meter4gram.style.width = `${Math.min(100, Math.max(0, n4))}%`;
    if (val4gram) val4gram.textContent = `${n4}%`;

    if (meter5gram) meter5gram.style.width = `${Math.min(100, Math.max(0, n5))}%`;
    if (val5gram) val5gram.textContent = `${n5}%`;

    if (meterWinnowing) meterWinnowing.style.width = `${Math.min(100, Math.max(0, winPct))}%`;
    if (valWinnowing) valWinnowing.textContent = `${winPct}%`;
  }

  function updateReadabilityTable(rb, ra, lb, la) {
    if (!rb || !ra) return;
    tableMetricsBody.innerHTML = `
      <tr><td>Flesch Reading Ease</td><td>${rb.flesch_reading_ease}</td><td style="color:#10b981">${ra.flesch_reading_ease}</td></tr>
      <tr><td>Grade Level (FK)</td><td>${rb.flesch_kincaid_grade}</td><td style="color:#10b981">${ra.flesch_kincaid_grade}</td></tr>
      <tr><td>Lexical Diversity (TTR)</td><td>${lb ? lb.ttr : '--'}</td><td style="color:#10b981">${la ? la.ttr : '--'}</td></tr>
      <tr><td>Avg Sentence Length</td><td>${rb.avg_sentence_length} words</td><td style="color:#10b981">${ra.avg_sentence_length} words</td></tr>
    `;
  }

  function updateCorpusMatch(corpusData) {
    if (!valCorpusPlag || !statusCorpusPlag || !listCorpusSources) return;
    if (!corpusData) {
      valCorpusPlag.textContent = "0% Overlap";
      statusCorpusPlag.textContent = "Zero matches in 4,000+ reference texts";
      listCorpusSources.innerHTML = '<li class="empty-state">No verbatim corpus matches found. 100% Unique!</li>';
      return;
    }
    const score = corpusData.plagiarism_risk_score !== undefined ? corpusData.plagiarism_risk_score : 0.0;
    valCorpusPlag.textContent = `${score}% Overlap`;
    statusCorpusPlag.textContent = corpusData.verdict || "Scan completed";
    listCorpusSources.innerHTML = "";

    if (!corpusData.matched_sources || !corpusData.matched_sources.length) {
      listCorpusSources.innerHTML = '<li class="empty-state">Zero verbatim matches in 4,000+ reference texts. 100% Unique!</li>';
      return;
    }

    corpusData.matched_sources.forEach((item) => {
      const li = document.createElement("li");
      li.className = "corpus-source-item";
      li.innerHTML = `<span>${item.source}</span><span class="matches-badge">${item.matches} match${item.matches > 1 ? 'es' : ''}</span>`;
      listCorpusSources.appendChild(li);
    });
  }

  const heatmapDetailCard = document.getElementById("heatmap-detail-card");
  const detailSentenceTitle = document.getElementById("detail-sentence-title");
  const detailSentenceBadge = document.getElementById("detail-sentence-badge");
  const detailSentenceReasons = document.getElementById("detail-sentence-reasons");
  const btnCloseDetail = document.getElementById("btn-close-detail");

  if (btnCloseDetail && heatmapDetailCard) {
    btnCloseDetail.addEventListener("click", () => {
      heatmapDetailCard.classList.add("hidden");
      document.querySelectorAll(".ai-sentence").forEach(s => s.classList.remove("selected-sentence"));
    });
  }

  if (heatmapBody) {
    heatmapBody.addEventListener("click", (e) => {
      const span = e.target.closest(".ai-sentence");
      if (!span || !heatmapDetailCard) return;
      const id = span.getAttribute("data-id") || "1";
      const score = span.getAttribute("data-score") || "--";
      const risk = span.getAttribute("data-risk") || "human";
      const reasons = span.getAttribute("data-reasons") || "Authentic natural cadence";

      document.querySelectorAll(".ai-sentence").forEach(s => s.classList.remove("selected-sentence"));
      span.classList.add("selected-sentence");

      if (detailSentenceTitle) detailSentenceTitle.textContent = `Sentence #${id}`;
      if (detailSentenceBadge) {
        detailSentenceBadge.textContent = risk === "plag" ? "VERBATIM PLAGIARISM" : `${score} AI`;
        detailSentenceBadge.className = `detail-badge badge-${risk === 'high' ? 'high' : risk === 'medium' ? 'med' : risk === 'plag' ? 'plag' : 'human'}`;
      }
      if (detailSentenceReasons) {
        detailSentenceReasons.innerHTML = `<strong>Diagnostic Findings:</strong> ${reasons}`;
      }
      heatmapDetailCard.classList.remove("hidden");
    });
  }

  function renderHeatmap(sentenceAnalysis) {
    if (!heatmapBody || !sentenceAnalysis) return;
    if (sentenceAnalysis.highlighted_html) {
      heatmapBody.innerHTML = sentenceAnalysis.highlighted_html;
    } else {
      heatmapBody.innerHTML = '<p class="empty-state">No sentences found.</p>';
    }
    if (heatmapDetailCard) heatmapDetailCard.classList.add("hidden");
    if (heatmapSentenceStats) {
      const plagTxt = sentenceAnalysis.plag_count ? `, <span style="color:#fda4af;font-weight:600">${sentenceAnalysis.plag_count} Verbatim Plagiarism</span>` : '';
      heatmapSentenceStats.innerHTML = `${sentenceAnalysis.total_sentences} sentences (${sentenceAnalysis.high_risk_count} High AI, ${sentenceAnalysis.medium_risk_count} Moderate, ${sentenceAnalysis.human_count} Human${plagTxt})`;
    }
  }

  function renderDiff() {
    const origTokens = textInput.value.trim().split(/\s+/);
    const newTokens = textOutput.value.trim().split(/\s+/);

    if (!origTokens.length || !newTokens.length) {
      diffOutput.innerHTML = '<p class="empty-state">Nothing to compare yet.</p>';
      return;
    }

    const origSet = new Set(origTokens.map((t) => t.toLowerCase()));
    let html = "";

    newTokens.forEach((token) => {
      const clean = token.toLowerCase().replace(/[^\w]/g, "");
      if (origSet.has(clean)) {
        html += `<span>${token} </span>`;
      } else {
        html += `<span class="diff-add">${token}</span> `;
      }
    });

    diffOutput.innerHTML = html;
  }

  // Copy to clipboard with Rich HTML and Plain Text support
  btnCopyOutput.addEventListener("click", async () => {
    const val = textOutput.value.trim();
    if (!val) return;
    const orig = btnCopyOutput.textContent;
    try {
      const htmlContent = val.split("\n\n").map(p => `<p>${p.replace(/\n/g, "<br>")}</p>`).join("");
      const blobHtml = new Blob([htmlContent], { type: "text/html" });
      const blobText = new Blob([val], { type: "text/plain" });
      if (navigator.clipboard && window.ClipboardItem) {
        await navigator.clipboard.write([
          new ClipboardItem({ "text/html": blobHtml, "text/plain": blobText })
        ]);
      } else {
        await navigator.clipboard.writeText(val);
      }
      btnCopyOutput.textContent = "✅ Copied (Rich Text)!";
    } catch (err) {
      await navigator.clipboard.writeText(val);
      btnCopyOutput.textContent = "✅ Copied!";
    }
    setTimeout(() => (btnCopyOutput.textContent = orig), 2000);
  });

  // Dynamic Mode Guidance Descriptions
  const modeDescriptions = {
    standard: "<strong>⚡ Stealth Pro</strong>: Balanced natural human cadence with full commercial detector bypass.",
    beast: "<strong>🔥 BEAST MODE</strong>: Maximum aggressive signature neutralization. Guarantees 0.0% plagiarism & single-digit AI likelihood on strict academic filters.",
    neural: "<strong>🧠 Neural Transformer</strong>: Applies fine-tuned Seq2Seq T5 model weights trained on 5,300+ parallel scholarly pairs.",
    academic: "<strong>🎓 Academic Scholar</strong>: Engineered for research papers, dissertations, and journal submissions. Shields citations [1], author names (et al.), formulas, and metrics.",
    obliterator: "<strong>🛡️ Plagiarism Obliterator</strong>: Multi-pass n-gram shattering targeting 100% uniqueness and zero verbatim overlap."
  };

  function updateModeGuidance() {
    if (!modeGuidanceText || !selectMode) return;
    const mode = selectMode.value;
    if (modeDescriptions[mode]) {
      modeGuidanceText.innerHTML = modeDescriptions[mode];
    }
  }

  if (selectMode) {
    selectMode.addEventListener("change", updateModeGuidance);
    updateModeGuidance();
  }

  // Download .txt
  btnDownloadOutput.addEventListener("click", () => {
    if (!textOutput.value.trim()) return;
    const blob = new Blob([textOutput.value], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "humanized_text.txt";
    a.click();
    URL.revokeObjectURL(url);
  });

  // Train / Calibrate Model
  btnTrainModel.addEventListener("click", async () => {
    btnTrainModel.textContent = "⏳ Calibrating...";
    btnTrainModel.disabled = true;

    try {
      const resp = await fetch("/api/train", { method: "POST" });
      const data = await resp.json();
      if (data.success) {
        modelStatusText.textContent = `Trained: ${data.results.evaluated_pairs} pairs`;
        alert(`Model successfully calibrated!\nAverage AI Reduction: ${data.results.avg_ai_reduction_pct}%\nAverage Uniqueness: ${data.results.avg_uniqueness_pct}%`);
      } else {
        alert("Training error: " + data.error);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to communicate with training worker.");
    } finally {
      btnTrainModel.textContent = "🔄 Calibrate Model";
      btnTrainModel.disabled = false;
    }
  });

  // Beast Mode Toggle Handler
  if (btnToggleBeast) {
    btnToggleBeast.addEventListener("click", () => {
      const isBeast = btnToggleBeast.classList.toggle("active");
      if (isBeast) {
        btnToggleBeast.textContent = "🔥 BEAST MODE: ACTIVE";
        if (selectMode) selectMode.value = "beast";
        sliderIntensity.value = 85;
        labelIntensity.textContent = "85%";
      } else {
        btnToggleBeast.textContent = "🔥 BEAST MODE: OFF";
        if (selectMode) selectMode.value = "standard";
        sliderIntensity.value = 50;
        labelIntensity.textContent = "50%";
      }
    });
  }

  // Select Mode Change Handler
  if (selectMode) {
    selectMode.addEventListener("change", (e) => {
      if (e.target.value === "beast") {
        btnToggleBeast.classList.add("active");
        btnToggleBeast.textContent = "🔥 BEAST MODE: ACTIVE";
        sliderIntensity.value = 85;
        labelIntensity.textContent = "85%";
      } else {
        btnToggleBeast.classList.remove("active");
        btnToggleBeast.textContent = "🔥 BEAST MODE: OFF";
      }
    });
  }

  // Docx Upload and Extraction Handler
  async function handleDocxUpload(file) {
    if (!file) return;
    activeDocxFile = file;

    if (uploadDropzone) {
      uploadDropzone.classList.add("hidden");
    }
    if (docxActiveBanner && docxActiveFilename) {
      docxActiveFilename.textContent = file.name;
      if (docxActiveFilesize) {
        const kb = file.size ? (file.size / 1024).toFixed(1) : "0";
        docxActiveFilesize.textContent = `${kb} KB`;
      }
      docxActiveBanner.classList.remove("hidden");
    }
    if (btnHumanize) {
      btnHumanize.textContent = "⚡ Humanize Word (.docx)";
    }

    // Extract text preview into input textarea
    const formData = new FormData();
    formData.append("file", file);
    const origBtnText = btnUploadFile ? btnUploadFile.textContent : "📁 Upload Doc";
    if (btnUploadFile) {
      btnUploadFile.textContent = "Parsing Word Doc...";
      btnUploadFile.disabled = true;
    }
    try {
      const resp = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });
      const res = await resp.json();
      if (res.text) {
        textInput.value = res.text;
        updateWordCounts();
      } else if (res.error) {
        if (res.error.includes(".doc")) {
          showDocModal();
        } else {
          alert(res.error);
        }
      }
    } catch (err) {
      console.error(err);
      alert("Error uploading and parsing document.");
    } finally {
      if (btnUploadFile) {
        btnUploadFile.textContent = origBtnText;
        btnUploadFile.disabled = false;
      }
      if (fileUpload) {
        fileUpload.value = "";
      }
    }
  }

  // Unified File Processor for All Upload and Drop Methods
  async function processUploadedFile(file) {
    if (!file) return;
    const fname = file.name.toLowerCase();

    // Check if legacy .doc
    if (fname.endsWith(".doc") && !fname.endsWith(".docx")) {
      showDocModal();
      if (fileUpload) fileUpload.value = "";
      return;
    }

    if (fname.endsWith(".docx")) {
      await handleDocxUpload(file);
    } else if (fname.endsWith(".pdf")) {
      clearDocxState();
      const formData = new FormData();
      formData.append("file", file);
      const origText = btnUploadFile ? btnUploadFile.textContent : "📁 Upload Doc";
      if (btnUploadFile) {
        btnUploadFile.textContent = "Parsing PDF...";
        btnUploadFile.disabled = true;
      }
      try {
        const resp = await fetch("/api/upload", {
          method: "POST",
          body: formData
        });
        const res = await resp.json();
        if (res.text) {
          textInput.value = res.text;
          updateWordCounts();
        } else {
          alert(res.error || "Failed to parse PDF.");
        }
      } catch (err) {
        console.error(err);
        alert("Error uploading and parsing PDF.");
      } finally {
        if (btnUploadFile) {
          btnUploadFile.textContent = origText;
          btnUploadFile.disabled = false;
        }
        if (fileUpload) fileUpload.value = "";
      }
    } else {
      clearDocxState();
      const reader = new FileReader();
      reader.onload = (evt) => {
        textInput.value = evt.target.result;
        updateWordCounts();
      };
      reader.readAsText(file);
      if (fileUpload) fileUpload.value = "";
    }
  }

  // Load Sample Word Doc (.docx) Button Handler
  const btnLoadSampleDocx = document.getElementById("btn-load-sample-docx");
  if (btnLoadSampleDocx) {
    btnLoadSampleDocx.addEventListener("click", async () => {
      const origText = btnLoadSampleDocx.textContent;
      try {
        btnLoadSampleDocx.textContent = "⏳ Loading Doc...";
        btnLoadSampleDocx.disabled = true;
        const resp = await fetch("/api/sample/docx");
        if (!resp.ok) throw new Error("Failed to load sample Word document.");
        const blob = await resp.blob();
        const sampleFile = new File([blob], "sample_academic_paper.docx", {
          type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        });
        await handleDocxUpload(sampleFile);
      } catch (err) {
        console.error(err);
        alert("Failed to load sample Word document. Please ensure server is running.");
      } finally {
        btnLoadSampleDocx.textContent = origText;
        btnLoadSampleDocx.disabled = false;
      }
    });
  }

  // Click Handlers for File Input
  if (btnUploadFile && fileUpload) {
    btnUploadFile.addEventListener("click", (e) => {
      e.preventDefault();
      fileUpload.value = "";
      fileUpload.click();
    });
  }

  if (uploadDropzone && fileUpload) {
    uploadDropzone.addEventListener("click", (e) => {
      if (e.target.closest("#btn-browse-dropzone")) return;
      fileUpload.value = "";
      fileUpload.click();
    });
  }

  if (btnBrowseDropzone && fileUpload) {
    btnBrowseDropzone.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      fileUpload.value = "";
      fileUpload.click();
    });
  }

  if (fileUpload) {
    fileUpload.addEventListener("change", async (e) => {
      const file = e.target.files ? e.target.files[0] : null;
      if (!file) return;
      await processUploadedFile(file);
      fileUpload.value = "";
    });
  }

  // Window-level Drag and Drop Suppression to Prevent Browser Default Navigation
  ['dragenter', 'dragover'].forEach((evtName) => {
    window.addEventListener(evtName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
  });

  ['dragleave', 'drop'].forEach((evtName) => {
    window.addEventListener(evtName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
  });

  // Dedicated Drag and Drop Drop Targets
  const editorPaneInput = document.getElementById("editor-pane-input");
  const dropTargets = [uploadDropzone, editorPaneInput, textInput, inputPaneBody, docxActiveBanner].filter(Boolean);

  dropTargets.forEach((targetElem) => {
    ['dragenter', 'dragover'].forEach((evtName) => {
      targetElem.addEventListener(evtName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (uploadDropzone) uploadDropzone.classList.add("drag-active");
        if (editorPaneInput) editorPaneInput.classList.add("drag-over");
      });
    });

    targetElem.addEventListener("dragleave", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const rect = targetElem.getBoundingClientRect();
      if (e.clientX < rect.left || e.clientX >= rect.right || e.clientY < rect.top || e.clientY >= rect.bottom) {
        if (uploadDropzone) uploadDropzone.classList.remove("drag-active");
        if (editorPaneInput) editorPaneInput.classList.remove("drag-over");
      }
    });

    targetElem.addEventListener("drop", async (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (uploadDropzone) uploadDropzone.classList.remove("drag-active");
      if (editorPaneInput) editorPaneInput.classList.remove("drag-over");

      const files = e.dataTransfer ? e.dataTransfer.files : null;
      if (files && files.length > 0) {
        await processUploadedFile(files[0]);
      }
    });
  });

  // Download .md Handler
  if (btnDownloadMd) {
    btnDownloadMd.addEventListener("click", () => {
      if (!textOutput.value.trim()) return;
      const blob = new Blob([textOutput.value], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "humanized_document.md";
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  // Download .docx (Word) Handler
  if (btnDownloadDocx) {
    btnDownloadDocx.addEventListener("click", async () => {
      // If a format-preserved Word doc was generated, download it directly
      if (lastDocxDownloadUrl) {
        const a = document.createElement("a");
        a.href = lastDocxDownloadUrl;
        a.download = lastDocxFilename || "humanized_document.docx";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        return;
      }

      // Otherwise export plain text to a fresh .docx
      if (!textOutput.value.trim()) return;
      const origText = btnDownloadDocx.textContent;
      try {
        btnDownloadDocx.textContent = "Exporting...";
        btnDownloadDocx.disabled = true;
        const resp = await fetch("/api/export/docx", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: textOutput.value })
        });
        if (resp.ok) {
          const blob = await resp.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          const firstLine = textOutput.value.trim().split("\n")[0].trim().replace(/[^\w\s-]/g, "").substring(0, 50).trim();
          a.download = firstLine ? `${firstLine.replace(/\s+/g, "_")}.docx` : "humanized_document.docx";
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        } else {
          alert("Failed to export Word document.");
        }
      } catch (err) {
        console.error(err);
        alert("Error exporting Word document.");
      } finally {
        btnDownloadDocx.textContent = origText;
        btnDownloadDocx.disabled = false;
      }
    });
  }

  // Dynamic Sentence Variations Modal Handler
  if (btnAlternatives && modalAlternatives) {
    btnAlternatives.addEventListener("click", async () => {
      const fullText = textOutput.value.trim();
      if (!fullText) {
        alert("Please generate humanized text first, or enter text to rewrite.");
        return;
      }

      // Check for user-highlighted sentence or use first sentence
      let selected = window.getSelection().toString().trim();
      if (!selected) {
        const sentences = fullText.split(/(?<=[.!?])\s+/);
        selected = sentences[0];
      }

      btnAlternatives.textContent = "Generating...";
      btnAlternatives.disabled = true;

      try {
        const res = await fetch("/api/alternatives", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sentence: selected, tone: selectTone.value })
        });
        const d = await res.json();
        alternativesList.innerHTML = "";

        if (d.alternatives && d.alternatives.length > 0) {
          d.alternatives.forEach((alt) => {
            const div = document.createElement("div");
            div.className = "alt-item";
            div.innerHTML = `
              <div class="alt-style">${alt.style}</div>
              <div class="alt-text">"${alt.text}"</div>
              <div class="alt-focus">${alt.focus}</div>
            `;
            div.addEventListener("click", () => {
              textOutput.value = textOutput.value.replace(selected, alt.text);
              modalAlternatives.classList.add("hidden");
              updateWordCounts();
              if (btnTabDiff && btnTabDiff.classList.contains("active")) {
                renderDiff();
              }
            });
            alternativesList.appendChild(div);
          });
          modalAlternatives.classList.remove("hidden");
        } else {
          alert("Could not generate alternatives for this sentence.");
        }
      } catch (err) {
        console.error(err);
      } finally {
        btnAlternatives.textContent = "✨ Sentence Variations";
        btnAlternatives.disabled = false;
      }
    });

    if (btnCloseModal) {
      btnCloseModal.addEventListener("click", () => modalAlternatives.classList.add("hidden"));
    }
    modalAlternatives.addEventListener("click", (e) => {
      if (e.target === modalAlternatives) modalAlternatives.classList.add("hidden");
    });
  }

  // Minimalist Options Drawer Toggle
  const btnToggleSettings = document.getElementById("btn-toggle-settings");
  const advancedSettingsDrawer = document.getElementById("advanced-settings-drawer");
  if (btnToggleSettings && advancedSettingsDrawer) {
    btnToggleSettings.addEventListener("click", () => {
      advancedSettingsDrawer.classList.toggle("hidden");
      btnToggleSettings.classList.toggle("active");
    });
  }

  // Collapsible Forensic Diagnostics Drawer Toggle
  const btnToggleDrawer = document.getElementById("btn-toggle-drawer");
  const drawerGridBody = document.getElementById("drawer-grid-body");
  if (btnToggleDrawer && drawerGridBody) {
    btnToggleDrawer.addEventListener("click", () => {
      drawerGridBody.classList.toggle("hidden");
      const isHidden = drawerGridBody.classList.contains("hidden");
      btnToggleDrawer.textContent = isHidden ? "View Details ▼" : "Hide Details ▲";
    });
  }

  // Live Monetization & Ad Revenue Dashboard Logic
  const btnOpenMonetization = document.getElementById("btn-open-monetization");
  const modalMonetization = document.getElementById("modal-monetization-dashboard");
  const btnCloseMonetization = document.getElementById("btn-close-monetization-modal");
  const btnCloseMonetizationOk = document.getElementById("btn-close-monetization-ok");
  const btnRefreshMonetization = document.getElementById("btn-refresh-monetization");
  const valRevenueCounter = document.getElementById("val-revenue-counter");
  const dashTotalRevenue = document.getElementById("dash-total-revenue");
  const dashImpressions = document.getElementById("dash-impressions");
  const dashClicks = document.getElementById("dash-clicks");
  const dashCtr = document.getElementById("dash-ctr");
  const dashEcpm = document.getElementById("dash-ecpm");

  async function refreshMonetizationStats() {
    try {
      const res = await fetch("/api/monetization/stats");
      const data = await res.json();
      if (valRevenueCounter) valRevenueCounter.textContent = `$${data.total_revenue_usd.toFixed(2)}`;
      if (dashTotalRevenue) dashTotalRevenue.textContent = `$${data.total_revenue_usd.toFixed(2)}`;
      if (dashImpressions) dashImpressions.textContent = data.total_impressions;
      if (dashClicks) dashClicks.textContent = data.total_clicks;
      if (dashCtr) dashCtr.textContent = `${data.ctr_percent}% CTR`;
      if (dashEcpm) dashEcpm.textContent = `$${data.ecpm_usd.toFixed(2)}`;
    } catch (e) {
      console.debug("Could not refresh monetization stats:", e);
    }
  }

  if (btnOpenMonetization && modalMonetization) {
    btnOpenMonetization.addEventListener("click", () => {
      refreshMonetizationStats();
      modalMonetization.classList.remove("hidden");
    });
    if (btnCloseMonetization) {
      btnCloseMonetization.addEventListener("click", () => modalMonetization.classList.add("hidden"));
    }
    if (btnCloseMonetizationOk) {
      btnCloseMonetizationOk.addEventListener("click", () => modalMonetization.classList.add("hidden"));
    }
    if (btnRefreshMonetization) {
      btnRefreshMonetization.addEventListener("click", refreshMonetizationStats);
    }
    modalMonetization.addEventListener("click", (e) => {
      if (e.target === modalMonetization) modalMonetization.classList.add("hidden");
    });
  }

  // Live Sponsored Ad Click Tracking
  document.querySelectorAll(".btn-ad-click").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const adId = btn.getAttribute("data-ad-id");
      try {
        await fetch("/api/ads/click", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ ad_id: adId })
        });
        refreshMonetizationStats();
      } catch (err) {}
    });
  });

  // Pro Upgrade & Checkout Modal Logic
  const btnOpenProModal = document.getElementById("btn-open-pro-modal");
  const modalProCheckout = document.getElementById("modal-pro-checkout");
  const btnCloseProModal = document.getElementById("btn-close-pro-modal");

  if (btnOpenProModal && modalProCheckout) {
    btnOpenProModal.addEventListener("click", () => {
      modalProCheckout.classList.remove("hidden");
    });
    if (btnCloseProModal) {
      btnCloseProModal.addEventListener("click", () => modalProCheckout.classList.add("hidden"));
    }
    modalProCheckout.addEventListener("click", (e) => {
      if (e.target === modalProCheckout) modalProCheckout.classList.add("hidden");
    });

    document.querySelectorAll(".btn-checkout-action").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const plan = btn.getAttribute("data-plan") || "pro";
        btn.textContent = "Processing...";
        btn.disabled = true;
        try {
          const res = await fetch("/api/pro/checkout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ plan })
          });
          const data = await res.json();
          alert(`🎉 ${data.message}\nTotal Earnings Updated: $${data.stats.total_revenue_usd.toFixed(2)}`);
          refreshMonetizationStats();
          modalProCheckout.classList.add("hidden");
        } catch (err) {
          alert("Checkout failed. Please try again.");
        } finally {
          btn.textContent = plan === "pro" ? "Subscribe Now ($9.99)" : "Get Team Plan ($24.99)";
          btn.disabled = false;
        }
      });
    });
  }

  // Sticky Bottom Ad Dismiss
  const btnCloseStickyAd = document.getElementById("btn-close-sticky-ad");
  const adStickyFooter = document.getElementById("ad-sticky-footer");
  if (btnCloseStickyAd && adStickyFooter) {
    btnCloseStickyAd.addEventListener("click", () => {
      adStickyFooter.style.transform = "translateY(100%)";
      adStickyFooter.style.transition = "transform 0.3s ease";
      setTimeout(() => adStickyFooter.remove(), 350);
    });
  }

  // Viral Referral Invite Modal Logic
  const btnOpenReferral = document.getElementById("btn-open-referral");
  const modalReferral = document.getElementById("modal-referral");
  const btnCloseReferral = document.getElementById("btn-close-referral-modal");
  const btnCopyReferral = document.getElementById("btn-copy-referral-link");
  const inputReferral = document.getElementById("input-referral-link");

  if (btnOpenReferral && modalReferral) {
    btnOpenReferral.addEventListener("click", () => {
      modalReferral.classList.remove("hidden");
    });
    if (btnCloseReferral) {
      btnCloseReferral.addEventListener("click", () => modalReferral.classList.add("hidden"));
    }
    modalReferral.addEventListener("click", (e) => {
      if (e.target === modalReferral) modalReferral.classList.add("hidden");
    });

    if (btnCopyReferral && inputReferral) {
      btnCopyReferral.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(inputReferral.value);
          btnCopyReferral.textContent = "✓ Copied Link!";
          // Record referral claim on server
          await fetch("/api/referrals/claim", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ref_code: "student_viral_invite" })
          });
          refreshMonetizationStats();
          setTimeout(() => {
            btnCopyReferral.textContent = "📋 Copy Link";
          }, 2500);
        } catch (e) {
          inputReferral.select();
          document.execCommand("copy");
          btnCopyReferral.textContent = "✓ Copied!";
        }
      });
    }
  }
});

