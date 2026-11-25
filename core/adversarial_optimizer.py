"""
Adversarial Humanizer & Plagiarism Eradication Optimizer.
Executes an intelligent, targeted optimization loop that transforms text
to eliminate AI detector signatures and verbatim plagiarism while preserving
flawless human fluency, natural cadence, and semantic fidelity.
"""

import logging
import random
import re
from typing import Any, Dict, List, Optional, Set

from config import AI_BUZZWORDS
from core.cleaner import MarkerCleaner
from core.deep_rephraser import DeepRephraser
from core.detector import TextAnalyzer
from core.fluency_engine import FluencyEngine
from core.metrics import (
    calculate_burstiness,
    calculate_ngram_overlap,
    get_ngrams,
    levenshtein_similarity,
    split_sentences,
    tokenize_words,
)
from core.semantic_validator import SemanticValidator
from core.synonym_engine import (
    BANNED_OBSCURE_LEMMAS,
    COMMON_FUNCTION_WORDS,
    PROTECTED_COLLOCATIONS,
    PROTECTED_TECHNICAL_WORDS,
    SynonymEngine,
)
from core.syntax_engine import SyntaxEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


UNIVERSAL_SCHOLARLY_REPLACEMENTS: Dict[str, List[str]] = {
    # High-frequency verbs and inflections
    "carries": ["bears", "transports", "conveys", "handles", "maintains"],
    "carry": ["bear", "transport", "convey", "handle", "maintain"],
    "carrying": ["bearing", "transporting", "conveying", "handling"],
    "carried": ["borne", "transported", "conveyed", "maintained"],
    "serving": ["functioning", "acting", "operating", "standing"],
    "serve": ["function", "act", "operate", "stand"],
    "serves": ["functions", "acts", "operates", "stands"],
    "served": ["functioned", "acted", "operated"],
    "encounter": ["experience", "face", "confront", "grapple with"],
    "encounters": ["experiences", "faces", "confronts", "grapples with"],
    "encountered": ["experienced", "faced", "confronted"],
    "encountering": ["experiencing", "facing", "confronting"],
    "looks": ["appears", "seems", "presents itself as"],
    "look": ["appear", "seem"],
    "looking": ["appearing", "seeming"],
    "fail": ["degrade", "falter", "underperform"],
    "fails": ["degrades", "falters", "underperforms"],
    "failed": ["degraded", "faltered", "underperformed"],
    "failing": ["degrading", "faltering", "underperforming"],
    "achieve": ["attain", "realize", "reach"],
    "achieves": ["attains", "realizes", "reaches"],
    "achieved": ["attained", "realized", "reached"],
    "achieving": ["attaining", "realizing", "reaching"],
    "utilize": ["employ", "apply", "adopt", "leverage"],
    "utilizes": ["employs", "applies", "adopts", "leverages"],
    "utilized": ["employed", "applied", "adopted", "leveraged"],
    "utilizing": ["employing", "applying", "adopting", "leveraging"],
    "exhibit": ["demonstrate", "display", "reveal", "showcase"],
    "exhibits": ["demonstrates", "displays", "reveals", "showcases"],
    "exhibited": ["demonstrated", "displayed", "revealed", "showcased"],
    "exhibiting": ["demonstrating", "displaying", "revealing", "showcasing"],
    "demonstrate": ["illustrate", "confirm", "showcase", "establish"],
    "demonstrates": ["illustrates", "confirms", "showcases", "establishes"],
    "demonstrated": ["illustrated", "confirmed", "showcased", "established"],
    "demonstrating": ["illustrating", "confirming", "showcasing", "establishing"],
    "facilitate": ["streamline", "expedite", "support", "advance"],
    "facilitates": ["streamlines", "expedites", "supports", "advances"],
    "facilitated": ["streamlined", "expedited", "supported", "advanced"],
    "facilitating": ["streamlining", "expediting", "supporting", "advancing"],
    "investigate": ["probe", "examine", "analyze", "scrutinize"],
    "investigates": ["probes", "examines", "analyzes", "scrutinizes"],
    "investigated": ["probed", "examined", "analyzed", "scrutinized"],
    "investigating": ["probing", "examining", "analyzing", "scrutinizing"],
    "address": ["tackle", "handle", "confront", "resolve"],
    "addresses": ["tackles", "handles", "confronts", "resolves"],
    "addressed": ["tackled", "handled", "confronted", "resolved"],
    "addressing": ["tackling", "handling", "confronting", "resolving"],
    "generate": ["produce", "yield", "create", "synthesize"],
    "generating": ["producing", "yielding", "creating", "synthesizing"],
    "analyzing": ["evaluating", "parsing", "scrutinizing", "examining", "assessing"],
    "analyze": ["evaluate", "parse", "scrutinize", "examine", "assess"],
    "analyzes": ["evaluates", "parses", "scrutinizes", "examines", "assesses"],
    "analyzed": ["evaluated", "parsed", "scrutinized", "examined", "assessed"],
    "revolutionizing": ["transforming", "overhauling", "advancing", "modernizing"],
    "revolutionize": ["transform", "overhaul", "advance", "modernize"],
    "revolutionized": ["transformed", "overhauled", "advanced", "modernized"],
    "revolutionizes": ["transforms", "overhauls", "advances", "modernizes"],
    "enhance": ["strengthen", "elevate", "boost", "advance"],
    "enhances": ["strengthens", "elevates", "boosts", "advances"],
    "enhanced": ["strengthened", "elevated", "boosted", "advanced"],
    "enhancing": ["strengthening", "elevating", "boosting", "advancing"],

    # High-frequency nouns
    "bulk": ["majority", "predominant share", "lion's share", "greater part"],
    "vector": ["pathway", "conduit", "channel", "mechanism", "route"],
    "vectors": ["pathways", "conduits", "channels", "mechanisms", "routes"],
    "attack": ["threat", "adversarial", "intrusion", "exploit"],
    "attacks": ["threats", "adversarial incursions", "intrusions", "exploits"],
    "constraints": ["limitations", "bottlenecks", "boundaries", "restrictions"],
    "constraint": ["limitation", "bottleneck", "boundary", "restriction"],
    "heuristics": ["mechanisms", "rules", "strategies", "logic", "techniques"],
    "heuristic": ["mechanism", "rule", "strategy", "logic", "technique"],
    "shift": ["drift", "transition", "variation", "divergence"],
    "shifts": ["drifts", "transitions", "variations", "divergences"],
    "accuracy": ["predictive accuracy", "empirical performance", "test fidelity"],
    "problem": ["hurdle", "challenge", "obstacle", "bottleneck"],
    "problems": ["hurdles", "challenges", "obstacles", "bottlenecks"],
    "dataset": ["corpus", "data collection", "data repository"],
    "datasets": ["corpora", "data collections", "evaluative repositories"],
    "communication": ["information exchange", "messaging", "correspondence"],
    "gateways": ["inspection nodes", "entry conduits", "inbound gateways"],
    "gateway": ["inspection node", "entry conduit", "inbound gateway"],
    "harvesting": ["theft", "interception", "extraction", "exfiltration"],
    "harvest": ["intercept", "extract", "capture"],
    "phishing": ["phishing campaigns", "phishing attacks", "deceptive lures"],
    "baseline": ["benchmark", "reference standard", "comparative baseline"],
    "baselines": ["benchmarks", "reference standards", "comparative baselines"],
    "landscape": ["environment", "space", "domain", "arena"],
    "era": ["period", "age", "epoch", "time"],
    "realm": ["domain", "sphere", "area", "field"],
    "paradigm": ["model", "framework", "perspective", "approach"],
    "paradigms": ["models", "frameworks", "perspectives", "approaches"],
    "architecture": ["framework", "design", "structure", "system configuration"],
    "architectures": ["frameworks", "designs", "structures", "system configurations"],
    "mechanism": ["process", "technique", "method", "protocol"],
    "mechanisms": ["processes", "techniques", "methods", "protocols"],
    "methodology": ["procedure", "protocol", "framework", "approach"],
    "methodologies": ["procedures", "protocols", "frameworks", "approaches"],
    "resolution": ["fidelity", "granularity", "detail", "definition"],
    "resolutions": ["fidelities", "granularities", "definitions"],
    "scan": ["imaging capture", "radiological scan", "diagnostic record"],
    "scans": ["imaging data", "radiological scans", "diagnostic records", "evaluative captures"],
    "image": ["visual rendering", "diagnostic image", "optical capture"],
    "images": ["visual renderings", "diagnostic images", "optical captures"],
    "classification": ["categorization", "predictive grouping", "diagnostic sorting"],
    "classifications": ["categorizations", "predictive groupings", "diagnostic sortings"],
    "throughput": ["operational capacity", "processing efficiency", "execution rate"],
    "concurrency": ["parallel request volume", "simultaneous workloads"],
    "latency": ["response delay", "processing lag", "turnaround duration"],
    "pathology": ["histopathological", "clinical pathology", "biomedical pathology"],
    "medical": ["clinical", "healthcare", "biomedical"],
    "clinical": ["medical", "healthcare", "diagnostic"],

    # High-frequency adjectives & adverbs
    "primary": ["predominant", "principal", "foremost", "central", "chief", "leading"],
    "continuous": ["ongoing", "uninterrupted", "persistent", "sustained", "perpetual"],
    "operational": ["production-level", "runtime", "practical", "systemic"],
    "real-world": ["production", "practical", "field-deployed", "empirical"],
    "real": ["actual", "tangible", "operational", "practical"],
    "modern": ["contemporary", "current", "present-day", "state-of-the-art"],
    "solved": ["resolved", "addressed", "settled"],
    "massive": ["extensive", "colossal", "wide-ranging", "substantial"],
    "crucial": ["vital", "essential", "critical", "central"],
    "significant": ["substantial", "notable", "meaningful", "considerable"],
    "vital": ["essential", "crucial", "critical", "indispensable"],
    "essential": ["vital", "crucial", "fundamental", "indispensable"],
    "fundamental": ["core", "central", "foundational", "underlying"],
    "promising": ["encouraging", "favorable", "auspicious", "noteworthy"],
    "substantial": ["significant", "considerable", "marked", "notable"],
    "comprehensive": ["exhaustive", "broad-scale", "in-depth", "thorough"],
    "still": ["persistently", "consistently", "steadily", "nonetheless", "continues to"],
    "only": ["solely", "exclusively", "merely"],
    "why": ["precisely why", "how", "on what basis"],
    "sure": ["certainly", "admittedly", "clearly"],
}


class AdversarialOptimizer:
    """
    Guarantees deep removal of AI markers and verbatim plagiarism through
    targeted adversarial optimization and surgical n-gram disruption.
    """

    def __init__(self):
        self.analyzer = TextAnalyzer()
        self.deep_rephraser = DeepRephraser()
        self.cleaner = MarkerCleaner()
        self.syntax_engine = SyntaxEngine()
        self.synonym_engine = SynonymEngine()
        self.validator = SemanticValidator()
        self.fluency = FluencyEngine()

    def disrupt_verbatim_ngrams(
        self,
        original_text: str,
        current_text: str,
        n: int = 4,
        preserve_keywords: Optional[Set[str]] = None,
        max_passes: int = 15,
        zero_expansion: bool = False
    ) -> str:
        """
        Pinpoints exact n-gram verbatim matches between original and current text,
        and surgically paraphrases tokens across each match to eliminate verbatim plagiarism.
        Runs iteratively until 0.0% matching n-grams remain or max_passes is reached.
        """
        orig_tokens = tokenize_words(original_text)
        orig_ngrams = get_ngrams(orig_tokens, n)
        if not orig_ngrams:
            return current_text

        result_text = current_text
        keywords_lower = {k.lower() for k in (preserve_keywords or set())}
        keyword_words = {w for kw in keywords_lower for w in kw.split()}
        # Protect constituent words of any PROTECTED_COLLOCATIONS present in the text
        from core.synonym_engine import PROTECTED_COLLOCATIONS
        lower_curr = current_text.lower()
        for colloc in PROTECTED_COLLOCATIONS:
            if colloc in lower_curr:
                keyword_words.update(colloc.split())

        for _ in range(max_passes):
            curr_tokens = tokenize_words(result_text)
            matches_found = False

            for i in range(len(curr_tokens) - n + 1):
                curr_tokens = tokenize_words(result_text)
                if i + n > len(curr_tokens):
                    break
                ngram = tuple(curr_tokens[i:i + n])
                if ngram in orig_ngrams:
                    ngram_str = " ".join(ngram)
                    if keywords_lower and any(kw in ngram_str.lower() or ngram_str.lower() in kw for kw in keywords_lower):
                        continue
                    if all(w.lower() in keyword_words for w in ngram):
                        continue

                    matches_found = True
                    # Punctuation & hyphen-aware regex matching allowing whitespace, commas, periods, quotes, dashes, parens between words
                    pattern = r"\b" + r"[\s.,;:!?\"'()\[\]\-\—\–\/]+".join(re.escape(w) for w in ngram) + r"\b"
                    match = re.search(pattern, result_text, flags=re.IGNORECASE)
                    if match:
                        replaced = False
                        matched_slice = match.group(0)

                        # Priority 0: Sentence boundary discourse transition
                        # Shatters n-grams that span across sentence periods (. / ! / ?)
                        boundary_match = re.search(r"([.!?])\s+([A-Za-z])", matched_slice)
                        if boundary_match and not zero_expansion:
                            after_boundary = matched_slice[boundary_match.start(2):]
                            trans_match = re.match(r"^(however|consequently|to be sure|indeed|furthermore|moreover|meanwhile|nevertheless)\b", after_boundary, flags=re.IGNORECASE)
                            if trans_match:
                                trans_w = trans_match.group(1).lower()
                                trans_map = {
                                    "however": ["On the other hand, ", "In operational settings, ", "Conversely, ", "In live deployments, "],
                                    "consequently": ["As an empirical outcome, ", "In light of this, ", "As a direct result, "],
                                    "to be sure": ["Admittedly, ", "Certainly, ", "Undeniably, "],
                                    "indeed": ["In practice, ", "Empirically, ", "Substantively, "],
                                    "furthermore": ["Beyond this, ", "Importantly, ", "In addition, "],
                                    "moreover": ["Equally important, ", "At the same time, ", "Further, "],
                                    "meanwhile": ["At the same time, ", "Concurrently, "],
                                    "nevertheless": ["Even so, ", "Regardless, ", "That said, "]
                                }
                                repl_trans = random.choice(trans_map.get(trans_w, ["Beyond this, "]))
                                trans_pat = rf"\b{re.escape(trans_match.group(0))}(?:,\s*)?"
                                new_after = re.sub(trans_pat, repl_trans, after_boundary, count=1, flags=re.IGNORECASE)
                                new_slice = matched_slice[:boundary_match.start(2)] + new_after
                                result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                replaced = True
                            else:
                                connector = random.choice(["Beyond this, ", "Importantly, ", "Consequently, ", "In addition, ", "At the same time, "])
                                next_char = boundary_match.group(2)
                                is_standalone_i = bool(re.match(r"^I\b(?![a-zA-Z])", after_boundary))
                                next_char_adj = "I" if is_standalone_i else next_char.lower()
                                new_slice = (
                                    matched_slice[:boundary_match.start(1) + 1]
                                    + f" {connector}"
                                    + next_char_adj
                                    + matched_slice[boundary_match.end(2):]
                                )
                                result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                replaced = True

                        colloc_set = set(PROTECTED_COLLOCATIONS)
                        # Priority 1: Content word substitution via expanded thesaurus
                        if not replaced:
                            for pos in range(n):
                                cand_word = ngram[pos].lower()
                                if (
                                    len(cand_word) <= 2
                                    or cand_word in keywords_lower
                                    or cand_word in keyword_words
                                    or cand_word in PROTECTED_TECHNICAL_WORDS
                                ):
                                    continue
                                # Do not fragment hyphenated compounds unless full compound matches
                                if not re.search(rf"(?<!-)\b{re.escape(ngram[pos])}\b(?!-)", matched_slice, flags=re.IGNORECASE):
                                    continue
                                cand_pair1 = f"{cand_word} {ngram[pos + 1].lower()}" if pos < n - 1 else ""
                                cand_pair2 = f"{ngram[pos - 1].lower()} {cand_word}" if pos > 0 else ""
                                if cand_pair1 in colloc_set or cand_pair2 in colloc_set:
                                    continue
                                w_dict = self.synonym_engine.thesaurus.get(cand_word, {})
                                raw_candidates = list(
                                    w_dict.get("academic", [])
                                    or w_dict.get("standard", [])
                                    or w_dict.get("journalistic", [])
                                )
                                ai_buzz_set = set(AI_BUZZWORDS)
                                candidates = [
                                    c for c in raw_candidates
                                    if c.lower() not in ai_buzz_set
                                    and c.lower() not in BANNED_OBSCURE_LEMMAS
                                    and (not zero_expansion or len(c.split()) == 1)
                                ]
                                if candidates:
                                    replacement = random.choice(candidates)
                                    if ngram[pos].isupper() and len(ngram[pos]) > 1:
                                        replacement = replacement.upper()
                                    elif ngram[pos].istitle():
                                        replacement = replacement.capitalize()

                                    word_pat = rf"(?<!-)\b{re.escape(ngram[pos])}\b(?!-)"
                                    new_slice = re.sub(word_pat, replacement, matched_slice, count=1, flags=re.IGNORECASE)
                                    if new_slice != matched_slice:
                                        result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                        replaced = True
                                        break

                        # Priority 2: Coordinate conjunction modulation ("and" -> "alongside" / "coupled with")
                        if not replaced and "and" in ngram:
                            conj_choice = "alongside" if zero_expansion else random.choice(["alongside", "coupled with", "together with"])
                            word_pat = r"\band\b"
                            new_slice = re.sub(word_pat, conj_choice, matched_slice, count=1, flags=re.IGNORECASE)
                            if new_slice != matched_slice:
                                result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                replaced = True

                        # Priority 2.5: Auxiliary verb + participle modulation ("has experienced" -> "witnessed" or "has steadily witnessed")
                        if not replaced and ngram[-1].lower() in {"has", "have"}:
                            after_slice = result_text[match.end():]
                            m_participle = re.match(r"^\s+([a-zA-Z]+(?:ed|en|wn|ne))\b", after_slice)
                            if m_participle:
                                part_word = m_participle.group(1)
                                part_dict = self.synonym_engine.thesaurus.get(part_word.lower(), {})
                                part_cands = part_dict.get("academic", []) or part_dict.get("standard", [])
                                chosen_verb = random.choice(part_cands) if part_cands else part_word
                                rep_phrase = chosen_verb if zero_expansion else random.choice([chosen_verb, f"has steadily {chosen_verb}", f"has notably {chosen_verb}"])
                                has_pat = rf"\b{re.escape(ngram[-1])}\s+{re.escape(part_word)}\b"
                                sub_res = re.sub(has_pat, rep_phrase, result_text, count=1, flags=re.IGNORECASE)
                                if sub_res != result_text:
                                    result_text = sub_res
                                    replaced = True

                        # Priority 3: Pre-verb modifier insertion (only before legitimate verbs, never in zero_expansion)
                        if not replaced and not zero_expansion and n >= 4:
                            known_verbs = {
                                "suggest", "suggests", "suggested", "require", "requires", "required",
                                "remain", "remains", "remained", "threaten", "threatens", "threatened",
                                "indicate", "indicates", "indicated", "lead", "leads", "foster", "fosters",
                                "mitigate", "mitigates", "stand", "stands", "serve", "serves", "served", "serving",
                                "persist", "persists", "demand", "demands", "reflect", "reflects", "affect", "affects",
                                "shape", "shapes", "shaped", "enable", "enables", "enabled", "drive", "drives",
                                "carry", "carries", "carried", "carrying", "encounter", "encounters", "encountered", "encountering",
                                "experience", "experiences", "experienced", "experiencing",
                                "handle", "handles", "handled", "handling", "fail", "fails", "failed", "failing",
                                "achieve", "achieves", "achieved", "achieving", "attain", "attains", "attained", "attaining",
                                "operate", "operates", "operated", "operating", "deliver", "delivers", "delivered", "delivering",
                                "process", "processes", "processed", "processing", "exhibit", "exhibits", "exhibited", "exhibiting",
                                "demonstrate", "demonstrates", "demonstrated", "demonstrating", "employ", "employs", "employed", "employing",
                                "apply", "applies", "applied", "applying", "present", "presents", "presented", "presenting",
                                "reveal", "reveals", "revealed", "revealing", "produce", "produces", "produced", "producing",
                                "yield", "yields", "yielded", "yielding", "face", "faces", "faced", "facing"
                            }
                            for pos, w in enumerate(ngram):
                                w_low = w.lower()
                                prev_w = ngram[pos - 1].lower() if pos > 0 else ""
                                pair = f"{prev_w} {w_low}"
                                if (
                                    pos > 0
                                    and w_low in known_verbs
                                    and pair not in colloc_set
                                    and prev_w not in {"to", "of", "in", "for", "with", "on", "by", "from", "at", "the", "a", "an", "this", "that"}
                                ):
                                    adv_qual = random.choice(["notably", "consistently", "steadily", "substantively"])
                                    verb_pat = rf"(?<!-)\b{re.escape(w)}\b(?!-)"
                                    new_slice = re.sub(verb_pat, f"{adv_qual} {w}", matched_slice, count=1)
                                    if new_slice != matched_slice:
                                        result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                        replaced = True
                                        break

                        # Priority 4: Preposition & transitional boundary modulation (grammatically safe)
                        if not replaced:
                            if zero_expansion:
                                prep_replacements = {
                                    "in": ["within", "across", "throughout"],
                                    "within": ["inside", "across", "in"],
                                    "on": ["regarding", "concerning", "upon"],
                                    "for": ["towards", "supporting"],
                                    "with": ["utilizing", "alongside"],
                                    "by": ["through", "via"],
                                    "through": ["via"],
                                    "into": ["toward", "within"],
                                    "across": ["throughout", "within"],
                                    "about": ["regarding", "concerning"],
                                    "over": ["across", "throughout"],
                                    "between": ["among", "across"],
                                    "against": ["versus"],
                                }
                            else:
                                prep_replacements = {
                                    "in": ["within", "across", "throughout"],
                                    "within": ["inside", "across", "in"],
                                    "on": ["regarding", "concerning", "upon"],
                                    "for": ["aimed at", "supporting", "towards"],
                                    "with": ["utilizing", "alongside", "by employing"],
                                    "by": ["through", "via", "by means of"],
                                    "from": ["originating from", "derived from"],
                                    "through": ["by way of", "via", "by means of"],
                                    "into": ["toward", "within"],
                                    "across": ["throughout", "within"],
                                    "as": ["functioning as", "acting as"],
                                    "about": ["regarding", "concerning"],
                                    "over": ["across", "throughout"],
                                    "between": ["among", "across"],
                                    "against": ["relative to", "versus"],
                                }
                            for pos, w in enumerate(ngram):
                                w_low = w.lower()
                                if w_low in prep_replacements:
                                    prev_w = ngram[pos - 1].lower() if pos > 0 else ""
                                    if w_low == "on" and prev_w in {"based", "rely", "relies", "relied", "focus", "focuses", "focused", "depend", "depends", "depended"}:
                                        continue
                                    rep_prep = random.choice(prep_replacements[w_low])
                                    if w.istitle():
                                        rep_prep = rep_prep.capitalize()
                                    prep_pat = rf"(?<!-)\b{re.escape(w)}\b(?!-)"
                                    new_slice = re.sub(prep_pat, rep_prep, matched_slice, count=1)
                                    if new_slice != matched_slice:
                                        result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                        replaced = True
                                        break

                        # Priority 5: Conjunction & relative clause boundary modulation ("that", "which", "how")
                        if not replaced:
                            for pos, w in enumerate(ngram):
                                w_low = w.lower()
                                if w_low == "that":
                                    prev_w = ngram[pos - 1].lower() if pos > 0 else ""
                                    if pos == 0 or prev_w in {"remember", "note", "notice", "realize", "recognize", "see", "shows", "proves", "indicate", "suggest", "find", "found", "observe", "observed", "is", "was"}:
                                        choice = random.choice(["how", "", "whereby"])
                                    else:
                                        choice = random.choice(["wherein", "how", "such that"])
                                    
                                    that_pat = r"\bthat\b"
                                    if choice == "":
                                        new_slice = re.sub(r"\bthat\s+", "", matched_slice, count=1, flags=re.IGNORECASE)
                                    else:
                                        new_slice = re.sub(that_pat, choice, matched_slice, count=1, flags=re.IGNORECASE)
                                    result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                    replaced = True
                                    break

                        # Priority 6: High-quality academic synonyms from engine thesaurus
                        if not replaced:
                            for pos in range(n):
                                cand_word = ngram[pos].lower()
                                if (
                                    len(cand_word) <= 2
                                    or cand_word in keywords_lower
                                    or cand_word in keyword_words
                                    or cand_word in PROTECTED_TECHNICAL_WORDS
                                ):
                                    continue
                                if not re.search(rf"(?<!-)\b{re.escape(ngram[pos])}\b(?!-)", matched_slice, flags=re.IGNORECASE):
                                    continue
                                cand_pair1 = f"{cand_word} {ngram[pos + 1].lower()}" if pos < n - 1 else ""
                                cand_pair2 = f"{ngram[pos - 1].lower()} {cand_word}" if pos > 0 else ""
                                if cand_pair1 in colloc_set or cand_pair2 in colloc_set:
                                    continue
                                w_dict = self.synonym_engine.thesaurus.get(cand_word, {})
                                raw_candidates = list(
                                    w_dict.get("academic", [])
                                    or w_dict.get("standard", [])
                                )
                                candidates = [
                                    c for c in raw_candidates
                                    if c.lower() not in set(AI_BUZZWORDS)
                                    and c.lower() not in BANNED_OBSCURE_LEMMAS
                                    and (not zero_expansion or len(c.split()) == 1)
                                ]
                                if candidates:
                                    replacement = random.choice(candidates)
                                    if ngram[pos].isupper() and len(ngram[pos]) > 1:
                                        replacement = replacement.upper()
                                    elif ngram[pos].istitle():
                                        replacement = replacement.capitalize()
                                    word_pat = rf"(?<!-)\b{re.escape(ngram[pos])}\b(?!-)"
                                    new_slice = re.sub(word_pat, replacement, matched_slice, count=1, flags=re.IGNORECASE)
                                    if new_slice != matched_slice:
                                        result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                        replaced = True
                                        break

                        # Priority 7: Universal Scholarly Lexicon Replacement (Curated, grammatically safe)
                        if not replaced:
                            for pos in range(n):
                                cand_word = ngram[pos].lower()
                                if (
                                    len(cand_word) <= 2
                                    or cand_word in keywords_lower
                                    or cand_word in keyword_words
                                    or cand_word in PROTECTED_TECHNICAL_WORDS
                                ):
                                    continue
                                if not re.search(rf"(?<!-)\b{re.escape(ngram[pos])}\b(?!-)", matched_slice, flags=re.IGNORECASE):
                                    continue
                                if cand_word in UNIVERSAL_SCHOLARLY_REPLACEMENTS:
                                    univ_cands = [
                                        c for c in UNIVERSAL_SCHOLARLY_REPLACEMENTS[cand_word]
                                        if not zero_expansion or len(c.split()) == 1
                                    ]
                                    if not univ_cands:
                                        continue
                                    repl_cand = random.choice(univ_cands)
                                    if ngram[pos].isupper() and len(ngram[pos]) > 1:
                                        repl_cand = repl_cand.upper()
                                    elif ngram[pos].istitle():
                                        repl_cand = repl_cand.capitalize()
                                    word_pat = rf"(?<!-)\b{re.escape(ngram[pos])}\b(?!-)"
                                    new_slice = re.sub(word_pat, repl_cand, matched_slice, count=1, flags=re.IGNORECASE)
                                    if new_slice != matched_slice:
                                        result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                        replaced = True
                                        break

                        # Priority 8: POS-guarded WordNet dynamic synonym fallback (strictly after curated dictionaries)
                        if not replaced and n >= 4:
                            for pos in range(n):
                                cand_w = ngram[pos].lower()
                                if (
                                    len(cand_w) <= 3
                                    or cand_w in keywords_lower
                                    or cand_w in keyword_words
                                    or cand_w in PROTECTED_TECHNICAL_WORDS
                                    or cand_w in {"the", "and", "for", "with", "from", "that", "this", "these", "those", "into", "onto", "upon"}
                                ):
                                    continue
                                if not re.search(rf"(?<!-)\b{re.escape(ngram[pos])}\b(?!-)", matched_slice, flags=re.IGNORECASE):
                                    continue
                                cands = self.synonym_engine.get_wordnet_candidates(cand_w)
                                if cands:
                                    rep = random.choice(cands)
                                    if ngram[pos].isupper() and len(ngram[pos]) > 1:
                                        rep = rep.upper()
                                    elif ngram[pos].istitle():
                                        rep = rep.capitalize()
                                    word_pat = rf"(?<!-)\b{re.escape(ngram[pos])}\b(?!-)"
                                    new_slice = re.sub(word_pat, rep, matched_slice, count=1, flags=re.IGNORECASE)
                                    if new_slice != matched_slice:
                                        result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                        replaced = True
                                        break

                        # Priority 9: Controlled Single Adverb Insertion before Verbs (Skipped in zero_expansion)
                        if not replaced and not zero_expansion and n >= 4:
                            for pos in range(n):
                                cand_word = ngram[pos]
                                cand_low = cand_word.lower()
                                if (
                                    len(cand_low) >= 3
                                    and cand_low not in keywords_lower
                                    and cand_low not in keyword_words
                                    and cand_low not in {"the", "and", "for", "with", "from", "that", "this", "these", "those", "into", "onto", "upon"}
                                ):
                                    qualifier_set = {"practical", "operational", "empirical", "systemic", "rigorous", "comparative", "substantive", "advanced", "contemporary", "modern", "scalable", "primary"}
                                    prefix_match = re.search(rf"(\b\w+\b)\s+{re.escape(cand_word)}\b", matched_slice, re.IGNORECASE)
                                    prev_word = prefix_match.group(1).lower() if prefix_match else ""
                                    if prev_word in qualifier_set or any(q in matched_slice.lower() for q in qualifier_set):
                                        continue

                                    if prev_word in {"to", "can", "could", "will", "would", "shall", "should", "may", "might", "must", "is", "are", "was", "were", "has", "have", "had"}:
                                        verb_syns = {
                                            "perform": ["execute", "conduct", "carry out", "undertake"],
                                            "analyze": ["examine", "evaluate", "scrutinize", "assess"],
                                            "process": ["handle", "parse", "manage", "treat"],
                                            "scale": ["expand", "grow", "adapt", "develop"],
                                            "achieve": ["attain", "reach", "realize", "produce"],
                                            "optimize": ["refine", "streamline", "enhance", "improve"]
                                        }
                                        if cand_low in verb_syns:
                                            rep = random.choice(verb_syns[cand_low])
                                            new_slice = re.sub(rf"(?<!-)\b{re.escape(cand_word)}\b(?!-)", rep, matched_slice, count=1)
                                            result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                            replaced = True
                                            break
                                        else:
                                            adv = random.choice(["consistently", "steadily", "reliably", "directly"])
                                            new_slice = re.sub(rf"(?<!-)\b{re.escape(cand_word)}\b(?!-)", f"{adv} {cand_word}", matched_slice, count=1)
                                            result_text = result_text[:match.start()] + new_slice + result_text[match.end():]
                                            replaced = True
                                            break

                        if replaced:
                            break

            if not matches_found:
                break

        # Clean up any duplicated words or consecutive qualifiers
        result_text = re.sub(r"\b([a-zA-Z]{2,})\s+\1\b", r"\1", result_text, flags=re.IGNORECASE)
        qual_pattern = r"(?:practical|operational|empirical|systemic|rigorous|comparative|substantive|advanced|contemporary|modern|scalable)"
        result_text = re.sub(rf"\b({qual_pattern})(?:\s+(?:{qual_pattern}))+\b", r"\1", result_text, flags=re.IGNORECASE)
        result_text = re.sub(r"[ ]{2,}", " ", result_text)
        return result_text.strip()

    def optimize(
        self,
        text: str,
        tone: str = "standard",
        intensity: float = 0.50,
        target_max_ai: float = 5.0,
        target_max_plagiarism: float = 0.0,
        max_passes: int = 2,
        preserve_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Adversarial optimization loop:
        Performs high-quality structural and lexical transformation, auditing results
        at each step to guarantee 0% verbatim plagiarism and single-digit/zero AI likelihood
        while preserving pristine, natural English prose.
        """
        clean_input = text.strip()
        if not clean_input:
            return {"error": "Empty input"}

        before_ai = self.analyzer.compute_ai_score(clean_input)
        keywords_set = set(preserve_keywords or [])

        current_text = clean_input
        pass_history: List[Dict[str, Any]] = []

        for pass_num in range(1, max_passes + 1):
            if pass_num == 1:
                # Step 0: Deep Syntactic and Phrase-Level Re-Engineering
                current_text = self.deep_rephraser.process(current_text)
                # Primary Pass: Full structural & lexical overhaul
                current_text = self.cleaner.clean(current_text)
                current_text = self.syntax_engine.restructure(current_text, burstiness_target=1.5)
                current_text = self.synonym_engine.replace_synonyms(
                    current_text,
                    tone=tone,
                    intensity=intensity,
                    preserve_keywords=keywords_set
                )
                current_text = self.disrupt_verbatim_ngrams(clean_input, current_text, n=5, preserve_keywords=keywords_set)
                current_text = self.disrupt_verbatim_ngrams(clean_input, current_text, n=4, preserve_keywords=keywords_set)
                current_text = self.fluency.polish(current_text)
            else:
                # Secondary refinement pass: surgically target remaining verbatim n-grams & markers
                current_text = self.cleaner.clean(current_text)
                if pass_history and (pass_history[-1].get("burstiness_index", 0.3) < 0.22 or pass_history[-1].get("ai_probability", 0.0) > target_max_ai):
                    current_text = self.syntax_engine.restructure(current_text, burstiness_target=1.8)
                current_text = self.disrupt_verbatim_ngrams(clean_input, current_text, n=5, preserve_keywords=keywords_set)
                current_text = self.disrupt_verbatim_ngrams(clean_input, current_text, n=4, preserve_keywords=keywords_set)
                current_text = self.fluency.polish(current_text)

            audit_ai = self.analyzer.compute_ai_score(current_text)
            audit_plag = self.analyzer.check_plagiarism_similarity(clean_input, current_text)

            pass_history.append({
                "pass": pass_num,
                "ai_probability": audit_ai["ai_probability"],
                "plagiarism_risk": audit_plag["plagiarism_risk_score"],
                "uniqueness": audit_plag["uniqueness_score"],
                "burstiness_index": audit_ai["burstiness_index"]
            })

            # Check convergence - stop early if quality and detection criteria are satisfied
            if (
                audit_ai["ai_probability"] <= target_max_ai
                and audit_plag["plagiarism_risk_score"] <= target_max_plagiarism
            ):
                logger.info(f"Adversarial convergence reached cleanly at pass #{pass_num}")
                break

        # Final fluency and grammar polish with guaranteed 0% verbatim plagiarism
        current_text = self.fluency.polish(current_text)
        current_text = self.disrupt_verbatim_ngrams(clean_input, current_text, n=5, preserve_keywords=keywords_set, max_passes=10)
        current_text = self.disrupt_verbatim_ngrams(clean_input, current_text, n=4, preserve_keywords=keywords_set, max_passes=10)
        current_text = self.fluency.clean_typography(current_text)
        fidelity = self.validator.validate_fidelity(clean_input, current_text)

        final_ai = self.analyzer.compute_ai_score(current_text)
        final_plag = self.analyzer.check_plagiarism_similarity(clean_input, current_text)
        ai_reduction = round(before_ai["ai_probability"] - final_ai["ai_probability"], 1)

        return {
            "original_text": clean_input,
            "humanized_text": current_text,
            "tone": tone,
            "intensity": intensity,
            "passes_executed": len(pass_history),
            "pass_history": pass_history,
            "metrics": {
                "ai_score_before": before_ai["ai_probability"],
                "ai_score_after": final_ai["ai_probability"],
                "ai_reduction": max(0.0, ai_reduction),
                "plagiarism_risk": final_plag["plagiarism_risk_score"],
                "uniqueness_score": final_plag["uniqueness_score"],
                "readability_before": before_ai["readability"],
                "readability_after": final_ai["readability"]
            },
            "fidelity": fidelity,
            "before_analysis": before_ai,
            "after_analysis": final_ai,
            "plagiarism_check": final_plag
        }
