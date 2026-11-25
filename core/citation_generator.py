"""
Decoupled Citation Engine & Reference Generator.
Hierarchical academic taxonomy across Computer Science, Engineering/Physics,
Mathematics/Statistics, Quantitative Finance, and Medical/Life Sciences.
Generates compliant BibTeX (.bib), LaTeX (\\cite{key}), and structured JSON
reference packages and injects contextual citations into academic manuscripts.
"""

import json
import random
import re
from typing import Any, Dict, List, Optional, Tuple


class CitationEngine:
    """
    Decoupled citation engine supporting contextual auto-detection,
    multi-discipline academic taxonomies, and multi-format exports.
    """

    TAXONOMY = {
        "computer_science": [
            {
                "id": "vaswani2017attention",
                "title": "Attention is All You Need",
                "authors": "A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser, and I. Polosukhin",
                "journal": "Advances in Neural Information Processing Systems",
                "year": 2017,
                "volume": "30",
                "keywords": ["transformer", "attention", "neural network", "deep learning", "nlp", "llm", "language model"]
            },
            {
                "id": "he2016deep",
                "title": "Deep Residual Learning for Image Recognition",
                "authors": "K. He, X. Zhang, S. Ren, and J. Sun",
                "journal": "IEEE Conference on Computer Vision and Pattern Recognition (CVPR)",
                "year": 2016,
                "volume": "1",
                "keywords": ["residual", "resnet", "vision", "convolutional", "accuracy", "classification", "layers"]
            },
            {
                "id": "goodfellow2014generative",
                "title": "Generative Adversarial Nets",
                "authors": "I. Goodfellow, J. Pouget-Abadie, M. Mirza, B. Xu, D. Warde-Farley, S. Ozair, A. Courville, and Y. Bengio",
                "journal": "Advances in Neural Information Processing Systems",
                "year": 2014,
                "volume": "27",
                "keywords": ["adversarial", "gan", "generator", "discriminator", "generative"]
            },
            {
                "id": "sommer2010outside",
                "title": "Outside the Closed World: On Using Machine Learning for Network Intrusion Detection",
                "authors": "R. Sommer and V. Paxson",
                "journal": "IEEE Symposium on Security and Privacy",
                "year": 2010,
                "volume": "31",
                "keywords": ["intrusion detection", "security", "telemetry", "drift", "anomaly", "gateway", "network"]
            }
        ],
        "engineering_physics": [
            {
                "id": "pope2000turbulent",
                "title": "Turbulent Flows",
                "authors": "S. B. Pope",
                "journal": "Cambridge University Press",
                "year": 2000,
                "volume": "1",
                "keywords": ["fluid", "navier-stokes", "turbulence", "reynolds", "velocity", "flow", "simulation"]
            },
            {
                "id": "oppenheim1999discrete",
                "title": "Discrete-Time Signal Processing",
                "authors": "A. V. Oppenheim and R. W. Schafer",
                "journal": "Prentice Hall",
                "year": 1999,
                "volume": "2",
                "keywords": ["signal", "fourier", "filter", "frequency", "sampling", "spectral"]
            }
        ],
        "mathematics_statistics": [
            {
                "id": "strang2006linear",
                "title": "Linear Algebra and Its Applications",
                "authors": "G. Strang",
                "journal": "Thomson Brooks/Cole",
                "year": 2006,
                "volume": "4",
                "keywords": ["eigenvalue", "matrix", "vector", "linear system", "orthogonal", "transformation"]
            },
            {
                "id": "hairer1993solving",
                "title": "Solving Ordinary Differential Equations I: Nonstiff Problems",
                "authors": "E. Hairer, S. P. Norsett, and G. Wanner",
                "journal": "Springer Series in Computational Mathematics",
                "year": 1993,
                "volume": "8",
                "keywords": ["differential equation", "finite difference", "runge-kutta", "convergence", "stability", "step size"]
            }
        ],
        "quantitative_finance": [
            {
                "id": "black1973pricing",
                "title": "The Pricing of Options and Corporate Liabilities",
                "authors": "F. Black and M. Scholes",
                "journal": "Journal of Political Economy",
                "year": 1973,
                "volume": "81",
                "keywords": ["option pricing", "black-scholes", "volatility", "stochastic", "derivative", "risk"]
            },
            {
                "id": "hull2017options",
                "title": "Options, Futures, and Other Derivatives",
                "authors": "J. C. Hull",
                "journal": "Pearson Education",
                "year": 2017,
                "volume": "10",
                "keywords": ["hedging", "futures", "portfolio", "arbitrage", "yield curve", "interest rate"]
            }
        ],
        "medical_life_sciences": [
            {
                "id": "altschul1990basic",
                "title": "Basic Local Alignment Search Tool (BLAST)",
                "authors": "S. F. Altschul, W. Gish, W. Miller, E. W. Myers, and D. J. Lipman",
                "journal": "Journal of Molecular Biology",
                "year": 1990,
                "volume": "215",
                "keywords": ["sequence", "alignment", "dna", "genome", "protein", "bioinformatics", "blast"]
            }
        ]
    }

    def __init__(self):
        pass

    def detect_discipline(self, text: str) -> str:
        """
        Determines the dominant academic discipline of the text based on keyword density.
        """
        lower = text.lower()
        discipline_scores: Dict[str, int] = {disc: 0 for disc in self.TAXONOMY}

        for disc, papers in self.TAXONOMY.items():
            for paper in papers:
                for kw in paper["keywords"]:
                    if kw in lower:
                        discipline_scores[disc] += 1

        best_disc = max(discipline_scores, key=discipline_scores.get)
        return best_disc if discipline_scores[best_disc] > 0 else "computer_science"

    def generate_references(
        self,
        discipline: Optional[str] = None,
        count: int = 3,
        text_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generates citations in BibTeX, LaTeX, and JSON format for the specified discipline.
        """
        target_disc = discipline or self.detect_discipline(text_context)
        papers = list(self.TAXONOMY.get(target_disc, self.TAXONOMY["computer_science"]))

        # Sort by relevance if text_context given
        if text_context:
            lower = text_context.lower()
            papers.sort(key=lambda p: sum(1 for kw in p["keywords"] if kw in lower), reverse=True)

        selected_papers = papers[:count] if len(papers) >= count else papers

        # 1. BibTeX format
        bibtex_entries = []
        for p in selected_papers:
            bib = f"""@article{{{p['id']},
  title = {{{p['title']}}},
  author = {{{p['authors']}}},
  journal = {{{p['journal']}}},
  year = {{{p['year']}}},
  volume = {{{p['volume']}}}
}}"""
            bibtex_entries.append(bib)

        # 2. LaTeX format
        latex_keys = [f"\\cite{{{p['id']}}}" for p in selected_papers]

        # 3. Standard IEEE plain text format
        plain_ieee = []
        for i, p in enumerate(selected_papers, 1):
            plain_ieee.append(f"[{i}] {p['authors']}, \"{p['title']},\" {p['journal']}, vol. {p['volume']}, {p['year']}.")

        return {
            "discipline": target_disc,
            "count": len(selected_papers),
            "bibtex": "\n\n".join(bibtex_entries),
            "latex_cite_keys": latex_keys,
            "plain_references": "\n".join(plain_ieee),
            "json_metadata": selected_papers
        }

    def inject_citations_into_text(
        self,
        text: str,
        count: int = 2,
        citation_format: str = "numeric"
    ) -> Tuple[str, List[str]]:
        """
        Injects citations directly into the text at sentence boundaries.
        format: 'numeric' for [1], [2], 'apa' for (Author, Year), or 'latex' for \\cite{key}.
        """
        refs_bundle = self.generate_references(text_context=text, count=count)
        selected = refs_bundle["json_metadata"]
        if not selected:
            return text, []

        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        if len(sentences) < len(selected):
            sentences = re.split(r"(?<=[.;!?])\s+", text.strip())

        injected_keys = []
        fmt_low = (citation_format or "numeric").lower()

        if len(sentences) >= 1 and len(selected) >= 1:
            for idx, p in enumerate(selected):
                target_sentence_idx = (idx * len(sentences)) // len(selected) if len(sentences) >= len(selected) else min(len(sentences) - 1, idx)
                raw = sentences[target_sentence_idx].rstrip()
                punc = raw[-1] if raw and raw[-1] in ".;!?" else "."
                s = raw[:-1] if raw and raw[-1] in ".;!?" else raw
                if "latex" in fmt_low or "cite" in fmt_low:
                    marker = f" \\cite{{{p['id']}}}"
                elif "apa" in fmt_low:
                    first_author = p["authors"].split(",")[0].split()[-1]
                    marker = f" ({first_author} et al., {p['year']})"
                else:
                    marker = f" [{idx + 1}]"
                sentences[target_sentence_idx] = f"{s}{marker}{punc}"
                injected_keys.append(p['id'])

        return " ".join(sentences), injected_keys

    def inject_citations(
        self,
        text: str,
        fmt: str = "IEEE",
        count: int = 2,
        discipline: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Injects citations cleanly and returns cited text + self-executing AI Auto-Fill BibTeX bundle.
        """
        cited_text, keys = self.inject_citations_into_text(text, count=count, citation_format=fmt)
        refs = self.generate_references(discipline=discipline, count=count, text_context=text)
        ai_header = (
            "% ==============================================================================\n"
            "% AI AUTO-FILL INSTRUCTIONS (CHATGPT / CLAUDE / GEMINI / DEEPSEEK)\n"
            "% ------------------------------------------------------------------------------\n"
            "% To verify or enrich these contextual placeholders with specific DOIs,\n"
            "% paste this file directly into any AI assistant while preserving citation keys.\n"
            "% ==============================================================================\n\n"
        )
        return {
            "cited_text": cited_text,
            "bib_text": ai_header + refs["bibtex"],
            "citation_count": len(keys),
            "citation_keys": keys,
            "discipline": refs["discipline"],
            "plain_references": refs["plain_references"],
        }
