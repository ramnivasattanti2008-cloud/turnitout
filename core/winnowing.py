"""
Authentic Winnowing Document Fingerprinting Engine.
Implements Schleimer, Wilkerson, and Aiken (2003) "Winnowing: Local Algorithms
for Document Fingerprinting" used by Turnitin and iThenticate similarity scanners:
1. Normalization: lowercasing, punctuation/formatting removal into token stream.
2. K-Gram Extraction (default k=5 consecutive words).
3. Karp-Rabin Rolling Hash (base=131, prime mod=2^61-1).
4. Winnowing Minimum-Hash Selection across sliding window w=4.
5. 8-Word Guarantee (k + w - 1 = 8 consecutive matching words) + Match Clustering.
"""

import re
from typing import Any, Dict, List, Set, Tuple


class WinnowingAnalyzer:
    """
    Deterministic simulator of Turnitin/iThenticate Karp-Rabin + Winnowing similarity detection.
    """

    BASE = 131
    MOD = (1 << 61) - 1  # Large Mersenne prime for collision-free rolling hashes

    @staticmethod
    def tokenize_stream(text: str) -> List[str]:
        """
        Normalizes prose text identically to Turnitin's similarity scanner while
        stripping preserved LaTeX math, citations, and structural markup.
        """
        if not text:
            return []
        cleaned = re.sub(r"\\begin\{(?:equation|align|matrix|figure|table)\*?\}[\s\S]*?\\end\{(?:equation|align|matrix|figure|table)\*?\}", " ", text)
        cleaned = re.sub(r"\$\$[\s\S]*?\$\$", " ", cleaned)
        cleaned = re.sub(r"\\\[[\s\S]*?\\\]", " ", cleaned)
        cleaned = re.sub(r"\$(?!\s*\d+(?:\.\d+)?\b)[^\n$]+\$", " ", cleaned)
        cleaned = re.sub(r"\\(?:cite|citep|citet|label|ref|section|subsection|chapter|usepackage|documentclass)(?:\[[^\]]*\])?(?:\{[^}]*\})+", " ", cleaned)
        cleaned = re.sub(r"```[\s\S]*?```", " ", cleaned)
        return re.findall(r"[a-z0-9]+", cleaned.lower())

    @classmethod
    def _hash_token(cls, token: str) -> int:
        """Maps a normalized word token to a stable 64-bit integer."""
        h = 0
        for ch in token:
            h = (h * 31 + ord(ch)) % cls.MOD
        return h

    @classmethod
    def _kgram_hash(cls, tokens: Tuple[str, ...]) -> int:
        """Computes polynomial Karp-Rabin hash for a k-gram of word tokens."""
        h = 0
        for tok in tokens:
            t_hash = cls._hash_token(tok)
            h = (h * cls.BASE + t_hash) % cls.MOD
        return h

    @classmethod
    def generate_fingerprints(
        cls, text: str, k: int = 5, w: int = 4
    ) -> Tuple[Set[int], List[Tuple[int, int, Tuple[str, ...]]]]:
        """
        Extracts sparse Winnowing fingerprints from text.
        Returns:
          - fingerprint_set: unique set of selected minimum hash integers
          - fingerprint_details: list of (hash_val, token_start_pos, kgram_tuple)
        """
        tokens = cls.tokenize_stream(text)
        if len(tokens) < k:
            return set(), []

        # Compute all k-gram rolling hashes
        hashes: List[Tuple[int, int, Tuple[str, ...]]] = []
        for i in range(len(tokens) - k + 1):
            kg = tuple(tokens[i : i + k])
            hashes.append((cls._kgram_hash(kg), i, kg))

        if len(hashes) <= w:
            # Document shorter than winnowing window: select global minimum hash
            min_item = min(hashes, key=lambda x: (x[0], -x[1]))
            return {min_item[0]}, [min_item]

        fingerprint_set: Set[int] = set()
        fingerprint_details: List[Tuple[int, int, Tuple[str, ...]]] = []
        last_selected_pos = -1

        # Slide window of size w across k-gram hashes; pick rightmost minimum on ties
        for i in range(len(hashes) - w + 1):
            window = hashes[i : i + w]
            # Rightmost minimum: lowest hash value, highest index on tie
            min_val, min_pos, min_kg = min(window, key=lambda x: (x[0], -x[1]))
            if min_pos != last_selected_pos:
                fingerprint_set.add(min_val)
                fingerprint_details.append((min_val, min_pos, min_kg))
                last_selected_pos = min_pos

        return fingerprint_set, fingerprint_details

    @classmethod
    def compare_documents(
        cls, source_text: str, candidate_text: str, k: int = 5, w: int = 4
    ) -> Dict[str, Any]:
        """
        Runs full Winnowing fingerprint comparison + match clustering between
        original source text and candidate humanized text.
        """
        src_fps, src_details = cls.generate_fingerprints(source_text, k=k, w=w)
        cand_fps, cand_details = cls.generate_fingerprints(candidate_text, k=k, w=w)

        if not cand_fps or not src_fps:
            return {
                "winnowing_similarity_pct": 0.0,
                "matching_fingerprints": 0,
                "total_candidate_fingerprints": len(cand_fps),
                "flagged_clusters": 0,
                "matched_passages": [],
                "eight_word_chains": 0,
                "status": "clean",
            }

        matching_hashes = src_fps.intersection(cand_fps)
        matched_items = [item for item in cand_details if item[0] in matching_hashes]
        matched_passages = [" ".join(item[2]) for item in matched_items]

        # Match Clustering (Turnitin logic): check adjacent matching fingerprint spans
        flagged_clusters = 0
        if len(matched_items) >= 2:
            consecutive = 1
            for idx in range(1, len(matched_items)):
                if matched_items[idx][1] - matched_items[idx - 1][1] <= (k + w):
                    consecutive += 1
                    if consecutive >= 2:
                        flagged_clusters += 1
                else:
                    consecutive = 1

        # Also explicitly check 8-word contiguous verbatim guarantee (k + w - 1 = 8)
        chain_len = k + w - 1
        src_tokens = cls.tokenize_stream(source_text)
        cand_tokens = cls.tokenize_stream(candidate_text)
        src_8grams = (
            {tuple(src_tokens[i : i + chain_len]) for i in range(len(src_tokens) - chain_len + 1)}
            if len(src_tokens) >= chain_len
            else set()
        )
        cand_8grams = (
            {tuple(cand_tokens[i : i + chain_len]) for i in range(len(cand_tokens) - chain_len + 1)}
            if len(cand_tokens) >= chain_len
            else set()
        )
        eight_word_matches = src_8grams.intersection(cand_8grams)

        sim_pct = round((len(matching_hashes) / max(1, len(cand_fps))) * 100.0, 1)

        return {
            "winnowing_similarity_pct": sim_pct,
            "matching_fingerprints": len(matching_hashes),
            "total_candidate_fingerprints": len(cand_fps),
            "flagged_clusters": flagged_clusters,
            "matched_passages": matched_passages[:10],
            "eight_word_chains": len(eight_word_matches),
            "status": "clean" if len(matching_hashes) == 0 and len(eight_word_matches) == 0 else "flagged",
        }
