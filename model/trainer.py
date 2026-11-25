"""
Model Training, Calibration, and Hyperparameter Optimization Pipeline.
Calibrates burstiness targets, lexical transition weights, and evaluates
paraphraser performance against empirical human benchmarks and commercial AI radars.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import DATASET_FILE, MODEL_DIR
from core.detector import TextAnalyzer
from core.humanizer import TextHumanizer
from core.metrics import calculate_ngram_overlap
from core.radar import AIRadar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ModelTrainer")


class ModelTrainer:
    """
    Trains and calibrates the humanization engine using collected human corpora
    and parallel evaluation datasets.
    """

    def __init__(self, model_dir: Optional[Path] = None, dataset_file: Optional[Path] = None):
        self.model_dir = model_dir or MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_file = dataset_file or DATASET_FILE
        self.humanizer = TextHumanizer()
        self.analyzer = TextAnalyzer()
        self.radar = AIRadar()

    def train_and_calibrate(self, max_eval_pairs: int = 1000) -> Dict[str, Any]:
        """
        Executes optimization over dataset pairs:
        1. Evaluates baseline AI score of raw samples.
        2. Tunes intensity parameters to maximize AI reduction while minimizing plagiarism overlap.
        3. Evaluates 5-detector radar clearance rates across commercial signatures.
        4. Persists optimized hyperparameter weights and calibration audit.
        """
        if not self.dataset_file.exists():
            from crawler.dataset_builder import DatasetBuilder
            builder = DatasetBuilder(self.dataset_file)
            builder.build_from_crawled_files()

        with open(self.dataset_file, "r", encoding="utf-8") as f:
            pairs = json.load(f)

        logger.info(f"Loaded {len(pairs)} pairs for calibration and training.")

        total_ai_reduction = 0.0
        total_uniqueness = 0.0
        total_eval_samples = 0
        pass_turnitin = 0
        pass_gptzero = 0
        pass_copyleaks = 0
        pass_winnowing = 0

        eval_records: List[Dict[str, Any]] = []

        # 1. Grid search for optimal Beast Mode intensity over representative sample
        candidate_intensities = [0.65, 0.75, 0.85, 0.90]
        intensity_scores: Dict[float, float] = {}

        subset_for_tuning = pairs[:20] if len(pairs) >= 20 else pairs
        for intensity in candidate_intensities:
            sample_score = 0.0
            for item in subset_for_tuning:
                ai_input = item.get("ai_style_input", "")
                res = self.humanizer.process(ai_input, mode="beast", intensity=intensity)
                red = res["metrics"]["ai_reduction"]
                uniq = res["metrics"]["uniqueness_score"]
                win_ok = 100.0 if res["metrics"].get("winnowing_matches", 0) == 0 else 0.0
                sample_score += (red * 0.40) + (uniq * 0.45) + (win_ok * 0.15)
            intensity_scores[intensity] = round(sample_score / max(1, len(subset_for_tuning)), 2)

        best_intensity = max(intensity_scores, key=intensity_scores.get)
        logger.info(f"Calibrated optimal Beast intensity: {best_intensity} (Scores: {intensity_scores})")

        # 2. Comprehensive evaluation run across evaluation pairs
        eval_pairs = pairs[:max_eval_pairs] if len(pairs) > max_eval_pairs else pairs
        logger.info(f"Evaluating Beast + Winnowing humanization across {len(eval_pairs)} pairs...")

        for item in eval_pairs:
            ai_input = item.get("ai_style_input", "")
            human_target = item.get("human_target", "")

            # Run Beast Mode transformation
            res = self.humanizer.process(ai_input, mode="beast", intensity=best_intensity)
            humanized_text = res["humanized_text"]

            ai_reduction = res["metrics"]["ai_reduction"]
            uniqueness = res["metrics"]["uniqueness_score"]
            win_matches = res["metrics"].get("winnowing_matches", 0)
            if win_matches == 0:
                pass_winnowing += 1

            # Overlap with target human text
            human_similarity = calculate_ngram_overlap(humanized_text, human_target, n=3)

            # Check radar clearance
            radar = res.get("radar_after") or self.radar.scan_all_detectors(humanized_text, reference_text=ai_input)
            dets = radar.get("detectors", {})
            if dets.get("turnitin", {}).get("status") == "pass":
                pass_turnitin += 1
            if dets.get("gptzero", {}).get("status") == "pass":
                pass_gptzero += 1
            if dets.get("copyleaks", {}).get("status") == "pass":
                pass_copyleaks += 1

            total_ai_reduction += ai_reduction
            total_uniqueness += uniqueness
            total_eval_samples += 1

            if len(eval_records) < 10:
                eval_records.append({
                    "id": item.get("id"),
                    "before_ai": res["metrics"]["ai_score_before"],
                    "after_ai": res["metrics"]["ai_score_after"],
                    "ai_reduction": ai_reduction,
                    "uniqueness": uniqueness,
                    "winnowing_matches": win_matches,
                    "human_overlap_3gram": human_similarity,
                    "turnitin_score": dets.get("turnitin", {}).get("score", 0.0),
                    "gptzero_score": dets.get("gptzero", {}).get("score", 0.0)
                })

        avg_reduction = round(total_ai_reduction / max(1, total_eval_samples), 1)
        avg_uniqueness = round(total_uniqueness / max(1, total_eval_samples), 1)
        turnitin_rate = round((pass_turnitin / max(1, total_eval_samples)) * 100.0, 1)
        gptzero_rate = round((pass_gptzero / max(1, total_eval_samples)) * 100.0, 1)
        copyleaks_rate = round((pass_copyleaks / max(1, total_eval_samples)) * 100.0, 1)
        winnowing_rate = round((pass_winnowing / max(1, total_eval_samples)) * 100.0, 1)

        # Save model checkpoint and calibration weights
        calibrated_model = {
            "model_version": "2.8.0-turnitout-beast",
            "optimal_intensity": best_intensity,
            "avg_ai_reduction_pct": avg_reduction,
            "avg_uniqueness_pct": avg_uniqueness,
            "winnowing_bypass_rate": winnowing_rate,
            "turnitin_bypass_rate": turnitin_rate,
            "gptzero_bypass_rate": gptzero_rate,
            "copyleaks_bypass_rate": copyleaks_rate,
            "evaluated_pairs": total_eval_samples,
            "dataset_size": len(pairs),
            "status": "calibrated_and_production_ready",
            "eval_records": eval_records
        }

        checkpoint_path = self.model_dir / "calibrated_weights.json"
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(calibrated_model, f, indent=2)

        logger.info(f"Model calibrated and saved to {checkpoint_path}")
        logger.info(f"Avg AI Reduction: {avg_reduction}% | Uniqueness: {avg_uniqueness}% | Turnitin Bypass: {turnitin_rate}%")
        return calibrated_model


if __name__ == "__main__":
    trainer = ModelTrainer()
    results = trainer.train_and_calibrate(max_eval_pairs=100)
    print("Training Results:", json.dumps(results, indent=2))
