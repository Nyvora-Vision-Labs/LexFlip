"""Fill the Llama judge cache on the cluster itself, next to the vLLM server.

Run from a copy of the repository on the node (no laptop, no tunnel, so a VPN
drop cannot interrupt it). It issues exactly the requests that exp10 and exp8
would issue for Llama, through llm_judge.score_matrix, so the cache files it
writes are the ones those scripts read. Copy results/llm_cache back afterwards.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import probes as P
import llm_judge as J
import specificity as SP
import gen_paraphrases as G
from data import load_pairs

M = "meta-llama/Llama-3.3-70B-Instruct"
NE = SP.neutral_edits(P.SOURCES)
jobs = [
    ("exp4", P.ALL),
    ("frjudge", load_pairs()),
    ("swap", [dict(original=e["simplification"], simplification=e["original"]) for e in P.edit]),
    ("spec_neutral", [dict(original=P.SOURCES[i], simplification=e) for i, e, _ in NE]),
    ("spec_paraphrase", [dict(original=P.SOURCES[i], simplification=p) for i, p in G.load()]),
]
for tag, pairs in jobs:
    J.score_matrix(pairs, tag=tag, model=M)
print("all Llama jobs done", flush=True)
