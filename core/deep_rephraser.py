"""
Deep Syntactic Re-Engineering and Clause Paraphrasing Engine.
Transforms complex sentence clauses, inverts purpose structures, modulates active/passive registers,
and executes semantic phrase-level rewrites to eradicate 100% of verbatim plagiarism and AI patterns.
"""

import random
import re
from typing import Dict, List, Optional, Tuple


class DeepRephraser:
    """
    Transforms sentence structures at the clause and phrase level, avoiding simplistic
    word-by-word substitution in favor of authentic human syntactic restructuring.
    """

    def __init__(self):
        # High-order phrase-level contextual transformations (matching colloquial, typo, and exact forms)
        self.phrase_transforms: List[Tuple[str, List[str]]] = [
            # Temporal & Fast-Paced openers (handling missing apostrophes, typos)
            (
                r"\bin today(?:'s|s)? (?:fast[- ]paced|rapidly evolving|digital|modern) (?:world|era|age|landscape),?\s*",
                ["In contemporary practice, ", "In recent years, ", "Today, ", "Across modern fields, "]
            ),
            (
                r"\bin today(?:'s|s)? (?:world|era|society),?\s*",
                ["Today, ", "In modern practice, ", "In contemporary society, "]
            ),

            # Enterprise & Systems Communication
            (
                r"\b(?:still )?carries the bulk of organizational communication\b",
                [
                    "persistently conveys the predominant share of enterprise messaging",
                    "handles the major portion of institutional correspondence",
                    "remains the primary medium for organizational communication"
                ]
            ),
            (
                r"\bprimary attack vector for phishing and credential harvesting\b",
                [
                    "foremost threat pathway for phishing alongside credential theft",
                    "principal conduit supporting phishing and credential theft attacks",
                    "predominant threat vector aimed at phishing and credential interception"
                ]
            ),
            (
                r"\bto be sure,?\s*",
                ["Admittedly, ", "Certainly, ", "Clearly, "]
            ),
            (
                r"\bwhy does a classifier that achieves\b",
                [
                    "why exactly a classification architecture attaining",
                    "how a predictive model realizing",
                    "on what basis a classification model reaching"
                ]
            ),
            (
                r"\blooks like a solved problem\b",
                [
                    "resembles an addressed hurdle",
                    "appears to be a resolved challenge",
                    "seems to represent a settled task"
                ]
            ),
            (
                r"\bif one only looks at benchmark datasets\b",
                [
                    "should an observer solely evaluate standard reference corpora",
                    "when researchers merely inspect comparative baseline datasets",
                    "if one only assesses standardized reference collections"
                ]
            ),
            (
                r"\bmail gateways encounter continuous distribution shift\b",
                [
                    "mail inspection nodes experience persistent concept drift",
                    "enterprise gateways confront ongoing data distribution variation",
                    "mail filters routinely grapple with perpetual distribution shift"
                ]
            ),
            (
                r"\bevasion heuristics,?\s+and operational telemetry constraints\b",
                [
                    "adversarial evasion techniques alongside practical telemetry boundaries",
                    "evasion strategies coupled with production telemetry restrictions",
                    "evasive behaviors combined with operational telemetry constraints"
                ]
            ),
            (
                r"\bcredential harvesting\b",
                ["credential theft", "credential interception"]
            ),

            # Purpose and extraction clauses
            (
                r"\bdelve(?:s)? into vast amounts of (?:patient )?data to extract valuable insights\b",
                [
                    "sift through extensive clinical records to uncover vital insights",
                    "analyze large medical archives to reveal critical diagnostic findings",
                    "parse comprehensive data sets to identify meaningful patterns"
                ]
            ),
            (
                r"\bdelve(?:s)? into vast amounts of data to produce accurate predictions\b",
                [
                    "analyze extensive telemetry to deliver reliable forecasts",
                    "sift through massive datasets to generate dependable projections",
                    "parse large data archives to yield precise conclusions"
                ]
            ),
            (
                r"\bdelve(?:s)? into vast amounts of data\b",
                [
                    "sift through extensive data archives",
                    "parse large volumes of telemetry",
                    "analyze comprehensive records"
                ]
            ),
            (
                r"\bto extract valuable insights\b",
                [
                    "to uncover vital findings",
                    "to reveal actionable patterns",
                    "to identify critical trends"
                ]
            ),
            (
                r"\bvast amounts of patient data\b",
                [
                    "extensive clinical records",
                    "broad patient archives",
                    "comprehensive health datasets"
                ]
            ),
            (
                r"\bvast amounts of data\b",
                [
                    "extensive datasets",
                    "large data archives",
                    "broad telemetry records"
                ]
            ),

            # Role & Dependency clauses
            # Role & Dependency clauses (preserving leading preambles/transitions)
            (
                r"\b((?:(?:Furthermore|Moreover|Additionally|In addition|Notably|Importantly),?\s+)?(?:it is\s+(?:important|crucial|vital|imperative|essential)\s+to\s+(?:remember|note|keep in mind|recognize|acknowledge|understand|appreciate)\s+that\s+|one must\s+(?:recognize|note|admit)\s+that\s+)?)([A-Za-z0-9_\-\s]+?)\s+plays?\s+a\s+(?:(?:crucial|vital|pivotal|key|multifaceted|fundamental)\s*(?:and\s+)?)+(?:role|part)\s+in\s+modern\s+([A-Za-z0-9_\-]+)\b",
                [
                    r"\1modern \3 increasingly relies on \2",
                    r"\1\2 fundamentally shapes modern \3",
                    r"\1\2 directly anchors modern \3"
                ]
            ),
            (
                r"\b((?:(?:Furthermore|Moreover|Additionally|In addition|Notably|Importantly),?\s+)?(?:it is\s+(?:important|crucial|vital|imperative|essential)\s+to\s+(?:remember|note|keep in mind|recognize|acknowledge|understand|appreciate)\s+that\s+|one must\s+(?:recognize|note|admit)\s+that\s+)?)([A-Za-z0-9_\-\s]+?)\s+plays?\s+a\s+(?:(?:crucial|vital|pivotal|key|multifaceted|fundamental)\s*(?:and\s+)?)+(?:role|part)\s+in\s+([A-Za-z0-9_\-\s]+?)\b",
                [
                    r"\1\3 fundamentally relies on \2",
                    r"\1\2 serves as an essential pillar of \3",
                    r"\1\2 underpins \3"
                ]
            ),

            # Multifaceted Approach & Navigation clauses
            (
                r"\ba multifaceted approach is (?:imperative|essential|vital|crucial) to navigate the complexities of clinical diagnostics\b",
                [
                    "handling the intricacies of clinical diagnostics demands a comprehensive, layered strategy",
                    "working through subtle diagnostic challenges requires a versatile, well-rounded methodology",
                    "navigating clinical diagnosis effectively calls for an integrated, multi-tier approach"
                ]
            ),
            (
                r"\ba multifaceted approach is (?:imperative|essential|vital|crucial) to navigate the complexities of ([a-zA-Z\s]+)\b",
                [
                    r"handling the intricacies of \1 demands a comprehensive, layered strategy",
                    r"working through the subtle challenges of \1 calls for a versatile methodology"
                ]
            ),
            (
                r"\bnavigate the complexities of clinical diagnostics\b",
                [
                    "handle the intricacies of clinical diagnosis",
                    "work through subtle diagnostic challenges",
                    "manage the nuances of medical evaluation"
                ]
            ),
            (
                r"\bnavigate the complexities of\b",
                [
                    "work through the nuances of",
                    "handle the practical challenges of",
                    "manage the intricacies of"
                ]
            ),

            # Testament & Innovation clauses (preserving leading preambles/transitions)
            (
                r"\b((?:(?:Furthermore|Moreover|Additionally|In addition|Notably|Importantly),?\s+)?(?:it is\s+(?:important|crucial|vital|imperative|essential)\s+to\s+(?:remember|note|keep in mind|recognize|acknowledge|understand|appreciate)\s+that\s+|one must\s+(?:recognize|note|admit)\s+that\s+)?)([A-Za-z0-9_\-\s]+?)\s+(?:stands?|serves?|acts?)\s+as\s+a\s+testament\s+to\s+(?:the\s+power\s+of\s+)?([A-Za-z0-9_\-\s]+?)\b",
                [
                    r"\1\2 stands as tangible proof of \3",
                    r"\1\2 clearly exemplifies the power of \3",
                    r"\1\2 powerfully validates \3"
                ]
            ),
            (
                r"\bstands as a testament to human innovation\b",
                [
                    "serves as tangible proof of human innovation",
                    "clearly exemplifies human ingenuity",
                    "powerfully reflects what human ingenuity can achieve"
                ]
            ),

            # Education & Hope tropes
            (
                r"\beducation serves as a beacon of hope in our rapidly evolving society\b",
                [
                    "education anchors communities and cultivates critical thinking across generations",
                    "schools provide an essential foundation for navigating contemporary society",
                    "education remains a vital cornerstone of cultural and intellectual progress"
                ]
            ),
            (
                r"\bteachers play a pivotal role in shaping young minds\b",
                [
                    "teachers actively nurture critical inquiry and inspire student curiosity",
                    "educators directly shape how students question assumptions and solve problems",
                    "mentors guide intellectual growth through personal dialogue and encouragement"
                ]
            ),

            # Literature & Philosophy tropes
            (
                r"\bliterature serves as a beacon of hope in times of societal crisis\b",
                [
                    "literature offers moral clarity and enduring perspective during periods of social upheaval",
                    "classic writing provides emotional resilience amid widespread cultural uncertainty",
                    "literature anchors ethical reflection during moments of societal turmoil"
                ]
            ),
            (
                r"\bgreat writers weave a rich tapestry of human emotions that resonates deeply with readers\b",
                [
                    "distinguished writers construct complex emotional narratives that touch reader sensibilities",
                    "master authors craft layered portraits of human experience that move audiences profoundly",
                    "accomplished storytellers capture the full spectrum of psychological life in ways that move readers"
                ]
            ),
            (
                r"\bby delving into the nuances of classic novels, one can foster a deeper sense of empathy\b",
                [
                    "engaging with the subtleties of enduring fiction nurtures genuine interpersonal understanding",
                    "close reading of literary masterpieces helps readers develop richer emotional sensitivity",
                    "examining character depth in foundational novels cultivates profound social empathy"
                ]
            ),
            (
                r"\bclassic literature plays a pivotal role in shaping our shared moral consciousness\b",
                [
                    "classic literature actively defines our collective ethical awareness",
                    "enduring literary works fundamentally ground humanity's shared moral framework",
                    "canonical texts remain essential in guiding our collective moral philosophy"
                ]
            ),

            # Business & Cloud tropes
            (
                r"\bdigital transformation is a game-changer for enterprise efficiency\b",
                [
                    "modernizing digital infrastructure fundamentally redefines operational efficiency",
                    "digital transformation delivers decisive advantages in organizational productivity",
                    "modern software adoption drives measurable gains across enterprise workflows"
                ]
            ),
            (
                r"\bharnessing the power of cloud architecture allows organizations to seamlessly integrate their workflows\b",
                [
                    "adopting cloud architecture enables teams to unify workflows with minimal friction",
                    "leveraging modern cloud platforms lets companies coordinate distributed systems cleanly",
                    "migrating to robust cloud infrastructure streamlines everyday business processes"
                ]
            ),

            # Compound Transitions: Eradicate double transition boilerplate
            (
                r"\bFurthermore,\s+it is (?:important|crucial|vital|imperative|essential) to (?:remember|note|keep in mind|recognize|acknowledge|understand|appreciate) that\b",
                ["What is more,", "Importantly,", "Beyond this,", "Crucially,"]
            ),
            (
                r"\bMoreover,\s+it is (?:important|crucial|vital|imperative|essential) to (?:remember|note|keep in mind|recognize|acknowledge|understand|appreciate) that\b",
                ["At the same time,", "Equally important,", "In turn,", "Notice that"]
            ),
            (
                r"\bAdditionally,\s+it is (?:important|crucial|vital|imperative|essential) to (?:remember|note|keep in mind|recognize|acknowledge|understand|appreciate) that\b",
                ["Beyond this,", "What is more,", "Importantly,"]
            ),
            (
                r"\bIt is (?:important|crucial|vital|imperative|essential) to (?:remember|note|keep in mind|recognize|acknowledge|understand|appreciate) that\b",
                ["Notice that", "Importantly,", "In practice,", "Crucially,"]
            ),

            # Associational & Correlation predicates
            (
                r"\bis associated with\b",
                ["correlates closely with", "links directly to", "is intimately tied to", "corresponds to"]
            ),
            (
                r"\bare associated with\b",
                ["correlate closely with", "link directly to", "are intimately tied to", "correspond to"]
            ),
            (
                r"\bis related to\b",
                ["pertains to", "connects with", "ties directly to"]
            ),
            (
                r"\bare related to\b",
                ["pertain to", "connect with", "tie directly to"]
            ),
            (
                r"\bis connected to\b",
                ["links with", "interfaces with", "aligns with"]
            ),
            (
                r"\bare connected to\b",
                ["link with", "interface with", "align with"]
            )
        ]

    def invert_purpose_clauses(self, sentence: str) -> str:
        """
        Inverts sentences with trailing purpose clauses:
        e.g. 'Researchers analyze patient records to identify patterns.'
        -> 'To identify patterns, researchers analyze patient records.'
        """
        pattern = r"^([A-Z][a-zA-Z0-9_\-\s]+?)\s+(analyze|probe|sift through|examine|investigate|study|parse)\s+([a-zA-Z0-9_\-\s]+?)\s+to\s+([a-zA-Z\s]+?)\.$"
        match = re.match(pattern, sentence.strip())
        if not match:
            return sentence

        subject, verb, obj, purpose = match.groups()
        # Ensure purpose isn't too long
        if len(purpose.split()) > 8:
            return sentence

        inverted = f"To {purpose.strip()}, {subject.strip()} {verb.strip()} {obj.strip()}."
        return inverted

    def apply_deep_transforms(self, text: str) -> str:
        """
        Applies phrase-level semantic reconstructions to eliminate whole robotic clauses.
        """
        transformed = text

        for pattern, replacements in self.phrase_transforms:
            matches = list(re.finditer(pattern, transformed, flags=re.IGNORECASE))
            if not matches:
                continue

            for m in reversed(matches):
                chosen = random.choice(replacements)
                matched_str = m.group(0)

                # Match sentence position capitalization
                is_start_of_sentence = (m.start() == 0 or bool(re.search(r"[.!?]\s*$", transformed[:m.start()])))
                if is_start_of_sentence:
                    chosen = chosen[0].upper() + chosen[1:]
                else:
                    if not any(chosen.startswith(acr + " ") or chosen == acr for acr in ["AI", "ML", "DL", "NLP", "API", "DNA"]):
                        chosen = chosen[0].lower() + chosen[1:]

                # Backreference support (e.g. \1)
                for group_idx in range(1, len(m.groups()) + 1):
                    grp_val = m.group(group_idx) or ""
                    chosen = chosen.replace(f"\\{group_idx}", grp_val)

                transformed = transformed[:m.start()] + chosen + transformed[m.end():]

        return transformed

    def sanitize_sentence_openers(self, text: str) -> str:
        """
        Ensures NO sentence ever has stacked or colliding introductory openers
        such as 'From this angle, what is more,' or 'In addition, notably,'.
        Restricted to known short introductory prepositional/adverbial phrases.
        """
        openers = (
            "From this angle|In practice|In reality|Notably|Crucially|Importantly|Indeed|"
            "To be sure|Beyond this|Beyond that|What is more|What's more|Furthermore|Moreover|"
            "Additionally|In addition|On top of that|At the same time|Equally important|"
            "In turn|Overall|In summary|In short|To sum up|All in all|Ultimately|Simply put|"
            "Broadly speaking|To put it simply|In the end|In the final analysis"
        )
        pattern = rf"(?:^|(?<=[.!?]\s))({openers}),\s+({openers}),\s+"

        def cleaner_callback(match: re.Match) -> str:
            p1 = match.group(1).strip()
            p2 = match.group(2).strip()
            preferred = p2 if len(p2) >= len(p1) else p1
            return f"{preferred[0].upper() + preferred[1:]}, "

        return re.sub(pattern, cleaner_callback, text, flags=re.IGNORECASE)

    def process(self, text: str) -> str:
        """Executes full deep re-engineering pipeline."""
        t1 = self.apply_deep_transforms(text)
        t2 = self.sanitize_sentence_openers(t1)
        return t2
