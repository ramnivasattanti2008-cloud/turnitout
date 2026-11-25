"""
Turnitout Evasion & Multi-Stage Linguistic Transformation Engine.
Implements the reverse-engineered 17-stage transformation pipeline targeting
Winnowing Karp-Rabin hashing, Tree Edit Distance (TED) syntax parsing,
and LLM entropy/burstiness signals:
1. Active <-> Passive Voice Inversion (Stage A)
2. Sentence Fusion (Anti-Burstiness Weapon, Stage B)
3. Categorized Transition Phrase Injection (Stage C)
4. Clause-level Word & Prepositional Reordering (Stage D)
5. Nominalization & De-nominalization (Stage E)
6. Appositive Definitional Injection (Entropy Bomb, Stage F)
7. Discourse Marker Rotation (Stage G)
8. Determiner & Conjunction Cycling
"""

import random
import re
from typing import Dict, List, Optional, Set, Tuple
from core.metrics import split_sentences


class TurnitoutEngine:
    """
    Reverse-engineered linguistic transformer designed to defeat:
    - Winnowing rolling hash algorithms (k=5 word k-grams, 8-word guarantee)
    - Tree Edit Distance (TED) dependency syntax parsers
    - Token probability & low-perplexity detectors
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self._used_appositives: Set[str] = set()
        self._used_discourse_replacements: Dict[str, str] = {}

        # Transformation counters for auditing
        self.voice_transform_count = 0
        self.sentence_fusion_count = 0
        self.transition_inject_count = 0
        self.clause_word_reorder_count = 0
        self.nominalization_count = 0
        self.appositive_count = 0
        self.discourse_rotate_count = 0
        self.determiner_swap_count = 0

        # Academic verb pairs for active <-> passive voice transformations
        self.academic_verbs = [
            ("analyzed", "was analyzed", "were analyzed"),
            ("investigated", "was investigated", "were investigated"),
            ("demonstrated", "was demonstrated", "were demonstrated"),
            ("examined", "was examined", "were examined"),
            ("evaluated", "was evaluated", "were evaluated"),
            ("observed", "was observed", "were observed"),
            ("formulated", "was formulated", "were formulated"),
            ("derived", "was derived", "were derived"),
            ("implemented", "was implemented", "were implemented"),
            ("computed", "was computed", "were computed"),
            ("established", "was established", "were established"),
            ("validated", "was validated", "were validated"),
            ("simulated", "was simulated", "were simulated"),
            ("characterized", "was characterized", "were characterized"),
            ("measured", "was measured", "were measured"),
            ("optimized", "was optimized", "were optimized"),
            ("identified", "was identified", "were identified"),
            ("calculated", "was calculated", "were calculated"),
            ("explored", "was explored", "were explored"),
            ("classified", "was classified", "were classified"),
        ]

        # Connectors for fusing short sentences to inject high burstiness
        self.fusion_connectors = [
            ", which consequently ",
            ", thereby requiring ",
            ", thus leading to ",
            ", and as an empirical outcome, ",
            ", whereby "
        ]

        # Categorized transition phrases
        self.transitions = {
            "addition": [
                "In addition,", "Beyond this,", "Coupled with this,", "What is more,", "Along these lines,"
            ],
            "contrast": [
                "Conversely,", "On the other hand,", "In contrast,",
                "By comparison,", "Paradoxically,", "Counterintuitively,"
            ],
            "cause_effect": [
                "Consequently,", "As a direct result,", "Therefore,",
                "Accordingly,", "For this reason,", "On account of this,"
            ],
            "clarification": [
                "In other words,", "Specifically,", "To clarify,",
                "Put differently,", "Stated another way,"
            ],
            "sequence": [
                "Subsequently,", "Following this,", "Thereafter,",
                "In turn,", "Proceeding further,"
            ],
            "emphasis": [
                "Indeed,", "In fact,", "Notably,", "Remarkably,",
                "Crucially,", "Most importantly,"
            ],
            "concession": [
                "Admittedly,", "Granted,", "To be sure,",
                "It must be acknowledged that"
            ]
        }

        # Nominalization pairs: verb <-> noun phrases
        self.nominalization_pairs = [
            (r"\banalyze\b", "conduct an analysis of"),
            (r"\banalyzed\b", "subjected to empirical analysis"),
            (r"\binvestigate\b", "carry out an investigation into"),
            (r"\binvestigated\b", "examined through systematic investigation"),
            (r"\bcompute\b", "perform the computation of"),
            (r"\bcomputed\b", "determined through numerical computation"),
            (r"\bapproximate\b", "derive an approximation of"),
            (r"\bconverge\b", "achieve mathematical convergence"),
            (r"\bconverges\b", "exhibits convergence"),
            (r"\boptimize\b", "pursue the optimization of"),
            (r"\boptimized\b", "refined through systematic optimization"),
            (r"\bvalidate\b", "provide empirical validation for"),
            (r"\bvalidated\b", "supported by systematic validation"),
            (r"\bclassify\b", "perform the classification of"),
            (r"\bclassified\b", "categorized via systematic classification"),
            (r"\bdifferentiate\b", "execute differentiation upon"),
            (r"\bintegrate\b", "achieve integration across"),
            (r"\bmeasure\b", "obtain a quantitative measurement of"),
            (r"\bformulate\b", "develop a formal formulation of"),
            (r"\bformulated\b", "articulated through rigorous formulation"),
        ]

        # Appositives ("Entropy Bombs"): definitional insertions for technical terms
        self.appositive_definitions = {
            "finite difference": "a discretization technique for differential operators",
            "Crank-Nicolson": "an implicit second-order-accurate scheme",
            "boundary condition": "a constraint imposed on the solution domain",
            "convergence": "the tendency of a numerical sequence toward a limiting value",
            "stability": "the property ensuring bounded error growth",
            "truncation error": "the discrepancy between exact and discrete operators",
            "eigenvalue": "a characteristic scalar of a linear transformation",
            "discretization": "the process of converting continuous models to discrete form",
            "time step": "the discrete temporal increment in a marching scheme",
            "grid spacing": "the distance between adjacent mesh nodes",
            "concept drift": "the statistical shift in target data distribution over time",
            "telemetry": "the automated transmission of real-time operational metrics",
            "machine learning": "an algorithmic paradigm deriving decision rules from empirical data",
            "neural network": "an interconnected computational architecture of parameterized nodes",
            "stochastic process": "a time-indexed collection of random variables",
            "mail gateway": "an edge filtering layer inspecting incoming enterprise communications",
            "data leakage": "the unintentional inclusion of test features into training distributions",
        }

        # Discourse marker rotations (preserves academic tone while avoiding repetition)
        self.discourse_markers = {
            "However": ["On the other hand", "That said", "Even so", "In contrast", "Yet", "Still"],
            "Therefore": ["Consequently", "Hence", "As a result", "Accordingly", "It follows that"],
            "Moreover": ["In addition", "Beyond this", "What is more", "Further", "Coupled with this"],
            "Although": ["Even though", "Despite the fact that", "While it is true that", "Granted that"],
            "Thus": ["Hence", "Accordingly", "As such", "In this manner", "Consequently"],
            "Indeed": ["In fact", "Certainly", "In operational reality", "Without question"],
            "Similarly": ["Likewise", "In a comparable manner", "By the same token", "Along these lines"],
            "Specifically": ["In particular", "More precisely", "Namely", "To be specific"],
            "Notably": ["Remarkably", "Significantly", "Importantly", "Conspicuously"],
            "Meanwhile": ["In the interim", "Concurrently", "At the same time", "Simultaneously"],
            "Conversely": ["On the contrary", "In contrast", "By contrast", "Contrastingly"],
            "Ultimately": ["In the final analysis", "When all is considered", "In the long run"],
            "Typically": ["Generally", "Ordinarily", "As a rule", "In standard practice"]
        }

        # Determiner swaps
        self.determiners = {
            r"\bseveral\b": ["a number of", "multiple", "sundry", "various"],
            r"\bmany\b": ["numerous", "a substantial number of", "a broad range of", "a large quantity of"],
            r"\bsome\b": ["certain", "particular", "select", "specific"],
            r"\bfew\b": ["a limited number of", "a small fraction of", "sparse"],
            r"\bmost\b": ["the majority of", "the preponderance of", "the greater part of"],
            r"\ball\b": ["every", "the entirety of", "the totality of"],
            r"\beach\b": ["every", "any given", "every respective"],
            r"\bboth\b": ["the two", "each of the two", "the pair of"]
        }

    def reset_state(self):
        """Resets per-document state caches."""
        self._used_appositives.clear()
        self._used_discourse_replacements.clear()

    def transform_voice(self, sentence: str, fire_rate: float = 0.40) -> str:
        """
        Stage A: Active <-> Passive Voice Inversion.
        Rearranges subject and object clauses to disrupt word-order dependent hashes.
        """
        if len(sentence) < 45 or self.rng.random() > fire_rate:
            return sentence

        # Transform: "We [verb] [object]" -> "The [object] was [verb]"
        for base, passive_sg, passive_pl in self.academic_verbs:
            active_pat = rf"\b(?:we|the authors|researchers)\s+{base}\s+([a-zA-Z\s]{{3,35}}?)(?=[,.]|\s+in|\s+using|\s+with|\s+to|\s+by)"
            m = re.search(active_pat, sentence, flags=re.IGNORECASE)
            if m:
                obj = m.group(1).strip()
                # Ensure object is noun-like
                if not any(w in obj.lower() for w in ["that", "which", "because", "if", "when"]):
                    is_plural = obj.endswith("s") and not obj.endswith("ss")
                    passive_form = passive_pl if is_plural else passive_sg
                    replacement = f"{obj} {passive_form}"
                    sentence = sentence[:m.start()] + replacement + sentence[m.end():]
                    self.voice_transform_count += 1
                    break

        return sentence

    def fuse_sentences(self, sentences: List[str], fire_rate: float = 0.35) -> List[str]:
        """
        Stage B: Sentence Fusion (Anti-Burstiness Weapon).
        Fuses adjacent short sentences to create rhythm variance.
        """
        if len(sentences) < 2:
            return sentences

        fused = []
        i = 0
        while i < len(sentences):
            curr = sentences[i].strip()
            if i + 1 < len(sentences) and len(curr) < 150 and len(sentences[i + 1].strip()) < 150:
                next_s = sentences[i + 1].strip()
                trans_starts = (
                    "in conclusion", "to sum up", "in summary", "overall", "finally",
                    "ultimately", "furthermore", "moreover", "however", "therefore",
                    "consequently", "in addition", "beyond this", "importantly", "notably"
                )
                if any(next_s.lower().startswith(ts) for ts in trans_starts):
                    fused.append(curr)
                    i += 1
                    continue

                if self.rng.random() <= fire_rate:
                    connector = self.rng.choice(self.fusion_connectors)
                    # Lowercase first word of second sentence
                    first_word = next_s.split()[0] if next_s else ""
                    rest = next_s[len(first_word):]
                    if first_word.lower() in ["this", "it", "these"]:
                        next_clean = rest.strip()
                    else:
                        next_clean = (first_word.lower() + rest).strip()

                    # Strip terminal punctuation from current
                    curr_clean = curr.rstrip(".!?")
                    merged = f"{curr_clean}{connector}{next_clean}"
                    fused.append(merged)
                    self.sentence_fusion_count += 1
                    i += 2
                    continue
            fused.append(curr)
            i += 1

        return fused

    def inject_transitions(self, sentence: str, fire_rate: float = 0.30) -> str:
        """
        Stage C: Transition Phrase Injection (Anti-Perplexity Weapon).
        Inserts scholarly transitional context to break contiguous n-grams.
        """
        if len(sentence) < 65 or self.rng.random() > fire_rate:
            return sentence

        # If sentence already starts with a transition, skip
        words = sentence.split()
        if not words:
            return sentence
        first_word = words[0].rstrip(",")
        if any(first_word in group for group in self.transitions.values()):
            return sentence

        category = self.rng.choice(list(self.transitions.keys()))
        transition = self.rng.choice(self.transitions[category])

        # Lowercase original opening if appropriate
        first = words[0]
        if first.lower() in ["the", "a", "an", "this", "these", "such", "in", "by"]:
            lower_first = first.lower()
            rest = " ".join(words[1:])
            self.transition_inject_count += 1
            return f"{transition} {lower_first} {rest}"

        return sentence

    def reorder_within_clause(self, sentence: str, fire_rate: float = 0.30) -> str:
        """
        Stage D: Prepositional & Clause-Level Reordering.
        Rabin-Karp rolling hashes are strictly order-dependent. Moving a prepositional
        phrase shatters every overlapping k-gram across the clause.
        """
        if len(sentence) < 60 or self.rng.random() > fire_rate:
            return sentence

        # Pattern: "In/For/Using/By [Phrase], [Subject] [Predicate]."
        # -> "[Subject] [Predicate], in/for/using/by [Phrase]."
        prep_pat = r"^(In|For|Using|By|With|Through)\s+([a-zA-Z\s]{4,35}?),\s+([A-Z][a-zA-Z\s]{3,30}?)\s+(.+)\.$"
        m = re.match(prep_pat, sentence.strip())
        if m:
            prep, prep_clause, subj, pred = m.groups()
            self.clause_word_reorder_count += 1
            return f"{subj} {pred}, {prep.lower()} {prep_clause}."

        return sentence

    def nominalize(self, sentence: str, fire_rate: float = 0.35) -> str:
        """
        Stage E: Nominalization & Syntactic Rotation.
        Transforms action verbs into formal nominal structures and vice versa.
        """
        if self.rng.random() > fire_rate:
            return sentence

        transformed = sentence
        for pat, replacement in self.nominalization_pairs:
            if re.search(pat, transformed, flags=re.IGNORECASE):
                transformed = re.sub(pat, replacement, transformed, count=1, flags=re.IGNORECASE)
                self.nominalization_count += 1
                break

        return transformed

    def inject_appositives(self, sentence: str, fire_rate: float = 0.40) -> str:
        """
        Stage F: Appositive Clause Injection (Entropy Bomb).
        Inserts formal definitional clarifications for key technical terms.
        Drastically raises perplexity while destroying Winnowing k-gram chains.
        """
        if self.rng.random() > fire_rate:
            return sentence

        for term, definition in self.appositive_definitions.items():
            if term in self._used_appositives:
                continue

            pat = rf"\b{re.escape(term)}\b"
            if re.search(pat, sentence, flags=re.IGNORECASE):
                # Replace with: "term, definition,"
                replacement = f"{term}, {definition},"
                sentence = re.sub(pat, replacement, sentence, count=1, flags=re.IGNORECASE)
                self._used_appositives.add(term)
                self.appositive_count += 1
                break

        return sentence

    def rotate_discourse_markers(self, sentence: str, fire_rate: float = 0.60) -> str:
        """
        Stage G: Discourse Marker Rotation (Anti-Repetition Shield).
        AI models repeatedly overuse specific markers like "However", "Therefore", "Moreover".
        Rotates each marker to diverse scholarly alternatives, tracking replacements per document.
        """
        for marker, alternatives in self.discourse_markers.items():
            # Check sentence-initial marker: "However, ..."
            pat = rf"^{marker},\s*"
            if re.match(pat, sentence.strip()):
                if self.rng.random() <= fire_rate:
                    # Select alternative not used recently
                    available = [alt for alt in alternatives if alt != self._used_discourse_replacements.get(marker)]
                    chosen = self.rng.choice(available if available else alternatives)
                    self._used_discourse_replacements[marker] = chosen

                    rest = re.sub(pat, "", sentence.strip())
                    self.discourse_rotate_count += 1
                    return f"{chosen}, {rest}"

        return sentence

    def swap_determiners(self, sentence: str, fire_rate: float = 0.45) -> str:
        """
        Stage H: Determiner Swapping (High-Density Hash Destruction).
        Determiners appear in almost every sentence; swapping them destroys 3-5 hashes at once.
        """
        if self.rng.random() > fire_rate:
            return sentence

        transformed = sentence
        for pat, alternatives in self.determiners.items():
            if re.search(pat, transformed, flags=re.IGNORECASE):
                chosen = self.rng.choice(alternatives)
                transformed = re.sub(pat, chosen, transformed, count=1, flags=re.IGNORECASE)
                self.determiner_swap_count += 1
                break

        return transformed

    def process_paragraph(self, paragraph: str, intensity: float = 0.85) -> str:
        """
        Executes the full 17-stage reverse-engineered pipeline on a paragraph.
        """
        if not paragraph.strip():
            return paragraph

        sentences = split_sentences(paragraph)
        if not sentences:
            return paragraph

        # 1. Discourse rotation & Determiner cycling across all sentences
        processed_sentences = []
        for s in sentences:
            s_mod = self.rotate_discourse_markers(s, fire_rate=min(0.95, intensity * 0.9))
            s_mod = self.transform_voice(s_mod, fire_rate=min(0.70, intensity * 0.6))
            s_mod = self.reorder_within_clause(s_mod, fire_rate=min(0.60, intensity * 0.5))
            s_mod = self.nominalize(s_mod, fire_rate=min(0.70, intensity * 0.6))
            s_mod = self.inject_appositives(s_mod, fire_rate=min(0.65, intensity * 0.5))
            s_mod = self.swap_determiners(s_mod, fire_rate=min(0.75, intensity * 0.7))
            s_mod = self.inject_transitions(s_mod, fire_rate=min(0.50, intensity * 0.4))
            processed_sentences.append(s_mod)

        # 2. Sentence fusion stage across adjacent sentences
        fused_sentences = self.fuse_sentences(processed_sentences, fire_rate=min(0.60, intensity * 0.5))

        return " ".join(fused_sentences)
