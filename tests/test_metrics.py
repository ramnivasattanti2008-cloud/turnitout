"""
Unit tests for metrics and similarity calculations.
"""

import unittest
from core.metrics import (
    calculate_burstiness,
    calculate_lexical_diversity,
    calculate_ngram_overlap,
    calculate_readability,
    count_syllables,
    levenshtein_similarity,
    split_sentences,
    tokenize_words,
)


class TestMetrics(unittest.TestCase):

    def test_tokenize_and_split(self):
        text = "Hello world! This is a test. Is it working?"
        words = tokenize_words(text)
        sentences = split_sentences(text)
        self.assertEqual(len(sentences), 3)
        self.assertIn("hello", words)
        self.assertIn("working", words)

    def test_syllable_count(self):
        self.assertEqual(count_syllables("the"), 1)
        self.assertEqual(count_syllables("programming"), 3)
        self.assertGreaterEqual(count_syllables("artificial"), 4)

    def test_readability(self):
        sample = (
            "The quick brown fox jumps over the lazy dog. "
            "Reading is a wonderful habit that enriches the human mind."
        )
        scores = calculate_readability(sample)
        self.assertIn("flesch_reading_ease", scores)
        self.assertIn("flesch_kincaid_grade", scores)
        self.assertGreater(scores["total_words"], 10)

    def test_ngram_overlap(self):
        text_a = "artificial intelligence is revolutionizing the world of science"
        text_b = "artificial intelligence is transforming our modern scientific world"
        # 3-gram overlap should be positive
        overlap = calculate_ngram_overlap(text_a, text_b, n=3)
        self.assertGreater(overlap, 0.0)

    def test_levenshtein(self):
        s1 = "This is a quick test sentence."
        s2 = "This is a quick test sentence."
        self.assertEqual(levenshtein_similarity(s1, s2), 100.0)

        s3 = "Completely distinct phrase with no common words."
        self.assertLess(levenshtein_similarity(s1, s3), 30.0)

    def test_burstiness(self):
        # Monotonous sentences (similar lengths)
        mono_text = "The dog ran home. The cat sat down. The bird flew high. The fish swam deep."
        std_mono, cv_mono = calculate_burstiness(mono_text)

        # Bursty sentences (varied lengths)
        bursty_text = (
            "Stop! In an extraordinary turn of events that baffled historians for decades, "
            "the treaty was completely rewritten overnight. Wow."
        )
        std_burst, cv_burst = calculate_burstiness(bursty_text)
        self.assertGreater(cv_burst, cv_mono)


if __name__ == "__main__":
    unittest.main()
