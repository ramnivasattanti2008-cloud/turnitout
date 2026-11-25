import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re, random
from core.detector import TextAnalyzer

orig = "Moreover, it is important to remember that machine learning algorithms serve as a testament to human innovation."
test_sentences = [
    "What is more, notice how machine learning algorithms steadily serve as tangible proof of human innovation.",
    "What is more, notice that advanced machine learning algorithms steadily serve as tangible proof of human innovation."
]

analyzer = TextAnalyzer()
for test_s in test_sentences:
    p = analyzer.check_plagiarism_similarity(orig, test_s)
    print("Test:", test_s)
    print("  plagiarism_risk_score:", p["plagiarism_risk_score"])
    print("  uniqueness_score:", p["uniqueness_score"])
    print("  matches:", p["matching_sequences"])
