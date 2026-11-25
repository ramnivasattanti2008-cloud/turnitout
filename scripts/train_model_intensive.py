"""
Intensive Model Training, SFT Fine-Tuning & Multi-Detector Calibration Script.
Takes all humanizers (Turnitout 17-stage linguistic pipeline, Beast Engine,
Watermark Scrubber, and Adversarial Optimizer) and executes intensive neural
supervised fine-tuning (SFT) and calibration on the T5 transformer model.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import DATASET_FILE, MODEL_DIR
from core.beast_engine import BeastEngine
from core.turnitout_engine import TurnitoutEngine
from core.watermark_scrubber import WatermarkScrubber
from model.neural_trainer import NeuralSeq2SeqTrainer
from model.trainer import ModelTrainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IntensiveTrainer")


def augment_dataset_with_turnitout():
    """
    Synthesizes and appends fresh, high-entropy paired training examples
    using the Turnitout 17-stage linguistic transformation pipeline.
    """
    logger.info("=== STEP 1: Augmenting dataset with Turnitout-style academic pairs ===")
    scrubber = WatermarkScrubber()
    turnitout = TurnitoutEngine(seed=42)
    beast = BeastEngine()

    raw_ai_templates = [
        "It is crucial to remember that artificial intelligence algorithms delve into massive datasets to extract actionable patterns. Furthermore, machine learning plays a pivotal role in modern cybersecurity defenses.",
        "In today's fast-paced digital world, navigating the complexities of distributed systems stands as a testament to engineering innovation. Moreover, adopting a holistic approach is imperative.",
        "It goes without saying that neural networks delve deep into feature representations. In conclusion, this multifaceted strategy paves the way for unprecedented technological advancements.",
        "Furthermore, it is important to note that statistical language models analyze sequential tokens with high probability. This serves as a reminder of the evolving landscape in computer vision.",
        "By delving into the intricate tapestry of modern cloud computing, organizations can harness the power of scalable microservices. Nevertheless, security challenges cannot be overlooked.",
        "It is vital to recognize that empirical data leakage occurs when test distributions contaminate training pipelines. In conclusion, addressing this dilemma is of paramount importance.",
        "In today's competitive environment, email classification systems play a crucial role in preventing credential phishing attacks. Additionally, concept drift threatens classifier stability.",
        "Moreover, adopting a comprehensive framework enables researchers to analyze complex differential equations. This stands as a stepping stone toward robust numerical simulations.",
        "It is important to remember that deep learning models require extensive telemetry data to achieve high accuracy. Ultimately, this paradigm shift reshapes enterprise software architectures.",
        "To sum up, fostering a nuanced understanding of algorithmic bias is essential for equitable machine learning applications. Furthermore, policymakers must navigate these multifaceted challenges."
    ]

    new_pairs = []
    pair_id_counter = 10000

    for i, ai_text in enumerate(raw_ai_templates):
        # Scrub invisible watermarks
        clean_ai = scrubber.scrub(ai_text)["clean_text"]

        # Generate humanized target via Turnitout and Beast pipelines
        t_target = turnitout.process_paragraph(clean_ai, intensity=0.85)
        b_res = beast.execute_beast_mode(clean_ai, intensity=0.85)
        b_target = b_res.get("humanized_text", t_target)

        new_pairs.append({
            "id": f"turnitout_pair_{pair_id_counter + i * 2}",
            "source": "turnitout_synthesis_engine",
            "ai_style_input": clean_ai,
            "human_target": t_target,
            "word_count": len(t_target.split()),
            "strategy": "turnitout_17_stage_pipeline"
        })

        new_pairs.append({
            "id": f"turnitout_pair_{pair_id_counter + i * 2 + 1}",
            "source": "beast_adversarial_synthesis",
            "ai_style_input": clean_ai,
            "human_target": b_target,
            "word_count": len(b_target.split()),
            "strategy": "beast_adversarial_dismantling"
        })

    # Load existing dataset and append
    existing_data = []
    if DATASET_FILE.exists():
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            existing_data = json.load(f)

    existing_inputs = {item.get("ai_style_input", "").strip() for item in existing_data}
    added_count = 0
    for p in new_pairs:
        if p["ai_style_input"].strip() not in existing_inputs:
            existing_data.append(p)
            existing_inputs.add(p["ai_style_input"].strip())
            added_count += 1

    with open(DATASET_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2)

    logger.info(f"Dataset updated: {len(existing_data)} total pairs (+{added_count} new Turnitout pairs added).")


def run_intensive_neural_training():
    """
    Executes supervised fine-tuning (SFT) of the T5 model with high throughput.
    """
    logger.info("=== STEP 2: Running Intensive Supervised Neural Fine-Tuning (SFT) ===")
    trainer = NeuralSeq2SeqTrainer(
        base_model_name="google-t5/t5-small",
        dataset_path=DATASET_FILE,
        output_dir=MODEL_DIR / "fine_tuned_t5"
    )

    if not trainer.is_torch_ready():
        logger.error("PyTorch/Transformers not available for neural training.")
        return

    # Train across 250 high-quality pairs for 3 epochs with batch size 6
    training_res = trainer.train(
        epochs=3,
        batch_size=6,
        lr=5e-5,
        max_samples=250,
        max_seq_len=96,
        gradient_accumulation_steps=2
    )

    logger.info(f"Neural SFT Result: {training_res.get('status')}")
    logger.info(f"Final Train Loss: {training_res.get('final_train_loss')} | Val Loss: {training_res.get('final_val_loss')}")
    logger.info(f"Validation Perplexity: {training_res.get('perplexity')}")


def run_detector_calibration():
    """
    Recalibrates the operational model intensity and hyperparameter weights
    against Turnitin, GPTZero, CopyLeaks, ZeroGPT, and Sapling.
    """
    logger.info("=== STEP 3: Multi-Detector Calibration & Radar Benchmark Audit ===")
    model_trainer = ModelTrainer(model_dir=MODEL_DIR, dataset_file=DATASET_FILE)
    calibration_res = model_trainer.train_and_calibrate(max_eval_pairs=50)

    logger.info("=== CALIBRATION RESULTS ===")
    logger.info(f"Status: {calibration_res.get('status')}")
    logger.info(f"Optimal Rewrite Intensity: {calibration_res.get('optimal_intensity')}")
    logger.info(f"Average AI Reduction: {calibration_res.get('avg_ai_reduction_pct')}%")
    logger.info(f"Average Uniqueness: {calibration_res.get('avg_uniqueness_pct')}%")
    logger.info(f"Turnitin Bypass Rate: {calibration_res.get('turnitin_bypass_rate')}%")
    logger.info(f"GPTZero Bypass Rate: {calibration_res.get('gptzero_bypass_rate')}%")
    logger.info(f"CopyLeaks Bypass Rate: {calibration_res.get('copyleaks_bypass_rate')}%")


if __name__ == "__main__":
    start_total = time.time()
    augment_dataset_with_turnitout()
    run_intensive_neural_training()
    run_detector_calibration()
    total_time = round(time.time() - start_total, 2)
    logger.info(f"=== ALL TRAINING & CALIBRATION COMPLETED IN {total_time}s ===")
