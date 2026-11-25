"""
Metrics calculation module for text analysis.
Provides readability metrics, lexical diversity metrics, and
string similarity / plagiarism overlap calculations.
"""

import math
import re
from typing import Dict, List, Set, Tuple


def tokenize_words(text: str) -> List[str]:
    """Tokenize text into lowercase alphabetic words."""
    return re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", text.lower())


def split_sentences(text: str) -> List[str]:
    """Split text into sentences handling standard punctuation abbreviations."""
    # Split on sentence terminals . ! ? followed by space or end
    raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    # Filter empty or whitespace
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return sentences if sentences else [text.strip()] if text.strip() else []


def count_syllables(word: str) -> int:
    """Estimate the number of syllables in an English word."""
    word = word.lower().strip()
    if len(word) <= 3:
        return 1
    # Remove silent e at the end
    word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
    # Consecutive vowels count as one syllable
    syllables = len(re.findall(r'[aeiouy]{1,2}', word))
    return max(1, syllables)


def calculate_readability(text: str) -> Dict[str, float]:
    """
    Calculate standard readability indexes:
    - Flesch Reading Ease
    - Flesch-Kincaid Grade Level
    - Automated Readability Index (ARI)
    """
    words = tokenize_words(text)
    sentences = split_sentences(text)
    
    num_words = max(1, len(words))
    num_sentences = max(1, len(sentences))
    num_syllables = sum(count_syllables(w) for w in words)
    num_chars = sum(len(w) for w in words)
    
    words_per_sentence = num_words / num_sentences
    syllables_per_word = num_syllables / num_words
    chars_per_word = num_chars / num_words
    
    # Flesch Reading Ease: 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)
    flesch_score = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)
    flesch_score = round(max(0.0, min(100.0, flesch_score)), 1)
    
    # Flesch-Kincaid Grade Level: 0.39*(words/sentences) + 11.8*(syllables/words) - 15.59
    fk_grade = (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59
    fk_grade = round(max(1.0, fk_grade), 1)
    
    # ARI: 4.71*(chars/words) + 0.5*(words/sentences) - 21.43
    ari = 4.71 * chars_per_word + 0.5 * words_per_sentence - 21.43
    ari = round(max(1.0, ari), 1)
    
    return {
        "flesch_reading_ease": flesch_score,
        "flesch_kincaid_grade": fk_grade,
        "automated_readability_index": ari,
        "avg_sentence_length": round(words_per_sentence, 1),
        "total_words": num_words,
        "total_sentences": num_sentences
    }


def calculate_lexical_diversity(text: str) -> Dict[str, float]:
    """
    Measure lexical richness:
    - Type-Token Ratio (TTR)
    - Hapax Legomena ratio (words occurring only once)
    """
    words = tokenize_words(text)
    if not words:
        return {"ttr": 0.0, "hapax_ratio": 0.0, "unique_words": 0}
    
    total_tokens = len(words)
    unique_tokens = len(set(words))
    
    freq_map: Dict[str, int] = {}
    for w in words:
        freq_map[w] = freq_map.get(w, 0) + 1
        
    hapax_count = sum(1 for count in freq_map.values() if count == 1)
    
    ttr = round(unique_tokens / total_tokens, 3)
    hapax_ratio = round(hapax_count / total_tokens, 3)
    
    return {
        "ttr": ttr,
        "hapax_ratio": hapax_ratio,
        "unique_words": unique_tokens
    }


def get_ngrams(tokens: List[str], n: int) -> Set[Tuple[str, ...]]:
    """Return set of n-grams from token sequence."""
    if len(tokens) < n:
        return set()
    return set(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))


def get_document_ngrams(text: str, n: int = 3) -> Set[Tuple[str, ...]]:
    """
    Extracts unique n-grams on a line-by-line / paragraph-by-paragraph basis, ensuring that n-grams
    do not artificially span across line breaks, bullet points, or layout elements.
    """
    units = [line.strip() for line in text.splitlines() if line.strip()]
    all_ngrams: Set[Tuple[str, ...]] = set()
    for u in units:
        tokens = tokenize_words(u)
        all_ngrams.update(get_ngrams(tokens, n))
    return all_ngrams


def calculate_ngram_overlap(text_a: str, text_b: str, n: int = 3) -> float:
    """
    Calculates Jaccard overlap between n-grams of two texts, respecting paragraph breaks.
    Useful for checking plagiarism / verbatim copying.
    """
    ngrams_a = get_document_ngrams(text_a, n)
    ngrams_b = get_document_ngrams(text_b, n)
    
    if not ngrams_a or not ngrams_b:
        return 0.0
        
    intersection = len(ngrams_a.intersection(ngrams_b))
    union = len(ngrams_a.union(ngrams_b))
    
    return round((intersection / union) * 100.0, 1) if union > 0 else 0.0


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Calculate normalised similarity (0-100%) between two strings
    using dynamic programming Levenshtein distance.
    Optimised for paragraph-sized texts.
    """
    # Token-level Levenshtein for speed and relevance to plagiarism
    tokens1 = tokenize_words(s1)
    tokens2 = tokenize_words(s2)
    
    n, m = len(tokens1), len(tokens2)
    if n == 0 and m == 0:
        return 100.0
    if n == 0 or m == 0:
        return 0.0
        
    # Standard DP table row compression
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, m + 1):
            temp = dp[j]
            if tokens1[i - 1] == tokens2[j - 1]:
                dp[j] = prev
            else:
                dp[j] = min(prev + 1, dp[j] + 1, dp[j - 1] + 1)
            prev = temp
            
    edit_dist = dp[m]
    max_len = max(n, m)
    similarity = max(0.0, 100.0 * (1.0 - (edit_dist / max_len)))
    return round(similarity, 1)


def calculate_burstiness(text: str) -> Tuple[float, float]:
    """
    Calculate sentence length burstiness (mean and standard deviation).
    Human writing exhibits high standard deviation in sentence lengths.
    LLMs produce flat, uniform distributions with low standard deviation.
    """
    sentences = split_sentences(text)
    if len(sentences) <= 1:
        return 0.0, 0.0
        
    lengths = [len(tokenize_words(s)) for s in sentences]
    mean_length = sum(lengths) / len(lengths)
    variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    
    # Burstiness index: std_dev / mean_length (coefficient of variation)
    coef_variation = (std_dev / mean_length) if mean_length > 0 else 0.0
    return round(std_dev, 2), round(coef_variation, 2)


def calculate_zippy_entropy(text: str) -> Dict[str, float]:
    """
    ZipPy Entropic Perplexity & Compression Scoring.
    Measures the lossless compression ratio of text using zlib and lzma.
    Human text with diverse vocabulary and irregular syntactic cadence has higher
    uncompressed entropy (compression ratio closer to 1.0) compared to predictable,
    redundant LLM text which compresses into much fewer bytes.
    """
    import zlib
    import lzma

    if not text.strip():
        return {
            "raw_bytes": 0,
            "zlib_bytes": 0,
            "compression_ratio": 1.0,
            "entropy_score": 100.0,
            "verdict": "Authentic Human Entropy"
        }

    raw_bytes = len(text.encode("utf-8"))
    zlib_bytes = len(zlib.compress(text.encode("utf-8"), level=9))
    lzma_bytes = len(lzma.compress(text.encode("utf-8")))

    # Ratio of compressed to uncompressed (higher = more entropic/unpredictable = human)
    zlib_ratio = round(zlib_bytes / max(1, raw_bytes), 3)

    # Scale entropy score (typically between 0.50 and 1.10 for text snippets)
    # Ratios >= 0.70 represent high perplexity / human variation
    if zlib_ratio >= 0.75:
        entropy_score = 98.0
        verdict = "High Entropy (Human-Authentic)"
    elif zlib_ratio >= 0.65:
        entropy_score = 85.0
        verdict = "Substantial Entropy (Pass)"
    elif zlib_ratio >= 0.50:
        entropy_score = 55.0
        verdict = "Moderate Entropy (Borderline)"
    else:
        entropy_score = 25.0
        verdict = "Low Entropy (Predictable AI)"

    return {
        "raw_bytes": raw_bytes,
        "zlib_bytes": zlib_bytes,
        "lzma_bytes": lzma_bytes,
        "compression_ratio": zlib_ratio,
        "entropy_score": entropy_score,
        "verdict": verdict
    }

