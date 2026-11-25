"""
Context-Aware Synonym Engine with Collocation Protection.
Provides high-quality, tone-adaptive synonym replacements,
idiom replacements, protected multi-word collocation preservation,
and protection of named entities / technical terms.
"""

import functools
import random
import re
from typing import Dict, List, Optional, Set, Tuple

try:
    from nltk.corpus import wordnet
except ImportError:
    wordnet = None

from config import AI_BUZZWORDS
from core.expanded_thesaurus import EXPANDED_ACADEMIC_THESAURUS


# Multi-word collocations and scientific terms that MUST NEVER have their
# constituent tokens replaced independently (e.g. "climate change" -> NEVER "climate alter").
PROTECTED_COLLOCATIONS: List[str] = [
    # Climate & Environmental Science
    "climate change",
    "global warming",
    "greenhouse gas",
    "greenhouse gases",
    "carbon emission",
    "carbon emissions",
    "carbon footprint",
    "carbon neutral",
    "fossil fuel",
    "fossil fuels",
    "renewable energy",
    "solar power",
    "wind power",
    "hydroelectric power",
    "clean energy",
    "alternative energy",
    "extreme weather",
    "extreme weather events",
    "rising temperatures",
    "sea level rise",
    "ecosystem services",
    "ecological balance",
    "sustainable development",
    "biodiversity loss",
    "environmental protection",

    # Health & Social Psychology
    "social media",
    "social media platforms",
    "mental health",
    "mental health challenges",
    "screen time",
    "depressive symptoms",
    "quality of life",
    "standard of living",
    "cost of living",
    "public health",
    "health care",
    "healthcare systems",
    "well-being",
    "data privacy",
    "algorithmic bias",
    "patient outcomes",
    "clinical adoption",
    "decision support",
    "electronic health records",
    "rare diseases",

    # Computer Science & Technology
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "neural networks",
    "deep neural networks",
    "data science",
    "computer science",
    "natural language processing",
    "computer vision",
    "cloud computing",
    "cloud infrastructure",
    "continuous delivery",
    "continuous integration",
    "information technology",
    "cross-functional teams",
    "big data",
    "cyber security",
    "cybersecurity",

    # Academic & Sociological Concepts
    "higher education",
    "human rights",
    "socioeconomic status",
    "socioeconomic conditions",
    "decision making",
    "decision-making",
    "critical thinking",
    "peer review",
    "peer-reviewed",
    "case study",
    "case studies",
    "real world",
    "real-world",
    "supply chain",
    "supply chains",
    "in recent years",
    "economic growth",
    "public policy",
    "to be sure",
    "era of computing",
    "digital transformation",
    "predictive models",
    "predictive architectures",
    "corporate data",
    "enterprise data",

    # Scientific & Statistical Methodology
    "ground truth",
    "loss function",
    "loss functions",
    "gradient descent",
    "reinforcement learning",
    "large language model",
    "large language models",
    "standard deviation",
    "confidence interval",
    "confidence intervals",
    "statistical significance",
    "sample size",
    "control group",
    "experimental group",
    "null hypothesis",
    "cross-validation",
    "feature extraction",
    "operating system",
    "operating systems",
    "open source",
    "real time",
    "real-time",
    "monte carlo",
    "linear regression",
    "logistic regression",
    "random forest",
    "support vector machine",
    "hyperparameter tuning",
    "latent space",
    "overfitting",
    "underfitting",

    # Machine Learning, Cybersecurity & Mail Systems
    "mail server",
    "mail servers",
    "mail gateway",
    "mail gateways",
    "email server",
    "email servers",
    "email gateway",
    "email gateways",
    "spam filter",
    "spam filters",
    "spam filtering",
    "spam classifier",
    "spam classifiers",
    "spam classification",
    "data leakage",
    "leakage audit",
    "empirical data",
    "empirical data leakage",
    "false positive",
    "false positives",
    "false negative",
    "false negatives",
    "true positive",
    "true positives",
    "true negative",
    "true negatives",
    "computer science and engineering",
    "concept drift",
    "distribution shift",
    "domain shift",
    "out of distribution",
    "feature distribution",
    "confusion matrix",
    "roc curve",
    "auc score",
    "precision and recall",
    "f1 score",
    "f1-score",
    "training set",
    "test set",
    "validation set",
    "cross validation",
    "cross-validation",
    "baseline model",
    "baseline models",
    "smtp gateway",
    "smtp gateways",
    "solved problem",
    "solved problems",
    "open problem",
    "open problems",
    "real-world problem",
    "real-world problems",
    "toy problem",
    "toy problems",
    "attack vector",
    "attack vectors",
    "credential harvesting",
    "evasion heuristic",
    "evasion heuristics",
    "adversarial evasion",
    "telemetry constraint",
    "telemetry constraints",
    "telemetry data",
    "gateway telemetry",
    # STEM Equations, Theorems & Scientific Models (Protected Collocations)
    "green's function", "green's theorem", "stokes' theorem", "gauss's theorem",
    "reynolds number", "mach number", "prandtl number", "nusselt number",
    "navier-stokes", "navier-stokes equations", "wave equation", "heat equation",
    "laplace equation", "black-scholes", "differential equation", "differential equations",
    "partial derivative", "partial derivatives", "boundary condition", "boundary conditions",
    "initial condition", "initial conditions", "finite difference", "crank-nicolson",
    "truncation error", "taylor series", "fourier transform", "stochastic process",
    "neural networks", "machine learning", "deep learning", "artificial intelligence"
]

# Sensitive technical terms that must NEVER be synonymized into colloquial words
PROTECTED_TECHNICAL_WORDS: Set[str] = {
    "server", "servers", "gateway", "gateways", "email", "emails",
    "spam", "ham", "classifier", "classifiers", "classification",
    "dataset", "datasets", "benchmark", "benchmarks", "telemetry",
    "protocol", "protocols", "smtp", "imap", "pop3", "dns", "dkim",
    "spf", "dmarc", "header", "headers", "payload", "payloads",
    "corpus", "corpora", "token", "tokens", "tokenizer", "tokenizers",
    "engineering", "algorithm", "algorithms", "heuristic", "heuristics",
    "pipeline", "pipelines", "accuracy", "precision", "recall", "latency",
    "throughput", "firewall", "firewalls", "proxy", "proxies",
    "socket", "sockets", "packet", "packets", "phishing", "malware",
    "metadata", "firmware", "database", "databases",
    "artificial", "intelligence", "neural", "network", "networks",
    # STEM Scientists, Theorems, Tools & Formal Nomenclature
    "navier-stokes", "boltzmann", "maxwell", "helmholtz", "schrodinger",
    "schrödinger", "heisenberg", "bernoulli", "lagrange", "lagrangian",
    "hamiltonian", "jacobian", "hessian", "wronskian", "cauchy", "riemann",
    "hilbert", "banach", "sobolev", "lebesgue", "gaussian", "bayesian",
    "boolean", "euclidean", "cartesian", "fibonacci", "hermitian", "abelian",
    "kolmogorov", "lyapunov", "reynolds", "prandtl", "nusselt", "markov",
    "laplace", "fourier", "dirichlet", "neumann", "poincare", "eigenvalue",
    "eigenvalues", "tensorflow", "pytorch", "comsol", "ansys", "openfoam",
    "matlab", "simulink", "crispr-cas9", "biobert", "adamw", "bert",
    "resnet-50", "squad", "black-scholes", "crank-nicolson", "functional",
    "equation", "equations", "formula", "formulas"
}

# Obscure, archaic, or broken WordNet lemmas that MUST NEVER be introduced into natural prose
BANNED_OBSCURE_LEMMAS: Set[str] = {
    "yesteryear", "bygone", "erstwhile", "quondam", "whilom", "observations",
    "doings", "disc", "manipulator", "convergency", "useable", "crossways",
    "unreal", "unusual person", "mark", "shade", "monitor lizard", "ghost", "specter",
    "holocene", "twelvemonth", "homo", "potpourri", "psychoanalysis",
    "pivotal", "tapestry", "delve", "delves", "delving", "multifaceted", "intertwined",
    "testament", "beacon", "plethora", "juxtaposition",
    "overarching", "commence", "commences", "commencing",
    "whilst", "heretofore", "henceforth", "peradventure", "betwixt", "forthwith",
    "schema", "panacea", "zeitgeist", "nexus", "linchpin",
    "cornerstone", "bedrock", "behoove", "verily", "whence", "wherefore",
    "standpoint", "figure", "espouse", "espouses", "espousing", "requisite",
    "promote", "promoted", "practice", "realism", "cope", "necessity"
}

# Common function words, particles, prepositions, and pronouns that must NEVER fall back to generic WordNet lookup
COMMON_FUNCTION_WORDS: Set[str] = {
    "a", "an", "the", "in", "on", "at", "for", "by", "to", "of", "with", "from",
    "as", "is", "was", "are", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "doing", "done", "it", "its", "it's", "they", "them",
    "their", "theirs", "we", "our", "ours", "us", "you", "your", "yours", "he",
    "she", "him", "her", "his", "hers", "that", "this", "these", "those", "which",
    "who", "whom", "whose", "what", "where", "when", "why", "how", "if", "or",
    "and", "but", "nor", "so", "yet", "not", "no", "yes", "through", "into",
    "onto", "upon", "over", "down", "up", "out", "about", "above", "below",
    "between", "both", "some", "any", "many", "much", "each", "few", "more",
    "most", "all", "such", "than", "then", "very", "also", "just", "even",
    "well", "back", "away", "like", "same", "only", "must", "should", "would",
    "could", "might", "shall", "will", "can", "work", "care", "make", "take",
    "give", "keep", "hold", "find", "call", "turn", "part", "case", "point",
    "hand", "side", "line", "time", "room", "deal"
}


class SynonymEngine:
    """
    Manages intelligent vocabulary replacement and tonal tuning.
    Maintains grammatical agreement, protects sensitive domain terms,
    and prevents destructive single-token substitutions inside protected collocations.
    """

    def __init__(self):
        # Comprehensive curated synonym dictionary for high-frequency academic,
        # professional, and everyday terms prone to AI repetition and plagiarism flags.
        self.thesaurus: Dict[str, Dict[str, List[str]]] = {
            # --- VERBS: High-Frequency Academic & Analytical ---
            "show": {
                "academic": ["demonstrate", "illustrate", "indicate", "evince", "reveal"],
                "casual": ["show", "point out", "highlight", "prove"],
                "journalistic": ["uncover", "reveal", "highlight", "signal"],
                "standard": ["reveal", "display", "demonstrate", "make clear"]
            },
            "shows": {
                "academic": ["demonstrates", "illustrates", "indicates", "evinces", "reveals"],
                "casual": ["shows", "points out", "highlights", "proves"],
                "journalistic": ["uncovers", "reveals", "highlights", "signals"],
                "standard": ["reveals", "displays", "demonstrates", "makes clear"]
            },
            "showing": {
                "academic": ["demonstrating", "illustrating", "indicating", "revealing"],
                "casual": ["showing", "pointing out", "highlighting"],
                "journalistic": ["uncovering", "revealing", "highlighting"],
                "standard": ["revealing", "displaying", "demonstrating"]
            },
            "showed": {
                "academic": ["demonstrated", "illustrated", "indicated", "evinced", "revealed"],
                "casual": ["showed", "pointed out", "highlighted", "proved"],
                "journalistic": ["uncovered", "revealed", "highlighted", "signaled"],
                "standard": ["revealed", "displayed", "demonstrated", "made clear"]
            },
            "use": {
                "academic": ["employ", "utilize", "apply", "leverage", "implement"],
                "casual": ["use", "try out", "tap into", "work with"],
                "journalistic": ["deploy", "adopt", "apply", "harness"],
                "standard": ["employ", "adopt", "work with", "apply"]
            },
            "uses": {
                "academic": ["employs", "utilizes", "applies", "leverages", "implements"],
                "casual": ["uses", "tries out", "taps into", "works with"],
                "journalistic": ["deploys", "adopts", "applies", "harnesses"],
                "standard": ["employs", "adopts", "works with", "applies"]
            },
            "using": {
                "academic": ["employing", "utilizing", "applying", "leveraging"],
                "casual": ["using", "drawing on", "working with"],
                "journalistic": ["deploying", "adopting", "harnessing"],
                "standard": ["employing", "adopting", "applying"]
            },
            "used": {
                "academic": ["employed", "utilized", "applied", "leveraged", "implemented"],
                "casual": ["used", "drawn on", "worked with"],
                "journalistic": ["deployed", "adopted", "applied", "harnessed"],
                "standard": ["employed", "adopted", "applied"]
            },
            "improve": {
                "academic": ["enhance", "augment", "optimize", "elevate", "refine"],
                "casual": ["boost", "sharpen", "level up", "step up"],
                "journalistic": ["bolster", "upgrade", "strengthen", "boost"],
                "standard": ["enhance", "boost", "upgrade", "strengthen"]
            },
            "improves": {
                "academic": ["enhances", "augments", "optimizes", "elevates", "refines"],
                "casual": ["boosts", "sharpens", "levels up", "steps up"],
                "journalistic": ["bolsters", "upgrades", "strengthens", "boosts"],
                "standard": ["enhances", "boosts", "upgrades", "strengthens"]
            },
            "improving": {
                "academic": ["enhancing", "augmenting", "optimizing", "refining"],
                "casual": ["boosting", "sharpening", "stepping up"],
                "journalistic": ["bolstering", "upgrading", "strengthening"],
                "standard": ["enhancing", "boosting", "upgrading"]
            },
            "improved": {
                "academic": ["enhanced", "augmented", "optimized", "refined", "elevated"],
                "casual": ["boosted", "sharpened", "stepped up"],
                "journalistic": ["bolstered", "upgraded", "strengthened", "boosted"],
                "standard": ["enhanced", "boosted", "upgraded", "strengthened"]
            },
            "create": {
                "academic": ["generate", "formulate", "establish", "synthesize", "construct"],
                "casual": ["make", "build", "craft", "put together"],
                "journalistic": ["forge", "produce", "generate", "launch"],
                "standard": ["develop", "produce", "build", "craft"]
            },
            "creates": {
                "academic": ["generates", "formulates", "establishes", "synthesizes"],
                "casual": ["makes", "builds", "crafts", "puts together"],
                "journalistic": ["forges", "produces", "generates", "launches"],
                "standard": ["develops", "produces", "builds", "crafts"]
            },
            "creating": {
                "academic": ["generating", "formulating", "establishing", "synthesizing"],
                "casual": ["making", "building", "crafting"],
                "journalistic": ["forging", "producing", "generating"],
                "standard": ["developing", "producing", "building"]
            },
            "created": {
                "academic": ["generated", "formulated", "established", "synthesized"],
                "casual": ["made", "built", "crafted"],
                "journalistic": ["forged", "produced", "generated", "launched"],
                "standard": ["developed", "produced", "built"]
            },
            "help": {
                "academic": ["facilitate", "assist", "expedite", "support"],
                "casual": ["help", "lend a hand", "back up", "make easier"],
                "journalistic": ["assist", "enable", "support", "propel"],
                "standard": ["aid", "support", "enable", "assist"]
            },
            "helps": {
                "academic": ["facilitates", "assists", "expedites", "supports"],
                "casual": ["helps", "lends a hand", "makes easier"],
                "journalistic": ["assists", "enables", "supports", "propels"],
                "standard": ["aids", "supports", "enables", "assists"]
            },
            "helping": {
                "academic": ["facilitating", "assisting", "expediting", "supporting"],
                "casual": ["helping", "lending a hand", "making easier"],
                "journalistic": ["assisting", "enabling", "supporting"],
                "standard": ["aiding", "supporting", "enabling"]
            },
            "helped": {
                "academic": ["facilitated", "assisted", "expedited", "supported"],
                "casual": ["helped", "backed up", "made easier"],
                "journalistic": ["assisted", "enabled", "supported"],
                "standard": ["aided", "supported", "enabled"]
            },
            "provide": {
                "academic": ["furnish", "render", "deliver", "yield", "supply"],
                "casual": ["give", "offer", "hand out", "bring to the table"],
                "journalistic": ["deliver", "supply", "offer", "provide"],
                "standard": ["offer", "deliver", "supply", "present"]
            },
            "provides": {
                "academic": ["furnishes", "renders", "delivers", "yields", "supplies"],
                "casual": ["gives", "offers", "delivers"],
                "journalistic": ["delivers", "supplies", "offers"],
                "standard": ["offers", "delivers", "supplies", "presents"]
            },
            "providing": {
                "academic": ["furnishing", "rendering", "delivering", "yielding", "supplying"],
                "casual": ["giving", "offering", "bringing"],
                "journalistic": ["delivering", "supplying", "offering"],
                "standard": ["offering", "delivering", "supplying", "presenting"]
            },
            "provided": {
                "academic": ["furnished", "rendered", "delivered", "yielded", "supplied"],
                "casual": ["given", "offered", "brought"],
                "journalistic": ["delivered", "supplied", "offered"],
                "standard": ["offered", "delivered", "supplied"]
            },
            "understand": {
                "academic": ["comprehend", "discern", "fathom", "ascertain", "grasp"],
                "casual": ["get", "grasp", "wrap one's head around", "catch on to"],
                "journalistic": ["grasp", "make sense of", "unravel", "decode"],
                "standard": ["grasp", "recognize", "comprehend", "interpret"]
            },
            "understands": {
                "academic": ["comprehends", "discerns", "fathoms", "ascertains"],
                "casual": ["gets", "grasps", "catches on to"],
                "journalistic": ["grasps", "decodes", "makes sense of"],
                "standard": ["grasps", "recognizes", "interprets"]
            },
            "change": {
                "academic": ["alter", "modify", "transform", "shift", "reconfigure"],
                "casual": ["switch up", "tweak", "shake up", "turn around"],
                "journalistic": ["overhaul", "reshape", "pivot", "transform"],
                "standard": ["reshape", "shift", "transform", "modify"]
            },
            "changes": {
                "academic": ["alters", "modifies", "transforms", "shifts"],
                "casual": ["tweaks", "shakes up", "switches"],
                "journalistic": ["overhauls", "reshapes", "pivots"],
                "standard": ["reshapes", "shifts", "transforms", "modifies"]
            },
            "changing": {
                "academic": ["altering", "modifying", "transforming", "shifting"],
                "casual": ["switching", "tweaking", "shifting"],
                "journalistic": ["reshaping", "overhauling", "pivoting"],
                "standard": ["reshaping", "shifting", "transforming"]
            },
            "changed": {
                "academic": ["altered", "modified", "transformed", "shifted"],
                "casual": ["switched", "tweaked", "turned around"],
                "journalistic": ["reshaped", "overhauled", "pivoted"],
                "standard": ["reshaped", "shifted", "transformed"]
            },
            "suggest": {
                "academic": ["indicate", "posit", "imply", "intimate", "propose"],
                "casual": ["hint", "point to", "suggest"],
                "journalistic": ["signal", "indicate", "suggest", "point to"],
                "standard": ["indicate", "point to", "propose", "suggest"]
            },
            "suggests": {
                "academic": ["indicates", "posits", "implies", "intimates", "signals"],
                "casual": ["hints at", "points to", "suggests"],
                "journalistic": ["signals", "indicates", "points to"],
                "standard": ["indicates", "points to", "signals", "suggests"]
            },
            "suggesting": {
                "academic": ["indicating", "positing", "implying", "intimating"],
                "casual": ["hinting", "pointing to"],
                "journalistic": ["signaling", "indicating", "pointing to"],
                "standard": ["indicating", "pointing to", "signaling"]
            },
            "suggested": {
                "academic": ["indicated", "posited", "implied", "intimated"],
                "casual": ["hinted", "pointed to"],
                "journalistic": ["signaled", "indicated", "pointed to"],
                "standard": ["indicated", "pointed to", "signaled"]
            },
            "require": {
                "academic": ["necessitate", "mandate", "demand", "call for", "entail"],
                "casual": ["need", "call for", "take"],
                "journalistic": ["demand", "require", "call for"],
                "standard": ["necessitate", "demand", "call for", "require"]
            },
            "requires": {
                "academic": ["necessitates", "mandates", "demands", "calls for", "entails"],
                "casual": ["needs", "calls for", "takes"],
                "journalistic": ["demands", "requires", "calls for"],
                "standard": ["necessitates", "demands", "calls for", "requires"]
            },
            "requiring": {
                "academic": ["necessitating", "mandating", "demanding", "calling for"],
                "casual": ["needing", "calling for"],
                "journalistic": ["demanding", "requiring"],
                "standard": ["necessitating", "demanding", "calling for"]
            },
            "required": {
                "academic": ["necessitated", "mandated", "demanded", "called for"],
                "casual": ["needed", "called for"],
                "journalistic": ["demanded", "required"],
                "standard": ["necessitated", "demanded", "called for"]
            },
            "remain": {
                "academic": ["persist", "endure", "continue to be", "abide"],
                "casual": ["stay", "keep being", "hang on"],
                "journalistic": ["stand as", "persist as", "continue as"],
                "standard": ["continue to be", "persist as", "remain"]
            },
            "remains": {
                "academic": ["persists as", "endures as", "continues to be", "stands as"],
                "casual": ["stays", "keeps being", "remains"],
                "journalistic": ["stands as", "persists as", "continues to be"],
                "standard": ["continues to be", "persists as", "stands as"]
            },
            "remaining": {
                "academic": ["persisting", "enduring", "continuing"],
                "casual": ["staying", "sticking around"],
                "journalistic": ["persisting", "continuing"],
                "standard": ["continuing", "persisting", "enduring"]
            },
            "remained": {
                "academic": ["persisted", "endured", "continued to be"],
                "casual": ["stayed", "kept being"],
                "journalistic": ["stood as", "persisted as"],
                "standard": ["continued to be", "persisted as"]
            },
            "threaten": {
                "academic": ["jeopardize", "endanger", "imperil", "destabilize"],
                "casual": ["put at risk", "hurt", "mess with"],
                "journalistic": ["imperil", "menace", "jeopardize", "endanger"],
                "standard": ["jeopardize", "endanger", "imperil", "put at risk"]
            },
            "threatens": {
                "academic": ["jeopardizes", "endangers", "imperils", "destabilizes"],
                "casual": ["puts at risk", "hurts"],
                "journalistic": ["imperils", "menaces", "jeopardizes"],
                "standard": ["jeopardizes", "endangers", "imperils", "puts at risk"]
            },
            "threatening": {
                "academic": ["jeopardizing", "endangering", "imperiling", "destabilizing"],
                "casual": ["putting at risk", "hurting"],
                "journalistic": ["imperiling", "jeopardizing"],
                "standard": ["jeopardizing", "endangering", "imperiling"]
            },
            "threatened": {
                "academic": ["jeopardized", "endangered", "imperiled", "destabilized"],
                "casual": ["put at risk", "hurt"],
                "journalistic": ["imperiled", "jeopardized"],
                "standard": ["jeopardized", "endangered", "imperiled"]
            },
            "connect": {
                "academic": ["interlink", "bridge", "interface", "unite"],
                "casual": ["link up", "reach out to", "connect with"],
                "journalistic": ["link", "unite", "bridge"],
                "standard": ["link", "bridge", "bring together", "interface"]
            },
            "connects": {
                "academic": ["interlinks", "bridges", "interfaces", "unites"],
                "casual": ["links up", "connects with"],
                "journalistic": ["links", "unites", "bridges"],
                "standard": ["links", "bridges", "brings together"]
            },
            "connecting": {
                "academic": ["interlinking", "bridging", "interfacing", "uniting"],
                "casual": ["linking up", "connecting"],
                "journalistic": ["linking", "bridging"],
                "standard": ["linking", "bridging", "bringing together"]
            },
            "connected": {
                "academic": ["interlinked", "bridged", "interfaced", "united"],
                "casual": ["linked up", "tied together"],
                "journalistic": ["linked", "bridged"],
                "standard": ["linked", "bridged", "brought together"]
            },
            "address": {
                "academic": ["confront", "tackle", "manage", "resolve", "grapple with"],
                "casual": ["deal with", "handle", "tackle"],
                "journalistic": ["tackle", "confront", "take on"],
                "standard": ["tackle", "confront", "handle", "manage"]
            },
            "addresses": {
                "academic": ["confronts", "tackles", "manages", "resolves", "grapples with"],
                "casual": ["deals with", "handles", "tackles"],
                "journalistic": ["tackles", "confronts", "takes on"],
                "standard": ["tackles", "confronts", "handles", "manages"]
            },
            "addressing": {
                "academic": ["confronting", "tackling", "managing", "resolving", "grappling with"],
                "casual": ["dealing with", "handling", "tackling"],
                "journalistic": ["tackling", "confronting", "taking on"],
                "standard": ["tackling", "confronting", "handling", "managing"]
            },
            "addressed": {
                "academic": ["confronted", "tackled", "managed", "resolved"],
                "casual": ["dealt with", "handled"],
                "journalistic": ["tackled", "confronted"],
                "standard": ["tackled", "confronted", "handled"]
            },
            "mitigate": {
                "academic": ["attenuate", "alleviate", "curb", "diminish", "curtail"],
                "casual": ["cut down on", "ease", "lessen"],
                "journalistic": ["curb", "blunt", "lessen", "temper"],
                "standard": ["curb", "alleviate", "lessen", "diminish"]
            },
            "mitigates": {
                "academic": ["attenuates", "alleviates", "curbs", "diminishes", "curtails"],
                "casual": ["cuts down on", "eases", "lessens"],
                "journalistic": ["curbs", "blunts", "lessens", "tempers"],
                "standard": ["curbs", "alleviates", "lessens", "diminishes"]
            },
            "mitigating": {
                "academic": ["attenuating", "alleviating", "curbing", "curtailing"],
                "casual": ["cutting down on", "easing", "lessening"],
                "journalistic": ["curbing", "blunting", "lessening"],
                "standard": ["curbing", "alleviating", "lessening"]
            },
            "mitigated": {
                "academic": ["attenuated", "alleviated", "curbed", "curtailed"],
                "casual": ["cut down", "eased", "lessened"],
                "journalistic": ["curbed", "blunted", "lessened"],
                "standard": ["curbed", "alleviated", "lessened"]
            },
            "transform": {
                "academic": ["revolutionize", "reconfigure", "remodel", "reshape"],
                "casual": ["shake up", "turn around", "remake"],
                "journalistic": ["overhaul", "reshape", "revolutionize"],
                "standard": ["reshape", "remodel", "revolutionize", "overhaul"]
            },
            "transforms": {
                "academic": ["revolutionizes", "reconfigures", "remodels", "reshapes"],
                "casual": ["shakes up", "turns around", "remakes"],
                "journalistic": ["overhauls", "reshapes", "revolutionizes"],
                "standard": ["reshapes", "remodels", "revolutionizes", "overhauls"]
            },
            "transforming": {
                "academic": ["revolutionizing", "reconfiguring", "remodeling", "reshaping"],
                "casual": ["shaking up", "remaking"],
                "journalistic": ["overhauling", "reshaping", "revolutionizing"],
                "standard": ["reshaping", "remodeling", "revolutionizing"]
            },
            "transformed": {
                "academic": ["revolutionized", "reconfigured", "remodeled", "reshaped"],
                "casual": ["shook up", "turned around", "remade"],
                "journalistic": ["overhauled", "reshaped", "revolutionized"],
                "standard": ["reshaped", "remodeled", "revolutionized"]
            },
            "foster": {
                "academic": ["cultivate", "nurture", "stimulate", "promote"],
                "casual": ["encourage", "build", "grow"],
                "journalistic": ["spur", "fuel", "foster", "cultivate"],
                "standard": ["cultivate", "encourage", "nurture", "stimulate"]
            },
            "fosters": {
                "academic": ["cultivates", "nurtures", "stimulates", "promotes"],
                "casual": ["encourages", "builds", "grows"],
                "journalistic": ["spurs", "fuels", "fosters", "cultivates"],
                "standard": ["cultivates", "encourages", "nurtures", "stimulates"]
            },
            "fostering": {
                "academic": ["cultivating", "nurturing", "stimulating", "promoting"],
                "casual": ["encouraging", "building"],
                "journalistic": ["spurring", "fueling", "cultivating"],
                "standard": ["cultivating", "encouraging", "nurturing"]
            },
            "fostered": {
                "academic": ["cultivated", "nurtured", "stimulated", "promoted"],
                "casual": ["encouraged", "built"],
                "journalistic": ["spurred", "fueled", "cultivated"],
                "standard": ["cultivated", "encouraged", "nurtured"]
            },
            "accelerate": {
                "academic": ["expedite", "precipitate", "quicken", "hasten"],
                "casual": ["speed up", "step up", "ramp up"],
                "journalistic": ["quicken", "speed up", "hasten"],
                "standard": ["expedite", "speed up", "hasten"]
            },
            "accelerates": {
                "academic": ["expedites", "precipitates", "quickens", "hastens"],
                "casual": ["speeds up", "steps up", "ramps up"],
                "journalistic": ["quickens", "speeds up", "hastens"],
                "standard": ["expedites", "speeds up", "hastens"]
            },
            "diminish": {
                "academic": ["curtail", "attenuate", "lessen", "deplete"],
                "casual": ["cut down", "drop", "shrink"],
                "journalistic": ["erode", "lessen", "weaken"],
                "standard": ["lessen", "reduce", "erode"]
            },
            "diminishes": {
                "academic": ["curtails", "attenuates", "lessens", "depletes"],
                "casual": ["cuts down", "drops", "shrinks"],
                "journalistic": ["erodes", "lessens", "weakens"],
                "standard": ["lessens", "reduces", "erodes"]
            },
            "exacerbate": {
                "academic": ["compound", "aggravate", "intensify", "magnify"],
                "casual": ["make worse", "worsen", "inflame"],
                "journalistic": ["worsen", "inflame", "deepen"],
                "standard": ["aggravate", "worsen", "compound"]
            },
            "exacerbates": {
                "academic": ["compounds", "aggravates", "intensifies", "magnifies"],
                "casual": ["makes worse", "worsens"],
                "journalistic": ["worsens", "deepens", "inflames"],
                "standard": ["aggravates", "worsens", "compounds"]
            },
            "assist": {
                "academic": ["support", "empower", "aid", "facilitate"],
                "casual": ["help", "back up", "lend a hand"],
                "journalistic": ["assist", "help", "support"],
                "standard": ["support", "aid", "help", "assist"]
            },
            "assists": {
                "academic": ["supports", "empowers", "aids", "facilitates"],
                "casual": ["helps", "backs up"],
                "journalistic": ["assists", "helps", "supports"],
                "standard": ["supports", "aids", "helps"]
            },
            "diagnose": {
                "academic": ["identify", "detect", "discern", "pinpoint"],
                "casual": ["spot", "find", "catch"],
                "journalistic": ["detect", "identify", "spot"],
                "standard": ["detect", "identify", "pinpoint"]
            },
            "diagnosing": {
                "academic": ["identifying", "detecting", "discerning", "pinpointing"],
                "casual": ["spotting", "finding", "catching"],
                "journalistic": ["detecting", "identifying", "spotting"],
                "standard": ["detecting", "identifying", "pinpointing"]
            },
            "predict": {
                "academic": ["forecast", "anticipate", "project", "foresee"],
                "casual": ["guess", "call", "predict"],
                "journalistic": ["forecast", "predict", "project"],
                "standard": ["forecast", "anticipate", "project"]
            },
            "predicting": {
                "academic": ["forecasting", "anticipating", "projecting", "foreseeing"],
                "casual": ["calling", "predicting"],
                "journalistic": ["forecasting", "projecting"],
                "standard": ["forecasting", "anticipating", "projecting"]
            },
            "demonstrate": {
                "academic": ["substantiate", "validate", "evince", "corroborate"],
                "casual": ["prove", "show", "back up"],
                "journalistic": ["prove", "show", "confirm"],
                "standard": ["substantiate", "validate", "confirm", "prove"]
            },
            "demonstrates": {
                "academic": ["substantiates", "validates", "evinces", "corroborates"],
                "casual": ["proves", "shows", "backs up"],
                "journalistic": ["proves", "shows", "confirms"],
                "standard": ["substantiates", "validates", "confirms", "proves"]
            },
            "facilitate": {
                "academic": ["streamline", "expedite", "catalyze", "enable"],
                "casual": ["make easier", "smooth the way for", "help"],
                "journalistic": ["pave the way for", "ease", "enable"],
                "standard": ["enable", "streamline", "expedite", "make easier"]
            },
            "facilitates": {
                "academic": ["streamlines", "expedites", "catalyzes", "enables"],
                "casual": ["makes easier", "helps"],
                "journalistic": ["eases", "enables", "paves the way for"],
                "standard": ["enables", "streamlines", "expedites"]
            },
            "implement": {
                "academic": ["operationalize", "enact", "execute", "institute"],
                "casual": ["carry out", "put in place", "set up"],
                "journalistic": ["roll out", "enact", "deploy"],
                "standard": ["execute", "enact", "carry out", "deploy"]
            },
            "implements": {
                "academic": ["operationalizes", "enacts", "executes", "institutes"],
                "casual": ["carries out", "puts in place"],
                "journalistic": ["rolls out", "enacts", "deploys"],
                "standard": ["executes", "enacts", "carries out"]
            },
            "examine": {
                "academic": ["scrutinize", "interrogate", "evaluate", "probe"],
                "casual": ["look at", "check out", "go over"],
                "journalistic": ["investigate", "probe", "explore"],
                "standard": ["scrutinize", "investigate", "evaluate", "inspect"]
            },
            "examines": {
                "academic": ["scrutinizes", "interrogates", "evaluates", "probes"],
                "casual": ["looks at", "checks out"],
                "journalistic": ["investigates", "probes", "explores"],
                "standard": ["scrutinizes", "investigates", "evaluates"]
            },
            "emphasize": {
                "academic": ["underscore", "accentuate", "foreground", "highlight"],
                "casual": ["stress", "point out", "highlight"],
                "journalistic": ["highlight", "stress", "spotlight"],
                "standard": ["highlight", "underscore", "stress", "accentuate"]
            },
            "emphasizes": {
                "academic": ["underscores", "accentuates", "foregrounds", "highlights"],
                "casual": ["stresses", "points out", "highlights"],
                "journalistic": ["highlights", "stresses", "spotlights"],
                "standard": ["highlights", "underscores", "stresses"]
            },
            "navigate": {
                "academic": ["traverse", "steer through", "negotiate", "manage"],
                "casual": ["work through", "get through", "handle"],
                "journalistic": ["tackle", "steer through", "manage"],
                "standard": ["steer through", "manage", "traverse"]
            },
            "navigates": {
                "academic": ["traverses", "steers through", "negotiates", "manages"],
                "casual": ["works through", "gets through"],
                "journalistic": ["steers through", "manages"],
                "standard": ["steers through", "manages", "traverses"]
            },
            "rely": {
                "academic": ["depend", "hinge", "rest", "lean"],
                "casual": ["count on", "bank on", "lean on"],
                "journalistic": ["depend on", "rely on", "hinge on"],
                "standard": ["depend", "hinge", "rest"]
            },
            "relies": {
                "academic": ["depends", "hinges", "rests", "leans"],
                "casual": ["counts on", "banks on", "leans on"],
                "journalistic": ["depends on", "hinges on", "rests on"],
                "standard": ["depends", "hinges", "rests"]
            },
            "expand": {
                "academic": ["broaden", "proliferate", "augment", "extend"],
                "casual": ["grow", "spread", "widen"],
                "journalistic": ["scale up", "widen", "extend"],
                "standard": ["broaden", "extend", "widen", "grow"]
            },
            "expands": {
                "academic": ["broadens", "proliferates", "augments", "extends"],
                "casual": ["grows", "spreads", "widens"],
                "journalistic": ["scales up", "widens", "extends"],
                "standard": ["broadens", "extends", "widens"]
            },
            "transition": {
                "academic": ["shift", "migrate", "convert", "pivot"],
                "casual": ["switch", "move over", "shift"],
                "journalistic": ["shift", "pivot", "move"],
                "standard": ["shift", "migrate", "transition"]
            },
            "transitioning": {
                "academic": ["shifting", "migrating", "converting", "pivoting"],
                "casual": ["switching", "moving over"],
                "journalistic": ["shifting", "pivoting"],
                "standard": ["shifting", "migrating", "transitioning"]
            },

            # --- NOUNS: Academic, Scientific & Analytical ---
            "problem": {
                "academic": ["dilemma", "impediment", "predicament", "hurdle"],
                "casual": ["snag", "hiccup", "headache", "trouble"],
                "journalistic": ["crisis", "setback", "bottleneck", "obstacle"],
                "standard": ["challenge", "hurdle", "obstacle", "issue"]
            },
            "problems": {
                "academic": ["dilemmas", "impediments", "predicaments", "hurdles"],
                "casual": ["snags", "hiccups", "headaches", "issues"],
                "journalistic": ["setbacks", "bottlenecks", "obstacles"],
                "standard": ["challenges", "hurdles", "obstacles", "issues"]
            },
            "challenge": {
                "academic": ["impediment", "predicament", "conundrum", "hurdle"],
                "casual": ["tough spot", "hurdle", "headache"],
                "journalistic": ["hurdle", "test", "trial", "obstacle"],
                "standard": ["obstacle", "hurdle", "difficulty", "trial"]
            },
            "challenges": {
                "academic": ["impediments", "predicaments", "conundrums", "hurdles"],
                "casual": ["hurdles", "difficulties", "headaches"],
                "journalistic": ["hurdles", "trials", "obstacles"],
                "standard": ["obstacles", "hurdles", "difficulties"]
            },
            "solution": {
                "academic": ["remedy", "resolution", "framework", "intervention"],
                "casual": ["fix", "answer", "way out"],
                "journalistic": ["answer", "fix", "remedy"],
                "standard": ["remedy", "resolution", "measure", "answer"]
            },
            "solutions": {
                "academic": ["remedies", "resolutions", "frameworks", "interventions"],
                "casual": ["fixes", "answers", "tools"],
                "journalistic": ["answers", "fixes", "remedies"],
                "standard": ["remedies", "resolutions", "measures", "answers"]
            },
            "intervention": {
                "academic": ["remedial measure", "policy initiative", "protocol"],
                "casual": ["action", "step", "move"],
                "journalistic": ["measure", "step", "initiative"],
                "standard": ["initiative", "measure", "step"]
            },
            "interventions": {
                "academic": ["remedial measures", "policy initiatives", "protocols", "concerted efforts"],
                "casual": ["actions", "steps", "moves"],
                "journalistic": ["measures", "steps", "initiatives"],
                "standard": ["initiatives", "measures", "steps"]
            },
            "result": {
                "academic": ["outcome", "consequence", "ramification", "corollary"],
                "casual": ["upshot", "takeaway", "what came out of it"],
                "journalistic": ["aftermath", "fallout", "outcome", "finding"],
                "standard": ["outcome", "finding", "consequence", "effect"]
            },
            "results": {
                "academic": ["outcomes", "consequences", "ramifications", "findings"],
                "casual": ["takeaways", "outcomes"],
                "journalistic": ["findings", "outcomes", "effects"],
                "standard": ["outcomes", "findings", "consequences"]
            },
            "method": {
                "academic": ["methodology", "technique", "approach", "paradigm"],
                "casual": ["way", "tactic", "strategy"],
                "journalistic": ["formula", "playbook", "technique", "strategy"],
                "standard": ["approach", "strategy", "technique", "system"]
            },
            "methods": {
                "academic": ["methodologies", "techniques", "approaches", "paradigms"],
                "casual": ["ways", "tactics", "strategies"],
                "journalistic": ["playbooks", "techniques", "strategies"],
                "standard": ["approaches", "strategies", "techniques"]
            },
            "impact": {
                "academic": ["ramification", "influence", "repercussion", "resonance"],
                "casual": ["footprint", "dent", "effect"],
                "journalistic": ["fallout", "imprint", "ripple effect", "consequence"],
                "standard": ["influence", "bearing", "effect", "consequence"]
            },
            "expansion": {
                "academic": ["proliferation", "growth", "amplification", "surge"],
                "casual": ["growth", "spread", "rise"],
                "journalistic": ["spread", "surge", "boom"],
                "standard": ["growth", "spread", "rise", "proliferation"]
            },
            "boundaries": {
                "academic": ["frontiers", "demarcations", "perimeters", "limits"],
                "casual": ["borders", "lines", "limits"],
                "journalistic": ["borders", "frontiers", "limits"],
                "standard": ["frontiers", "borders", "limits"]
            },
            "adolescents": {
                "academic": ["young individuals", "youth cohorts", "teenagers", "juveniles"],
                "casual": ["teens", "teenagers", "young people"],
                "journalistic": ["young people", "teens", "youth"],
                "standard": ["young people", "teenagers", "youth"]
            },
            "anxiety": {
                "academic": ["psychological distress", "apprehension", "nervous tension"],
                "casual": ["stress", "worry", "nerves"],
                "journalistic": ["stress", "distress", "unease"],
                "standard": ["distress", "apprehension", "stress"]
            },
            "symptoms": {
                "academic": ["manifestations", "indications", "markers", "signs"],
                "casual": ["signs", "warning signs", "red flags"],
                "journalistic": ["signs", "indicators", "markers"],
                "standard": ["manifestations", "signs", "indicators"]
            },
            "policymakers": {
                "academic": ["legislative authorities", "regulatory bodies", "institutional leaders"],
                "casual": ["leaders", "officials", "decision-makers"],
                "journalistic": ["officials", "regulators", "lawmakers"],
                "standard": ["regulators", "legislators", "officials"]
            },
            "educators": {
                "academic": ["pedagogical instructors", "academic faculty", "instructors"],
                "casual": ["teachers", "school staff", "instructors"],
                "journalistic": ["teachers", "educators", "instructors"],
                "standard": ["instructors", "teachers", "academic leaders"]
            },
            "livelihoods": {
                "academic": ["means of economic subsistence", "socioeconomic sustenance", "living conditions"],
                "casual": ["jobs", "ways of living", "earnings"],
                "journalistic": ["jobs", "living conditions", "economic livelihoods"],
                "standard": ["means of subsistence", "living conditions", "livelihoods"]
            },
            "ecosystems": {
                "academic": ["ecological systems", "natural habitats", "biomes"],
                "casual": ["habitats", "natural environments"],
                "journalistic": ["habitats", "ecosystems", "environments"],
                "standard": ["ecological systems", "natural habitats", "environments"]
            },
            "temperatures": {
                "academic": ["thermal levels", "ambient temperatures", "thermal readings"],
                "casual": ["heat levels", "temperatures"],
                "journalistic": ["temperatures", "heat levels"],
                "standard": ["thermal levels", "temperatures"]
            },
            "events": {
                "academic": ["phenomena", "episodes", "occurrences", "manifestations"],
                "casual": ["happenings", "events"],
                "journalistic": ["occurrences", "episodes", "events"],
                "standard": ["phenomena", "occurrences", "episodes"]
            },
            "emissions": {
                "academic": ["discharges", "effluents", "pollutants", "atmospheric releases"],
                "casual": ["pollution", "fumes", "exhaust"],
                "journalistic": ["pollution", "discharges", "releases"],
                "standard": ["discharges", "pollutants", "releases"]
            },
            "sources": {
                "academic": ["origins", "supplies", "reservoirs", "streams"],
                "casual": ["supplies", "options", "places"],
                "journalistic": ["sources", "supplies", "origins"],
                "standard": ["origins", "supplies", "sources"]
            },
            "research": {
                "academic": ["empirical scholarship", "scholarly investigations", "empirical inquiry"],
                "casual": ["studies", "investigations", "work"],
                "journalistic": ["studies", "findings", "inquiry"],
                "standard": ["studies", "investigations", "scholarly inquiry"]
            },
            "framework": {
                "academic": ["conceptual schema", "analytical architecture", "paradigm"],
                "casual": ["system", "setup", "structure"],
                "journalistic": ["blueprint", "system", "structure"],
                "standard": ["structure", "architecture", "paradigm"]
            },
            "evidence": {
                "academic": ["empirical substantiation", "corroboration", "verifiable documentation"],
                "casual": ["proof", "data", "facts"],
                "journalistic": ["proof", "evidence", "findings"],
                "standard": ["corroboration", "documentation", "proof"]
            },
            "data": {
                "academic": ["empirical records", "observational records", "datasets"],
                "casual": ["info", "records", "numbers"],
                "journalistic": ["records", "information", "metrics"],
                "standard": ["information", "records", "datasets"]
            },
            "algorithm": {
                "academic": ["computational model", "analytical framework", "system", "architecture"],
                "casual": ["tool", "program", "system"],
                "journalistic": ["engine", "model", "system", "program"],
                "standard": ["model", "system", "program", "framework"]
            },
            "algorithms": {
                "academic": ["computational models", "analytical frameworks", "systems", "architectures"],
                "casual": ["tools", "programs", "systems"],
                "journalistic": ["engines", "models", "systems", "programs"],
                "standard": ["models", "systems", "programs", "frameworks"]
            },
            "infrastructure": {
                "academic": ["foundational architecture", "underlying systems", "frameworks"],
                "casual": ["setup", "systems", "backbone"],
                "journalistic": ["systems", "framework", "backbone"],
                "standard": ["architecture", "systems", "foundations"]
            },
            "disease": {
                "academic": ["pathology", "disorder", "clinical condition", "affliction"],
                "casual": ["illness", "sickness", "condition"],
                "journalistic": ["disease", "illness", "condition"],
                "standard": ["condition", "disorder", "illness"]
            },
            "diseases": {
                "academic": ["pathologies", "disorders", "clinical conditions", "afflictions"],
                "casual": ["illnesses", "conditions"],
                "journalistic": ["diseases", "illnesses", "conditions"],
                "standard": ["conditions", "disorders", "illnesses"]
            },
            "treatment": {
                "academic": ["therapeutic regimen", "clinical intervention", "therapy"],
                "casual": ["cure", "care", "therapy"],
                "journalistic": ["treatment", "therapy", "intervention"],
                "standard": ["therapy", "clinical intervention", "treatment"]
            },
            "treatments": {
                "academic": ["therapeutic regimens", "clinical interventions", "therapies"],
                "casual": ["cures", "treatments", "therapies"],
                "journalistic": ["treatments", "therapies", "interventions"],
                "standard": ["therapies", "clinical interventions", "treatments"]
            },
            "adoption": {
                "academic": ["integration", "implementation", "rollout", "uptake"],
                "casual": ["pickup", "use", "take-up"],
                "journalistic": ["rollout", "uptake", "adoption"],
                "standard": ["implementation", "integration", "uptake"]
            },
            "clinicians": {
                "academic": ["medical practitioners", "healthcare professionals", "physicians"],
                "casual": ["doctors", "caregivers"],
                "journalistic": ["doctors", "physicians", "specialists"],
                "standard": ["physicians", "medical practitioners", "clinicians"]
            },
            "first": {
                "academic": ["initial", "primary", "foundational", "foremost"],
                "casual": ["first", "initial", "starting"],
                "journalistic": ["first", "initial", "opening"],
                "standard": ["initial", "primary", "first"]
            },
            "second": {
                "academic": ["subsequent", "secondary", "further", "additional"],
                "casual": ["second", "next", "another"],
                "journalistic": ["second", "subsequent", "following"],
                "standard": ["subsequent", "secondary", "second"]
            },
            "key": {
                "academic": ["fundamental", "critical", "essential", "primary", "central"],
                "casual": ["big", "main", "vital"],
                "journalistic": ["major", "central", "critical"],
                "standard": ["essential", "fundamental", "critical"]
            },
            "breakthrough": {
                "academic": ["milestone", "innovation", "advancement", "discovery"],
                "casual": ["leap", "breakthrough", "discovery"],
                "journalistic": ["milestone", "leap", "breakthrough"],
                "standard": ["milestone", "innovation", "breakthrough"]
            },
            "breakthroughs": {
                "academic": ["milestones", "innovations", "advancements", "discoveries"],
                "casual": ["leaps", "breakthroughs", "discoveries"],
                "journalistic": ["milestones", "breakthroughs", "discoveries"],
                "standard": ["milestones", "innovations", "discoveries"]
            },
            "advancement": {
                "academic": ["progression", "evolution", "breakthrough", "progress"],
                "casual": ["step forward", "progress", "growth"],
                "journalistic": ["advance", "progress", "growth"],
                "standard": ["progression", "advance", "evolution"]
            },
            "advancements": {
                "academic": ["progressions", "evolutions", "breakthroughs", "strides"],
                "casual": ["steps forward", "advancements", "developments"],
                "journalistic": ["advances", "developments", "strides"],
                "standard": ["advancements", "evolutions", "developments"]
            },
            "automated": {
                "academic": ["algorithmic", "autonomous", "computational", "machine-driven"],
                "casual": ["automatic", "robotic", "automated"],
                "journalistic": ["automated", "automated-driven", "autonomous"],
                "standard": ["autonomous", "automated", "computerized"]
            },
            "system": {
                "academic": ["framework", "architecture", "mechanism", "platform"],
                "casual": ["setup", "tool", "system"],
                "journalistic": ["network", "platform", "system"],
                "standard": ["framework", "platform", "architecture"]
            },
            "systems": {
                "academic": ["frameworks", "architectures", "mechanisms", "platforms"],
                "casual": ["setups", "tools", "systems"],
                "journalistic": ["networks", "platforms", "systems"],
                "standard": ["frameworks", "platforms", "architectures"]
            },
            "processing": {
                "academic": ["computation", "analysis", "handling", "interpretation"],
                "casual": ["handling", "crunching", "work"],
                "journalistic": ["processing", "analysis", "handling"],
                "standard": ["computation", "processing", "analysis"]
            },
            "concern": {
                "academic": ["reservation", "apprehension", "consideration"],
                "casual": ["worry", "doubt"],
                "journalistic": ["concern", "worry"],
                "standard": ["reservation", "consideration", "concern"]
            },
            "concerns": {
                "academic": ["reservations", "apprehensions", "critical considerations"],
                "casual": ["worries", "fears", "doubts"],
                "journalistic": ["worries", "concerns", "fears"],
                "standard": ["reservations", "considerations", "worries"]
            },
            "obstacle": {
                "academic": ["impediment", "hurdle", "barrier", "bottleneck"],
                "casual": ["roadblock", "snag", "hurdle"],
                "journalistic": ["hurdle", "barrier", "roadblock"],
                "standard": ["impediment", "hurdle", "barrier"]
            },
            "obstacles": {
                "academic": ["impediments", "hurdles", "barriers", "bottlenecks"],
                "casual": ["roadblocks", "snags", "hurdles"],
                "journalistic": ["hurdles", "barriers", "roadblocks"],
                "standard": ["impediments", "hurdles", "barriers"]
            },
            "widespread": {
                "academic": ["pervasive", "broad-scale", "ubiquitous", "system-wide"],
                "casual": ["everywhere", "all-over", "broad"],
                "journalistic": ["broad", "wide-scale", "sweeping"],
                "standard": ["broad-scale", "extensive", "system-wide"]
            },

            # --- ADJECTIVES: Academic & Analytical ---
            "important": {
                "academic": ["essential", "significant", "salient", "substantive", "consequential"],
                "casual": ["big deal", "crucial", "essential", "key"],
                "journalistic": ["critical", "defining", "vital", "major"],
                "standard": ["essential", "critical", "noteworthy", "key"]
            },
            "significant": {
                "academic": ["substantial", "momentous", "considerable", "pronounced"],
                "casual": ["huge", "major", "meaningful", "serious"],
                "journalistic": ["dramatic", "notable", "striking", "major"],
                "standard": ["substantial", "notable", "meaningful", "marked"]
            },
            "pressing": {
                "academic": ["acute", "urgent", "imperative", "exigent"],
                "casual": ["urgent", "huge", "serious"],
                "journalistic": ["urgent", "critical", "burning"],
                "standard": ["urgent", "critical", "acute"]
            },
            "excessive": {
                "academic": ["inordinate", "disproportionate", "immoderate", "surplus"],
                "casual": ["too much", "over-the-top", "heavy"],
                "journalistic": ["heavy", "surplus", "inordinate"],
                "standard": ["inordinate", "disproportionate", "heavy"]
            },
            "heightened": {
                "academic": ["intensified", "elevated", "amplified", "magnified"],
                "casual": ["increased", "higher", "stepped up"],
                "journalistic": ["elevated", "sharpened", "heightened"],
                "standard": ["elevated", "intensified", "amplified"]
            },
            "concerted": {
                "academic": ["coordinated", "collaborative", "unified", "harmonized"],
                "casual": ["joined-up", "team", "together"],
                "journalistic": ["joint", "coordinated", "united"],
                "standard": ["coordinated", "collaborative", "joint"]
            },
            "contemporary": {
                "academic": ["present-day", "current", "modern-era"],
                "casual": ["today's", "current", "modern"],
                "journalistic": ["today's", "present-day", "current"],
                "standard": ["present-day", "current", "modern"]
            },
            "extreme": {
                "academic": ["severe", "acute", "drastic", "harsh"],
                "casual": ["wild", "harsh", "intense"],
                "journalistic": ["severe", "intense", "harsh"],
                "standard": ["severe", "acute", "intense"]
            },
            "rapid": {
                "academic": ["swift", "accelerated", "brisk"],
                "casual": ["fast", "quick", "speedy"],
                "journalistic": ["brisk", "swift", "rapid"],
                "standard": ["swift", "accelerated", "brisk"]
            },
            "crucial": {
                "academic": ["vital", "pivotal", "indispensable", "foundational"],
                "casual": ["key", "huge", "must-have"],
                "journalistic": ["vital", "critical", "pivotal"],
                "standard": ["vital", "essential", "critical"]
            },
            "essential": {
                "academic": ["indispensable", "fundamental", "vital", "requisite"],
                "casual": ["must-have", "key", "vital"],
                "journalistic": ["vital", "critical", "key"],
                "standard": ["indispensable", "vital", "fundamental"]
            },
            "effective": {
                "academic": ["efficacious", "potent", "productive", "operative"],
                "casual": ["solid", "working well", "super effective", "reliable"],
                "journalistic": ["proven", "impactful", "compelling", "productive"],
                "standard": ["impactful", "successful", "productive", "reliable"]
            },
            "complex": {
                "academic": ["intricate", "layered", "convoluted", "sophisticated"],
                "casual": ["tricky", "complicated", "tangled", "messy"],
                "journalistic": ["intricate", "tangled", "layered", "knotty"],
                "standard": ["intricate", "layered", "detailed", "sophisticated"]
            },
            "various": {
                "academic": ["diverse", "heterogeneous", "multifarious", "assorted"],
                "casual": ["all kinds of", "a bunch of", "different", "plenty of"],
                "journalistic": ["wide-ranging", "array of", "assorted", "varied"],
                "standard": ["different", "diverse", "distinct", "varied"]
            },
            "difficult": {
                "academic": ["arduous", "onerous", "formidable", "laborious"],
                "casual": ["tough", "hard", "rough", "demanding"],
                "journalistic": ["daunting", "thorny", "stiff", "formidable"],
                "standard": ["challenging", "demanding", "arduous", "taxing"]
            },
            "fast": {
                "academic": ["rapid", "swift", "accelerated"],
                "casual": ["quick", "speedy", "snappy"],
                "journalistic": ["rapid", "swift", "brisk"],
                "standard": ["rapid", "swift", "brisk"]
            },
            "new": {
                "academic": ["novel", "contemporary", "unprecedented", "nascent"],
                "casual": ["fresh", "brand-new", "latest"],
                "journalistic": ["emerging", "fresh", "groundbreaking", "novel"],
                "standard": ["fresh", "novel", "emerging", "modern"]
            },
            "vast": {
                "academic": ["comprehensive", "sweeping", "extensive", "voluminous"],
                "casual": ["huge", "massive", "giant"],
                "journalistic": ["massive", "enormous", "wide-ranging"],
                "standard": ["extensive", "broad", "comprehensive", "sweeping"]
            },
            "sustainable": {
                "academic": ["viable", "enduring", "ecologically sound", "long-term viable"],
                "casual": ["green", "lasting", "eco-friendly"],
                "journalistic": ["green", "lasting", "viable"],
                "standard": ["viable", "enduring", "ecologically sound"]
            },
            "vulnerable": {
                "academic": ["susceptible", "exposed", "defenseless", "fragile"],
                "casual": ["at risk", "fragile", "exposed"],
                "journalistic": ["exposed", "at risk", "fragile"],
                "standard": ["susceptible", "exposed", "at risk"]
            },

            # --- ADVERBS ---
            "clearly": {
                "academic": ["manifestly", "evidently", "patently", "unambiguously"],
                "casual": ["obviously", "plain and simple", "for sure"],
                "journalistic": ["distinctly", "visibly", "unmistakably"],
                "standard": ["evidently", "plainly", "noticeably", "distinctly"]
            },
            "quickly": {
                "academic": ["expeditiously", "swiftly", "promptly"],
                "casual": ["in no time", "fast", "on the fly"],
                "journalistic": ["swiftly", "rapidly", "in short order"],
                "standard": ["swiftly", "rapidly", "promptly"]
            },
            "greatly": {
                "academic": ["profoundly", "substantially", "measurably"],
                "casual": ["a ton", "massively", "hugely"],
                "journalistic": ["sharply", "dramatically", "markedly"],
                "standard": ["considerably", "substantially", "markedly"]
            },
            "disproportionately": {
                "academic": ["asymmetrically", "unevenly", "inequitably"],
                "casual": ["unfairly", "way more"],
                "journalistic": ["unevenly", "heavily", "sharply"],
                "standard": ["unevenly", "asymmetrically", "heavily"]
            },
            "increasingly": {
                "academic": ["progressively", "steadily", "more and more"],
                "casual": ["more and more", "steadily"],
                "journalistic": ["steadily", "progressively"],
                "standard": ["steadily", "progressively", "more and more"]
            },
            "substantially": {
                "academic": ["considerably", "markedly", "measurably", "meaningfully"],
                "casual": ["a lot", "massively", "greatly"],
                "journalistic": ["markedly", "sharply", "significantly"],
                "standard": ["considerably", "markedly", "meaningfully"]
            },
            "widely": {
                "academic": ["broadly", "extensively", "universally", "pervasively"],
                "casual": ["everywhere", "all over", "widely"],
                "journalistic": ["broadly", "extensively"],
                "standard": ["broadly", "extensively", "universally"]
            },
            "deeply": {
                "academic": ["profoundly", "acutely", "intensely"],
                "casual": ["really", "super", "heavily"],
                "journalistic": ["profoundly", "acutely"],
                "standard": ["profoundly", "acutely", "intensely"]
            },

            # --- AI Buzzword Neutralizers & Expanded Academic Terms ---
            "multifaceted": {
                "academic": ["layered", "complex", "diverse", "broad-ranging"],
                "casual": ["varied", "many-sided", "diverse"],
                "journalistic": ["varied", "wide-ranging", "complex"],
                "standard": ["varied", "layered", "diverse", "wide-ranging"]
            },
            "nuanced": {
                "academic": ["subtle", "fine-grained", "measured", "refined"],
                "casual": ["detailed", "subtle"],
                "journalistic": ["detailed", "subtle", "measured"],
                "standard": ["subtle", "detailed", "refined"]
            },
            "intertwined": {
                "academic": ["interconnected", "inseparable", "linked", "interwoven"],
                "casual": ["tied together", "linked", "connected"],
                "journalistic": ["linked", "entangled", "connected"],
                "standard": ["connected", "linked", "interconnected"]
            },
            "holistic": {
                "academic": ["comprehensive", "integrated", "broad-based", "thorough"],
                "casual": ["all-around", "complete", "whole"],
                "journalistic": ["broad", "comprehensive", "integrated"],
                "standard": ["comprehensive", "integrated", "well-rounded"]
            },
            "plethora": {
                "academic": ["wealth", "abundance", "broad spectrum", "vast collection"],
                "casual": ["abundance", "wide array", "bunch"],
                "journalistic": ["host", "wealth", "range"],
                "standard": ["wealth", "abundance", "broad array"]
            },
            "myriad": {
                "academic": ["countless", "innumerable", "numerous", "multitudinous"],
                "casual": ["countless", "numerous", "broad array"],
                "journalistic": ["numerous", "countless", "broad range of"],
                "standard": ["numerous", "countless", "varied"]
            },
            "juxtaposition": {
                "academic": ["contrast", "interplay", "coexistence", "side-by-side comparison"],
                "casual": ["contrast", "comparison", "mix"],
                "journalistic": ["contrast", "comparison", "counterpoint"],
                "standard": ["contrast", "comparison", "interplay"]
            },
            "overarching": {
                "academic": ["central", "predominant", "foundational", "underlying"],
                "casual": ["main", "key", "overall"],
                "journalistic": ["central", "main", "underlying"],
                "standard": ["central", "primary", "underlying"]
            },
            "testament": {
                "academic": ["tangible proof", "clear evidence", "demonstration", "manifestation"],
                "casual": ["proof", "sign", "reflection"],
                "journalistic": ["proof", "evidence", "sign"],
                "standard": ["proof", "evidence", "demonstration"]
            },
            "beacon": {
                "academic": ["symbol", "touchstone", "guiding standard", "anchor"],
                "casual": ["guiding light", "anchor", "symbol"],
                "journalistic": ["symbol", "anchor", "standard"],
                "standard": ["symbol", "anchor", "guide"]
            },
            "tapestry": {
                "academic": ["mosaic", "spectrum", "intricate array", "synthesis"],
                "casual": ["mix", "collection", "blend"],
                "journalistic": ["mosaic", "blend", "weave"],
                "standard": ["mosaic", "spectrum", "array"]
            },
            "delve": {
                "academic": ["probe", "examine", "investigate", "explore"],
                "casual": ["look into", "explore", "examine"],
                "journalistic": ["investigate", "explore", "probe"],
                "standard": ["examine", "explore", "investigate"]
            },
            "delves": {
                "academic": ["probes", "examines", "investigates", "explores"],
                "casual": ["looks into", "explores", "examines"],
                "journalistic": ["investigates", "explores", "probes"],
                "standard": ["examines", "explores", "investigates"]
            },
            "delving": {
                "academic": ["probing", "examining", "investigating", "exploring"],
                "casual": ["looking into", "exploring", "examining"],
                "journalistic": ["investigating", "exploring", "probing"],
                "standard": ["examining", "exploring", "investigating"]
            },
            "recognize": {
                "academic": ["acknowledge", "discern", "observe", "appreciate", "identify"],
                "casual": ["notice", "see", "spot"],
                "journalistic": ["acknowledge", "identify", "note"],
                "standard": ["acknowledge", "observe", "identify", "appreciate"]
            },
            "recognizes": {
                "academic": ["acknowledges", "discerns", "observes", "appreciates", "identifies"],
                "casual": ["notices", "sees", "spots"],
                "journalistic": ["acknowledges", "identifies", "notes"],
                "standard": ["acknowledges", "observes", "identifies"]
            },
            "society": {
                "academic": ["the public sphere", "social institutions", "contemporary culture", "communities"],
                "casual": ["our world", "society", "communities"],
                "journalistic": ["the public", "communities", "society"],
                "standard": ["contemporary culture", "communities", "the public sphere"]
            },
            "modern": {
                "academic": ["contemporary", "present-day", "current", "recent"],
                "casual": ["current", "recent", "new"],
                "journalistic": ["contemporary", "current", "present-day"],
                "standard": ["contemporary", "present-day", "current"]
            },
            "recent": {
                "academic": ["contemporary", "present-day", "current", "latest"],
                "casual": ["recent", "fresh", "latest"],
                "journalistic": ["current", "latest", "recent"],
                "standard": ["current", "recent", "contemporary"]
            },
            "year": {
                "academic": ["year", "twelve-month period", "annual period"],
                "casual": ["year", "stretch of time", "twelve months"],
                "journalistic": ["year", "annual period"],
                "standard": ["year", "period"]
            },
            "years": {
                "academic": ["years", "times", "periods", "decades"],
                "casual": ["years", "times", "stretches"],
                "journalistic": ["years", "period", "decades"],
                "standard": ["years", "times", "periods"]
            },
            "human": {
                "academic": ["humanity", "scholars", "individuals", "people", "practitioners"],
                "casual": ["people", "folks", "humans", "individuals"],
                "journalistic": ["people", "individuals", "the public"],
                "standard": ["individuals", "people", "humanity"]
            },
            "humans": {
                "academic": ["people", "scholars", "individuals", "professionals", "practitioners"],
                "casual": ["people", "folks", "everyone"],
                "journalistic": ["people", "individuals", "citizens"],
                "standard": ["individuals", "people", "humanity"]
            },
            "ingenuity": {
                "academic": ["innovation", "creativity", "intellect", "resourcefulness", "expertise"],
                "casual": ["cleverness", "creativity", "skill", "know-how"],
                "journalistic": ["innovation", "talent", "invention", "creativity"],
                "standard": ["creativity", "innovation", "resourcefulness"]
            },
            "complexities": {
                "academic": ["intricacies", "dynamics", "challenges", "nuances", "mechanisms"],
                "casual": ["difficulties", "twists", "tricky parts"],
                "journalistic": ["challenges", "intricacies", "dynamics"],
                "standard": ["intricacies", "nuances", "challenges"]
            },
            "complexity": {
                "academic": ["intricacy", "depth", "sophistication", "structural nuance"],
                "casual": ["difficulty", "depth", "detail"],
                "journalistic": ["intricacy", "sophistication", "challenge"],
                "standard": ["intricacy", "depth", "sophistication"]
            },
            "imperative": {
                "academic": ["essential", "critical", "vital", "fundamental", "indispensable"],
                "casual": ["must-have", "key", "urgent"],
                "journalistic": ["vital", "urgent", "critical"],
                "standard": ["essential", "vital", "critical"]
            },
            "valuable": {
                "academic": ["substantive", "meaningful", "significant", "actionable", "useful"],
                "casual": ["useful", "helpful", "handy", "great"],
                "journalistic": ["crucial", "vital", "significant"],
                "standard": ["useful", "substantive", "meaningful"]
            },
            "insights": {
                "academic": ["findings", "observations", "perspectives", "conclusions", "understandings"],
                "casual": ["takeaways", "clues", "points", "ideas"],
                "journalistic": ["findings", "revelations", "conclusions"],
                "standard": ["findings", "perspectives", "observations"]
            },
            "insight": {
                "academic": ["finding", "perspective", "understanding", "observation"],
                "casual": ["takeaway", "idea", "point"],
                "journalistic": ["revelation", "finding", "perspective"],
                "standard": ["perspective", "understanding", "finding"]
            },
            "massive": {
                "academic": ["extensive", "substantial", "large-scale", "vast", "broad"],
                "casual": ["huge", "giant", "big", "vast"],
                "journalistic": ["major", "substantial", "large-scale"],
                "standard": ["extensive", "substantial", "vast"]
            },
            "workflow": {
                "academic": ["operational process", "pipeline", "procedure", "working method"],
                "casual": ["routine", "way of working", "process"],
                "journalistic": ["process", "pipeline", "operations"],
                "standard": ["process", "pipeline", "operational routine"]
            },
            "workflows": {
                "academic": ["operational processes", "pipelines", "working procedures"],
                "casual": ["routines", "processes", "ways of working"],
                "journalistic": ["processes", "pipelines", "operations"],
                "standard": ["processes", "operational pipelines", "working procedures"]
            },
            "automation": {
                "academic": ["automated execution", "algorithmic efficiency", "autonomous processing"],
                "casual": ["automated tools", "tech", "automation"],
                "journalistic": ["automated systems", "algorithmic tools"],
                "standard": ["automated execution", "autonomous workflows"]
            },
            "enterprise": {
                "academic": ["organizational", "corporate", "institutional"],
                "casual": ["business", "company", "firm"],
                "journalistic": ["corporate", "commercial", "enterprise"],
                "standard": ["corporate", "organizational", "institutional"]
            },
            "enterprises": {
                "academic": ["organizations", "institutions", "companies", "firms"],
                "casual": ["businesses", "companies", "firms"],
                "journalistic": ["corporations", "companies", "institutions"],
                "standard": ["organizations", "enterprises", "institutions"]
            },
            "analysis": {
                "academic": ["investigation", "examination", "inquiry", "assessment", "evaluation"],
                "casual": ["breakdown", "review", "check", "study"],
                "journalistic": ["examination", "review", "investigation"],
                "standard": ["examination", "inquiry", "investigation", "evaluation"]
            },
            "analyses": {
                "academic": ["investigations", "examinations", "inquiries", "assessments"],
                "casual": ["breakdowns", "reviews", "studies"],
                "journalistic": ["examinations", "evaluations", "reviews"],
                "standard": ["examinations", "inquiries", "investigations"]
            },
            "research": {
                "academic": ["inquiry", "investigation", "study", "scholarly examination"],
                "casual": ["study", "work", "investigation"],
                "journalistic": ["investigation", "study", "findings"],
                "standard": ["inquiry", "study", "investigation"]
            },
            "study": {
                "academic": ["investigation", "inquiry", "scholarly examination", "project"],
                "casual": ["project", "work", "look"],
                "journalistic": ["investigation", "inquiry", "report"],
                "standard": ["investigation", "inquiry", "study"]
            },
            "studies": {
                "academic": ["investigations", "inquiries", "scholarly examinations", "projects"],
                "casual": ["projects", "works", "reports"],
                "journalistic": ["investigations", "inquiries", "reports"],
                "standard": ["investigations", "studies", "projects"]
            },
            "method": {
                "academic": ["approach", "methodology", "technique", "framework"],
                "casual": ["way", "trick", "system"],
                "journalistic": ["approach", "technique", "tactic"],
                "standard": ["approach", "technique", "framework"]
            },
            "methods": {
                "academic": ["approaches", "methodologies", "techniques", "frameworks"],
                "casual": ["ways", "tricks", "systems"],
                "journalistic": ["approaches", "tactics", "techniques"],
                "standard": ["approaches", "techniques", "frameworks"]
            },
            "challenge": {
                "academic": ["difficulty", "hurdle", "obstacle", "impediment"],
                "casual": ["problem", "roadblock", "issue"],
                "journalistic": ["hurdle", "obstacle", "dilemma"],
                "standard": ["hurdle", "obstacle", "challenge"]
            },
            "challenges": {
                "academic": ["difficulties", "hurdles", "obstacles", "impediments"],
                "casual": ["problems", "roadblocks", "issues"],
                "journalistic": ["hurdles", "obstacles", "dilemmas"],
                "standard": ["hurdles", "obstacles", "difficulties"]
            },
            "solution": {
                "academic": ["remedy", "answer", "resolution", "countermeasure"],
                "casual": ["fix", "way out", "answer"],
                "journalistic": ["remedy", "fix", "resolution"],
                "standard": ["resolution", "remedy", "answer"]
            },
            "solutions": {
                "academic": ["remedies", "answers", "resolutions", "countermeasures"],
                "casual": ["fixes", "answers", "ways out"],
                "journalistic": ["remedies", "fixes", "resolutions"],
                "standard": ["resolutions", "remedies", "answers"]
            },
            "develop": {
                "academic": ["build", "construct", "engineer", "formulate", "cultivate"],
                "casual": ["make", "build", "come up with"],
                "journalistic": ["forge", "produce", "roll out"],
                "standard": ["build", "construct", "engineer", "formulate"]
            },
            "develops": {
                "academic": ["builds", "constructs", "engineers", "formulates", "cultivates"],
                "casual": ["makes", "builds", "comes up with"],
                "journalistic": ["forges", "produces", "rolls out"],
                "standard": ["builds", "constructs", "engineers"]
            },
            "developing": {
                "academic": ["building", "constructing", "engineering", "formulating"],
                "casual": ["making", "building", "creating"],
                "journalistic": ["forging", "producing", "rolling out"],
                "standard": ["building", "constructing", "engineering"]
            },
            "developed": {
                "academic": ["built", "constructed", "engineered", "formulated"],
                "casual": ["made", "built", "created"],
                "journalistic": ["forged", "produced", "launched"],
                "standard": ["built", "constructed", "formulated"]
            },
            "model": {
                "academic": ["architecture", "framework", "system", "structure"],
                "casual": ["setup", "tool", "system"],
                "journalistic": ["architecture", "tool", "framework"],
                "standard": ["framework", "architecture", "structure"]
            },
            "models": {
                "academic": ["architectures", "frameworks", "systems", "structures"],
                "casual": ["setups", "tools", "systems"],
                "journalistic": ["architectures", "frameworks", "tools"],
                "standard": ["frameworks", "architectures", "systems"]
            },
            "data": {
                "academic": ["information", "empirical evidence", "observations", "records"],
                "casual": ["info", "facts", "numbers"],
                "journalistic": ["records", "information", "figures"],
                "standard": ["information", "records", "empirical evidence"]
            },
            "process": {
                "academic": ["procedure", "operation", "workflow", "mechanism"],
                "casual": ["routine", "way", "steps"],
                "journalistic": ["pipeline", "procedure", "operation"],
                "standard": ["procedure", "workflow", "operation"]
            },
            "processes": {
                "academic": ["procedures", "operations", "workflows", "mechanisms"],
                "casual": ["routines", "steps", "ways"],
                "journalistic": ["pipelines", "procedures", "operations"],
                "standard": ["procedures", "workflows", "operations"]
            },
            "effective": {
                "academic": ["efficacious", "productive", "impactful", "successful"],
                "casual": ["working", "great", "solid"],
                "journalistic": ["impactful", "successful", "proven"],
                "standard": ["productive", "impactful", "successful"]
            },
            "efficiency": {
                "academic": ["operational speed", "productivity", "effectiveness", "streamlined performance"],
                "casual": ["speed", "productivity", "pace"],
                "journalistic": ["output", "speed", "productivity"],
                "standard": ["productivity", "streamlined performance", "operational speed"]
            },
            "significant": {
                "academic": ["notable", "substantial", "meaningful", "consequential", "marked"],
                "casual": ["big", "major", "huge"],
                "journalistic": ["notable", "substantial", "major"],
                "standard": ["notable", "substantial", "meaningful"]
            },
            "significantly": {
                "academic": ["substantially", "notably", "markedly", "considerably"],
                "casual": ["a lot", "way more", "greatly"],
                "journalistic": ["considerably", "substantially", "markedly"],
                "standard": ["substantially", "notably", "considerably"]
            },
            "strategy": {
                "academic": ["plan", "methodology", "approach", "tactic"],
                "casual": ["game plan", "tactic", "idea"],
                "journalistic": ["tactic", "roadmap", "plan"],
                "standard": ["plan", "approach", "methodology"]
            },
            "strategies": {
                "academic": ["plans", "methodologies", "approaches", "tactics"],
                "casual": ["game plans", "tactics", "approaches"],
                "journalistic": ["tactics", "roadmaps", "plans"],
                "standard": ["plans", "approaches", "methodologies"]
            },
            "impact": {
                "academic": ["effect", "consequence", "influence", "repercussion"],
                "casual": ["mark", "splash", "hit"],
                "journalistic": ["fallout", "influence", "effect"],
                "standard": ["effect", "influence", "consequence"]
            },
            "impacts": {
                "academic": ["effects", "influences", "repercussions", "consequences"],
                "casual": ["marks", "hits", "effects"],
                "journalistic": ["fallout", "influences", "effects"],
                "standard": ["effects", "influences", "consequences"]
            },
            "feature": {
                "academic": ["characteristic", "attribute", "element", "component"],
                "casual": ["trait", "aspect", "part"],
                "journalistic": ["attribute", "element", "hallmark"],
                "standard": ["characteristic", "attribute", "element"]
            },
            "features": {
                "academic": ["characteristics", "attributes", "elements", "components"],
                "casual": ["traits", "aspects", "parts"],
                "journalistic": ["attributes", "elements", "hallmarks"],
                "standard": ["characteristics", "attributes", "elements"]
            },
            "factor": {
                "academic": ["element", "driver", "consideration", "aspect"],
                "casual": ["piece", "thing", "driver"],
                "journalistic": ["driver", "element", "catalyst"],
                "standard": ["element", "driver", "consideration"]
            },
            "factors": {
                "academic": ["elements", "drivers", "considerations", "aspects"],
                "casual": ["pieces", "things", "drivers"],
                "journalistic": ["drivers", "elements", "catalysts"],
                "standard": ["elements", "drivers", "considerations"]
            },
            "volume": {
                "academic": ["scale", "quantity", "magnitude", "scope"],
                "casual": ["amount", "size", "pile"],
                "journalistic": ["scale", "quantity", "extent"],
                "standard": ["quantity", "scale", "magnitude"]
            },
            "volumes": {
                "academic": ["quantities", "amounts", "scales", "aggregations"],
                "casual": ["amounts", "heaps", "masses"],
                "journalistic": ["quantities", "volumes", "stores"],
                "standard": ["quantities", "amounts", "scales"]
            },
            "organization": {
                "academic": ["institution", "enterprise", "entity", "agency"],
                "casual": ["company", "firm", "outfit"],
                "journalistic": ["corporation", "institution", "agency"],
                "standard": ["institution", "enterprise", "organization"]
            },
            "organizations": {
                "academic": ["institutions", "enterprises", "entities", "agencies"],
                "casual": ["companies", "firms", "groups"],
                "journalistic": ["corporations", "institutions", "agencies"],
                "standard": ["institutions", "enterprises", "organizations"]
            },
            "adopt": {
                "academic": ["implement", "embrace", "integrate", "deploy"],
                "casual": ["take on", "try out", "bring in"],
                "journalistic": ["implement", "adopt", "roll out"],
                "standard": ["implement", "embrace", "integrate"]
            },
            "adopts": {
                "academic": ["implements", "embraces", "integrates", "deploys"],
                "casual": ["takes on", "tries out", "brings in"],
                "journalistic": ["implements", "adopts", "rolls out"],
                "standard": ["implements", "embraces", "integrates"]
            },
            "adopting": {
                "academic": ["implementing", "embracing", "integrating", "deploying"],
                "casual": ["taking on", "trying out", "bringing in"],
                "journalistic": ["implementing", "adopting", "rolling out"],
                "standard": ["implementing", "embracing", "integrating"]
            },
            "adopted": {
                "academic": ["implemented", "embraced", "integrated", "deployed"],
                "casual": ["taken on", "tried out", "brought in"],
                "journalistic": ["implemented", "adopted", "rolled out"],
                "standard": ["implemented", "embraced", "integrated"]
            },
            "navigate": {
                "academic": ["manage", "address", "negotiate", "traverse"],
                "casual": ["steer through", "handle", "deal with"],
                "journalistic": ["tackle", "handle", "confront"],
                "standard": ["manage", "address", "negotiate"]
            },
            "navigates": {
                "academic": ["manages", "addresses", "negotiates", "traverses"],
                "casual": ["steers through", "handles", "deals with"],
                "journalistic": ["tackles", "handles", "confronts"],
                "standard": ["manages", "addresses", "negotiates"]
            },
            "navigating": {
                "academic": ["managing", "addressing", "negotiating", "traversing"],
                "casual": ["steering through", "handling", "dealing with"],
                "journalistic": ["tackling", "handling", "confronting"],
                "standard": ["managing", "addressing", "negotiating"]
            },
            "stand": {
                "academic": ["serve", "act", "function", "remain"],
                "casual": ["act", "serve", "stand"],
                "journalistic": ["serve", "act", "remain"],
                "standard": ["serve", "act", "function"]
            },
            "stands": {
                "academic": ["serves", "acts", "functions", "remains"],
                "casual": ["acts", "serves", "stands"],
                "journalistic": ["serves", "acts", "remains"],
                "standard": ["serves", "acts", "functions"]
            },
            "clear": {
                "academic": ["evident", "distinct", "lucid", "transparent", "apparent"],
                "casual": ["plain", "easy to see", "obvious"],
                "journalistic": ["unmistakable", "clear", "distinct"],
                "standard": ["evident", "distinct", "lucid"]
            },
            "clearly": {
                "academic": ["evidently", "distinctly", "lucidly", "transparently"],
                "casual": ["plainly", "obviously", "for sure"],
                "journalistic": ["plainly", "distinctly", "visibly"],
                "standard": ["evidently", "distinctly", "lucidly"]
            },
            "corporate": {
                "academic": ["organizational", "institutional", "enterprise", "commercial"],
                "casual": ["business", "company", "firm"],
                "journalistic": ["corporate", "commercial", "industry"],
                "standard": ["organizational", "enterprise", "institutional"]
            },
            "widely": {
                "academic": ["broadly", "extensively", "commonly", "routinely"],
                "casual": ["a lot", "all over", "widely"],
                "journalistic": ["broadly", "across the board", "extensively"],
                "standard": ["broadly", "extensively", "commonly"]
            },
            "potential": {
                "academic": ["capabilities", "promise", "capacity", "aptitude"],
                "casual": ["promise", "power", "reach"],
                "journalistic": ["promise", "capabilities", "potential"],
                "standard": ["capacity", "capabilities", "promise"]
            },
            "advanced": {
                "academic": ["sophisticated", "cutting-edge", "high-level", "state-of-the-art"],
                "casual": ["high-tech", "leading-edge", "top-tier"],
                "journalistic": ["cutting-edge", "state-of-the-art", "sophisticated"],
                "standard": ["sophisticated", "cutting-edge", "high-level"]
            },
            "era": {
                "academic": ["epoch", "period", "phase", "age"],
                "casual": ["age", "time", "generation"],
                "journalistic": ["period", "era", "age"],
                "standard": ["period", "age", "epoch"]
            },
            "computing": {
                "academic": ["computation", "computational systems", "information processing"],
                "casual": ["tech", "computers", "digital tools"],
                "journalistic": ["digital tech", "computing", "technology"],
                "standard": ["computation", "computer systems", "data processing"]
            },
            "pattern": {
                "academic": ["structural trend", "regularity", "systematic trend"],
                "casual": ["trend", "habit", "format"],
                "journalistic": ["trend", "pattern", "regularity"],
                "standard": ["structural trend", "regularity", "trend"]
            },
            "patterns": {
                "academic": ["structural trends", "regularities", "systematic patterns"],
                "casual": ["trends", "habits", "formats"],
                "journalistic": ["trends", "patterns", "regularities"],
                "standard": ["structural trends", "regularities", "trends"]
            },
            "recognition": {
                "academic": ["identification", "detection", "discernment", "analysis"],
                "casual": ["spotting", "identifying", "catching"],
                "journalistic": ["detection", "identification", "spotting"],
                "standard": ["identification", "detection", "discernment"]
            },
            "enterprise": {
                "academic": ["organizational", "corporate", "institutional", "industry"],
                "casual": ["company", "business", "corporate"],
                "journalistic": ["corporate", "business", "enterprise"],
                "standard": ["organizational", "corporate", "institutional"]
            },
            "corporate": {
                "academic": ["enterprise", "organizational", "institutional", "business"],
                "casual": ["company", "business", "workplace"],
                "journalistic": ["company", "business", "corporate"],
                "standard": ["enterprise", "organizational", "institutional"]
            },
            "data": {
                "academic": ["information", "datasets", "empirical records", "observations"],
                "casual": ["info", "records", "details"],
                "journalistic": ["information", "records", "figures"],
                "standard": ["information", "datasets", "records"]
            },
            "complexities": {
                "academic": ["intricacies", "nuances", "multifaceted challenges", "complex dynamics"],
                "casual": ["tricky parts", "difficulties", "headaches"],
                "journalistic": ["hurdles", "challenges", "intricacies"],
                "standard": ["intricacies", "nuances", "challenges"]
            },
            "complexity": {
                "academic": ["intricacy", "nuance", "structural sophistication"],
                "casual": ["difficulty", "tricky part"],
                "journalistic": ["complexity", "hurdle"],
                "standard": ["intricacy", "nuance", "sophistication"]
            },
            "reflection": {
                "academic": ["manifestation", "testament", "demonstration", "indication"],
                "casual": ["mirror", "sign", "proof"],
                "journalistic": ["sign", "indication", "reflection"],
                "standard": ["manifestation", "indication", "demonstration"]
            },
            "immense": {
                "academic": ["substantial", "profound", "considerable", "tremendous"],
                "casual": ["huge", "massive", "giant"],
                "journalistic": ["vast", "massive", "substantial"],
                "standard": ["substantial", "vast", "considerable"]
            },
            "scalable": {
                "academic": ["elastic", "expandable", "adaptable", "extensible"],
                "casual": ["flexible", "growing", "expandable"],
                "journalistic": ["elastic", "expandable", "scalable"],
                "standard": ["elastic", "expandable", "adaptable"]
            },
            "infrastructure": {
                "academic": ["architectures", "foundations", "frameworks", "systems"],
                "casual": ["setup", "systems", "backbone"],
                "journalistic": ["frameworks", "networks", "systems"],
                "standard": ["architectures", "frameworks", "foundations"]
            },
            "predictive": {
                "academic": ["forecasting", "prognostic", "anticipatory"],
                "casual": ["future-looking", "predictive"],
                "journalistic": ["forecasting", "predictive"],
                "standard": ["forecasting", "prognostic", "anticipatory"]
            },
            "rigorous": {
                "academic": ["stringent", "exhaustive", "meticulous", "comprehensive"],
                "casual": ["tough", "strict", "thorough"],
                "journalistic": ["strict", "thorough", "exhaustive"],
                "standard": ["stringent", "meticulous", "thorough"]
            },
            "validation": {
                "academic": ["verification", "confirmation", "substantiation", "benchmarking"],
                "casual": ["checking", "testing", "proofing"],
                "journalistic": ["testing", "verification", "confirmation"],
                "standard": ["verification", "confirmation", "substantiation"]
            },
            "benchmarks": {
                "academic": ["standards", "evaluations", "metrics", "criteria"],
                "casual": ["tests", "scores", "marks"],
                "journalistic": ["standards", "tests", "metrics"],
                "standard": ["standards", "evaluations", "metrics"]
            },
            "datasets": {
                "academic": ["corpora", "data collections", "data repositories", "empirical datasets"],
                "casual": ["data sets", "records", "files"],
                "journalistic": ["data sets", "records", "databases"],
                "standard": ["corpora", "data collections", "data repositories"]
            },
            "facilitate": {
                "academic": ["enable", "foster", "support", "streamline"],
                "casual": ["help", "make easy", "back"],
                "journalistic": ["help", "ease", "enable"],
                "standard": ["enable", "support", "streamline"]
            },
            "facilitates": {
                "academic": ["enables", "fosters", "supports", "streamlines"],
                "casual": ["helps", "makes easy"],
                "journalistic": ["helps", "eases", "enables"],
                "standard": ["enables", "supports", "streamlines"]
            },
            "facilitated": {
                "academic": ["enabled", "fostered", "supported", "streamlined"],
                "casual": ["helped", "backed"],
                "journalistic": ["helped", "enabled"],
                "standard": ["enabled", "supported", "streamlined"]
            },
            "facilitating": {
                "academic": ["enabling", "fostering", "supporting", "streamlining"],
                "casual": ["helping", "backing"],
                "journalistic": ["helping", "enabling"],
                "standard": ["enabling", "supporting", "streamlining"]
            },
            "accuracy": {
                "academic": ["precision", "exactness", "predictive performance", "fidelity"],
                "casual": ["correctness", "precision", "exactness"],
                "journalistic": ["precision", "accuracy", "exactness"],
                "standard": ["precision", "exactness", "fidelity"]
            },
            "precision": {
                "academic": ["accuracy", "exactness", "fidelity", "rigor"],
                "casual": ["exactness", "sharpness"],
                "journalistic": ["precision", "exactness"],
                "standard": ["exactness", "accuracy", "fidelity"]
            },
            "metrics": {
                "academic": ["performance indicators", "evaluation criteria", "benchmarks", "quantitative measures"],
                "casual": ["scores", "numbers", "stats"],
                "journalistic": ["indicators", "measures", "metrics"],
                "standard": ["performance indicators", "measures", "benchmarks"]
            },
            "metric": {
                "academic": ["performance indicator", "evaluation criterion", "benchmark", "quantitative measure"],
                "casual": ["score", "number", "stat"],
                "journalistic": ["indicator", "measure", "metric"],
                "standard": ["performance indicator", "measure", "benchmark"]
            },
            "baseline": {
                "academic": ["benchmark reference", "standard comparator", "reference standard"],
                "casual": ["starting point", "benchmark"],
                "journalistic": ["benchmark", "standard", "baseline"],
                "standard": ["benchmark reference", "reference standard"]
            },
            "dataset": {
                "academic": ["corpus", "data repository", "data collection", "empirical dataset"],
                "casual": ["data set", "file", "records"],
                "journalistic": ["data set", "records", "database"],
                "standard": ["corpus", "data collection", "data repository"]
            },
            "hypothesis": {
                "academic": ["proposition", "postulate", "theoretical premise", "conjecture"],
                "casual": ["theory", "guess", "idea"],
                "journalistic": ["theory", "premise", "hypothesis"],
                "standard": ["proposition", "postulate", "theoretical premise"]
            },
            "hypotheses": {
                "academic": ["propositions", "postulates", "theoretical premises", "conjectures"],
                "casual": ["theories", "guesses", "ideas"],
                "journalistic": ["theories", "premises", "hypotheses"],
                "standard": ["propositions", "postulates", "theoretical premises"]
            },
            "correlation": {
                "academic": ["statistical association", "interrelationship", "systematic association"],
                "casual": ["link", "connection", "tie"],
                "journalistic": ["link", "relationship", "connection"],
                "standard": ["statistical association", "relationship", "connection"]
            },
            "methodology": {
                "academic": ["methodological framework", "analytical approach", "research design"],
                "casual": ["method", "way of doing it", "approach"],
                "journalistic": ["approach", "method", "framework"],
                "standard": ["methodological framework", "analytical approach"]
            },
            "empirical": {
                "academic": ["observational", "data-driven", "evidence-based", "experimental"],
                "casual": ["hands-on", "real-world", "tested"],
                "journalistic": ["real-world", "data-backed", "observed"],
                "standard": ["evidence-based", "data-driven", "observational"]
            },
            "statistical": {
                "academic": ["quantitative", "computational", "probabilistic"],
                "casual": ["number-based", "math"],
                "journalistic": ["data-driven", "quantitative"],
                "standard": ["quantitative", "probabilistic", "data-driven"]
            },
            "findings": {
                "academic": ["empirical results", "outcomes", "observations", "conclusions"],
                "casual": ["results", "findings", "takeaways"],
                "journalistic": ["results", "findings", "discoveries"],
                "standard": ["empirical results", "outcomes", "observations"]
            },
            "finding": {
                "academic": ["empirical result", "outcome", "observation", "conclusion"],
                "casual": ["result", "finding", "takeaway"],
                "journalistic": ["result", "finding", "discovery"],
                "standard": ["empirical result", "outcome", "observation"]
            },
            "significant": {
                "academic": ["substantial", "notable", "statistically meaningful", "consequential"],
                "casual": ["big", "major", "important"],
                "journalistic": ["major", "notable", "substantial"],
                "standard": ["substantial", "notable", "meaningful"]
            },
            "significantly": {
                "academic": ["substantially", "measurably", "notably", "consequentially"],
                "casual": ["a lot", "way more", "greatly"],
                "journalistic": ["substantially", "measurably", "notably"],
                "standard": ["substantially", "measurably", "notably"]
            },
            "demonstrate": {
                "academic": ["illustrate", "evince", "substantiate", "exhibit"],
                "casual": ["show", "prove", "point out"],
                "journalistic": ["show", "reveal", "highlight"],
                "standard": ["illustrate", "show", "substantiate"]
            },
            "demonstrates": {
                "academic": ["illustrates", "evinces", "substantiates", "exhibits"],
                "casual": ["shows", "proves", "points out"],
                "journalistic": ["shows", "reveals", "highlights"],
                "standard": ["illustrates", "shows", "substantiates"]
            },
            "demonstrated": {
                "academic": ["illustrated", "evinced", "substantiated", "exhibited"],
                "casual": ["showed", "proved"],
                "journalistic": ["showed", "revealed", "highlighted"],
                "standard": ["illustrated", "showed", "substantiated"]
            },
            "demonstrating": {
                "academic": ["illustrating", "evincing", "substantiating", "exhibiting"],
                "casual": ["showing", "proving"],
                "journalistic": ["showing", "revealing", "highlighting"],
                "standard": ["illustrating", "showing", "substantiating"]
            },
            "robust": {
                "academic": ["resilient", "computationally stable", "rigorous", "enduring"],
                "casual": ["strong", "solid", "tough"],
                "journalistic": ["strong", "resilient", "reliable"],
                "standard": ["resilient", "rigorous", "stable"]
            },
            "robustness": {
                "academic": ["resilience", "stability", "methodological rigor", "endurance"],
                "casual": ["strength", "toughness"],
                "journalistic": ["reliability", "resilience"],
                "standard": ["resilience", "stability", "rigor"]
            },
            "fidelity": {
                "academic": ["accuracy", "exactitude", "precision", "truthfulness"],
                "casual": ["accuracy", "quality"],
                "journalistic": ["fidelity", "accuracy"],
                "standard": ["accuracy", "precision", "exactitude"]
            },
            "discrepancy": {
                "academic": ["divergence", "variance", "inconsistency", "disparity"],
                "casual": ["difference", "mismatch"],
                "journalistic": ["gap", "difference", "inconsistency"],
                "standard": ["divergence", "variance", "disparity"]
            },
            "discrepancies": {
                "academic": ["divergences", "variances", "inconsistencies", "disparities"],
                "casual": ["differences", "mismatches"],
                "journalistic": ["gaps", "differences", "inconsistencies"],
                "standard": ["divergences", "variances", "disparities"]
            },
            "strategic": {
                "academic": ["foundational", "high-level", "tactical", "policy-level", "long-term"],
                "casual": ["key", "smart", "planned"],
                "journalistic": ["strategic", "high-level", "crucial"],
                "standard": ["foundational", "tactical", "high-level"]
            },
            "priorities": {
                "academic": ["imperatives", "core objectives", "focal areas", "strategic focal points"],
                "casual": ["top goals", "main targets", "focal points"],
                "journalistic": ["key priorities", "imperatives", "core targets"],
                "standard": ["imperatives", "core objectives", "focal areas"]
            },
            "priority": {
                "academic": ["imperative", "core objective", "focal area", "primary focus"],
                "casual": ["main focus", "top goal"],
                "journalistic": ["key priority", "imperative", "core focus"],
                "standard": ["imperative", "core objective", "primary focus"]
            },
            "workflows": {
                "academic": ["operational processes", "execution pipelines", "workstreams", "procedures"],
                "casual": ["working processes", "routines"],
                "journalistic": ["operations", "processes", "pipelines"],
                "standard": ["operational processes", "execution pipelines", "procedures"]
            },
            "workflow": {
                "academic": ["operational process", "execution pipeline", "workstream", "procedure"],
                "casual": ["working routine", "process"],
                "journalistic": ["operation", "process", "pipeline"],
                "standard": ["operational process", "execution pipeline", "procedure"]
            },
            "automated": {
                "academic": ["algorithm-driven", "programmatic", "systematic", "computational"],
                "casual": ["hands-free", "automatic"],
                "journalistic": ["automated", "software-driven", "computerized"],
                "standard": ["programmatic", "systematic", "algorithmic"]
            },
            "automation": {
                "academic": ["programmatic execution", "systematic execution", "algorithmic automation"],
                "casual": ["automated systems", "automation"],
                "journalistic": ["automation", "mechanization"],
                "standard": ["programmatic execution", "systematic execution"]
            },
            "framework": {
                "academic": ["architectural structure", "operational framework", "conceptual schema"],
                "casual": ["setup", "system", "foundation"],
                "journalistic": ["framework", "structure", "system"],
                "standard": ["operational framework", "conceptual structure", "system"]
            },
            "frameworks": {
                "academic": ["architectural structures", "operational frameworks", "conceptual systems"],
                "casual": ["setups", "systems"],
                "journalistic": ["frameworks", "structures"],
                "standard": ["operational frameworks", "conceptual systems"]
            },
            "paradigm": {
                "academic": ["methodological model", "conceptual framework", "structural archetype"],
                "casual": ["approach", "way of thinking"],
                "journalistic": ["model", "approach", "framework"],
                "standard": ["conceptual framework", "methodological model"]
            },
            "paradigms": {
                "academic": ["methodological models", "conceptual frameworks", "structural archetypes"],
                "casual": ["approaches", "models"],
                "journalistic": ["models", "approaches"],
                "standard": ["conceptual frameworks", "methodological models"]
            },
            "mitigate": {
                "academic": ["attenuate", "alleviate", "lessen", "curtail", "temper"],
                "casual": ["cut down", "ease", "reduce"],
                "journalistic": ["curb", "reduce", "alleviate"],
                "standard": ["attenuate", "lessen", "alleviate"]
            },
            "mitigates": {
                "academic": ["attenuates", "alleviates", "lessens", "curtails", "tempers"],
                "casual": ["cuts down", "eases", "reduces"],
                "journalistic": ["curbs", "reduces", "alleviates"],
                "standard": ["attenuates", "lessens", "alleviates"]
            },
            "mitigated": {
                "academic": ["attenuated", "alleviated", "lessened", "curtailed", "tempered"],
                "casual": ["cut down", "eased", "reduced"],
                "journalistic": ["curbed", "reduced", "alleviated"],
                "standard": ["attenuated", "lessened", "alleviated"]
            },
            "mitigating": {
                "academic": ["attenuating", "alleviating", "lessening", "curtailing"],
                "casual": ["cutting down", "easing", "reducing"],
                "journalistic": ["curbing", "reducing", "alleviating"],
                "standard": ["attenuating", "lessening", "alleviating"]
            },
            "mitigation": {
                "academic": ["attenuation", "alleviation", "risk abatement", "reduction"],
                "casual": ["relief", "reduction"],
                "journalistic": ["abatement", "reduction", "relief"],
                "standard": ["attenuation", "alleviation", "reduction"]
            },
            "stakeholders": {
                "academic": ["interested parties", "key participants", "institutional actors", "constituents"],
                "casual": ["people involved", "players"],
                "journalistic": ["stakeholders", "parties involved"],
                "standard": ["interested parties", "key participants", "constituents"]
            },
            "stakeholder": {
                "academic": ["interested party", "key participant", "institutional actor", "constituent"],
                "casual": ["person involved", "player"],
                "journalistic": ["stakeholder", "party involved"],
                "standard": ["interested party", "key participant", "constituent"]
            },
            "scalability": {
                "academic": ["elastic expansion", "system throughput capacity", "extensibility"],
                "casual": ["room to grow", "expandability"],
                "journalistic": ["scalability", "growth capacity"],
                "standard": ["elastic expansion", "throughput capacity"]
            },
            "throughput": {
                "academic": ["processing capacity", "execution volume", "data handling rate"],
                "casual": ["output", "speed"],
                "journalistic": ["volume", "capacity", "flow rate"],
                "standard": ["processing capacity", "data handling rate"]
            },
            "latency": {
                "academic": ["response delay", "temporal latency", "turnaround delay"],
                "casual": ["lag", "delay"],
                "journalistic": ["response lag", "delay"],
                "standard": ["response delay", "temporal latency"]
            },
            "compliance": {
                "academic": ["regulatory adherence", "conformance", "statutory alignment"],
                "casual": ["following rules", "compliance"],
                "journalistic": ["compliance", "adherence to rules"],
                "standard": ["regulatory adherence", "conformance"]
            },
            "governance": {
                "academic": ["institutional oversight", "regulatory governance", "operational oversight"],
                "casual": ["management", "control"],
                "journalistic": ["oversight", "supervision", "governance"],
                "standard": ["institutional oversight", "regulatory governance"]
            },
            "deployment": {
                "academic": ["operational rollout", "implementation", "systemic release"],
                "casual": ["launch", "rollout"],
                "journalistic": ["rollout", "release", "launch"],
                "standard": ["operational rollout", "implementation"]
            },
            "deployments": {
                "academic": ["operational rollouts", "implementations", "systemic releases"],
                "casual": ["launches", "rollouts"],
                "journalistic": ["rollouts", "releases"],
                "standard": ["operational rollouts", "implementations"]
            },
            "pipeline": {
                "academic": ["execution pathway", "processing chain", "workflow sequence"],
                "casual": ["pipeline", "process"],
                "journalistic": ["pipeline", "sequence"],
                "standard": ["execution pathway", "processing chain"]
            },
            "pipelines": {
                "academic": ["execution pathways", "processing chains", "workflow sequences"],
                "casual": ["pipelines", "processes"],
                "journalistic": ["pipelines", "sequences"],
                "standard": ["execution pathways", "processing chains"]
            },
            "adherence": {
                "academic": ["conformance", "fidelity", "alignment", "rigorous compliance"],
                "casual": ["following", "keeping to"],
                "journalistic": ["compliance", "adherence", "conformance"],
                "standard": ["conformance", "alignment", "fidelity"]
            },
            "benchmark": {
                "academic": ["reference standard", "comparative baseline", "evaluative standard"],
                "casual": ["standard", "bar", "test"],
                "journalistic": ["benchmark", "yardstick", "standard"],
                "standard": ["reference standard", "baseline standard", "evaluative standard"]
            },
            "benchmarks": {
                "academic": ["reference standards", "comparative baselines", "evaluative criteria"],
                "casual": ["standards", "yardsticks"],
                "journalistic": ["benchmarks", "yardsticks", "standards"],
                "standard": ["reference standards", "baseline standards"]
            },
            "against": {
                "academic": ["relative to", "in comparison with", "measured against"],
                "casual": ["compared to", "versus"],
                "journalistic": ["against", "compared to"],
                "standard": ["relative to", "in comparison with"]
            },
            "scores": {
                "academic": ["metrics", "evaluations", "indices", "performance ratings"],
                "casual": ["results", "points"],
                "journalistic": ["scores", "ratings", "metrics"],
                "standard": ["metrics", "evaluations", "measures"]
            },
            "score": {
                "academic": ["metric", "evaluation", "index", "performance rating"],
                "casual": ["result", "point"],
                "journalistic": ["score", "rating", "metric"],
                "standard": ["metric", "evaluation", "measure"]
            },
            "split": {
                "academic": ["partition", "division", "segmentation"],
                "casual": ["cut", "split"],
                "journalistic": ["division", "split"],
                "standard": ["partition", "division"]
            },
            "splits": {
                "academic": ["partitions", "divisions", "segmentations"],
                "casual": ["cuts", "splits"],
                "journalistic": ["divisions", "splits"],
                "standard": ["partitions", "divisions"]
            }
        }

        # Merge expansive academic & analytical lexicon
        self.thesaurus.update(EXPANDED_ACADEMIC_THESAURUS)

        # Protected patterns (don't replace numbers, quotes, acronyms, specific entities)
        self.protected_regex = re.compile(r"^[A-Z]{2,}$|^\d+.*$")

    @classmethod
    @functools.lru_cache(maxsize=8192)
    def _cached_wordnet_candidates(cls, w_low: str) -> Tuple[str, ...]:
        if not wordnet:
            return ()
        try:
            # Infer POS constraints from morphological suffix to eliminate grammatical breakage
            pos_filter = None
            req_suffix = None
            if w_low.endswith("ly") and len(w_low) > 4:
                pos_filter = "r"
                req_suffix = "ly"
            elif w_low.endswith("ing") and len(w_low) > 5:
                pos_filter = ("v", "a", "s")
                req_suffix = "ing"
            elif w_low.endswith("ed") and len(w_low) > 4:
                pos_filter = ("v", "a", "s")
                req_suffix = "ed"

            synsets = wordnet.synsets(w_low, pos=pos_filter) if pos_filter and isinstance(pos_filter, str) else wordnet.synsets(w_low)
            if not synsets:
                return ()

            candidates: List[str] = []
            seen = {w_low}
            ai_buzz_set = set(AI_BUZZWORDS)

            for syn in synsets[:2]:
                if pos_filter and isinstance(pos_filter, tuple) and syn.pos() not in pos_filter:
                    continue
                for lemma in syn.lemmas():
                    raw_lemma = lemma.name()
                    # Skip proper nouns
                    if raw_lemma[0].isupper():
                        continue
                    name = raw_lemma.lower().replace("_", " ")
                    if req_suffix and not name.endswith(req_suffix):
                        continue
                    if (
                        name not in seen
                        and len(name.split()) <= 1  # Strictly 1-to-1 clean single-word swap
                        and len(name) >= 3
                        and name not in ai_buzz_set
                        and name not in BANNED_OBSCURE_LEMMAS
                        and name not in PROTECTED_TECHNICAL_WORDS
                        and not any(char.isdigit() for char in name)
                    ):
                        seen.add(name)
                        candidates.append(name)
                        if len(candidates) >= 4:
                            break
                if len(candidates) >= 4:
                    break

            return tuple(candidates)
        except Exception:
            return ()

    def get_wordnet_candidates(self, word: str, tone: str = "standard") -> List[str]:
        """
        Dynamically extracts contextually appropriate synonyms from NLTK WordNet
        for words not found in the static thesaurus.
        Filters out multi-word idioms with underscores, identical words,
        known AI buzzwords, and obscure lemmas.
        """
        w_low = word.lower().strip()
        if len(w_low) <= 3 or w_low in COMMON_FUNCTION_WORDS:
            return []

        return list(self._cached_wordnet_candidates(w_low))

    def mask_protected_collocations(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Finds occurrences of protected multi-word collocations, citations, mathematical
        expressions, and statistical brackets in text, replaces them with unique placeholder tokens,
        and returns the masked text along with a mapping dict to restore them later.
        """
        mapping: Dict[str, str] = {}
        masked = text
        counter = 0

        # Step 0: Shield Academic Citations, Equations, and Statistical Brackets
        citation_patterns = [
            # Bracket numerical citations e.g. [1], [1, 2], [3-5]
            re.compile(r"\[\d+(?:[–,-]\s*\d+)*\]"),
            # Author et al. mentions e.g. Smith et al. (2023) or Smith et al.
            re.compile(r"\b[A-Z][a-zA-Z\s\.,&]+(?:\s+et\s+al\.)?\s*(?:\(\d{4}[a-z]?\))"),
            # Parenthetical author citations e.g. (Smith et al., 2023), (Johnson & Lee, 2021)
            re.compile(r"\([A-Z][a-zA-Z\s\.,&]+(?:\s+et\s+al\.)?,\s*\d{4}[a-z]?\)"),
            # Statistical expressions e.g. (p < 0.05), (p = 0.001), (t = 2.45, p < 0.01)
            re.compile(r"\([pP]\s*[<=><]\s*\d+(?:\.\d+)?\)"),
            re.compile(r"\([tFrR]\s*=\s*[\d\.-]+,\s*[pP]\s*[<=><]\s*[\d\.-]+\)"),
            # Exact percentage expressions e.g. 15%, 98.5%
            re.compile(r"\b\d+(?:\.\d+)?%"),
            # Inline LaTeX math e.g. $E=mc^2$
            re.compile(r"\$[^\$]+\$"),
        ]

        for c_pat in citation_patterns:
            def repl_cit(m: re.Match) -> str:
                nonlocal counter
                placeholder = f"__CITREF_{counter}__"
                mapping[placeholder] = m.group(0)
                counter += 1
                return placeholder
            masked = c_pat.sub(repl_cit, masked)

        # Step 1: Shield Multi-Word Domain Collocations
        # Sort by length descending so longer collocations match first
        sorted_collocations = sorted(PROTECTED_COLLOCATIONS, key=len, reverse=True)

        for colloc in sorted_collocations:
            pattern = re.compile(rf"\b{re.escape(colloc)}\b", flags=re.IGNORECASE)
            def repl(m: re.Match) -> str:
                nonlocal counter
                placeholder = f"__COLLOC_{counter}__"
                mapping[placeholder] = m.group(0)
                counter += 1
                return placeholder
            masked = pattern.sub(repl, masked)

        return masked, mapping

    def unmask_protected_collocations(self, text: str, mapping: Dict[str, str]) -> str:
        """Restores protected multi-word collocations from placeholder tokens."""
        result = text
        for placeholder, original in mapping.items():
            result = result.replace(placeholder, original)
        return result

    def replace_synonyms(
        self,
        text: str,
        tone: str = "standard",
        intensity: float = 0.35,
        preserve_keywords: Optional[Set[str]] = None
    ) -> str:
        """
        Substitutes candidate words with context-appropriate synonyms based on tone and intensity.
        Respects casing (Capitalized, lowercase) and strictly shields protected collocations.
        """
        if not text:
            return ""

        # Step 1: Shield protected collocations from single-token replacement
        masked_text, colloc_map = self.mask_protected_collocations(text)

        preserve = {k.lower() for k in (preserve_keywords or set())}
        preserve_words = set()
        for kw in preserve:
            preserve_words.update(kw.split())

        ai_buzz_set = set(AI_BUZZWORDS)
        words = masked_text.split(" ")
        new_words: List[str] = []

        for token in words:
            # Check if this token contains a protected collocation, citation, or LaTeX placeholder
            if "__COLLOC_" in token or "__CITREF_" in token or "XLTXMASK" in token:
                new_words.append(token)
                continue

            # Strip punctuation for lookup
            match = re.match(r"^([^\w]*)([\w'-]+)([^\w]*)$", token)
            if not match:
                new_words.append(token)
                continue

            prefix, core, suffix = match.groups()
            core_lower = core.lower()

            if (
                core_lower in preserve
                or core_lower in preserve_words
                or core_lower in PROTECTED_TECHNICAL_WORDS
                or any(core_lower in kw for kw in preserve)
                or ("-" in core_lower and core_lower not in self.thesaurus)
                or (core_lower in COMMON_FUNCTION_WORDS and core_lower not in self.thesaurus)
                or self.protected_regex.match(core)
                or random.random() > intensity
            ):
                new_words.append(token)
                continue

            candidates = []
            if core_lower in self.thesaurus:
                tone_dict = self.thesaurus[core_lower]
                raw_cands = tone_dict.get(tone) or tone_dict.get("standard") or []
                candidates = [
                    c for c in raw_cands
                    if c.lower() not in ai_buzz_set and c.lower() not in BANNED_OBSCURE_LEMMAS
                ]

            if not candidates:
                new_words.append(token)
                continue

            chosen = random.choice(candidates)

            # Preserve title/upper case
            if core.isupper() and len(core) > 1:
                replacement = chosen.upper()
            elif core.istitle():
                replacement = chosen.capitalize()
            else:
                replacement = chosen

            new_words.append(f"{prefix}{replacement}{suffix}")

        processed_text = " ".join(new_words)

        # Step 2: Unmask protected collocations
        return self.unmask_protected_collocations(processed_text, colloc_map)
