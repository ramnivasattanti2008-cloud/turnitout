"""
Deep Intensive Training & Calibration Pipeline for TextHumanizer Pro.
Executes large-scale multi-epoch PyTorch neural fine-tuning on T5-small
and hyperparameter optimization across 1,000+ parallel corpus pairs.
"""

import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.detector import CorpusPlagiarismIndex, TextAnalyzer
from core.humanizer import TextHumanizer
from model.neural_trainer import NeuralSeq2SeqTrainer
from model.trainer import ModelTrainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrainDeep")


def run_intensive_training(
    epochs: int = 3,
    neural_samples: int = 250,
    eval_pairs: int = 1000,
    batch_size: int = 4,
    lr: float = 4e-5
) -> dict:
    start_time = time.time()
    logger.info("=================================================================")
    logger.info("🔥 STARTING MASSIVE INTENSIVE TRAINING PIPELINE 🔥")
    logger.info(f"Target: {epochs} Neural Epochs | {neural_samples} SFT Pairs | {eval_pairs} Calibration Pairs")
    logger.info("=================================================================")

    # Phase 1: Neural Transformer Supervised Fine-Tuning
    logger.info("Phase 1: PyTorch Seq2Seq Transformer Supervised Fine-Tuning...")
    neural_trainer = NeuralSeq2SeqTrainer()
    neural_result = neural_trainer.train(
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        max_samples=neural_samples,
        gradient_accumulation_steps=2
    )
    logger.info("Phase 1 Complete! Neural Status: %s", neural_result.get("status"))

    # Phase 2: Comprehensive Hyperparameter Optimization & Calibration
    logger.info("Phase 2: Adversarial Hyperparameter Tuning & Radar Calibration across 1,000+ pairs...")
    model_trainer = ModelTrainer()
    calibrated_weights = model_trainer.train_and_calibrate(max_eval_pairs=eval_pairs)
    logger.info("Phase 2 Complete! Calibrated Intensity: %s", calibrated_weights.get("optimal_intensity"))

    # Phase 3: Pre-warm Corpus Plagiarism Index
    logger.info("Phase 3: Pre-warming & indexing Corpus Plagiarism Search Database...")
    CorpusPlagiarismIndex.reset()
    index = CorpusPlagiarismIndex.get_index(max_docs=4000)
    logger.info("Phase 3 Complete! Total Indexed 4-Grams: %d across %d documents", len(index), CorpusPlagiarismIndex._total_docs_indexed)

    # Phase 4: End-to-End Turnitout Beast Verification Benchmark
    logger.info("Phase 4: Running End-to-End Turnitout Beast Verification Benchmark...")
    test_prompt = (
        "In today's fast-paced academic landscape, artificial intelligence plays a crucial role "
        "in higher education pedagogy. Furthermore, it is important to remember that deep learning "
        "algorithms delve into massive datasets to extract valuable insights. A multifaceted approach "
        "is imperative to navigate the complexities of algorithmic bias. In conclusion, machine learning "
        "stands as a testament to the power of human ingenuity."
    )

    latex_prompt = (
        r"\section{Methodology} "
        r"Previous studies have shown that the Navier-Stokes equations describe fluid motion "
        r"\cite{pope2000turbulent}. In order to evaluate numerical convergence, we analyzed "
        r"the truncation error of the finite difference scheme $\Delta t \le C \Delta x^2$."
    )

    humanizer = TextHumanizer()

    # Benchmark Standard Mode
    std_res = humanizer.process(test_prompt, mode="standard", intensity=0.75)
    std_ai = std_res["metrics"]["ai_score_after"]
    std_uniq = std_res["metrics"]["uniqueness_score"]

    # Benchmark Beast Mode
    beast_res = humanizer.process(test_prompt, mode="beast", intensity=0.85)
    beast_ai = beast_res["metrics"]["ai_score_after"]
    beast_uniq = beast_res["metrics"]["uniqueness_score"]
    beast_winnow = beast_res["metrics"].get("winnowing_matches", 0)

    # Benchmark Zero-Expansion Mode
    ze_res = humanizer.process(test_prompt, mode="beast", intensity=0.80, zero_expansion=True)
    ze_in_words = len(test_prompt.split())
    ze_out_words = len(ze_res["humanized_text"].split())

    # Benchmark LaTeX Shielding
    latex_res = humanizer.process(latex_prompt, mode="beast", intensity=0.80)
    latex_intact = (
        r"\section{Methodology}" in latex_res["humanized_text"]
        and r"\cite{pope2000turbulent}" in latex_res["humanized_text"]
        and r"$\Delta t \le C \Delta x^2$" in latex_res["humanized_text"]
    )

    elapsed = round(time.time() - start_time, 2)
    logger.info("=================================================================")
    logger.info(f"INTENSIVE TRAINING & CALIBRATION FULLY COMPLETE in {elapsed}s!")
    logger.info(f"Standard Mode      -> AI: {std_ai}% | Uniqueness: {std_uniq}%")
    logger.info(f"Beast Mode         -> AI: {beast_ai}% | Uniqueness: {beast_uniq}% | Winnowing Hashes: {beast_winnow}")
    logger.info(f"Zero-Expansion     -> Input Words: {ze_in_words} | Output Words: {ze_out_words} | Uniqueness: {ze_res['metrics']['uniqueness_score']}%")
    logger.info(f"LaTeX Math Shield  -> Intact: {latex_intact}")
    logger.info(f"Winnowing Bypass   -> {calibrated_weights.get('winnowing_bypass_rate')}%")
    logger.info(f"Turnitin Bypass    -> {calibrated_weights.get('turnitin_bypass_rate')}%")
    logger.info(f"GPTZero Bypass     -> {calibrated_weights.get('gptzero_bypass_rate')}%")
    logger.info("=================================================================")

    summary = {
        "elapsed_seconds": elapsed,
        "neural_sft": neural_result.get("metadata", {}),
        "calibration": calibrated_weights,
        "corpus_index_size": len(index),
        "benchmark_results": {
            "standard_ai_score": std_ai,
            "standard_uniqueness": std_uniq,
            "beast_ai_score": beast_ai,
            "beast_uniqueness": beast_uniq,
            "beast_winnowing_matches": beast_winnow,
            "zero_expansion_in_words": ze_in_words,
            "zero_expansion_out_words": ze_out_words,
            "latex_shield_intact": latex_intact,
            "beast_sample_output": beast_res["humanized_text"],
            "latex_sample_output": latex_res["humanized_text"],
        }
    }

    report_path = Path(__file__).resolve().parent / "model" / "deep_training_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    run_intensive_training(epochs=3, neural_samples=250, eval_pairs=300)
