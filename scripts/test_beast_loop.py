import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.beast_engine import BeastEngine

b = BeastEngine()
text = (
    "Furthermore, it is crucial to recognize that artificial intelligence plays a "
    "multifaceted and pivotal role in modern society. Moreover, it is important to remember "
    "that machine learning algorithms serve as a testament to human innovation."
)

failures = 0
for i in range(50):
    res = b.execute_beast_mode(text)
    m = res["metrics"]
    if m["plagiarism_risk_score"] > 0.0 or m["verbatim_overlap"] > 0:
        print(f"Run {i} failed: plag_risk={m['plagiarism_risk_score']}, overlap={m['verbatim_overlap']}")
        print("  Humanized:", res["humanized_text"])
        print("  Matching:", res["plagiarism_check"]["matching_sequences"])
        failures += 1

print(f"Done 50 runs, failures: {failures}")
