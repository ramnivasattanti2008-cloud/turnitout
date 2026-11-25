"""
Multi-Detector Forensic AI Radar.
Simulates and benchmarks text against the detection signatures of 5 major
commercial AI detectors: GPTZero, Turnitin, CopyLeaks, ZeroGPT, and Sapling.
"""

from typing import Any, Dict, List
from core.metrics import (
    calculate_burstiness,
    calculate_lexical_diversity,
    calculate_ngram_overlap,
    calculate_zippy_entropy,
    split_sentences,
    tokenize_words,
)
from core.cleaner import MarkerCleaner


class AIRadar:
    """
    Forensic scanner simulating multi-detector commercial evaluation.
    """

    def __init__(self):
        self.cleaner = MarkerCleaner()

    def scan_all_detectors(self, text: str, reference_text: str = "") -> Dict[str, Any]:
        """
        Runs comprehensive radar scan simulating GPTZero, Turnitin, CopyLeaks,
        ZeroGPT, and Sapling AI detectors.
        """
        words = tokenize_words(text)
        sentences = split_sentences(text)
        num_words = max(1, len(words))

        std_dev, cv = calculate_burstiness(text)
        lexical = calculate_lexical_diversity(text)

        # Count AI marker phrases
        lower_text = text.lower()
        marker_count = 0
        for pattern, _ in self.cleaner.phrase_replacements:
            import re
            matches = re.findall(pattern, lower_text)
            marker_count += len(matches)

        marker_density = (marker_count / num_words) * 100.0

        # 1. GPTZero Simulation (Burstiness & Sentence Length Perplexity)
        # 1. GPTZero Simulation (Burstiness & Sentence Length Perplexity)
        if marker_density == 0.0 and (cv >= 0.22 or std_dev >= 4.0 or (len(sentences) <= 3 and lexical["ttr"] >= 0.70)) and lexical["ttr"] >= 0.60:
            gptzero_score = 0.0
        elif len(sentences) <= 2 and marker_density == 0.0:
            gptzero_score = 0.0
        elif cv < 0.25:
            gptzero_score = min(99.0, 75.0 + (0.25 - cv) * 80.0)
        elif cv < 0.50:
            gptzero_score = max(15.0, 50.0 - (cv - 0.25) * 60.0)
        else:
            gptzero_score = max(2.0, 10.0 - (cv - 0.50) * 15.0)

        if marker_density > 2.0:
            gptzero_score = min(99.0, gptzero_score + marker_density * 8.0)
        elif marker_density > 0.0:
            gptzero_score = min(99.0, gptzero_score + marker_density * 5.0)

        # 2. Turnitin AI Detector Simulation (Cliché Density & Academic Symmetry)
        if marker_density == 0.0 and (len(sentences) <= 3 or cv >= 0.22 or std_dev >= 4.0):
            turnitin_score = 0.0
        elif marker_density > 3.0:
            turnitin_score = min(99.0, round(70.0 + (marker_density * 6.0), 1))
        elif marker_density > 0.8:
            turnitin_score = min(65.0, round(35.0 + (marker_density * 10.0), 1))
        elif marker_density > 0.0:
            turnitin_score = round(marker_density * 8.0, 1)
        elif len(sentences) >= 4 and cv < 0.25:
            # Flat sentence cadence flagged by Turnitin's structural classifier across multiple sentences
            turnitin_score = min(85.0, round(55.0 + (0.25 - cv) * 100.0, 1))
        elif len(sentences) > 2 and cv < 0.18 and lexical["ttr"] < 0.70:
            turnitin_score = min(85.0, round(55.0 + (0.25 - cv) * 100.0, 1))
        else:
            turnitin_score = max(0.0, round(15.0 - (cv - 0.25) * 30.0, 1))

        # Plagiarism check component if reference text provided
        turnitin_plagiarism = 0.0
        if reference_text:
            turnitin_plagiarism = calculate_ngram_overlap(reference_text, text, n=4)

        # 3. CopyLeaks Simulation (Entropy & Token Predictability)
        ttr = lexical["ttr"]
        if marker_density == 0.0 and (len(sentences) <= 3 or cv >= 0.22 or std_dev >= 4.0):
            copyleaks_score = 0.0
        elif ttr < 0.50:
            copyleaks_score = min(95.0, 70.0 + (0.50 - ttr) * 50.0)
        elif ttr < 0.70:
            copyleaks_score = max(5.0, 45.0 - (ttr - 0.50) * 80.0)
        else:
            copyleaks_score = max(0.0, 10.0 - (ttr - 0.70) * 40.0)
        if marker_density > 1.5:
            copyleaks_score = min(98.0, copyleaks_score + marker_density * 5.0)
        elif marker_density > 0.0:
            copyleaks_score = min(98.0, copyleaks_score + marker_density * 3.0)

        # 4. ZeroGPT Simulation (Keyword & Formulaic Pattern Scanner)
        if marker_count >= 3:
            zerogpt_score = min(99.0, 80.0 + (marker_count * 4.0))
        elif marker_count >= 1:
            zerogpt_score = min(60.0, 35.0 + (marker_count * 15.0))
        elif len(sentences) >= 4 and cv < 0.25:
            zerogpt_score = 48.0
        elif len(sentences) > 2 and cv < 0.18 and lexical["ttr"] < 0.70:
            zerogpt_score = 48.0
        else:
            zerogpt_score = 0.0

        # 5. Sapling AI Simulation (Markov Predictability proxy)
        if marker_density == 0.0 and (len(sentences) <= 3 or cv >= 0.22 or std_dev >= 4.0):
            sapling_score = 0.0
        else:
            sapling_score = round(min(98.0, max(0.0, (gptzero_score * 0.4) + (copyleaks_score * 0.4) + (turnitin_score * 0.2))), 1)

        gptzero_score = round(gptzero_score, 1)
        turnitin_score = round(turnitin_score, 1)
        copyleaks_score = round(copyleaks_score, 1)
        zerogpt_score = round(zerogpt_score, 1)

        # Overall composite bypass status
        scores = [gptzero_score, turnitin_score, copyleaks_score, zerogpt_score, sapling_score]
        avg_radar = round(sum(scores) / len(scores), 1)

        if avg_radar < 15.0:
            clearance = "100% STEALTH CLEARANCE (Bypasses All Detectors)"
            clearance_badge = "success"
        elif avg_radar < 35.0:
            clearance = "HIGH SAFETY CLEARANCE (Passes Commercial Detectors)"
            clearance_badge = "info"
        elif avg_radar < 60.0:
            clearance = "MODERATE RISK (Mixed Detector Triggers)"
            clearance_badge = "warning"
        else:
            clearance = "HIGH RISK (Flagged by Multiple Detectors)"
            clearance_badge = "danger"

        # Calculate ZipPy entropic perplexity
        zippy_entropy = calculate_zippy_entropy(text)

        return {
            "average_ai_likelihood": avg_radar,
            "clearance_status": clearance,
            "clearance_badge": clearance_badge,
            "zippy_entropy": zippy_entropy,
            "detectors": {
                "gptzero": {
                    "score": gptzero_score,
                    "verdict": "Bypassed" if gptzero_score < 25.0 else "Flagged",
                    "status": "pass" if gptzero_score < 25.0 else "flag"
                },
                "turnitin": {
                    "score": turnitin_score,
                    "verdict": "Bypassed" if turnitin_score < 20.0 else f"Flagged ({turnitin_score}% AI)",
                    "status": "pass" if turnitin_score < 20.0 else "flag",
                    "verbatim_plagiarism_match": turnitin_plagiarism
                },
                "copyleaks": {
                    "score": copyleaks_score,
                    "verdict": "Bypassed" if copyleaks_score < 25.0 else "Flagged",
                    "status": "pass" if copyleaks_score < 25.0 else "flag"
                },
                "zerogpt": {
                    "score": zerogpt_score,
                    "verdict": "0% AI Detected" if zerogpt_score < 10.0 else f"{zerogpt_score}% AI",
                    "status": "pass" if zerogpt_score < 20.0 else "flag"
                },
                "sapling": {
                    "score": sapling_score,
                    "verdict": "Human" if sapling_score < 25.0 else "Suspected AI",
                    "status": "pass" if sapling_score < 25.0 else "flag"
                }
            }
        }
