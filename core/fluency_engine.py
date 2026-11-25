"""
Fluency and Grammar Perfection Engine.
Enforces phonetic article agreement ('a' vs 'an'), infinitive verb normalization,
subject-verb agreement smoothing, typographical punctuation harmony, and grammatical repair.
"""

import re
from typing import List


class FluencyEngine:
    """
    Polishes text post-transformation to ensure 100% natural fluency,
    grammatical agreement, and flawless typography.
    """

    def __init__(self):
        # Words starting with vowel letters that take 'a' due to consonant sound (e.g. /juː/ or /w/)
        self.consonant_sound_exceptions = {
            "unique", "universal", "university", "uniform", "unilateral", "union",
            "european", "euphemism", "euphoric", "one", "one-time", "useful", "user"
        }
        # Words starting with consonant letters that take 'an' due to silent h
        self.vowel_sound_exceptions = {
            "hour", "hourly", "honest", "honestly", "honor", "honorable", "heir", "heiress"
        }

    def fix_articles(self, text: str) -> str:
        """
        Ensures correct usage of 'a' vs 'an' based on following word phonetics.
        e.g. 'a intelligent' -> 'an intelligent', 'an unique' -> 'a unique'
        """
        def article_replacer(match: re.Match) -> str:
            article = match.group(1)
            word = match.group(2)
            word_lower = word.lower()

            is_capitalized = article[0].isupper()

            if word_lower in self.consonant_sound_exceptions:
                correct = "A" if is_capitalized else "a"
            elif word_lower in self.vowel_sound_exceptions:
                correct = "An" if is_capitalized else "an"
            elif word_lower[0] in "aeiou":
                correct = "An" if is_capitalized else "an"
            else:
                correct = "A" if is_capitalized else "a"

            return f"{correct} {word}"

        pattern = r"\b([Aa]n?)\s+([a-zA-Z]+)\b"
        return re.sub(pattern, article_replacer, text)

    def fix_infinitives(self, text: str) -> str:
        """
        Corrects inflected verbs following the infinitive marker 'to'.
        e.g. 'to explores' -> 'to explore', 'to cultivates' -> 'to cultivate'
        """
        def infinitive_replacer(match: re.Match) -> str:
            to_word = match.group(1)
            verb = match.group(2)

            verb_lower = verb.lower()
            if verb_lower.endswith("es") and len(verb_lower) > 4:
                base = verb[:-2] + "e" if not verb_lower.endswith(("shes", "ches", "sses")) else verb[:-2]
            elif verb_lower.endswith("s") and not verb_lower.endswith(("ss", "is", "us")):
                base = verb[:-1]
            else:
                base = verb

            if verb.isupper():
                base = base.upper()
            elif verb.istitle():
                base = base.capitalize()

            return f"{to_word} {base}"

        verbs = (
            "explore|explores|examine|examines|cultivate|cultivates|investigate|investigates|"
            "shape|shapes|nurture|nurtures|drive|drives|leverage|leverages|enhance|enhances|"
            "foster|fosters|utilize|utilizes|implement|implements|navigate|navigates"
        )
        pattern = rf"\b([Tt]o)\s+({verbs})\b"
        return re.sub(pattern, infinitive_replacer, text)

    def repair_grammar_glitches(self, text: str) -> str:
        """
        Repairs common machine paraphrase glitches such as missing linking verbs,
        stacked conflicting adverbs, and repeated words.
        """
        # 1. Missing linking verbs: e.g. "AI a clear reflection" -> "AI is a clear reflection"
        text = re.sub(
            r"\b([A-Z][a-zA-Z0-9_\-]+)\s+(a(?:n)?\s+(?:clear|direct|living|distinct)\s+(?:reflection|sign|proof|evidence|testament))\b",
            r"\1 is \2",
            text
        )

        # 2. Fix stacked conflicting adverbs
        stacked_adverbs = [
            (r"\band\s+simultaneously,\s*(?:crucially|notably|importantly),\s*", "and crucially, "),
            (r"\band\s+simultaneously,\s*", "and "),
            (r"\band\s+(?:in addition|moreover|additionally),\s*(?:in practice|notably|crucially|importantly),\s*", "and "),
            (r"\band\s+(?:in addition|additionally|moreover),\s*", "and "),
            (r"\b(in addition|additionally|moreover|what is more|furthermore),\s+(in practice|notably|crucially|importantly),\s*", r"\1, "),
            (r"\b(simultaneously|concurrently),\s+(crucially|notably|importantly|significantly),\s*", r"\2, "),
            (r"\b(crucially|notably|importantly),\s+(yet\s+remember|remember),\s*", r"\1, "),
            (r"\b(while|whereas|and)\s+(?:overall|in summary|in short|to sum up|all told|ultimately|in reality|in practice),\s*", r"\1 "),
            (r"\bTo be sure,\s+(yet\s+remember|remember),\s*", "To be sure, "),
            (r"\b(yet|and)\s+remember,\s*", r"\1 "),
            (r"\b(Moreover|Furthermore|Additionally),\s+(beyond that|what's more|on top of that),\s*", r"\2, "),
            (r";\s*(?:in turn|consequently),\s*(?:simply put|broadly speaking|overall|in summary|in short|to sum up|all told|ultimately|in reality|in practice),\s*", "; in turn, "),
            (r";\s*consequently,\s*(?:importantly|crucially|notably|in practice),\s*", "; consequently, "),
            (r"\bAll told,\s+in the end,\s*", "Ultimately, "),
            (r"\bIn conclusion,\s+all told,\s*", "In the end, "),
            (r"\bIn the end,\s+all told,\s*", "In the end, "),
            (r"\b(?:Furthermore|Moreover|In addition|Beyond this|Consequently|Importantly),\s+however,\s*", "However, "),
            (r"\bhowever,\s+(?:furthermore|moreover|in addition|beyond this|consequently|importantly),\s*", "However, "),
            (r"\bfurthermore\b", "in addition"),
            (r"\bFurthermore\b", "In addition"),
            (r"\bmoreover\b", "additionally"),
            (r"\bMoreover\b", "Additionally")
        ]
        for pat, rep in stacked_adverbs:
            text = re.sub(pat, rep, text, flags=re.IGNORECASE)

        # 3. Subject-verb agreement smoothing for common plurals (with optional adverb modifier)
        text = re.sub(r"\b(systems|models|algorithms|tools|frameworks|solutions|networks|approaches|architectures)(\s+[a-zA-Z]+ly)?\s+stands\b", lambda m: f"{m.group(1)}{m.group(2) or ''} stand", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(systems|models|algorithms|tools|frameworks|solutions|networks|approaches|architectures)(\s+[a-zA-Z]+ly)?\s+serves\b", lambda m: f"{m.group(1)}{m.group(2) or ''} serve", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(systems|models|algorithms|tools|frameworks|solutions|networks|approaches|architectures)(\s+[a-zA-Z]+ly)?\s+provides\b", lambda m: f"{m.group(1)}{m.group(2) or ''} provide", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(systems|models|algorithms|tools|frameworks|solutions|networks|approaches|architectures)(\s+[a-zA-Z]+ly)?\s+acts\b", lambda m: f"{m.group(1)}{m.group(2) or ''} act", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(systems|models|algorithms|tools|frameworks|solutions|networks|approaches|architectures)(\s+[a-zA-Z]+ly)?\s+delivers\b", lambda m: f"{m.group(1)}{m.group(2) or ''} deliver", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(systems|models|algorithms|tools|frameworks|solutions|networks|approaches|architectures)(\s+[a-zA-Z]+ly)?\s+leads\b", lambda m: f"{m.group(1)}{m.group(2) or ''} lead", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(systems|models|algorithms|tools|frameworks|solutions|networks|approaches|architectures)(\s+[a-zA-Z]+ly)?\s+exemplifies\b", lambda m: f"{m.group(1)}{m.group(2) or ''} exemplify", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(systems|models|algorithms|tools|frameworks|solutions|networks|approaches|architectures)(\s+[a-zA-Z]+ly)?\s+reflects\b", lambda m: f"{m.group(1)}{m.group(2) or ''} reflect", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(systems|models|algorithms|tools|frameworks|solutions|networks|approaches|architectures)(\s+[a-zA-Z]+ly)?\s+validates\b", lambda m: f"{m.group(1)}{m.group(2) or ''} validate", text, flags=re.IGNORECASE)

        # 4. Repeated words & duplicated adverbs/adjectives
        text = re.sub(r"\b([a-zA-Z]{2,})\s+\1\b", r"\1", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(current|present-day)\s+(contemporary)\b", r"\2", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(contemporary)\s+(current|present-day)\b", r"\1", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(increasingly|deeply|truly|genuinely|remarkably|consistently)\s+(?:to\s+)?\1\b", r"\1", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(?:current|contemporary|modern|present-day)\s+(the\s+public\s+sphere)\b", r"\1", text, flags=re.IGNORECASE)

        # 4b. Collapse any consecutive stacked qualifiers/adjectives
        qualifiers_pats = r"(?:practical|operational|empirical|systemic|rigorous|comparative|substantive|advanced|contemporary|modern)"
        text = re.sub(rf"\b({qualifiers_pats})(?:\s+(?:{qualifiers_pats}))+\b", r"\1", text, flags=re.IGNORECASE)

        # 4c. Convert qualifiers preceding past participles (-ed) into proper adverbs (-ly)
        def _adv_repl(match):
            q = match.group(1)
            participle = match.group(2)
            if q.lower() == "substantive":
                return f"substantively {participle}"
            elif q.lower() == "systemic":
                return f"systemically {participle}"
            elif q.lower() == "empirical":
                return f"empirically {participle}"
            elif q.lower() == "practical":
                return f"practically {participle}"
            elif q.lower() == "operational":
                return f"operationally {participle}"
            elif q.lower() == "comparative":
                return f"comparatively {participle}"
            elif q.lower() == "rigorous":
                return f"rigorously {participle}"
            return f"{q}ly {participle}"

        text = re.sub(rf"\b(practical|operational|empirical|systemic|rigorous|comparative|substantive)\s+([a-zA-Z]+ed)\b", _adv_repl, text, flags=re.IGNORECASE)

        # 5. Fix accidental adverb insertions inside protected collocations
        adv_pats = r"(?:consistently|steadily|notably|substantively|truly|increasingly|genuinely|measurably)"
        text = re.sub(rf"\b(social)\s+{adv_pats}\s+(media)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(climate)\s+{adv_pats}\s+(change)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(screen)\s+{adv_pats}\s+(time)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(mental)\s+{adv_pats}\s+(health)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(solar|wind|hydroelectric)\s+{adv_pats}\s+(power|energy)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(artificial)\s+{adv_pats}\s+(intelligence)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(machine|deep)\s+{adv_pats}\s+(learning)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(neural)\s+{adv_pats}\s+(networks?)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(data|computer)\s+{adv_pats}\s+(science)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(higher)\s+{adv_pats}\s+(education)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(public)\s+{adv_pats}\s+(health)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(greenhouse)\s+{adv_pats}\s+(gases?)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(fossil)\s+{adv_pats}\s+(fuels?)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(carbon)\s+{adv_pats}\s+(emissions?|footprint)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(renewable)\s+{adv_pats}\s+(energy)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b(global)\s+{adv_pats}\s+(warming)\b", r"\1 \2", text, flags=re.IGNORECASE)

        # 6. Automatic normalization of rogue archaic/clinical machine lemmas
        archaic_normalizations = [
            (r"\bholocene\b", "recent"),
            (r"\bHolocene\b", "Recent"),
            (r"\btwelvemonth\b", "year"),
            (r"\bTwelvemonth\b", "Year"),
            (r"\bhomo\b", "human"),
            (r"\bHomo\b", "Human"),
            (r"\bpotpourri\b", "collection"),
            (r"\bpsychoanalysis\b", "analysis"),
            (r"\bPsychoanalysis\b", "Analysis"),
            (r"\bwhilst\b", "while"),
            (r"\bheretofore\b", "previously"),
            (r"\bhenceforth\b", "from now on"),
            (r"\bperadventure\b", "perhaps"),
            (r"\bbetwixt\b", "between"),
            (r"\bforthwith\b", "promptly"),
            (r"\bvis-a-vis\b", "regarding"),
            (r"\bzeitgeist\b", "spirit of the era"),
            (r"\bTo be surely,\b", "Indeed,"),
            (r"\bto be surely,\b", "indeed,"),
            (r"\bTo be sure,\b", "Indeed,"),
            (r"\bto be sure,\b", "indeed,"),
            (r"\bera of figure\b", "era of computation"),
            (r"\bbroad book of\b", "extensive quantities of"),
            (r"\bstandpoint as\b", "serves as"),
            (r"\ban earn expression\b", "a clear reflection"),
            (r"\bIt is (?:necessity|requirement)\s+that\b", "It is essential that"),
            (r"\bit is (?:necessity|requirement)\s+that\b", "it is essential that"),
            (r"\bcare the practical\b", "address the practical"),
            (r"\bstudy done\b", "resolve"),
            (r"\ba distinct contemplation of\b", "a clear reflection of"),
            (r"\bDeep learning architecture serve as\b", "Deep learning architectures serve as"),
            (r"\bdeep learning architecture serve as\b", "deep learning architectures serve as"),
            (r"\bDeep learning architecture stand\b", "Deep learning architectures stand"),
            (r"\bdeep learning architecture stand\b", "deep learning architectures stand"),
            (r"\bDeep learning architecture function\b", "Deep learning architectures function"),
            (r"\bdeep learning architecture function\b", "deep learning architectures function"),
            (r"\bDeep learning architecture remain\b", "Deep learning architectures remain"),
            (r"\bdeep learning architecture remain\b", "deep learning architectures remain"),
            (r"\bIn realism,\b", "In practice,"),
            (r"\bin realism,\b", "in practice,"),
            (r"\bcope the (?:intricacies|complexities|hurdles)\b", "manage the intricacies"),
            (r"\bdeal the (?:practical\s+)?(?:difficulties|challenges|complexities|intricacies|hurdles)\b", "deal with the practical difficulties"),
            (r"\bdeal the\b", "deal with the"),
            (r"\bdeal\s+the\b", "deal with the"),
            (r"\bcope\s+the\b", "cope with the"),
            (r"\benable(?:s)? promote\b", "enable sophisticated"),
            (r"\bpromote (?:practice|pattern) recognition\b", "sophisticated pattern recognition"),
            (r"\bKey strategic priority for\b", "Key strategic priorities for"),
            (r"\b1; in turn, [eE]xecutive\b", "1. Executive"),
        ]
        for pat, rep in archaic_normalizations:
            text = re.sub(pat, rep, text)

        # 7. Singular subject + base verb agreement repair (e.g. "the investigation show" -> "the investigation shows")
        singular_endings = r"(?:tion|ment|ness|ity|ism|ance|ence|cy|er|or|ure|ology|work|study|model|system|framework)"
        base_verbs = r"(?:stand|serve|provide|act|deliver|lead|reflect|indicate|demonstrate|show|reveal|illustrate|require|yield)"
        def singular_sv_replacer(m: re.Match) -> str:
            det = m.group(1)
            noun = m.group(2)
            verb = m.group(3)
            # Add 's' or 'es' to verb
            v_lower = verb.lower()
            if v_lower.endswith(("ch", "sh", "ss", "x", "z", "o")):
                new_verb = verb + "es"
            else:
                new_verb = verb + "s"
            return f"{det} {noun} {new_verb}"

        text = re.sub(
            rf"\b(the|this|a|an|each|every)\s+([a-zA-Z]+{singular_endings})\s+({base_verbs})\b",
            singular_sv_replacer,
            text,
            flags=re.IGNORECASE
        )

        return text

    def clean_typography(self, text: str) -> str:
        """
        Sanitizes punctuation, double connectors, and typographical collisions.
        """
        # Punctuation collisions
        text = re.sub(r",\s*,+", ",", text)
        text = re.sub(r";\s*;+", ";", text)
        text = re.sub(r",\s*;", ";", text)
        text = re.sub(r";\s*,", ";", text)
        text = re.sub(r"\.\s*,", ".", text)
        text = re.sub(r",\s*\.", ".", text)
        text = re.sub(r"—\s*—+", "—", text)
        text = re.sub(r"[ ]{2,}", " ", text)

        # Capitalize after sentence-ending punctuation or start of text
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        text = re.sub(
            r"([.!?]\s+)([a-z])",
            lambda m: m.group(1) + m.group(2).upper(),
            text
        )

        # Lowercase common function words erroneously capitalized after commas
        common_lowers = [
            "this", "that", "these", "those", "the", "a", "an", "which", "while", "where",
            "because", "since", "and", "but", "or", "when", "if", "with", "by", "from", "in", "it"
        ]
        pat_comma_cap = rf",\s+({'|'.join([w.capitalize() for w in common_lowers])})\b"
        text = re.sub(pat_comma_cap, lambda m: f", {m.group(1).lower()}", text)

        # Space after comma/semicolon/colon if omitted
        text = re.sub(r"([,;:])([a-zA-Z])", r"\1 \2", text)

        # Preserve common uppercase technical acronyms
        acronyms = ["AI", "ML", "DL", "NLP", "API", "DNA", "RNA", "COVID", "USA", "UK", "MIT", "GPU", "CPU"]
        for acr in acronyms:
            text = re.sub(rf"\b{acr.capitalize()}\b", acr, text)

        # Clean trailing spacing before punctuation and within brackets/parentheses
        text = re.sub(r"\s+([,.;!?])", r"\1", text)
        text = re.sub(r"\(\s+", "(", text)
        text = re.sub(r"\s+\)", ")", text)
        text = re.sub(r"\[\s+", "[", text)
        text = re.sub(r"\s+\]", "]", text)
        return text.strip()

    def polish(self, text: str) -> str:
        """Runs complete fluency, article, repair, and typography perfection pipeline."""
        if not text:
            return ""
        s1 = self.clean_typography(text)
        s2 = self.repair_grammar_glitches(s1)
        s3 = self.fix_articles(s2)
        s4 = self.fix_infinitives(s3)
        return self.clean_typography(s4)
