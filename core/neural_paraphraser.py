"""
Neural Transformer Paraphraser and Deep Model Pipeline.
Integrates Hugging Face Transformers with PyTorch for sequence-to-sequence
deep neural paraphrasing with beam search, nucleus sampling, and repetition penalties.
"""

import logging
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


from pathlib import Path
from config import BASE_DIR

FINE_TUNED_DIR = BASE_DIR / "model" / "fine_tuned_t5"


class NeuralParaphraser:
    """
    Deep neural seq2seq paraphraser utilizing pre-trained transformer models
    and fine-tuning pipelines.
    """

    def __init__(self, model_name: Optional[str] = None):
        if model_name:
            self.model_name = model_name
        elif (FINE_TUNED_DIR / "config.json").exists():
            self.model_name = str(FINE_TUNED_DIR)
            logger.info(f"Using locally fine-tuned checkpoint: {self.model_name}")
        else:
            self.model_name = "google-t5/t5-small"
        self.model = None
        self.tokenizer = None
        self._is_ready = False
        self._torch_available = False

        # Verify PyTorch availability
        try:
            import torch
            import transformers
            self._torch_available = True
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"PyTorch & Transformers detected. Device: {self.device}")
        except ImportError:
            logger.info("PyTorch / Transformers not yet loaded in environment. Running in hybrid heuristic-adversarial mode.")

    def load_model(self) -> bool:
        """Loads transformer weights and tokenizer into memory."""
        if not self._torch_available:
            return False

        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            logger.info(f"Loading transformer model: {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
            self._is_ready = True
            logger.info(f"Successfully loaded {self.model_name} on {self.device}.")
            return True
        except Exception as e:
            logger.warning(f"Could not load neural model {self.model_name}: {e}. Falling back to adversarial engine.")
            self._is_ready = False
            return False

    def paraphrase_sentence(
        self,
        sentence: str,
        num_beams: int = 4,
        temperature: float = 0.85,
        repetition_penalty: float = 1.35
    ) -> str:
        """Generates deep neural paraphrase for a single sentence."""
        if not self._is_ready:
            if not self.load_model():
                return sentence

        import torch

        # Prepare T5 format matching fine-tuned training task: 'humanize: <sentence>'
        prompt = f"humanize: {sentence.strip()}"
        inputs = self.tokenizer(
            prompt,
            padding="longest",
            truncation=True,
            max_length=256,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=256,
                num_beams=num_beams,
                num_return_sequences=1,
                no_repeat_ngram_size=3,
                repetition_penalty=repetition_penalty,
                temperature=temperature,
                do_sample=True,
                top_p=0.92
            )

        paraphrased = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        import re
        paraphrased = re.sub(r"^(paraphrase|paraphraser|humanize|paraphrased):\s*", "", paraphrased, flags=re.IGNORECASE).strip()
        return paraphrased

    def is_available(self) -> bool:
        """Returns True if neural transformer pipeline is loaded and ready."""
        return self._is_ready
