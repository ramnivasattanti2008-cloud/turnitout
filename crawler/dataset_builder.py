"""
Dataset Builder for TextHumanizer Pro.
Creates paired training examples (AI-style robotic text <-> authentic human text)
from harvested web samples and synthetic generators with incremental deduplication.
"""

import json
import logging
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CRAWLED_DATA_DIR, DATASET_FILE
from core.metrics import calculate_lexical_diversity, split_sentences, tokenize_words

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class DatasetBuilder:
    """
    Constructs high-quality parallel pairs (AI-Generated Style -> Human Target)
    for model training, calibration, and benchmarking.
    """

    def __init__(self, data_file: Optional[Path] = None):
        self.data_file = data_file or DATASET_FILE
        self.ai_markers = [
            "In today's fast-paced world, ",
            "It is important to remember that ",
            "plays a crucial role in ",
            "stands as a testament to ",
            "By delving deeper into this multifaceted approach, ",
            "Furthermore, ",
            "In conclusion, "
        ]

    def robotize_paragraph(self, human_text: str) -> str:
        """
        Synthetically transforms an organic human paragraph into typical AI-generated prose
        by flattening burstiness, injecting ChatGPT markers, and standardizing sentence structures.
        """
        sentences = split_sentences(human_text)
        if not sentences:
            return human_text

        ai_sentences: List[str] = []
        openers = [
            "In today's rapidly evolving landscape, ",
            "It is crucial to note that ",
            "Navigating the complexities of modern thought, ",
            "When examining the intricate tapestry of this subject, ",
            "It goes without saying that ",
            "At the forefront of modern discourse, "
        ]
        opener = random.choice(openers)
        first = sentences[0].strip()
        first_clean = first[0].lower() + first[1:] if first else ""
        ai_sentences.append(opener + first_clean)

        for i, s in enumerate(sentences[1:], start=1):
            s_clean = s.strip()
            # Inject transitional boilerplate
            if i % 2 == 1:
                trans = random.choice([
                    "Furthermore, ", "Moreover, ", "Additionally, ",
                    "By delving deeper into this perspective, ",
                    "Consequently, it becomes evident that "
                ])
                s_clean = trans + s_clean[0].lower() + s_clean[1:]
            elif "important" in s_clean:
                s_clean = s_clean.replace("important", "pivotal and of paramount importance")
            elif "clear" in s_clean:
                s_clean = s_clean.replace("clear", "crystal clear and undeniably profound")
            ai_sentences.append(s_clean)

        # Add formulaic AI conclusion
        closers = [
            "In conclusion, this stands as a profound testament to the ever-evolving dynamic.",
            "Ultimately, this multifaceted approach paves the way for deeper systemic understanding.",
            "To sum up, fostering a holistic perspective remains crucial for future development."
        ]
        ai_sentences.append(random.choice(closers))
        return " ".join(ai_sentences)

    def build_from_crawled_files(self) -> List[Dict[str, Any]]:
        """
        Reads crawled Wikipedia and Gutenberg samples, builds parallel pairs,
        deduplicates, and saves them to the dataset file.
        """
        dataset: List[Dict[str, Any]] = []
        seen_targets = set()

        # Load existing dataset if present to preserve previous pairs
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    dataset = json.load(f)
                for item in dataset:
                    seen_targets.add(item.get("human_target", "").strip()[:80])
            except Exception as e:
                logger.warning(f"Could not load existing dataset: {e}")

        sources = [
            CRAWLED_DATA_DIR / "wikipedia_samples.json",
            CRAWLED_DATA_DIR / "gutenberg_samples.json",
            CRAWLED_DATA_DIR / "arxiv_samples.json"
        ]

        pair_id = len(dataset) + 1
        new_count = 0

        for src_path in sources:
            if not src_path.exists():
                continue
            try:
                with open(src_path, "r", encoding="utf-8") as f:
                    samples = json.load(f)
                for item in samples:
                    human_text = item.get("text", "").strip()
                    if len(human_text.split()) < 35:
                        continue

                    prefix = human_text[:80]
                    if prefix in seen_targets:
                        continue

                    seen_targets.add(prefix)
                    ai_text = self.robotize_paragraph(human_text)
                    dataset.append({
                        "id": f"pair_{pair_id:04d}",
                        "source": item.get("source", "web_harvest"),
                        "ai_style_input": ai_text,
                        "human_target": human_text,
                        "word_count": len(human_text.split()),
                        "lexical_diversity": calculate_lexical_diversity(human_text)
                    })
                    pair_id += 1
                    new_count += 1
            except Exception as e:
                logger.error(f"Error processing {src_path}: {e}")

        # If empty, add foundational pairs
        if not dataset:
            dataset = self.get_foundational_pairs()

        # Save dataset
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"Built paired dataset: {len(dataset)} total examples ({new_count} newly added) at {self.data_file}")
        return dataset

    def get_foundational_pairs(self) -> List[Dict[str, Any]]:
        """Provides high-quality initial paired samples covering varied domains."""
        pairs = [
            {
                "id": "pair_0001",
                "source": "technology",
                "ai_style_input": (
                    "In today's fast-paced digital era, artificial intelligence plays a crucial role in modern software engineering. "
                    "Furthermore, it is important to remember that machine learning algorithms delve into vast amounts of data to produce accurate predictions. "
                    "Moreover, a multifaceted approach is required to navigate the complexities of ethical deployment. "
                    "In conclusion, AI stands as a testament to human innovation."
                ),
                "human_target": (
                    "Modern software development increasingly relies on artificial intelligence. "
                    "Algorithms sift through terabytes of raw telemetry to spot subtle architectural regressions, yet ethical oversight remains tricky. "
                    "Engineers cannot simply automate accountability; practical guardrails demand deliberate human scrutiny at every release milestone."
                )
            },
            {
                "id": "pair_0002",
                "source": "education",
                "ai_style_input": (
                    "It is crucial to note that education serves as a beacon of hope in our rapidly evolving society. "
                    "Furthermore, teachers play a pivotal role in shaping young minds and fostering a rich tapestry of critical thinking. "
                    "Additionally, by delving deeper into interactive pedagogies, schools can seamlessly integrate technology into classroom environments. "
                    "In conclusion, modern education paves the way for tomorrow's leaders."
                ),
                "human_target": (
                    "Great schools do more than convey facts—they teach children how to question assumptions. "
                    "When teachers abandon rigid lecturing in favor of lively debate, students naturally lean into difficult problems. "
                    "Digital tools help organize course materials, but genuine curiosity still hinges on personal mentorship."
                )
            },
            {
                "id": "pair_0003",
                "source": "science",
                "ai_style_input": (
                    "Climate change represents an ever-evolving challenge with profound impacts across the globe. "
                    "Moreover, scientists are harnessing the power of renewable energy to mitigate severe ecological consequences. "
                    "It goes without saying that sustainable policies must be implemented across all sectors. "
                    "Ultimately, addressing this double-edged sword requires a holistic global strategy."
                ),
                "human_target": (
                    "Shifting weather patterns threaten coastal infrastructure far faster than municipal budgets can adapt. "
                    "Solar and wind installations continue breaking generation records, but grid storage remains a formidable bottleneck. "
                    "Without substantial investments in transmission networks, decarbonization targets will slip out of reach."
                )
            }
        ]

        for p in pairs:
            p["word_count"] = len(p["human_target"].split())
            p["lexical_diversity"] = calculate_lexical_diversity(p["human_target"])
        return pairs


if __name__ == "__main__":
    builder = DatasetBuilder()
    ds = builder.build_from_crawled_files()
    print(f"Generated {len(ds)} training pairs.")
