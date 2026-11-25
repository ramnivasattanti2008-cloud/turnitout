"""
AI Cliché & Marker Cleaner.
Detects and dynamically replaces common AI filler phrases, robotic transition markers,
and predictable LLM sentence openings with authentic human cadences, strictly preserving
part of speech and grammatical structure.
"""

import random
import re
from typing import Dict, List, Tuple


class MarkerCleaner:
    """
    Cleans formulaic AI tropes, cliché metaphors, and robotic transitional boilerplate
    while strictly preserving grammatical agreement and verb tenses.
    """

    def __init__(self):
        # Precise phrase mappings with humanized alternatives (regex pattern, list of natural replacements)
        self.phrase_replacements: List[Tuple[str, List[str]]] = [
            # Openings & conclusions (with punctuation matching)
            (r"\bIn conclusion,?\b", ["Ultimately,", "In the end,", "In the final analysis,", "Taken as a whole,"]),
            (r"\bTo sum up,?\b", ["In short,", "Broadly speaking,", "To put it simply,"]),
            (r"\bIn summary,?\b", ["Overall,", "Simply put,", "Taken together,"]),
            (r"\b(?:Furthermore|Moreover|Additionally|In addition),\s+(?:it is\s+(?:crucial|important|vital|imperative|essential)\s+to\s+(?:remember|note|keep in mind|recognize|acknowledge|understand|appreciate)\s+that|one must\s+(?:recognize|note|admit)\s+that)\b", ["Importantly,", "Crucially,", "Beyond this,", "What is more,"]),
            (r"\bIt is (?:crucial|important|vital|imperative|essential) to (?:remember|note|keep in mind|recognize|acknowledge|understand|appreciate) that\b", ["Notably,", "Importantly,", "Crucially,", "In practice,"]),
            (r"\bIt goes without saying that\b", ["Naturally,", "Of course,", "Undoubtedly,"]),
            (r"\bServes as a reminder that\b", ["reminds us that", "shows that", "makes clear that"]),
            (r"\bSheds light on\b", ["illuminates", "clarifies", "explains", "exposes"]),
            (r"\bUnderscores the importance of\b", ["highlights", "stresses", "demonstrates the weight of"]),

            # Temporal LLM openers
            (r"\bin today's (?:fast-paced|competitive|digital|modern|rapidly evolving)?\s*(?:[a-zA-Z-]+\s+)?(?:world|era|age|landscape|environment),?\b", ["Today,", "In recent years,", "In contemporary practice,", "In the modern era,"]),

            # Clichés & Metaphors (strictly respecting verb tenses and parts of speech)
            (r"\bdelve into\b", ["examine", "explore", "probe", "sift through", "investigate"]),
            (r"\bdelves into\b", ["examines", "explores", "probes", "sifts through", "investigates"]),
            (r"\bdelving into\b", ["examining", "exploring", "probing", "sifting through", "investigating"]),
            (r"\bby delving (?:deeper )?into\b", ["by examining", "by exploring", "by looking into"]),

            # Role phrases (with gerund vs nominal complements)
            (r"\bplays a (?:(?:crucial|vital|pivotal|key|multifaceted)\s*(?:and\s+)?)+role in\s+([a-z]+ing)\b", [r"is central to \1", r"proves essential for \1", r"directly aids in \1"]),
            (r"\bplay a (?:(?:crucial|vital|pivotal|key|multifaceted)\s*(?:and\s+)?)+role in\s+([a-z]+ing)\b", [r"are central to \1", r"prove essential for \1", r"directly aid in \1"]),
            (r"\bplays a (?:(?:crucial|vital|pivotal|key|multifaceted)\s*(?:and\s+)?)+role in\b", ["is central to", "fundamentally shapes", "underpins", "anchors"]),
            (r"\bplay a (?:(?:crucial|vital|pivotal|key|multifaceted)\s*(?:and\s+)?)+role in\b", ["are central to", "fundamentally shape", "underpin", "anchor"]),

            # Testament phrases (maintaining linking verbs!)
            (r"\bstands as a testament to\b", ["powerfully reflects", "stands as proof of", "clearly exemplifies", "serves as living proof of", "powerfully validates"]),
            (r"\bstand as a testament to\b", ["powerfully reflect", "stand as proof of", "clearly exemplify", "serve as living proof of", "powerfully validate"]),
            (r"\b(?:bears?|serves? as|stands? as)?\s*(?:a\s+)?testament to\b", ["clearly exemplifies", "stands as tangible proof of", "powerfully validates", "serves as direct evidence of"]),
            (r"\ba testament to\b", ["clear proof of", "a direct reflection of", "evidence of", "a reflection of"]),

            # Stepping stone
            (r"\bstands as a stepping stone to\b", ["serves as a foundation for", "acts as a stepping stone toward", "provides a doorway to"]),
            (r"\ba stepping stone to\b", ["a practical foundation for", "a doorway to", "a stepping stone to", "a key building block for"]),

            # Tapestry & Beacon
            (r"\brich tapestry of\b", ["rich variety of", "broad spectrum of", "diverse array of", "interconnected web of"]),
            (r"\btapestry of\b", ["mosaic of", "spectrum of", "blend of", "array of"]),
            (r"\bbeacon of hope\b", ["symbol of promise", "promising sign", "source of optimism", "vital anchor"]),
            (r"\b(?:rapidly |ever-)?evolving landscape\b", ["rapidly shifting environment", "fast-moving field", "dynamic space", "changing landscape"]),

            # Approaches
            (r"\ba multifaceted approach\b", ["a layered strategy", "a versatile plan", "a comprehensive methodology", "a well-rounded approach"]),
            (r"\ba holistic approach\b", ["a comprehensive plan", "an integrated framework", "an all-around strategy"]),

            # Navigating (both -ing and base verb)
            (r"\bnavigating the complexities of\b", ["working through the nuances of", "handling the challenges of", "managing the intricacies of", "tackling"]),
            (r"\bnavigate the complexities of\b", ["work through the nuances of", "handle the challenges of", "manage the intricacies of", "tackle"]),

            # Imperative
            (r"\b(?:is )?imperative to\b", ["is essential to", "is vital to", "is necessary to", "is required to"]),
            (r"\bimperative\b", ["essential", "vital", "critical", "necessary"]),

            # Harnessing (both -ing and base verb)
            (r"\bharnessing the power of\b", ["tapping into", "leveraging", "capitalizing on", "putting to work"]),
            (r"\bharness the power of\b", ["tap into", "leverage", "capitalize on", "put to work"]),

            # Other markers
            (r"\bgame-changer\b", ["major breakthrough", "turning point", "decisive shift"]),
            (r"\ba double-edged sword\b", ["a delicate trade-off", "a mixed blessing", "a complex balance"]),
            (r"\bat the forefront of\b", ["leading", "spearheading", "at the cutting edge of"]),
            (r"\bsounds like\b", ["appears to be", "seems to be", "resembles"]),
            (r"\bsound like\b", ["appear to be", "seem to be", "resemble"]),
            (r"\bto be sure,?\s*", ["Admittedly, ", "Certainly, ", "Clearly, "]),
            (r"\bdelves into\b", ["probes", "investigates", "examines", "explores"]),
            (r"\bdelve into\b", ["probe", "investigate", "examine", "explore"]),

            (r"\bto foster\b", ["to cultivate", "to build", "to nurture", "to encourage"]),
            (r"\bfosters a (?:deep |profound )?sense of\b", ["builds", "cultivates", "nurtures", "inspires"]),
            (r"\bfoster a (?:deep |profound )?sense of\b", ["build", "cultivate", "nurture", "inspire"]),
            (r"\bfosters\b", ["builds", "cultivates", "encourages"]),
            (r"\bfoster\b", ["build", "cultivate", "encourage"]),

            (r"\bpaves the way for\b", ["opens clear paths for", "sets the stage for", "makes room for"]),
            (r"\bpave the way for\b", ["open clear paths for", "set the stage for", "make room for"]),
            (r"\bpoised to\b", ["ready to", "geared up to", "set to"]),
            (r"\ba profound (?:impact|sense)\b", ["a lasting impression", "a deep mark", "a strong impression"]),
            (r"\bseamlessly integrates\b", ["integrates cleanly", "meshes smoothly", "blends naturally"]),
            (r"\bseamlessly integrate\b", ["integrate cleanly", "mesh smoothly", "blend naturally"]),
            (r"\bin the realm of\b", ["within", "in the field of", "across"]),
            (r"\bresonates deeply with\b", ["strikes a chord with", "hits home with", "strongly connects with"]),
            (r"\bundeniably\b", ["clearly", "certainly", "truly"]),

            # Transitional adverbs (comma-sensitive)
            (r"\bFurthermore,\s*", ["What is more, ", "Beyond this, ", "Additionally, ", "In addition, "]),
            (r"\bfurthermore\b", ["in addition", "additionally", "also"]),
            (r"\bFurthermore\b", ["In addition", "Additionally", "Also"]),
            (r"\bMoreover,\s*", ["Equally important, ", "At the same time, ", "Further, ", "In turn, "]),
            (r"\bmoreover\b", ["further", "in addition", "additionally"]),
            (r"\bMoreover\b", ["Further", "In addition", "Additionally"]),
            (r"\bNevertheless,?\b", ["Still,", "Even so,", "That said,", "Regardless,"]),
            (r"\bNotwithstanding,?\b", ["Despite this,", "Regardless,", "Even with that,"]),

            # Standalone AI buzzwords that LLMs constantly overuse
            (r"\bmultifaceted\b", ["varied", "layered", "diverse", "broad-ranging", "wide-ranging"]),
            (r"\bnuanced\b", ["subtle", "detailed", "fine-grained", "measured", "refined"]),
            (r"\bintertwined(?:\s+with)?\b", ["connected with", "linked to", "tied to", "woven into"]),
            (r"\bholistic\b", ["comprehensive", "well-rounded", "broad", "integrated", "thorough"]),
            (r"\bplethora of\b", ["wealth of", "abundance of", "broad array of", "wide variety of"]),
            (r"\bmyriad(?:\s+of)?\b", ["countless", "numerous", "broad range of", "wide array of"]),
            (r"\bjuxtaposition(?:\s+of)?\b", ["contrast between", "interplay between", "comparison of"]),
            (r"\boverarching\b", ["central", "primary", "underlying", "core", "foundational"]),
            (r"\bpivotal\b", ["central", "essential", "critical", "key", "decisive"]),
            (r"\bparamount\b", ["primary", "essential", "foremost", "central"]),
            (r"\bunderscores\b", ["highlights", "stresses", "demonstrates", "accentuates"]),
            (r"\bunderscore\b", ["highlight", "stress", "demonstrate", "accentuate"])
        ]

    def clean(self, text: str) -> str:
        """
        Scans text and substitutes all detected AI cliché markers with organic human phrasing.
        Preserves natural casing and surrounding punctuation.
        """
        cleaned = text

        for pattern, replacements in self.phrase_replacements:
            matches = list(re.finditer(pattern, cleaned, flags=re.IGNORECASE))
            if not matches:
                continue

            for m in reversed(matches):
                chosen = random.choice(replacements)
                matched_str = m.group(0)

                # Keep capitalization style
                if matched_str[0].isupper():
                    chosen = chosen[0].upper() + chosen[1:]
                else:
                    chosen = chosen[0].lower() + chosen[1:]

                # Expand backreferences (e.g. \1)
                for group_idx in range(1, len(m.groups()) + 1):
                    grp_val = m.group(group_idx) or ""
                    chosen = chosen.replace(f"\\{group_idx}", grp_val)

                cleaned = cleaned[:m.start()] + chosen + cleaned[m.end():]

        # Clean redundant double commas and spacing
        cleaned = re.sub(r",\s*,+", ",", cleaned)
        cleaned = re.sub(r"[ ]{2,}", " ", cleaned)
        return cleaned.strip()
