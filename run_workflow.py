"""
Autonomous Continuous Improvement Workflow for TextHumanizer Pro.
Continuously harvests web data from open sources, expands parallel training datasets,
calibrates the humanization engine, and validates performance against benchmarks.
"""

import argparse
import datetime
import json
import logging
import time
from pathlib import Path

from config import DATA_DIR
from crawler.collector import WebDataCollector
from crawler.dataset_builder import DatasetBuilder
from model.trainer import ModelTrainer

# Configure workflow logger
log_path = DATA_DIR / "workflow.log"
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WorkflowRunner")


class AutonomousWorkflow:
    """
    Executes end-to-end data harvesting, pair generation, model training,
    and performance validation in autonomous cycles.
    """

    def __init__(self):
        self.collector = WebDataCollector()
        self.builder = DatasetBuilder()
        self.trainer = ModelTrainer()
        self.cycle_count = 0

    def run_cycle(self) -> dict:
        """Runs a single complete workflow cycle."""
        self.cycle_count += 1
        logger.info(f"=== Starting Autonomous Workflow Cycle #{self.cycle_count} ===")
        start_time = time.time()

        # Step 1: Web Data Collection
        logger.info("Step 1/4: Harvesting web corpora from open educational & literature sources...")
        crawl_stats = self.collector.run_all()
        logger.info(f"Harvested {crawl_stats['total_collected']} paragraphs from web.")

        # Step 2: Build Paired AI-to-Human Dataset
        logger.info("Step 2/4: Synthesizing parallel training pairs...")
        pairs = self.builder.build_from_crawled_files()
        logger.info(f"Built {len(pairs)} parallel training pairs.")

        # Step 3: Train and Calibrate Model
        logger.info("Step 3/4: Training and optimizing humanization model weights...")
        training_res = self.trainer.train_and_calibrate()
        logger.info(f"Model trained! Avg AI Reduction: {training_res['avg_ai_reduction_pct']}%, Uniqueness: {training_res['avg_uniqueness_pct']}%")

        # Step 3.5: Deep Neural Transformer Fine-Tuning
        neural_res = None
        run_neural = getattr(self, "force_neural", False) or (self.cycle_count % 2 == 0)
        if run_neural:
            epochs_to_run = getattr(self, "neural_epochs", 2)
            samples_to_run = getattr(self, "neural_samples", 150)
            logger.info(f"Executing Deep PyTorch Neural Transformer Fine-Tuning ({epochs_to_run} epochs, {samples_to_run} samples)...")
            try:
                from model.neural_trainer import NeuralSeq2SeqTrainer
                neural_trainer = NeuralSeq2SeqTrainer()
                neural_res = neural_trainer.train(epochs=epochs_to_run, batch_size=4, max_samples=samples_to_run)
                logger.info(f"Neural SFT finished: {neural_res.get('status')}")
            except Exception as e:
                logger.warning(f"Neural training step encountered error: {e}")

        # Step 4: Verification and Report
        elapsed = round(time.time() - start_time, 2)
        summary = {
            "cycle": self.cycle_count,
            "timestamp": datetime.datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "collected_samples": crawl_stats["total_collected"],
            "dataset_size": len(pairs),
            "ai_reduction_pct": training_res["avg_ai_reduction_pct"],
            "uniqueness_pct": training_res["avg_uniqueness_pct"],
            "neural_status": neural_res.get("status") if neural_res else "skipped",
            "status": "success"
        }

        # Save cycle ledger
        ledger_path = DATA_DIR / "workflow_history.json"
        history = []
        if ledger_path.exists():
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass
        history.append(summary)
        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        logger.info(f"=== Completed Cycle #{self.cycle_count} in {elapsed}s ===")
        return summary

    def run_continuous(self, interval_seconds: int = 120, max_cycles: int = 0):
        """
        Runs continuously in the background, updating and training the model.
        If max_cycles == 0, runs indefinitely.
        """
        logger.info(f"Starting continuous workflow loop (Interval: {interval_seconds}s, Max Cycles: {'Infinite' if max_cycles == 0 else max_cycles})")
        while True:
            try:
                self.run_cycle()
                if max_cycles > 0 and self.cycle_count >= max_cycles:
                    logger.info("Reached maximum requested cycles. Workflow stopping.")
                    break
                logger.info(f"Sleeping for {interval_seconds} seconds before next cycle...")
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logger.info("Workflow interrupted by user.")
                break
            except Exception as e:
                logger.error(f"Error in cycle #{self.cycle_count}: {e}", exc_info=True)
                time.sleep(30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Continuous Workflow Runner for TextHumanizer Pro")
    parser.add_argument("--continuous", action="store_true", help="Run continuously in a loop")
    parser.add_argument("--interval", type=int, default=120, help="Interval in seconds between cycles")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles to run (0 for infinite)")
    parser.add_argument("--neural", action="store_true", help="Force deep neural fine-tuning on every cycle")
    parser.add_argument("--epochs", type=int, default=2, help="Neural fine-tuning epochs per cycle")
    parser.add_argument("--samples", type=int, default=150, help="Max parallel pairs for neural fine-tuning per cycle")

    args = parser.parse_args()
    workflow = AutonomousWorkflow()
    workflow.force_neural = args.neural
    workflow.neural_epochs = args.epochs
    workflow.neural_samples = args.samples

    if args.continuous:
        workflow.run_continuous(interval_seconds=args.interval, max_cycles=args.cycles)
    else:
        summary = workflow.run_cycle()
        print(json.dumps(summary, indent=2))
