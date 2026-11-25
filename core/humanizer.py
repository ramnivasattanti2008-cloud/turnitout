"""
Core Humanizer & Plagiarism Remover Pipeline.
Coordinates marker eradication, syntactic restructuring, synonym paraphrasing,
burstiness injection, and verification diagnostics.
"""

import re
from typing import Any, Dict, List, Optional, Set

from core.adversarial_optimizer import AdversarialOptimizer
from core.beast_engine import BeastEngine
from core.cleaner import MarkerCleaner
from core.detector import TextAnalyzer
from core.fluency_engine import FluencyEngine
from core.turnitout_engine import TurnitoutEngine
from core.watermark_scrubber import WatermarkScrubber
from core.metrics import calculate_readability, split_sentences, tokenize_words
from core.neural_paraphraser import NeuralParaphraser
from core.radar import AIRadar
from core.semantic_validator import SemanticValidator
from core.synonym_engine import SynonymEngine
from core.syntax_engine import SyntaxEngine


class TextHumanizer:
    """
    State-of-the-art paragraph humanizer and plagiarism remover.
    Bypasses AI detectors and eradicates verbatim plagiarism while preserving core meaning.
    """

    def __init__(self):
        self.cleaner = MarkerCleaner()
        self.syntax_engine = SyntaxEngine()
        self.synonym_engine = SynonymEngine()
        self.analyzer = TextAnalyzer()
        self.validator = SemanticValidator()
        self.fluency = FluencyEngine()
        self.radar = AIRadar()
        self.adversarial_optimizer = AdversarialOptimizer()
        self.beast = BeastEngine()
        self.scrubber = WatermarkScrubber()
        self.turnitout = TurnitoutEngine()
        self._neural = None

    @property
    def neural(self) -> NeuralParaphraser:
        if self._neural is None:
            self._neural = NeuralParaphraser()
        return self._neural

    def process(
        self,
        text: str,
        tone: str = "standard",
        intensity: float = 0.50,
        preserve_keywords: Optional[List[str]] = None,
        adversarial_mode: bool = True,
        mode: str = "standard",
        zero_expansion: bool = False,
        inject_citations: bool = False,
        citation_format: str = "IEEE",
        options: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete multi-stage transformation on input text.
        Supports Beast Mode, Zero-Expansion Mode (1:1 parity), Academic Citations,
        multi-paragraph documents, deep adversarial optimization, and 6-detector verification.
        """
        clean_input = self.scrubber.scrub(text.strip())["clean_text"]
        if not clean_input:
            return {
                "original_text": "",
                "humanized_text": "",
                "before_analysis": {},
                "after_analysis": {},
                "plagiarism_check": {},
                "radar_before": {},
                "radar_after": {},
                "summary": "No text provided."
            }

        # Check for specialized execution modes
        mode_str = (mode or "standard").lower()
        if mode_str in ("beast", "obliterator", "academic"):
            eff_intensity = max(intensity, 0.78) if mode_str == "obliterator" else intensity
            vocab = "scholar" if mode_str in ("beast", "academic", "obliterator") else "standard"
            return self.beast.execute_beast_mode(
                clean_input,
                vocabulary_level=vocab,
                intensity=eff_intensity,
                preserve_keywords=preserve_keywords,
                zero_expansion=zero_expansion,
                inject_citations=inject_citations,
                citation_format=citation_format,
                options=options
            )
        elif mode_str in ("neural", "transformer", "sft"):
            tone = "academic"
            intensity = max(intensity, 0.65)
            sentences = split_sentences(clean_input)
            neural_sentences = []
            for s in sentences:
                if len(s.split()) >= 4:
                    try:
                        p_s = self.neural.paraphrase_sentence(s)
                        neural_sentences.append(p_s if p_s else s)
                    except Exception:
                        neural_sentences.append(s)
                else:
                    neural_sentences.append(s)
            clean_input = " ".join(neural_sentences)

        from core.format_preserver import FormatPreserver

        def humanize_unit(u: str) -> str:
            res = self.process_single_paragraph(
                u,
                tone=tone,
                intensity=intensity,
                preserve_keywords=preserve_keywords,
                adversarial_mode=adversarial_mode
            )
            return res.get("humanized_text", u)

        combined_humanized = FormatPreserver.process_and_reconstruct(clean_input, humanize_unit)
        combined_humanized = self.fluency.polish(combined_humanized)

        before_ai = self.analyzer.compute_ai_score(clean_input)
        after_ai = self.analyzer.compute_ai_score(combined_humanized)
        plag = self.analyzer.check_plagiarism_similarity(clean_input, combined_humanized)
        radar_before = self.radar.scan_all_detectors(clean_input)
        radar_after = self.radar.scan_all_detectors(combined_humanized, reference_text=clean_input)

        return {
            "original_text": clean_input,
            "humanized_text": combined_humanized,
            "tone": tone,
            "intensity": intensity,
            "zero_expansion": zero_expansion,
            "metrics": {
                "ai_score_before": before_ai["ai_probability"],
                "ai_score_after": after_ai["ai_probability"],
                "ai_reduction": max(0.0, round(before_ai["ai_probability"] - after_ai["ai_probability"], 1)),
                "plagiarism_risk": plag["plagiarism_risk_score"],
                "plagiarism_risk_score": plag["plagiarism_risk_score"],
                "uniqueness_score": plag["uniqueness_score"],
                "winnowing_matches": plag.get("winnowing", {}).get("matching_fingerprints", 0),
                "readability_before": before_ai["readability"],
                "readability_after": after_ai["readability"]
            },
            "before_analysis": before_ai,
            "after_analysis": after_ai,
            "sentence_analysis_before": self.analyzer.analyze_sentence_ai(clean_input),
            "sentence_analysis_after": self.analyzer.analyze_sentence_ai(combined_humanized),
            "plagiarism_check": plag,
            "radar_before": radar_before,
            "radar_after": radar_after,
            "summary": f"Humanized formatted document. Uniqueness: {plag['uniqueness_score']}%."
        }

    def transform_text_block(
        self,
        text: str,
        mode: str = "beast",
        tone: str = "academic",
        intensity: float = 0.70,
        preserve_keywords: Optional[List[str]] = None,
        zero_expansion: bool = False,
        options: Optional[Dict[str, bool]] = None
    ) -> str:
        """
        Ultra-fast direct block humanization without redundant forensic/radar re-computation.
        Ideal for document loops (.docx paragraphs, tables).
        """
        mode_str = (mode or "beast").lower()
        if mode_str in ("beast", "academic", "obliterator"):
            eff_intensity = max(intensity, 0.78) if mode_str == "obliterator" else intensity
            return self.beast.transform_single_block(
                text,
                vocabulary_level="scholar",
                intensity=eff_intensity,
                preserve_keywords=preserve_keywords,
                zero_expansion=zero_expansion,
                options=options
            )
        else:
            res = self.process_single_paragraph(
                text,
                tone=tone,
                intensity=intensity,
                preserve_keywords=preserve_keywords
            )
            return res.get("humanized_text", text)

    def process_single_paragraph(
        self,
        clean_input: str,
        tone: str = "standard",
        intensity: float = 0.50,
        preserve_keywords: Optional[List[str]] = None,
        adversarial_mode: bool = True
    ) -> Dict[str, Any]:
        """Processes an individual paragraph with adversarial optimization and fluency polish."""
        if adversarial_mode:
            res = self.adversarial_optimizer.optimize(
                text=clean_input,
                tone=tone,
                intensity=intensity,
                preserve_keywords=preserve_keywords
            )
            # Apply grammar fluency perfection
            res["humanized_text"] = self.fluency.polish(res["humanized_text"])
            kw_map = {}
            masked_txt = res["humanized_text"]
            if preserve_keywords:
                for idx, kw in enumerate(sorted(preserve_keywords, key=len, reverse=True)):
                    if kw and kw.strip():
                        tok = f"XKWPROTECT{idx}X"
                        pat = re.compile(re.escape(kw.strip()), re.IGNORECASE)
                        def _stash(m, _tok=tok, _idx=idx):
                            kw_map[f"{_tok}_{len(kw_map)}"] = m.group(0)
                            return f"{_tok}_{len(kw_map) - 1}"
                        # Use deterministic single replacement key per match
                        def _stash_det(m, _tok=tok):
                            k = f"{_tok}U{len(kw_map)}U"
                            kw_map[k] = m.group(0)
                            return k
                        masked_txt = pat.sub(_stash_det, masked_txt)
            disrupted_txt = self.adversarial_optimizer.disrupt_verbatim_ngrams(clean_input, masked_txt, n=4, max_passes=5)
            for k, orig in kw_map.items():
                disrupted_txt = disrupted_txt.replace(k, orig)
            res["humanized_text"] = disrupted_txt
            after_ai = self.analyzer.compute_ai_score(res["humanized_text"])
            plag = self.analyzer.check_plagiarism_similarity(clean_input, res["humanized_text"])
            if "metrics" in res:
                res["metrics"]["ai_score_after"] = after_ai["ai_probability"]
                res["metrics"]["plagiarism_risk"] = plag["plagiarism_risk_score"]
                res["metrics"]["plagiarism_risk_score"] = plag["plagiarism_risk_score"]
                res["metrics"]["uniqueness_score"] = plag["uniqueness_score"]
            res["plagiarism_check"] = plag
            res["after_analysis"] = after_ai
            res["radar_before"] = self.radar.scan_all_detectors(clean_input)
            res["radar_after"] = self.radar.scan_all_detectors(res["humanized_text"], reference_text=clean_input)
            res["sentence_analysis_before"] = self.analyzer.analyze_sentence_ai(clean_input)
            res["sentence_analysis_after"] = self.analyzer.analyze_sentence_ai(res["humanized_text"])
            return res

        tone_cfg = TONE_MODIFIERS.get(tone, TONE_MODIFIERS["standard"])
        burstiness_target = tone_cfg.get("burstiness_target", 1.4)
        synonym_rate = min(0.65, max(0.20, intensity * tone_cfg.get("synonym_rate", 0.35) * 1.5))
        keywords_set = set(preserve_keywords or [])

        # Step 1: Pre-analysis of original text
        before_ai_analysis = self.analyzer.compute_ai_score(clean_input)

        # Step 2: Stage 1 - AI Cliché & Marker Eradication
        stage1_text = self.cleaner.clean(clean_input)

        # Step 3: Stage 2 - Syntactic Restructuring & Burstiness Injection
        stage2_text = self.syntax_engine.restructure(stage1_text, burstiness_target=burstiness_target)

        # Step 4: Stage 3 - Lexical Paraphrasing & Tone Adaptation
        stage3_text = self.synonym_engine.replace_synonyms(
            stage2_text,
            tone=tone,
            intensity=synonym_rate,
            preserve_keywords=keywords_set
        )

        # Step 5: Stage 4 - Micro-Punctuation Polish & Flow Tuning
        humanized_result = self._polish_text(stage3_text)

        # Step 6: Post-analysis of transformed text
        after_ai_analysis = self.analyzer.compute_ai_score(humanized_result)

        # Step 7: Plagiarism Similarity Check
        plagiarism_report = self.analyzer.check_plagiarism_similarity(clean_input, humanized_result)

        # Calculate improvement metrics
        ai_reduction = round(before_ai_analysis["ai_probability"] - after_ai_analysis["ai_probability"], 1)

        return {
            "original_text": clean_input,
            "humanized_text": humanized_result,
            "tone": tone,
            "intensity": intensity,
            "metrics": {
                "ai_score_before": before_ai_analysis["ai_probability"],
                "ai_score_after": after_ai_analysis["ai_probability"],
                "ai_reduction": max(0.0, ai_reduction),
                "plagiarism_risk": plagiarism_report["plagiarism_risk_score"],
                "uniqueness_score": plagiarism_report["uniqueness_score"],
                "readability_before": before_ai_analysis["readability"],
                "readability_after": after_ai_analysis["readability"]
            },
            "before_analysis": before_ai_analysis,
            "after_analysis": after_ai_analysis,
            "plagiarism_check": plagiarism_report,
            "summary": (
                f"Successfully humanized text. AI likelihood reduced by {ai_reduction}%. "
                f"Uniqueness score: {plagiarism_report['uniqueness_score']}%."
            )
        }

    def get_sentence_alternatives(self, sentence: str, tone: str = "standard") -> List[Dict[str, str]]:
        """Generates 3 distinct humanized alternatives for any chosen sentence."""
        return self.beast.generate_sentence_alternatives(sentence, tone=tone)

    def _polish_text(self, text: str) -> str:
        """Fix capitalization, double spaces, and punctuation anomalies."""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s+([,.;!?])", r"\1", text)
        text = re.sub(r"([.!?])\s*([a-z])", lambda m: m.group(1) + " " + m.group(2).upper(), text)

        # Ensure first letter is capitalized
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        # Ensure sentence ends with punctuation
        if text and text[-1] not in ".!?":
            text += "."

        return text.strip()
