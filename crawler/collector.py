"""
Web Data Collector for TextHumanizer Pro.
Collects and extracts authentic human writing samples from open public knowledge bases
(Wikipedia, Project Gutenberg, public academic resources) to build empirical training corpora.
"""

import json
import logging
import random
import re
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CRAWLED_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# 80+ diverse academic, philosophical, literary, scientific, legal, and cultural topics
WIKIPEDIA_TOPIC_POOL = [
    "Artificial_intelligence", "Cognitive_science", "History_of_science", "Philosophy_of_mind",
    "Linguistics", "Creative_writing", "Neuroscience", "Quantum_computing",
    "Astrophysics", "Evolutionary_biology", "Epistemology", "World_history",
    "Behavioral_economics", "Machine_learning", "Semantics", "Microbiology",
    "Ancient_Greece", "Renaissance", "Information_theory", "Cellular_biology",
    "Social_psychology", "Genetics", "Cybernetics", "Ecology",
    "Thermodynamics", "Literary_criticism", "Anthropology", "Architecture",
    "Complexity_theory", "Game_theory", "Bioinformatics", "Nanotechnology",
    "Moral_philosophy", "History_of_mathematics", "Environmental_science",
    "Political_philosophy", "Archaeology", "Optics", "Comparative_literature",
    "Jurisprudence", "Constitutional_law", "Human_rights", "Pharmacology",
    "Epidemiology", "Immunology", "Oncology", "Logic",
    "Existentialism", "Deontology", "Ethics", "Aesthetics",
    "Particle_physics", "Materials_science", "Robotics", "Poetics",
    "Rhetoric", "Modernist_literature", "Historiography", "Sociology",
    "Macroeconomics", "Political_economy", "International_relations", "Metaphysics",
    "Pragmatism", "Philosophy_of_language", "Hermeneutics", "Phenomenology",
    "Epigenetics", "Virology", "Organic_chemistry", "Geology",
    "Climatology", "Oceanography", "Economic_history", "Cultural_anthropology"
]

GUTENBERG_SOURCES = [
    ("Emerson_Self_Reliance", "https://www.gutenberg.org/files/16643/16643-0.txt"),
    ("Francis_Bacon_Essays", "https://www.gutenberg.org/cache/epub/564/pg564.txt"),
    ("Thoreau_Walden", "https://www.gutenberg.org/cache/epub/205/pg205.txt"),
    ("Jonathan_Swift_Essays", "https://www.gutenberg.org/cache/epub/1080/pg1080.txt"),
    ("John_Stuart_Mill_On_Liberty", "https://www.gutenberg.org/cache/epub/34901/pg34901.txt"),
    ("Bertrand_Russell_Problems_of_Philosophy", "https://www.gutenberg.org/cache/epub/5827/pg5827.txt"),
    ("Aristotle_Nicomachean_Ethics", "https://www.gutenberg.org/cache/epub/8438/pg8438.txt"),
    ("William_James_Pragmatism", "https://www.gutenberg.org/cache/epub/284/pg284.txt")
]


class WebDataCollector:
    """
    Crawls open public web sources to harvest high-quality human writing samples
    with incremental expansion and deduplication.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or CRAWLED_DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 HumanizerBot/2.0"
        })

    def fetch_wikipedia_paragraphs(self, topics: Optional[List[str]] = None, max_articles: int = 4) -> List[Dict[str, str]]:
        """
        Fetches well-edited human encyclopedic articles from Wikipedia API.
        Extracts clean paragraphs and incrementally updates the sample store.
        """
        dest_file = self.output_dir / "wikipedia_samples.json"
        existing_samples: List[Dict[str, str]] = []
        seen_texts = set()

        if dest_file.exists():
            try:
                with open(dest_file, "r", encoding="utf-8") as f:
                    existing_samples = json.load(f)
                for item in existing_samples:
                    seen_texts.add(item.get("text", "").strip()[:80])
            except Exception as e:
                logger.warning(f"Could not load existing wiki samples: {e}")

        # Select topics: sample randomly from pool if not provided
        if topics:
            target_topics = topics[:max_articles]
        else:
            target_topics = random.sample(WIKIPEDIA_TOPIC_POOL, min(max_articles, len(WIKIPEDIA_TOPIC_POOL)))

        new_collected: List[Dict[str, str]] = []

        for topic in target_topics:
            url = f"https://en.wikipedia.org/api/rest_v1/page/html/{topic}"
            logger.info(f"Fetching Wikipedia article: {topic}")
            try:
                resp = self.session.get(url, timeout=12)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for p in soup.find_all("p"):
                        cleaned_p = re.sub(r"\[\d+\]", "", p.get_text())
                        cleaned_p = re.sub(r"\s+", " ", cleaned_p).strip()
                        word_count = len(cleaned_p.split())
                        prefix = cleaned_p[:80]
                        if 40 <= word_count <= 250 and prefix not in seen_texts:
                            seen_texts.add(prefix)
                            item = {
                                "source": f"wikipedia/{topic}",
                                "text": cleaned_p,
                                "word_count": word_count
                            }
                            new_collected.append(item)
                            existing_samples.append(item)
                else:
                    logger.warning(f"Wikipedia returned {resp.status_code} for {topic}")
            except Exception as e:
                logger.error(f"Error fetching {topic}: {e}")
            time.sleep(0.5)

        with open(dest_file, "w", encoding="utf-8") as f:
            json.dump(existing_samples, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(existing_samples)} total Wikipedia paragraphs ({len(new_collected)} newly added) to {dest_file}")
        return existing_samples

    def fetch_gutenberg_essays(self) -> List[Dict[str, str]]:
        """
        Fetches public domain literature from Project Gutenberg mirrors.
        Normalizes CRLF and parses authentic human literary paragraphs.
        """
        dest_file = self.output_dir / "gutenberg_samples.json"
        existing_samples: List[Dict[str, str]] = []
        seen_texts = set()

        if dest_file.exists():
            try:
                with open(dest_file, "r", encoding="utf-8") as f:
                    existing_samples = json.load(f)
                for item in existing_samples:
                    seen_texts.add(item.get("text", "").strip()[:80])
            except Exception as e:
                logger.warning(f"Could not load existing gutenberg samples: {e}")

        # Choose 2 sources per cycle
        chosen_sources = random.sample(GUTENBERG_SOURCES, min(2, len(GUTENBERG_SOURCES)))
        new_collected: List[Dict[str, str]] = []

        for title, url in chosen_sources:
            logger.info(f"Fetching Gutenberg text: {title}")
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code == 200:
                    content = resp.text.replace("\r\n", "\n").replace("\r", "\n")
                    raw_paragraphs = content.split("\n\n")
                    added_from_title = 0
                    for p in raw_paragraphs:
                        clean_p = re.sub(r"\s+", " ", p).strip()
                        word_count = len(clean_p.split())
                        prefix = clean_p[:80]
                        # Filter Gutenberg boilerplate
                        if 45 <= word_count <= 220 and prefix not in seen_texts:
                            lower_p = clean_p.lower()
                            if not any(k in lower_p for k in ["gutenberg", "license", "ebook", "http", "transcribed", "project"]):
                                seen_texts.add(prefix)
                                item = {
                                    "source": f"gutenberg/{title}",
                                    "text": clean_p,
                                    "word_count": word_count
                                }
                                new_collected.append(item)
                                existing_samples.append(item)
                                added_from_title += 1
                                if added_from_title >= 40:
                                    break
            except Exception as e:
                logger.error(f"Error fetching Gutenberg {title}: {e}")
            time.sleep(0.5)

        with open(dest_file, "w", encoding="utf-8") as f:
            json.dump(existing_samples, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(existing_samples)} total Gutenberg paragraphs ({len(new_collected)} newly added) to {dest_file}")
        return existing_samples

    def fetch_arxiv_abstracts(self, max_results: int = 15) -> List[Dict[str, str]]:
        """
        Harvests authentic peer-reviewed scientific paper abstracts from open ArXiv API
        across computational linguistics, AI, cognitive science, physics, and economics.
        """
        import xml.etree.ElementTree as ET

        dest_file = self.output_dir / "arxiv_samples.json"
        existing_samples: List[Dict[str, str]] = []
        seen_texts = set()

        if dest_file.exists():
            try:
                with open(dest_file, "r", encoding="utf-8") as f:
                    existing_samples = json.load(f)
                for item in existing_samples:
                    seen_texts.add(item.get("text", "").strip()[:80])
            except Exception as e:
                logger.warning(f"Could not load existing arxiv samples: {e}")

        categories = ["cs.AI", "cs.CL", "stat.ML", "q-bio.NC", "physics.soc-ph", "econ.GN"]
        chosen_cat = random.choice(categories)
        new_collected: List[Dict[str, str]] = []

        url = f"http://export.arxiv.org/api/query?search_query=cat:{chosen_cat}&start=0&max_results={max_results}"
        logger.info(f"Fetching ArXiv scientific abstracts: category {chosen_cat}")
        try:
            resp = self.session.get(url, timeout=12)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                entries = root.findall("{http://www.w3.org/2005/Atom}entry")
                for e in entries:
                    summary_elem = e.find("{http://www.w3.org/2005/Atom}summary")
                    title_elem = e.find("{http://www.w3.org/2005/Atom}title")
                    if summary_elem is None:
                        continue
                    clean_summary = re.sub(r"\s+", " ", summary_elem.text or "").strip()
                    word_count = len(clean_summary.split())
                    prefix = clean_summary[:80]
                    if 45 <= word_count <= 300 and prefix not in seen_texts:
                        seen_texts.add(prefix)
                        title_str = (title_elem.text or "").strip().replace("\n", " ") if title_elem is not None else "scientific_paper"
                        item = {
                            "source": f"arxiv/{chosen_cat}/{title_str[:40]}",
                            "text": clean_summary,
                            "word_count": word_count
                        }
                        new_collected.append(item)
                        existing_samples.append(item)
        except Exception as e:
            logger.error(f"Error fetching ArXiv {chosen_cat}: {e}")

        with open(dest_file, "w", encoding="utf-8") as f:
            json.dump(existing_samples, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(existing_samples)} total ArXiv abstracts ({len(new_collected)} newly added) to {dest_file}")
        return existing_samples

    def run_all(self) -> Dict[str, int]:
        """Execute complete web harvest."""
        wiki = self.fetch_wikipedia_paragraphs(max_articles=4)
        gutenberg = self.fetch_gutenberg_essays()
        arxiv = self.fetch_arxiv_abstracts(max_results=15)
        return {
            "wikipedia_count": len(wiki),
            "gutenberg_count": len(gutenberg),
            "arxiv_count": len(arxiv),
            "total_collected": len(wiki) + len(gutenberg) + len(arxiv)
        }


if __name__ == "__main__":
    collector = WebDataCollector()
    summary = collector.run_all()
    print("Collector finished:", summary)
