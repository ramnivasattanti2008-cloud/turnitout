"""
PyTorch Neural Fine-Tuning Engine for TextHumanizer Pro.
Performs supervised fine-tuning of Seq2Seq transformer models (google-t5/t5-small)
on harvested parallel AI-to-Human corpora to specialize weights for humanization and anti-plagiarism.
Includes:
- Incremental continual training from existing checkpoints
- Multi-epoch supervised training with gradient accumulation
- Learning rate scheduling with linear warmup and decay
- Validation loss and perplexity tracking
- Benchmark test inference verification
"""

import json
import logging
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import BASE_DIR, DATASET_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NeuralTrainer")

OUTPUT_DIR = BASE_DIR / "model" / "fine_tuned_t5"


class NeuralSeq2SeqTrainer:
    """
    Trains and fine-tunes T5 seq2seq models with PyTorch on humanization datasets.
    Supports incremental continuous learning, validation tracking, and perplexity evaluation.
    """

    def __init__(
        self,
        base_model_name: str = "google-t5/t5-small",
        dataset_path: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ):
        self.base_model_name = base_model_name
        self.dataset_path = dataset_path or DATASET_FILE
        self.output_dir = output_dir or OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def is_torch_ready(self) -> bool:
        """Checks if PyTorch and Transformers are available."""
        try:
            import torch
            import transformers
            return True
        except ImportError:
            return False

    def load_dataset(
        self,
        max_samples: int = 500,
        val_split: float = 0.10
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Loads paired training samples from dataset file, cleans entries,
        and splits into training and validation sets.
        """
        if not self.dataset_path.exists():
            logger.error(f"Dataset file {self.dataset_path} does not exist.")
            return [], []

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        valid_items = []
        for item in data:
            ai_inp = item.get("ai_style_input", "").strip()
            target = item.get("human_target", "").strip()
            if ai_inp and target and len(ai_inp.split()) >= 8 and len(target.split()) >= 8:
                valid_items.append({
                    "input_text": f"humanize: {ai_inp}",
                    "target_text": target
                })

        random.seed(42)
        if len(valid_items) > max_samples:
            sampled_items = random.sample(valid_items, max_samples)
        else:
            sampled_items = list(valid_items)
            random.shuffle(sampled_items)

        val_size = max(4, int(len(sampled_items) * val_split))
        val_pairs = sampled_items[:val_size]
        train_pairs = sampled_items[val_size:]

        return train_pairs, val_pairs

    def train(
        self,
        epochs: int = 3,
        batch_size: int = 4,
        lr: float = 4e-5,
        max_samples: int = 250,
        max_seq_len: int = 128,
        gradient_accumulation_steps: int = 2
    ) -> Dict[str, Any]:
        """
        Executes intensive, high-quality supervised fine-tuning on CPU/GPU.
        Continuously adapts attention heads and embeddings to paraphrase patterns and saves checkpoint.
        """
        if not self.is_torch_ready():
            logger.warning("PyTorch/Transformers not installed. Skipping neural fine-tuning.")
            return {"status": "skipped", "reason": "torch_not_installed"}

        import torch
        from transformers import (
            AutoModelForSeq2SeqLM,
            AutoTokenizer,
            get_linear_schedule_with_warmup,
        )

        # Optimize thread pool for multi-core processors
        if hasattr(torch, "set_num_threads"):
            optimal_threads = min(12, max(4, (os.cpu_count() or 4) - 1))
            torch.set_num_threads(optimal_threads)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Starting Intensive Neural SFT on device: {device} (Threads: {torch.get_num_threads()})")

        train_pairs, val_pairs = self.load_dataset(max_samples=max_samples)
        if not train_pairs:
            logger.warning("No pairs loaded for neural fine-tuning.")
            return {"status": "skipped", "reason": "empty_dataset"}

        logger.info(f"Loaded {len(train_pairs)} training pairs and {len(val_pairs)} validation pairs.")

        # Continual learning: load previous checkpoint if available, else base model
        if (self.output_dir / "config.json").exists():
            model_source = str(self.output_dir)
            logger.info(f"Loading existing checkpoint for continual fine-tuning from: {model_source}")
        else:
            model_source = self.base_model_name
            logger.info(f"Loading base pre-trained model: {model_source}")

        tokenizer = AutoTokenizer.from_pretrained(model_source)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_source).to(device)

        # Prepare optimizer and scheduler
        num_update_steps_per_epoch = math.ceil(len(train_pairs) / (batch_size * gradient_accumulation_steps))
        max_train_steps = epochs * num_update_steps_per_epoch
        warmup_steps = int(max_train_steps * 0.1)

        optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
        lr_scheduler = get_linear_schedule_with_warmup(
            optimizer=optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=max_train_steps
        )

        start_time = time.time()
        step_count = 0
        epoch_history = []
        best_val_loss = float("inf")

        for epoch in range(epochs):
            model.train()
            total_train_loss = 0.0
            epoch_steps = 0
            optimizer.zero_grad()

            logger.info(f"=== Epoch {epoch + 1}/{epochs} (Steps per epoch: ~{num_update_steps_per_epoch}) ===")

            for i in range(0, len(train_pairs), batch_size):
                batch_pairs = train_pairs[i : i + batch_size]
                inputs = [p["input_text"] for p in batch_pairs]
                targets = [p["target_text"] for p in batch_pairs]

                input_enc = tokenizer(
                    inputs,
                    padding=True,
                    truncation=True,
                    max_length=max_seq_len,
                    return_tensors="pt"
                ).to(device)

                target_enc = tokenizer(
                    text_target=targets,
                    padding=True,
                    truncation=True,
                    max_length=max_seq_len,
                    return_tensors="pt"
                ).to(device)

                labels = target_enc["input_ids"]
                labels[labels == tokenizer.pad_token_id] = -100

                outputs = model(
                    input_ids=input_enc["input_ids"],
                    attention_mask=input_enc["attention_mask"],
                    labels=labels
                )

                loss = outputs.loss / gradient_accumulation_steps
                loss.backward()

                total_train_loss += outputs.loss.item()
                epoch_steps += 1

                if epoch_steps % gradient_accumulation_steps == 0 or (i + batch_size >= len(train_pairs)):
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()
                    lr_scheduler.step()
                    optimizer.zero_grad()
                    step_count += 1

                    if step_count % 10 == 0:
                        cur_loss = total_train_loss / epoch_steps
                        cur_lr = lr_scheduler.get_last_lr()[0]
                        logger.info(f"Step {step_count}/{max_train_steps} | Loss: {cur_loss:.4f} | LR: {cur_lr:.2e}")

            avg_epoch_train_loss = round(total_train_loss / max(1, epoch_steps), 4)

            # Evaluate on Validation Set
            model.eval()
            total_val_loss = 0.0
            val_steps = 0
            with torch.no_grad():
                for j in range(0, len(val_pairs), batch_size):
                    val_batch = val_pairs[j : j + batch_size]
                    v_inputs = [p["input_text"] for p in val_batch]
                    v_targets = [p["target_text"] for p in val_batch]

                    v_in_enc = tokenizer(
                        v_inputs,
                        padding=True,
                        truncation=True,
                        max_length=max_seq_len,
                        return_tensors="pt"
                    ).to(device)

                    v_tg_enc = tokenizer(
                        text_target=v_targets,
                        padding=True,
                        truncation=True,
                        max_length=max_seq_len,
                        return_tensors="pt"
                    ).to(device)

                    v_labels = v_tg_enc["input_ids"]
                    v_labels[v_labels == tokenizer.pad_token_id] = -100

                    v_out = model(
                        input_ids=v_in_enc["input_ids"],
                        attention_mask=v_in_enc["attention_mask"],
                        labels=v_labels
                    )
                    total_val_loss += v_out.loss.item()
                    val_steps += 1

            avg_val_loss = round(total_val_loss / max(1, val_steps), 4)
            perplexity = round(math.exp(min(10.0, avg_val_loss)), 2)

            logger.info(
                f"Epoch {epoch + 1} Complete | Train Loss: {avg_epoch_train_loss} | "
                f"Val Loss: {avg_val_loss} | Perplexity: {perplexity}"
            )

            epoch_history.append({
                "epoch": epoch + 1,
                "train_loss": avg_epoch_train_loss,
                "val_loss": avg_val_loss,
                "perplexity": perplexity
            })

            # Checkpoint the best weights
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                logger.info(f"New best validation loss: {best_val_loss}. Saving checkpoint...")
                model.save_pretrained(self.output_dir)
                tokenizer.save_pretrained(self.output_dir)

        # Final checkpoint ensure saved
        model.save_pretrained(self.output_dir)
        tokenizer.save_pretrained(self.output_dir)

        elapsed = round(time.time() - start_time, 2)

        # Test inference validation
        sample_prompt = "humanize: Furthermore, it is important to remember that deep learning algorithms delve into massive datasets."
        sample_out = ""
        try:
            model.eval()
            test_ids = tokenizer(sample_prompt, return_tensors="pt").to(device)
            with torch.no_grad():
                gen_ids = model.generate(
                    **test_ids,
                    max_length=128,
                    num_beams=3,
                    no_repeat_ngram_size=2
                )
            sample_out = tokenizer.decode(gen_ids[0], skip_special_tokens=True).strip()
            logger.info(f"Sample Model Inference Test: '{sample_out}'")
        except Exception as e:
            logger.warning(f"Inference test warning: {e}")

        metadata = {
            "base_model": self.base_model_name,
            "samples_trained": len(train_pairs),
            "val_samples": len(val_pairs),
            "epochs": epochs,
            "total_steps": step_count,
            "final_train_loss": avg_epoch_train_loss,
            "final_val_loss": avg_val_loss,
            "best_val_loss": best_val_loss,
            "perplexity": perplexity,
            "elapsed_seconds": elapsed,
            "device": device,
            "threads": torch.get_num_threads(),
            "epoch_history": epoch_history,
            "sample_inference_test": sample_out,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "production_fine_tuned_ready"
        }

        with open(self.output_dir / "training_meta.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Intensive Neural SFT Finished in {elapsed}s! Checkpoint saved to {self.output_dir}")
        return {
            "status": "success",
            "metadata": metadata,
            "final_train_loss": avg_epoch_train_loss,
            "final_val_loss": avg_val_loss,
            "perplexity": perplexity
        }


if __name__ == "__main__":
    trainer = NeuralSeq2SeqTrainer()
    res = trainer.train(epochs=2, batch_size=4, max_samples=100)
    print("Fine-tuning result:", res)
