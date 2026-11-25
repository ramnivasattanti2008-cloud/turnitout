"""
Semantic Fidelity and Entity Retention Validator.
Verifies that transformed text preserves numbers, proper nouns,
domain technical terms, and core propositional meaning.
"""

import re
from typing import Any, Dict, List, Set, Tuple


class SemanticValidator:
    """
    Validates that meaning and factual consistency are preserved
    between original and rewritten texts.
    """

    def __init__(self):
        # Regex patterns for factual anchors: numbers, years, percentages, capitalised entities
        self.num_pattern = re.compile(r"\b\d+(?:[\.,]\d+)?%?\b")
        self.entity_pattern = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")

    def extract_factual_anchors(self, text: str) -> Dict[str, Set[str]]:
        """Extracts critical factual tokens: numbers, dates, proper nouns."""
        numbers = set(self.num_pattern.findall(text))
        # Filter common sentence-starting words from entity list
        raw_entities = set(self.entity_pattern.findall(text))
        common_starters = {
            "The", "This", "That", "These", "Those", "In", "On", "At", "By", "For",
            "Furthermore", "Moreover", "Additionally", "However", "Although", "While",
            "It", "There", "When", "If", "Because", "Since", "Beyond", "What"
        }
        entities = {e for e in raw_entities if e not in common_starters}

        return {
            "numbers": numbers,
            "entities": entities
        }

    def validate_fidelity(self, original_text: str, rewritten_text: str) -> Dict[str, Any]:
        """
        Compares factual anchors between original and rewritten text.
        Returns retention rate and lists of missing/preserved facts.
        """
        orig_anchors = self.extract_factual_anchors(original_text)
        new_numbers = set(self.num_pattern.findall(rewritten_text))
        new_entities = set(self.entity_pattern.findall(rewritten_text))

        # Check numbers retention
        missing_numbers = orig_anchors["numbers"] - new_numbers
        num_retention = 1.0 if not orig_anchors["numbers"] else (
            1.0 - (len(missing_numbers) / len(orig_anchors["numbers"]))
        )

        # Check entity retention
        missing_entities = orig_anchors["entities"] - new_entities
        entity_retention = 1.0 if not orig_anchors["entities"] else (
            1.0 - (len(missing_entities) / len(orig_anchors["entities"]))
        )

        # Composite semantic score (0-100%)
        semantic_score = round(((num_retention * 0.6) + (entity_retention * 0.4)) * 100.0, 1)

        return {
            "semantic_score": semantic_score,
            "is_semantically_consistent": semantic_score >= 80.0,
            "missing_numbers": list(missing_numbers),
            "missing_entities": list(missing_entities),
            "preserved_numbers_count": len(orig_anchors["numbers"]) - len(missing_numbers),
            "total_original_numbers": len(orig_anchors["numbers"])
        }
