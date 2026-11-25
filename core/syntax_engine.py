"""
Syntax Restructuring and Burstiness Injection Engine.
Transforms sentence structures, inverts clauses, alternates active/passive cadence,
and varies sentence lengths to eliminate robotic rhythm and destroy verbatim n-grams.
"""

import random
import re
from typing import List, Tuple
from core.metrics import split_sentences, tokenize_words


class SyntaxEngine:
    """
    Performs structural transformations on sentences to induce human-like burstiness,
    clause variation, and syntactic diversity.
    """

    def __init__(self):
        # Conjunctions for merging short sentences
        self.merge_conjunctions = [
            ", and ",
            ", while ",
            "; in turn, ",
            ", yet ",
            "; consequently, "
        ]

        # Natural human discourse markers for sentence openings
        self.organic_openers = [
            "In practice, ",
            "Notably, ",
            "Indeed, ",
            "Viewed closely, ",
            "To be sure, ",
            "From this angle, ",
            "In reality, "
        ]

    def transform_participial_clauses(self, sentence: str) -> str:
        """
        Fronts trailing participial clauses:
        e.g. 'The proliferation of platforms has revolutionized communication, enabling individuals to connect.'
        -> 'By enabling individuals to connect, the proliferation of platforms has revolutionized communication.'
        e.g. 'Artificial intelligence is transforming healthcare by analyzing complex medical data to improve patient outcomes.'
        -> 'By analyzing complex medical data to improve patient outcomes, artificial intelligence is transforming healthcare.'
        """
        pattern_a = r"^([A-Z][^,]+?),\s+(enabling|allowing|facilitating|providing|creating|ensuring|helping|resulting in)\s+(.+)\.$"
        match_a = re.match(pattern_a, sentence.strip())
        if match_a:
            main, part, rest = match_a.groups()
            first_word = main.split()[0]
            if first_word.lower() in ["the", "a", "an", "this", "these", "those", "such", "in", "artificial"]:
                main_lower = first_word.lower() + main[len(first_word):]
            else:
                main_lower = main
            prefix = "By " if not part.startswith("by") else ""
            return f"{prefix}{part} {rest}, {main_lower}."

        pattern_b = r"^([A-Z][^,]+?)\s+(?:,\s+)?by\s+([a-zA-Z]+ing)\s+(.+)\.$"
        match_b = re.match(pattern_b, sentence.strip())
        if match_b:
            main, part, rest = match_b.groups()
            first_word = main.split()[0]
            if first_word.lower() in ["the", "a", "an", "this", "these", "those", "such", "in", "artificial"]:
                main_lower = first_word.lower() + main[len(first_word):]
            else:
                main_lower = main
            return f"By {part} {rest}, {main_lower}."

        return sentence

    def transform_such_as_clauses(self, sentence: str) -> str:
        """
        Restructures exemplification clauses cleanly without awkward phrasing:
        e.g. 'Renewable energy sources such as solar and wind power are becoming indispensable.'
        -> 'Solar and wind power, alongside other renewable energy sources, are becoming indispensable.'
        e.g. 'Transitioning to renewable energy sources such as solar and wind power is essential to mitigate carbon emissions.'
        -> 'Adopting solar and wind power, alongside other renewable energy sources, is essential to mitigate carbon emissions.'
        """
        pattern = r"^([A-Z][a-zA-Z\s]+?)\s+such as\s+([a-zA-Z\s]+?)\s+(are|is)\s+(.+)\.$"
        match = re.match(pattern, sentence.strip())
        if not match:
            return sentence

        category, examples, copula, predicate = match.groups()

        # Handle gerund openers like 'Transitioning to renewable energy sources'
        gerund_match = re.match(r"^(Transitioning to|Shifting toward|Adopting|Implementing|Investing in|Moving toward)\s+(.+)$", category.strip(), flags=re.IGNORECASE)
        if gerund_match:
            action, core_cat = gerund_match.groups()
            return f"Adopting {examples.strip()}, alongside other {core_cat.strip().lower()}, {copula} {predicate}."

        first_word = category.split()[0]
        cat_lower = first_word.lower() + category[len(first_word):] if first_word.lower() in ["the", "a", "an"] else category.lower()
        if cat_lower.startswith("other "):
            cat_phrase = cat_lower
        else:
            cat_phrase = f"other {cat_lower}"
        return f"{examples.strip().capitalize()}, alongside {cat_phrase}, {copula} {predicate}."

    def transform_superlative_openers(self, sentence: str) -> str:
        """
        Restructures formulaic superlative claims:
        e.g. 'Climate change remains one of the most pressing global challenges of our time.'
        -> 'Among the most critical global challenges of our time, climate change continues to persist as a paramount concern.'
        """
        pattern = r"^([A-Z][a-zA-Z0-9_\-\s]+?)\s+(remains|stands as|is)\s+one of the most\s+([a-zA-Z]+)\s+([a-zA-Z0-9_\-\s]+?)\s+of (our time|the modern era|today)\.$"
        match = re.match(pattern, sentence.strip(), flags=re.IGNORECASE)
        if not match:
            return sentence

        subject, verb, adj, scope, era = match.groups()
        # Choose a fresh synonym for the adjective if possible
        adj_map = {
            "pressing": "critical", "urgent": "acute", "critical": "vital",
            "significant": "consequential", "important": "foundational"
        }
        new_adj = adj_map.get(adj.lower(), "salient")
        return f"Among the most {new_adj} {scope.strip()} of {era.strip()}, {subject.strip()} persists as a primary concern."

    def transform_research_clauses(self, sentence: str) -> str:
        """
        Restructures empirical / academic evidence statements:
        e.g. 'However, research suggests that excessive screen time is associated with heightened anxiety and depressive symptoms among adolescents.'
        -> 'However, empirical findings indicate that excessive screen time correlates closely with heightened anxiety and depressive symptoms among adolescents.'
        """
        pattern = r"^((?:However,\s+|Moreover,\s+|Furthermore,\s+)?)(research|studies|evidence|data)\s+(suggests|suggest|indicates|indicate|shows|show)\s+that\s+(.+)$"
        match = re.match(pattern, sentence.strip(), flags=re.IGNORECASE)
        if not match:
            return sentence

        lead, subject, verb, clause = match.groups()
        lead_str = lead or ""
        subj_choice = "empirical findings" if "research" in subject.lower() or "studies" in subject.lower() else "scholarly evidence"
        verb_choice = "indicate" if subj_choice == "empirical findings" else "suggests"
        return f"{lead_str}{subj_choice} {verb_choice} that {clause}"

    def transform_addressing_clauses(self, sentence: str) -> str:
        """
        Restructures intervention statements:
        e.g. 'Addressing these mental health challenges requires concerted interventions from educators, policymakers, and technology companies.'
        -> 'Tackling these mental health challenges necessitates concerted interventions from educators, policymakers, and technology companies.'
        """
        pattern = r"^(Addressing|Tackling|Confronting|Managing)\s+(these|such|the)\s+([a-zA-Z0-9_\-\s]+?)\s+(requires|demands|necessitates)\s+(.+)$"
        match = re.match(pattern, sentence.strip(), flags=re.IGNORECASE)
        if not match:
            return sentence

        verb, determiner, issue, req_verb, rest = match.groups()
        new_lead = "Tackling" if verb.lower() == "addressing" else "Addressing"
        new_req = "necessitates" if req_verb.lower() in ["requires", "demands"] else "calls for"
        return f"{new_lead} {determiner.lower()} {issue.strip()} {new_req} {rest}"

    def transform_consequential_coordination(self, sentence: str) -> str:
        """
        Restructures dual subject threat / impact structures:
        e.g. 'Rising temperatures and extreme weather events threaten ecosystems and human livelihoods across the globe.'
        -> 'Across the globe, ecosystems and human livelihoods face severe threats from rising temperatures alongside extreme weather events.'
        """
        pattern = r"^([A-Z][a-zA-Z\s]+?)\s+and\s+([a-zA-Z\s]+?)\s+(threaten|jeopardize|imperil)\s+([a-zA-Z\s]+?)\s+(across\s+the\s+globe|worldwide|globally)\.$"
        match = re.match(pattern, sentence.strip(), flags=re.IGNORECASE)
        if not match:
            return sentence

        subj1, subj2, verb, obj, loc = match.groups()
        loc_str = loc.strip().capitalize()
        return f"{loc_str}, {obj.strip()} face heightened risks from {subj1.strip().lower()} alongside {subj2.strip().lower()}."

    def split_compound_sentence(self, sentence: str) -> List[str]:
        """
        Splits overly long, symmetrical compound sentences (>= 22 words) into
        two punchy, natural statements to inject high human burstiness and shatter n-grams.
        """
        clean = sentence.strip()
        words = tokenize_words(clean)
        if len(words) < 22:
            return [clean]

        # Try splitting at ", while " or ", and " or ", but "
        split_pats = [
            (r",\s+while\s+", ". Meanwhile, "),
            (r",\s+whereas\s+", ". In contrast, "),
            (r",\s+and\s+(thereby|thus|consequently)\s+", ". As a result, "),
            (r",\s+and\s+therefore\s+", ". Therefore, "),
            (r",\s+but\s+", ". However, ")
        ]
        for pat, replacement in split_pats:
            if re.search(pat, clean, flags=re.IGNORECASE):
                spl = re.sub(pat, replacement, clean, count=1, flags=re.IGNORECASE)
                parts = [p.strip() for p in spl.split(". ") if p.strip()]
                res = []
                for idx, p in enumerate(parts):
                    if not p.endswith("."):
                        p += "."
                    res.append(p)
                return res

        return [clean]

    def invert_subordinate_clauses(self, sentence: str) -> str:
        """
        Inverts dependent and main clauses:
        e.g. 'Although X happened, Y succeeded.' -> 'Y succeeded, although X happened.'
        e.g. 'Because A occurred, B resulted.' -> 'B resulted, largely because A occurred.'
        """
        # Match 'Although/While/Since/Because/When [Clause 1], [Clause 2].'
        pattern = r"^(Although|Even though|While|Because|Since|When|If)\s+([^,]+),\s+(.+)$"
        match = re.match(pattern, sentence.strip(), flags=re.IGNORECASE)
        if not match:
            return sentence

        conjunction, clause1, clause2 = match.groups()
        # Clean terminal punctuation from clause 2
        clause2_clean = clause2.rstrip(".!?")
        terminator = sentence[-1] if sentence[-1] in ".!?" else "."

        # Guard against inverting short fixed idioms or sentence fragments
        if len(clause1.split()) < 4 or len(clause2_clean.split()) < 4:
            return sentence

        # Check if clause 2 starts with lower or capital
        c2_words = clause2_clean.split(" ")
        if c2_words:
            c2_capitalized = c2_words[0].capitalize() + " " + " ".join(c2_words[1:])
        else:
            c2_capitalized = clause2_clean

        # Build inverted sentence
        conj_lower = conjunction.lower()
        if conj_lower in ["because", "since"]:
            conj_phrase = f", primarily because {clause1}"
        else:
            conj_phrase = f", {conj_lower} {clause1}"

        inverted = f"{c2_capitalized}{conj_phrase}{terminator}"
        return inverted

    def convert_passive_patterns(self, sentence: str) -> str:
        """
        Converts predictable passive phrases to active voice, and vice-versa,
        shattering verbatim strings.
        e.g. 'Developing countries are disproportionately affected by environmental shifts'
        -> 'Environmental shifts disproportionately affect developing countries'
        """
        # Pattern 1: 'X are/is [adverb] affected/impacted by Y'
        pat_affected = r"\b([A-Z][a-zA-Z0-9_\-\s]+?)\s+(are|is|were|was)\s+([a-zA-Z]+ly\s+)?(affected|impacted|shaped|influenced)\s+by\s+([a-zA-Z0-9_\-\s]+?)(?:(?=[\.,;])|$)"
        m_aff = re.search(pat_affected, sentence)
        if m_aff:
            subj, copula, adv, verb, agent = m_aff.groups()
            adv_str = adv or ""
            # Simple plural check
            v_active = "affect" if "are" in copula or "were" in copula else "affects"
            if verb == "impacted":
                v_active = "impact" if "are" in copula or "were" in copula else "impacts"
            elif verb == "shaped":
                v_active = "shape" if "are" in copula or "were" in copula else "shapes"
            elif verb == "influenced":
                v_active = "influence" if "are" in copula or "were" in copula else "influences"

            agent_cap = agent.strip().capitalize()
            subj_lower = subj.strip()[0].lower() + subj.strip()[1:]
            active_clause = f"{agent_cap} {adv_str}{v_active} {subj_lower}"
            new_s = sentence[:m_aff.start()] + active_clause + sentence[m_aff.end():]
            return re.sub(r"[ ]{2,}", " ", new_s)

        # Pattern 2: 'was/is [verb]ed by [agent]'
        pattern = r"\b(was|is|were|are)\s+([a-zA-Z]+ed)\s+by\s+([A-Za-z\s]+?)(?:(?=[\.,;])|$)"
        match = re.search(pattern, sentence)
        if not match:
            return sentence

        aux, verb, agent = match.groups()
        agent_clean = agent.strip()
        if len(agent_clean.split()) > 4:
            return sentence

        active_phrase = f"{agent_clean} {verb} "
        new_sentence = sentence[:match.start()] + active_phrase + sentence[match.end():]
        return re.sub(r"[ ]{2,}", " ", new_sentence)

    def inject_burstiness(self, sentences: List[str], target_ratio: float = 1.4) -> List[str]:
        """
        Varies sentence lengths dynamically:
        - Pairs short, adjacent sentences with coordinating junctions or em-dashes.
        - Keeps select sentences short and punchy for rhetorical cadence.
        - Inverts clauses where possible.
        """
        if len(sentences) <= 1:
            return sentences

        transformed: List[str] = []
        i = 0
        n = len(sentences)

        while i < n:
            current = sentences[i].strip()
            curr_words = tokenize_words(current)
            curr_len = len(curr_words)

            # Try clause restructuring first
            current = self.transform_superlative_openers(current)
            current = self.transform_research_clauses(current)
            current = self.transform_addressing_clauses(current)
            current = self.transform_consequential_coordination(current)
            current = self.transform_participial_clauses(current)
            current = self.transform_such_as_clauses(current)
            current = self.invert_subordinate_clauses(current)
            current = self.convert_passive_patterns(current)

            # If current sentence and next sentence are short/medium, occasionally merge for rhythmic variance
            if curr_len < 22 and i + 1 < n and random.random() < 0.65:
                next_sent = sentences[i + 1].strip()
                next_words = tokenize_words(next_sent)

                if len(next_words) < 22 and not re.match(r"^(in conclusion|to sum up|in summary|ultimately|taken as a whole|in the end)\b", next_sent.strip(), flags=re.IGNORECASE):
                    # Merge them
                    curr_stripped = current.rstrip(".!?")
                    next_stripped = next_sent.rstrip(".!?")
                    terminator = next_sent[-1] if next_sent[-1] in ".!?" else "."

                    # Strip redundant transitional phrases from second sentence if merging
                    next_clean = re.sub(
                        r"^(Beyond this|Beyond that|What is more|What's more|Furthermore|Moreover|In addition|On top of that|Additionally|Plus|Remember|Notably|Significantly|Crucially|Importantly|In practice|To be sure|Further|In turn|Overall|In summary|In short|To sum up|All in all|Ultimately|Taken together|Simply put|Broadly speaking|To put it simply|In the end|In the final analysis|Equally important|Equally pivotal|As a result|Consequently|Hence),\s*",
                        "",
                        next_stripped,
                        flags=re.IGNORECASE
                    )
                    next_tokens = next_clean.split(" ")
                    if next_tokens and len(next_tokens[0]) > 0:
                        first_tok = next_tokens[0]
                        if first_tok not in ["AI", "ML", "DL", "NLP", "API", "DNA", "RNA", "USA", "UK"]:
                            next_tokens[0] = first_tok[0].lower() + first_tok[1:]
                        next_body = " ".join(next_tokens)
                    else:
                        next_body = next_clean

                    connector = random.choice(self.merge_conjunctions)
                    merged = f"{curr_stripped}{connector}{next_body}{terminator}"
                    transformed.append(merged)
                    i += 2
                    continue

            # If sentence is very long (> 28 words) with conjunctions, occasionally split it for punchiness
            if curr_len > 26 and random.random() < 0.50:
                # Look for split points: ', but ', ', and ', '; '
                split_match = re.search(r",\s+(and|but|however|yet)\s+", current)
                if split_match:
                    part1 = current[:split_match.start()].strip() + "."
                    part2_opener = split_match.group(1).capitalize()
                    part2 = part2_opener + " " + current[split_match.end():].strip()
                    transformed.append(part1)
                    transformed.append(part2)
                    i += 1
                    continue

            # Add occasional human rhetorical touch to opening of select middle sentences
            if i > 0 and curr_len > 8 and random.random() < 0.18:
                # Ensure it doesn't already start with an introductory phrase or adverb with a comma
                if not re.match(r"^[A-Z][a-z]+,\s+", current) and not any(current.startswith(op.strip()) for op in self.organic_openers):
                    words_in_sent = current.split()
                    if len(words_in_sent) > 3 and not words_in_sent[0].endswith(","):
                        opener = random.choice(self.organic_openers)
                        words_in_sent[0] = words_in_sent[0].lower()
                        current = opener + " ".join(words_in_sent)

            transformed.append(current)
            i += 1

        return transformed

    def restructure(self, text: str, burstiness_target: float = 1.4) -> str:
        """Full syntactic restructuring pipeline."""
        sentences = split_sentences(text)
        if not sentences:
            return text

        restructured = self.inject_burstiness(sentences, target_ratio=burstiness_target)
        return " ".join(restructured)
