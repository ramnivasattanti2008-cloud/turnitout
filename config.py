"""
Configuration settings for TextHumanizer Pro.
Includes AI detection thresholds, typical LLM clichés/markers,
tone definitions, and directory paths.
"""

import os
from pathlib import Path

# Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"
CRAWLED_DATA_DIR = DATA_DIR / "crawled"
DATASET_FILE = DATA_DIR / "paired_humanize_dataset.json"

# Web App Configuration
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# Google Ads & Google AdSense Monetization Configuration
GOOGLE_ADSENSE_ID = os.environ.get("GOOGLE_ADSENSE_ID", "").strip()
GOOGLE_ADSENSE_SLOT_TOP = os.environ.get("GOOGLE_ADSENSE_SLOT_TOP", "").strip()
GOOGLE_ADSENSE_SLOT_MIDDLE = os.environ.get("GOOGLE_ADSENSE_SLOT_MIDDLE", "").strip()
GOOGLE_ADSENSE_SLOT_BOTTOM = os.environ.get("GOOGLE_ADSENSE_SLOT_BOTTOM", "").strip()
GOOGLE_TAG_ID = os.environ.get("GOOGLE_TAG_ID", "").strip()
MONETIZATION_ENABLED = os.environ.get("MONETIZATION_ENABLED", "true").lower() in ("true", "1", "yes")

# ads.txt publisher record
# Format: google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
ADSENSE_PUB_RAW = GOOGLE_ADSENSE_ID.replace("ca-", "").strip() if GOOGLE_ADSENSE_ID else "pub-0000000000000000"
ADS_TXT_CONTENT = os.environ.get(
    "ADS_TXT_CONTENT",
    f"google.com, {ADSENSE_PUB_RAW}, DIRECT, f08c47fec0942fa0\n"
)

# AI Detector Lexicon & Clichés
# Commonly overused LLM phrases and filler buzzwords
AI_MARKER_PHRASES = [
    # Openings & Transitions
    "in conclusion", "to sum up", "in summary", "delve into", "delving into",
    "it is crucial to remember", "it is important to note", "plays a crucial role",
    "plays a vital role", "plays a pivotal role", "a testament to", "testament to the",
    "rich tapestry", "tapestry of", "beacon of hope", "beacon of", "ever-evolving landscape",
    "rapidly evolving landscape", "in today's fast-paced world", "in today's digital era",
    "in today's digital age", "a multifaceted approach", "a holistic approach",
    "navigating the complexities", "harnessing the power", "game-changer", "a double-edged sword",
    "sheds light on", "serves as a reminder", "it goes without saying", "at the forefront of",
    "fosters a sense of", "intertwined with", "stands as a testament", "underscores the importance",
    "paves the way", "vital component", "integral part", "paramount importance",
    "undeniably", "furthermore", "moreover", "nonetheless", "notwithstanding",
    "by delving deeper", "unravel the intricacies", "a stepping stone", "poised to",
    "a profound impact", "seamlessly integrate", "in the realm of", "resonates deeply with"
]

AI_WORDS = [
    "delve", "tapestry", "beacon", "pivotal", "paramount", "underscores", 
    "multifaceted", "holistic", "intertwined", "foster", "testament",
    "nuanced", "imperative", "juxtaposition", "myriad", "plethora", "overarching"
]
AI_BUZZWORDS = AI_WORDS


# Detection Weights (Perplexity, Burstiness, Cliché Density, Lexical Diversity)
DETECTION_WEIGHTS = {
    "burstiness": 0.30,       # Variance in sentence lengths and structures
    "cliche_density": 0.30,   # Presence of AI marker phrases and buzzwords
    "lexical_diversity": 0.25,# Type-Token Ratio & unique vocabulary
    "repetition_penalty": 0.15# Repeated n-gram phrases and syntactic symmetry
}

# Tone Profiles
TONE_MODIFIERS = {
    "standard": {
        "formality": 0.5,
        "burstiness_target": 1.4,
        "synonym_rate": 0.35,
        "description": "Natural human writing with standard rhythm and clear flow."
    },
    "academic": {
        "formality": 0.85,
        "burstiness_target": 1.2,
        "synonym_rate": 0.30,
        "description": "Scholarly, authoritative vocabulary, rigorous syntax, academic transitions."
    },
    "casual": {
        "formality": 0.2,
        "burstiness_target": 1.8,
        "synonym_rate": 0.45,
        "description": "Conversational, engaging, expressive, varied sentence lengths, natural idioms."
    },
    "journalistic": {
        "formality": 0.6,
        "burstiness_target": 1.5,
        "synonym_rate": 0.35,
        "description": "Concise, punchy, active voice, informative with compelling storytelling rhythm."
    },
    "executive": {
        "formality": 0.75,
        "burstiness_target": 1.3,
        "synonym_rate": 0.30,
        "description": "Direct, business-focused, strategic clarity, high impact, fluff-free."
    }
}
