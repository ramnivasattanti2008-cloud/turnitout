"""
Best-in-Class Intensive Training, Continual SFT & Forensic Calibration Pipeline.
Executes advanced multi-epoch neural fine-tuning on harvested ArXiv, Wikipedia,
and Turnitout-style adversarial parallel corpora.
- 4 full epochs with cosine learning rate scheduling on 12 CPU threads
- Full gradient clipping and validation perplexity tracking
- Comprehensive multi-detector radar calibration across 5 commercial engines
"""

import json
import logging
import os
import random
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import CRAWLED_DATA_DIR, DATASET_FILE, MODEL_DIR
from core.beast_engine import BeastEngine
from core.metrics import split_sentences
from core.turnitout_engine import TurnitoutEngine
from core.watermark_scrubber import WatermarkScrubber
from model.neural_trainer import NeuralSeq2SeqTrainer
from model.trainer import ModelTrainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BestModelTrainer")


def build_academic_parallel_corpus():
    """
    Harvests authentic academic passages from ArXiv and Wikipedia,
    creates AI-robotic counterparts, and generates high-entropy targets
    using the 17-stage Turnitout linguistic engine and Beast Mode.
    """
    logger.info("=== STEP 1: Harvesting and Synthesizing Multi-Domain Academic Corpus ===")
    scrubber = WatermarkScrubber()
    turnitout = TurnitoutEngine(seed=1337)
    beast = BeastEngine()

    raw_academic_texts = []

    # 1. Load ArXiv abstracts
    arxiv_file = CRAWLED_DATA_DIR / "arxiv_samples.json"
    if arxiv_file.exists():
        try:
            with open(arxiv_file, "r", encoding="utf-8") as f:
                arxiv_data = json.load(f)
            for item in arxiv_data:
                txt = item.get("text", "").strip()
                if len(txt.split()) >= 30:
                    raw_academic_texts.append(txt)
        except Exception as e:
            logger.warning(f"Could not load ArXiv samples: {e}")

    # 2. Load Wikipedia technical samples
    wiki_file = CRAWLED_DATA_DIR / "wikipedia_samples.json"
    if wiki_file.exists():
        try:
            with open(wiki_file, "r", encoding="utf-8") as f:
                wiki_data = json.load(f)
            for item in wiki_data[:100]:
                txt = item.get("text", "").strip()
                if len(txt.split()) >= 35:
                    raw_academic_texts.append(txt)
        except Exception as e:
            logger.warning(f"Could not load Wikipedia samples: {e}")

    logger.info(f"Loaded {len(raw_academic_texts)} raw academic/technical excerpts.")

    # Synthetic AI transforms
    ai_cliches = [
        "In today's fast-paced digital world, ",
        "It is important to remember that ",
        "By delving into the multifaceted dimensions of this approach, ",
        "Furthermore, modern algorithms play a crucial role in ",
        "Stands as a testament to the ever-evolving landscape of "
    ]

    new_pairs = []
    for idx, text in enumerate(raw_academic_texts[:60]):
        # Scrub watermarks
        clean_src = scrubber.scrub(text)["clean_text"]
        sentences = split_sentences(clean_src)
        if len(sentences) < 2:
            continue

        short_excerpt = " ".join(sentences[:3])

        # Synthesize robotic AI version
        cliche_opener = ai_cliches[idx % len(ai_cliches)]
        ai_input = f"{cliche_opener}{short_excerpt[0].lower()}{short_excerpt[1:]}"

        # Generate humanized target via Turnitout and Beast pipelines
        t_target = turnitout.process_paragraph(ai_input, intensity=0.85)
        b_res = beast.execute_beast_mode(ai_input, intensity=0.85)
        b_target = b_res.get("humanized_text", t_target)

        new_pairs.append({
            "id": f"sft_best_pair_{idx * 2}",
            "source": "arxiv_wikipedia_sft_harvest",
            "ai_style_input": ai_input,
            "human_target": t_target,
            "word_count": len(t_target.split()),
            "strategy": "turnitout_winnowing_evasion"
        })

        new_pairs.append({
            "id": f"sft_best_pair_{idx * 2 + 1}",
            "source": "arxiv_wikipedia_sft_harvest",
            "ai_style_input": ai_input,
            "human_target": b_target,
            "word_count": len(b_target.split()),
            "strategy": "beast_adversarial_rephrasing"
        })

    # Append to dataset file with deduplication
    existing_data = []
    if DATASET_FILE.exists():
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            existing_data = json.load(f)

    existing_inputs = {item.get("ai_style_input", "").strip() for item in existing_data}
    added = 0
    for p in new_pairs:
        if p["ai_style_input"].strip() not in existing_inputs:
            existing_data.append(p)
            existing_inputs.add(p["ai_style_input"].strip())
            added += 1

    with open(DATASET_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2)

    logger.info(f"Dataset updated with {added} new high-quality academic pairs (Total pairs: {len(existing_data)}).")


def run_best_neural_training():
    """
    Executes intensive 4-epoch continual SFT fine-tuning with AdamW and linear warmup.
    """
    logger.info("=== STEP 2: Running High-Performance 4-Epoch Neural SFT Fine-Tuning ===")
    trainer = NeuralSeq2SeqTrainer(
        base_model_name="google-t5/t5-small",
        dataset_path=DATASET_FILE,
        output_dir=MODEL_DIR / "fine_tuned_t5"
    )

    if not trainer.is_torch_ready():
        logger.error("PyTorch/Transformers not installed. Skipping.")
        return

    # Train across 360 samples for 4 epochs with batch size 6, grad accum 2
    res = trainer.train(
        epochs=4,
        batch_size=6,
        lr=4e-5,
        max_samples=360,
        max_seq_len=96,
        gradient_accumulation_steps=2
    )

    logger.info("=== NEURAL TRAINING COMPLETED ===")
    logger.info(f"Status: {res.get('status')}")
    logger.info(f"Final Train Loss: {res.get('final_train_loss')}")
    logger.info(f"Final Validation Loss: {res.get('final_val_loss')}")
    logger.info(f"Validation Perplexity: {res.get('perplexity')}")


def run_comprehensive_calibration():
    """
    Recalibrates weights across 100 dataset evaluation pairs.
    """
    logger.info("=== STEP 3: Comprehensive Multi-Detector Radar Calibration ===")
    trainer = ModelTrainer(model_dir=MODEL_DIR, dataset_file=DATASET_FILE)
    calibration = trainer.train_and_calibrate(max_eval_pairs=100)

    logger.info("=== CALIBRATION SUMMARY ===")
    logger.info(f"Model Version: {calibration.get('model_version')}")
    logger.info(f"Optimal Rewrite Intensity: {calibration.get('optimal_intensity')}")
    logger.info(f"Average AI Reduction: {calibration.get('avg_ai_reduction_pct')}%")
    logger.info(f"Average Uniqueness: {calibration.get('avg_uniqueness_pct')}%")
    logger.info(f"Turnitin Bypass Rate: {calibration.get('turnitin_bypass_rate')}%")
    logger.info(f"GPTZero Bypass Rate: {calibration.get('gptzero_bypass_rate')}%")
    logger.info(f"CopyLeaks Bypass Rate: {calibration.get('copyleaks_bypass_rate')}%")


if __name__ == "__main__":
    t_start = time.time()
    build_academic_parallel_corpus()
    run_best_neural_training()
    run_comprehensive_calibration()
    elapsed = round(time.time() - t_start, 2)
    logger.info(f"=== BEST-IN-CLASS TRAINING FINISHED IN {elapsed}s ===")
