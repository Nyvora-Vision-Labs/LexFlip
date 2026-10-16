"""The LEXFLIP probe sets, rebuilt exactly as exp4_challenge.py builds them.

exp4 constructs its probes at module level; the revision analyses need the same
373 items (same pool, same seeds, same order) without re-running exp4, so the
construction is repeated here verbatim and checked against exp4's saved rule
list on import.
"""
import os, json
import numpy as np
from augment import lexflip_edits, unrelated_pairs, tier, _sents

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

ref = _sents("A-25.jsonl") + _sents("code_securite_routiere.jsonl")
_rng = np.random.default_rng(7)
POOL = [ref[i] for i in _rng.choice(len(ref), size=400, replace=False)]
ED = lexflip_edits(POOL, seed=7, per_sentence=1)
n = len(ED)
RULES = [r for _, _, r in ED]
T1 = np.array([tier(r) == 1 for r in RULES])
SOURCES = [o for o, _, _ in ED]

ident = [dict(original=o, simplification=o) for o, _, _ in ED]
edit = [dict(original=o, simplification=p) for o, p, _ in ED]
UNREL_RAW = unrelated_pairs(n, seed=77)
unrel = [dict(original=a, simplification=b) for a, b in UNREL_RAW]
ALL = ident + edit + unrel

_saved = os.path.join(ROOT, "results", "exp4_challenge.json")
if os.path.exists(_saved):
    assert json.load(open(_saved))["rules"] == RULES, "probe rebuild drifted from exp4"


def split3(v):
    v = np.asarray(v, float)
    return v[:n], v[n:2 * n], v[2 * n:]
