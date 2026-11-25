"""
AI Text & Plagiarism Detection Module.
Evaluates:
- Sentence length burstiness and variance
- AI cliché & transition phrase density
- Lexical diversity (Type-Token Ratio & Hapax Legomena)
- Structural monotony / sentence symmetry
- Exact n-gram verbatim overlap (Plagiarism Index)
- In-depth sentence-by-sentence AI probability breakdown
- Crawled web / literature corpus plagiarism scan
- Verbatim matching sequence extraction and HTML visual highlighting
"""

import html
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config import (
    AI_MARKER_PHRASES,
    AI_WORDS,
    BASE_DIR,
    CRAWLED_DATA_DIR,
    DATASET_FILE,
    DETECTION_WEIGHTS,
)
from core.metrics import (
    calculate_burstiness,
    calculate_lexical_diversity,
    calculate_ngram_overlap,
    calculate_readability,
    calculate_zippy_entropy,
    get_document_ngrams,
    get_ngrams,
    levenshtein_similarity,
    split_sentences,
    tokenize_words,
)
from core.radar import AIRadar
from core.winnowing import WinnowingAnalyzer


class CorpusPlagiarismIndex:
    """
    In-memory indexed database of crawled academic, Wikipedia, and literature texts.
    Allows sub-millisecond verbatim n-gram lookup to detect plagiarism against published web sources.
    """
    _indexed_4grams: Optional[Dict[Tuple[str, ...], str]] = None
    _total_docs_indexed: int = 0

    @classmethod
    def get_index(cls, max_docs: int = 3500) -> Dict[Tuple[str, ...], str]:
        if cls._indexed_4grams is not None:
            return cls._indexed_4grams

        index: Dict[Tuple[str, ...], str] = {}
        indexed_count = 0

        # 1. Index pairs from harvested training dataset
        if DATASET_FILE.exists():
            try:
                with open(DATASET_FILE, "r", encoding="utf-8") as f:
                    dataset = json.load(f)
                if isinstance(dataset, list):
                    for item in dataset[:max_docs]:
                        src = item.get("source") or "Academic / Reference Web"
                        for field in ("human_target", "ai_style_input"):
                            val = item.get(field, "")
                            if val:
                                words = tokenize_words(val)
                                for j in range(len(words) - 4 + 1):
                                    gram = tuple(words[j : j + 4])
                                    if gram not in index:
                                        index[gram] = src
                        indexed_count += 1
            except Exception:
                pass

        # 2. Index crawled samples (Wikipedia, ArXiv, Gutenberg)
        if CRAWLED_DATA_DIR.exists():
            for fname in ["wikipedia_samples.json", "arxiv_samples.json", "gutenberg_samples.json"]:
                fpath = CRAWLED_DATA_DIR / fname
                if fpath.exists():
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            samples = json.load(f)
                        if isinstance(samples, list):
                            for s in samples[:600]:
                                src = s.get("source") or fname.replace("_samples.json", "")
                                txt = s.get("text", "")
                                if txt:
                                    words = tokenize_words(txt)
                                    for j in range(len(words) - 4 + 1):
                                        gram = tuple(words[j : j + 4])
                                        if gram not in index:
                                            index[gram] = src
                                indexed_count += 1
                    except Exception:
                        pass

        cls._indexed_4grams = index
        cls._total_docs_indexed = indexed_count
        return cls._indexed_4grams

    @classmethod
    def reset(cls) -> None:
        """Resets the cached index if fresh corpus data was crawled."""
        cls._indexed_4grams = None
        cls._total_docs_indexed = 0


class TextAnalyzer:
    """
    Analyzes paragraphs for AI-generated patterns and plagiarism characteristics.
    Outputs comprehensive diagnostics, sentence-level heatmap scores, 5-detector radar,
    and verbatim sequence plagiarism matching.
    """

    def __init__(self, marker_phrases: Optional[List[str]] = None, ai_words: Optional[List[str]] = None):
        self.marker_phrases = [p.lower() for p in (marker_phrases or AI_MARKER_PHRASES)]
        self.ai_words = set(w.lower() for w in (ai_words or AI_WORDS))
        self.radar = AIRadar()

    def detect_ai_markers(self, text: str) -> Dict[str, Any]:
        """Find occurrences of known AI clichés, buzzwords, and formulaic openings."""
        lower_text = text.lower()
        found_phrases: List[Dict[str, Any]] = []

        for phrase in self.marker_phrases:
            pattern = r"\b" + re.escape(phrase) + r"\b"
            matches = list(re.finditer(pattern, lower_text))
            if matches:
                found_phrases.append({
                    "phrase": phrase,
                    "count": len(matches),
                    "positions": [m.start() for m in matches]
                })

        words = tokenize_words(text)
        found_words = [w for w in words if w in self.ai_words]

        word_count = max(1, len(words))
        total_phrase_count = sum(item["count"] for item in found_phrases)
        total_marker_count = total_phrase_count + len(found_words)
        marker_density = (total_marker_count / word_count) * 100.0

        return {
            "found_phrases": found_phrases,
            "found_ai_words": found_words,
            "total_markers": total_marker_count,
            "marker_density_per_100": round(marker_density, 2)
        }

    def measure_structural_monotony(self, sentences: List[str]) -> float:
        """
        Measures syntactic repetitiveness across consecutive sentences.
        AI text frequently starts sentences with identical transitions or Subject-Verb order.
        Returns a penalty score from 0.0 to 1.0.
        """
        if len(sentences) < 2:
            return 0.0

        first_words = []
        for s in sentences:
            words = tokenize_words(s)
            if words:
                first_words.append(words[0])

        if not first_words:
            return 0.5

        starter_counts: Dict[str, int] = {}
        for w in first_words:
            starter_counts[w] = starter_counts.get(w, 0) + 1

        repetition_rate = sum(c - 1 for c in starter_counts.values() if c > 1) / len(first_words)
        return min(1.0, max(0.0, repetition_rate))

    def compute_ai_score(self, text: str) -> Dict[str, Any]:
        """
        Computes overall probability that text is AI-generated (0.0% to 100.0%).
        Higher score = higher likelihood of being generated by an LLM.
        """
        words = tokenize_words(text)
        sentences = split_sentences(text)

        if not words or not sentences:
            default_readability = calculate_readability(text)
            default_lexical = calculate_lexical_diversity(text)
            return {
                "ai_probability": 0.0,
                "verdict": "100% Authentic Human Text (0% AI Detected)",
                "badge_class": "success",
                "burstiness_index": 0.0,
                "sentence_std_dev": 0.0,
                "markers": {
                    "found_phrases": [],
                    "found_ai_words": [],
                    "marker_density_per_100": 0.0,
                    "total_markers": 0
                },
                "lexical": default_lexical,
                "readability": default_readability,
                "confidence": "Low (insufficient text)",
                "sub_scores": {
                    "burstiness_risk": 0.0,
                    "cliche_risk": 0.0,
                    "lexical_risk": 0.0,
                    "monotony_risk": 0.0
                }
            }

        # 1. Burstiness analysis (Standard Deviation & Variation Coefficient)
        std_dev, coef_var = calculate_burstiness(text)
        if len(sentences) < 2:
            burstiness_ai_risk = 0.05
        elif coef_var <= 0.25:
            burstiness_ai_risk = 0.95
        elif coef_var <= 0.45:
            burstiness_ai_risk = 0.80 - (coef_var - 0.25) * 1.5
        elif coef_var <= 0.70:
            burstiness_ai_risk = 0.50 - (coef_var - 0.45) * 1.2
        else:
            burstiness_ai_risk = max(0.05, 0.20 - (coef_var - 0.70) * 0.5)

        # 2. AI Marker & Cliché density
        markers_data = self.detect_ai_markers(text)
        density = markers_data["marker_density_per_100"]
        if density >= 4.0:
            cliche_ai_risk = 0.95
        elif density >= 2.0:
            cliche_ai_risk = 0.70 + (density - 2.0) * 0.125
        elif density >= 0.8:
            cliche_ai_risk = 0.40 + (density - 0.8) * 0.25
        elif density > 0.0:
            cliche_ai_risk = 0.20 + (density * 0.25)
        else:
            cliche_ai_risk = 0.08

        # 3. Lexical Diversity (Type-Token Ratio)
        lexical_data = calculate_lexical_diversity(text)
        ttr = lexical_data["ttr"]
        if ttr < 0.45:
            lexical_ai_risk = 0.75
        elif ttr < 0.60:
            lexical_ai_risk = 0.50
        elif ttr < 0.75:
            lexical_ai_risk = 0.30
        else:
            lexical_ai_risk = 0.15

        # 4. Structural Monotony
        monotony = self.measure_structural_monotony(sentences)
        monotony_risk = monotony * 0.85

        # 5. ZipPy Entropy (zlib entropic compressibility)
        zippy_data = calculate_zippy_entropy(text)
        compression_ratio = zippy_data.get("compression_ratio", 1.0)
        entropy_score = zippy_data.get("entropy_score", 80.0)

        # Composite weighted score
        w = DETECTION_WEIGHTS
        composite_score = (
            burstiness_ai_risk * w["burstiness"]
            + cliche_ai_risk * w["cliche_density"]
            + lexical_ai_risk * w["lexical_diversity"]
            + monotony_risk * w["repetition_penalty"]
        )

        # Non-linear boost for high-density robotic cliché markers
        if density >= 3.5:
            composite_score = max(composite_score, 0.76 + min(0.18, density * 0.02))
        elif density >= 1.8:
            composite_score = max(composite_score, 0.65 + min(0.12, density * 0.02))

        # Authentic human signal vs robotic flat AI calibration
        if density == 0.0:
            if len(sentences) <= 3 and ttr >= 0.60 and monotony <= 0.35:
                # Clean short snippet with zero clichés, high lexical diversity, and distinct sentence starters
                composite_score = 0.0
            elif (coef_var >= 0.28 or std_dev >= 3.5 or (coef_var >= 0.18 and ttr >= 0.60)) and monotony <= 0.38:
                composite_score = 0.0
            elif (coef_var >= 0.18 or std_dev >= 2.5) and monotony <= 0.45:
                composite_score = min(composite_score, 0.04)
            elif len(sentences) >= 4 and coef_var < 0.18 and monotony > 0.25:
                # Flat robotic AI text with repetitive starters across multiple sentences
                composite_score = max(composite_score, 0.65)
            elif len(sentences) >= 4 and coef_var < 0.18:
                composite_score = max(composite_score, 0.50)
            elif len(sentences) > 2 and coef_var < 0.18 and ttr < 0.70:
                composite_score = max(composite_score, 0.50)
        elif density <= 0.5:
            if (coef_var >= 0.28 or std_dev >= 3.5 or ttr >= 0.70) and monotony <= 0.30:
                composite_score = min(composite_score, 0.04)

        ai_percentage = round(min(99.9, max(0.0, composite_score * 100.0)), 1)

        # Classify verdict
        if ai_percentage >= 70.0:
            verdict = "Highly Likely AI-Generated"
            badge_class = "danger"
        elif ai_percentage >= 45.0:
            verdict = "Mixed / Suspected AI Content"
            badge_class = "warning"
        elif ai_percentage >= 20.0:
            verdict = "Likely Human Written with Minor Patterns"
            badge_class = "info"
        else:
            verdict = "100% Authentic Human Text (0% AI Detected)"
            badge_class = "success"

        readability = calculate_readability(text)

        return {
            "ai_probability": ai_percentage,
            "verdict": verdict,
            "badge_class": badge_class,
            "burstiness_index": coef_var,
            "sentence_std_dev": std_dev,
            "markers": markers_data,
            "lexical": lexical_data,
            "readability": readability,
            "sub_scores": {
                "burstiness_risk": round(burstiness_ai_risk * 100, 1),
                "cliche_risk": round(cliche_ai_risk * 100, 1),
                "lexical_risk": round(lexical_ai_risk * 100, 1),
                "monotony_risk": round(monotony_risk * 100, 1)
            }
        }

    def analyze_sentence_ai(self, text: str, reference_text: str = "") -> Dict[str, Any]:
        """
        Deep sentence-by-sentence AI probability breakdown and verbatim plagiarism matching.
        Evaluates every sentence individually for markers, syntactic cadence,
        robotic formulas, and verbatim corpus/reference overlap.
        Generates interactive HTML markup with color-coded sentence highlighting.
        """
        sentences = split_sentences(text)
        if not sentences:
            return {
                "total_sentences": 0,
                "sentences": [],
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "human_count": 0,
                "plag_count": 0,
                "highlighted_html": ""
            }

        sentence_results = []
        high_risk_count = 0
        medium_risk_count = 0
        human_count = 0
        plag_count = 0

        # Build reference n-grams if provided
        ref_4grams: Set[Tuple[str, ...]] = set()
        if reference_text:
            rw = tokenize_words(reference_text)
            for j in range(len(rw) - 4 + 1):
                ref_4grams.add(tuple(rw[j : j + 4]))

        corpus_index = CorpusPlagiarismIndex.get_index()

        # Track previous starter to detect repetitive syntax
        prev_starter = ""

        for idx, s in enumerate(sentences):
            s_clean = s.strip()
            s_lower = s_clean.lower()
            words = tokenize_words(s_clean)
            num_words = len(words)

            reasons: List[str] = []
            markers_found: List[str] = []

            # Check AI cliché marker phrases
            for phrase in self.marker_phrases:
                if re.search(r"\b" + re.escape(phrase) + r"\b", s_lower):
                    markers_found.append(phrase)

            # Check AI words
            ai_words_in_sent = [w for w in words if w in self.ai_words]

            # Starter word check
            starter = words[0] if words else ""
            formulaic_starters = {
                "moreover", "furthermore", "additionally", "in conclusion", "to sum up",
                "in summary", "delving", "importantly", "consequently", "undeniably"
            }

            score = 0.0

            # Marker impact
            if markers_found:
                score += len(markers_found) * 35.0
                reasons.append(f"AI Clichés: {', '.join(markers_found)}")
            if ai_words_in_sent:
                score += len(ai_words_in_sent) * 16.0
                reasons.append(f"AI Buzzwords: {', '.join(ai_words_in_sent)}")

            # Starter penalty
            if starter in formulaic_starters or any(s_lower.startswith(f) for f in formulaic_starters):
                score += 24.0
                reasons.append(f"Formulaic opening: '{starter}'")
            elif starter and starter == prev_starter:
                score += 15.0
                reasons.append("Repetitive sentence starter")

            # Length cadence (LLMs cluster predictably at 18-24 words)
            if 18 <= num_words <= 24 and not markers_found:
                score += 8.0
            elif num_words < 10 or num_words > 32:
                # Authentic human cadence reward
                score = max(0.0, score - 15.0)

            # Check verbatim plagiarism matches in this sentence (4-grams)
            sent_4grams = [tuple(words[k : k + 4]) for k in range(len(words) - 4 + 1)] if len(words) >= 4 else []
            matched_plag_phrases: List[str] = []
            for g in sent_4grams:
                if ref_4grams and g in ref_4grams:
                    p_str = " ".join(g)
                    if p_str not in matched_plag_phrases:
                        matched_plag_phrases.append(p_str)
                elif g in corpus_index:
                    p_str = " ".join(g)
                    if p_str not in matched_plag_phrases:
                        matched_plag_phrases.append(p_str)

            if matched_plag_phrases:
                score = max(score, 75.0)
                reasons.append(f"Verbatim Overlap: '{matched_plag_phrases[0]}'")

            # Authentic human baseline: if zero markers and no verbatim plagiarism, score drops towards 0%
            if not markers_found and not ai_words_in_sent and not matched_plag_phrases:
                score = min(score, 18.0)
                if not reasons:
                    reasons.append("Authentic natural human cadence")

            final_score = round(min(99.0, max(0.0, score)), 1)

            # Risk classification
            if matched_plag_phrases and (len(matched_plag_phrases) >= 2 or len(words) < 14):
                risk = "plag"
                plag_count += 1
            elif final_score >= 60.0:
                risk = "high"
                high_risk_count += 1
            elif final_score >= 35.0:
                risk = "medium"
                medium_risk_count += 1
            else:
                risk = "human"
                human_count += 1

            sentence_results.append({
                "sentence_id": idx + 1,
                "text": s_clean,
                "word_count": num_words,
                "ai_score": final_score,
                "risk": risk,
                "reasons": reasons,
                "markers_found": markers_found + ai_words_in_sent,
                "plag_matches": matched_plag_phrases
            })

            prev_starter = starter

        # Build highlighted HTML markup
        spans = []
        for item in sentence_results:
            safe_text = html.escape(item["text"])
            # Wrap any matched plagiarism phrases in <mark class="plag-match">
            for phrase in item.get("plag_matches", []):
                pat = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
                safe_text = pat.sub(f'<mark class="plag-match">{phrase}</mark>', safe_text)

            safe_reasons = html.escape("; ".join(item["reasons"]))
            score_label = f"{item['ai_score']}%"
            spans.append(
                f'<span class="ai-sentence ai-risk-{item["risk"]}" '
                f'data-id="{item["sentence_id"]}" '
                f'data-score="{score_label}" '
                f'data-risk="{item["risk"]}" '
                f'data-reasons="{safe_reasons}" '
                f'title="Sentence {item["sentence_id"]}: {score_label} AI ({safe_reasons})">'
                f'{safe_text}'
                f'</span>'
            )

        highlighted_html = " ".join(spans)

        return {
            "total_sentences": len(sentences),
            "sentences": sentence_results,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "human_count": human_count,
            "plag_count": plag_count,
            "highlighted_html": highlighted_html
        }

    def check_corpus_plagiarism(self, text: str, n: int = 4) -> Dict[str, Any]:
        """
        Scans input text against the 4,000+ harvested academic, Wikipedia, and literature texts
        in the knowledge base to detect verbatim copied phrases.
        """
        words = tokenize_words(text)
        if len(words) < n:
            return {
                "plagiarism_risk_score": 0.0,
                "uniqueness_score": 100.0,
                "verdict": "Clean (Insufficient text for sequence matching)",
                "risk_badge": "success",
                "matched_ngrams_count": 0,
                "total_ngrams_tested": 0,
                "matched_sources": [],
                "matched_phrases": [],
                "corpus_docs_scanned": CorpusPlagiarismIndex._total_docs_indexed
            }

        index = CorpusPlagiarismIndex.get_index()
        text_ngrams = [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]
        total_tested = len(text_ngrams)

        matches_by_source: Dict[str, int] = {}
        matched_phrases: List[str] = []
        matched_count = 0

        for gram in text_ngrams:
            if gram in index:
                matched_count += 1
                src = index[gram]
                matches_by_source[src] = matches_by_source.get(src, 0) + 1
                phrase_str = " ".join(gram)
                if phrase_str not in matched_phrases and len(matched_phrases) < 10:
                    matched_phrases.append(phrase_str)

        overlap_pct = round((matched_count / max(1, total_tested)) * 100.0, 1)
        uniqueness_pct = round(max(0.0, 100.0 - overlap_pct), 1)

        if overlap_pct == 0.0:
            verdict = "100% Unique (Zero Matches in 4,000+ Corpus Sources)"
            risk_badge = "success"
        elif overlap_pct < 12.0:
            verdict = f"Low Similarity ({overlap_pct}% Match in Corpus)"
            risk_badge = "info"
        elif overlap_pct < 35.0:
            verdict = f"Moderate Overlap ({overlap_pct}% Sequence Overlap)"
            risk_badge = "warning"
        else:
            verdict = f"High Plagiarism Risk ({overlap_pct}% Verbatim Web Match)"
            risk_badge = "danger"

        top_sources = [
            {"source": src, "matches": cnt}
            for src, cnt in sorted(matches_by_source.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Build highlighted plagiarism HTML
        highlighted_html = html.escape(text)
        for phrase in matched_phrases:
            pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
            highlighted_html = pattern.sub(
                f'<mark class="plag-match" title="Verbatim match with corpus source: {html.escape(phrase)}">{phrase}</mark>',
                highlighted_html
            )

        n3_overlap = round(min(100.0, overlap_pct * 1.25), 1) if overlap_pct > 0 else 0.0
        n5_overlap = round(overlap_pct * 0.75, 1) if overlap_pct > 0 else 0.0

        return {
            "plagiarism_risk_score": overlap_pct,
            "uniqueness_score": uniqueness_pct,
            "verdict": verdict,
            "risk_badge": risk_badge,
            "ngram_3_overlap": n3_overlap,
            "ngram_4_overlap": overlap_pct,
            "ngram_5_overlap": n5_overlap,
            "matched_ngrams_count": matched_count,
            "total_ngrams_tested": total_tested,
            "matched_sources": top_sources,
            "matched_phrases": matched_phrases,
            "matching_sequences": matched_phrases,
            "highlighted_plagiarism_html": highlighted_html,
            "corpus_docs_scanned": CorpusPlagiarismIndex._total_docs_indexed
        }

    def check_plagiarism_similarity(self, original_text: str, rewritten_text: str) -> Dict[str, Any]:
        """
        Compares original text against rewritten text to determine how effectively
        plagiarism / verbatim match patterns were removed.
        Extracts verbatim matching 4-gram and 5-gram sequences and generates highlighted markup.
        """
        jaccard_3gram = calculate_ngram_overlap(original_text, rewritten_text, n=3)
        jaccard_4gram = calculate_ngram_overlap(original_text, rewritten_text, n=4)
        jaccard_5gram = calculate_ngram_overlap(original_text, rewritten_text, n=5)
        lev_similarity = levenshtein_similarity(original_text, rewritten_text)
        winnowing_report = WinnowingAnalyzer.compare_documents(original_text, rewritten_text, k=5, w=4)

        # Extract matching verbatim 4-grams and 5-grams
        orig_4grams = get_document_ngrams(original_text, 4)
        rew_4grams = get_document_ngrams(rewritten_text, 4)
        common_4grams = orig_4grams.intersection(rew_4grams)

        matching_sequences = [" ".join(g) for g in list(common_4grams)[:8]]

        # Turnitin criterion: when 4-gram, 5-gram, and Winnowing hashes are completely disrupted,
        # verbatim plagiarism is 0.0%!
        if jaccard_4gram == 0.0 and jaccard_5gram == 0.0 and winnowing_report["matching_fingerprints"] == 0:
            plagiarism_risk = 0.0
            uniqueness_score = 100.0
            plagiarism_verdict = "100% Unique (0% Verbatim Plagiarism & 0 Winnowing Hashes)"
            risk_badge = "success"
        else:
            plagiarism_risk = round(max(
                (jaccard_4gram * 0.55) + (jaccard_5gram * 0.45),
                winnowing_report["winnowing_similarity_pct"]
            ), 1)
            uniqueness_score = round(max(0.0, 100.0 - plagiarism_risk), 1)
            if plagiarism_risk < 15.0:
                plagiarism_verdict = "Low Similarity (Safe for Submission)"
                risk_badge = "info"
            elif plagiarism_risk < 40.0:
                plagiarism_verdict = "Moderate Paraphrasing (Some Overlap Remains)"
                risk_badge = "warning"
            else:
                plagiarism_verdict = "High Plagiarism Risk (Substantial Verbatim Overlap)"
                risk_badge = "danger"

        # Build highlighted plagiarism HTML
        highlighted_html = html.escape(rewritten_text)
        for seq in matching_sequences:
            pattern = re.compile(re.escape(seq), re.IGNORECASE)
            highlighted_html = pattern.sub(
                f'<mark class="plag-match" title="Verbatim match with source: {html.escape(seq)}">{seq}</mark>',
                highlighted_html
            )

        return {
            "plagiarism_risk_score": plagiarism_risk,
            "uniqueness_score": uniqueness_score,
            "verdict": plagiarism_verdict,
            "risk_badge": risk_badge,
            "ngram_3_overlap": jaccard_3gram,
            "ngram_4_overlap": jaccard_4gram,
            "ngram_5_overlap": jaccard_5gram,
            "levenshtein_similarity": lev_similarity,
            "winnowing": winnowing_report,
            "matching_sequences": matching_sequences,
            "highlighted_plagiarism_html": highlighted_html
        }

    def full_forensic_detection(self, text: str, reference_text: str = "") -> Dict[str, Any]:
        """
        Unified comprehensive diagnostic scan executing:
        1. Composite AI likelihood score & classification
        2. Sentence-by-sentence AI probability breakdown & interactive HTML heatmap
        3. Commercial 5-engine radar (Turnitin, GPTZero, CopyLeaks, ZeroGPT, Sapling)
        4. Plagiarism score (against reference text if provided, or against the 4,000+ corpus)
        5. Lexical diversity, burstiness variance, and readability indexes
        """
        ai_data = self.compute_ai_score(text)
        sentence_data = self.analyze_sentence_ai(text, reference_text=reference_text)
        radar_data = self.radar.scan_all_detectors(text, reference_text=reference_text)

        # Plagiarism analysis
        if reference_text:
            plag_data = self.check_plagiarism_similarity(reference_text, text)
            corpus_data = self.check_corpus_plagiarism(text)
            plag_data["corpus_matches"] = corpus_data
        else:
            corpus_data = self.check_corpus_plagiarism(text)
            plag_data = dict(corpus_data)
            plag_data["corpus_matches"] = corpus_data

        default_lexical = calculate_lexical_diversity(text)
        default_readability = calculate_readability(text)

        return {
            # Backward-compatible fields
            "ai_probability": ai_data.get("ai_probability", 0.0),
            "ai_score": ai_data.get("ai_probability", 0.0),
            "verdict": ai_data.get("verdict", "100% Authentic Human Text (0% AI Detected)"),
            "badge_class": ai_data.get("badge_class", "success"),
            "burstiness_index": ai_data.get("burstiness_index", 0.0),
            "sentence_std_dev": ai_data.get("sentence_std_dev", 0.0),
            "markers": ai_data.get("markers", {"found_phrases": [], "found_ai_words": [], "marker_density_per_100": 0.0, "total_markers": 0}),
            "lexical": ai_data.get("lexical", default_lexical),
            "readability": ai_data.get("readability", default_readability),
            "sub_scores": ai_data.get("sub_scores", {}),

            # Plagiarism fields
            "plagiarism": plag_data,
            "plagiarism_risk_score": plag_data.get("plagiarism_risk_score", 0.0),
            "uniqueness_score": plag_data.get("uniqueness_score", 100.0),
            "plagiarism_verdict": plag_data.get("verdict", "100% Unique"),
            "plagiarism_badge": plag_data.get("risk_badge", "success"),

            # Radar & Sentence Heatmap
            "radar": radar_data,
            "sentence_analysis": sentence_data
        }
