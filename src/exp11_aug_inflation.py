"""Does an augmented evaluation set inflate Pearson r? (Reviewer D, JudgeBERT.)

The paper explains the gap between our retrained scalar baseline and the
published JudgeBERT correlation by evaluation-set augmentation: identical pairs
(label 10) and unrelated pairs (label 1) in a test set stretch the label range,
so any scorer that passes the two endpoint checks gains correlation without
judging better. This tests that directly, with no training involved.

For each of the ten seeded test splits, every scorer is correlated with the
human label on (a) the human test items only and (b) the same items plus one
identical pair (o, o) and one unrelated pair per test item, the 2:1 mixture of
the DA configuration. Identical pairs are the test items' own FrJudge originals.
Unrelated pairs come from the two statutes, as in the DA augmentation. The
prompted judges were not re-queried: their identical and unrelated scores are
the LexFlip probe scores of the same kind of pair.

Writes results/exp11_aug_inflation.json.
"""
import os, sys, json, pickle
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probes as P
import stats_utils as su
import features as F
from data import load_pairs
from splits import make_split, SEEDS
from augment import unrelated_pairs
from exp8_specificity import metric_scores

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
CACHE = os.path.join(OUT, "exp11_raw.pkl")

PP = load_pairs()
y = np.array([p["label"] for p in PP])
RAW = dict(pickle.load(open(os.path.join(OUT, "raw_metric_scores.pkl"), "rb")))
X = np.array([F.featurize(p["original"], p["simplification"]) for p in PP])
RAW["surface: token Jaccard"] = X[:, F.FEATURE_NAMES.index("jaccard")]
RAW["surface: -|len diff|"] = -X[:, F.FEATURE_NAMES.index("abs_len_diff")]

if os.path.exists(CACHE):
    IDENT, UNREL = pickle.load(open(CACHE, "rb"))
else:
    IDENT = metric_scores([dict(original=p["original"], simplification=p["original"]) for p in PP])
    UNREL = metric_scores([dict(original=a, simplification=b)
                           for a, b in unrelated_pairs(len(PP), seed=1105, max_rouge=0.25)])
    pickle.dump((IDENT, UNREL), open(CACHE, "wb"))

# prompted judges: FrJudge scores, and LexFlip identical/unrelated probe scores
for name, corp, probe in (("LLM-judge (deepseek-chat, k=5)", "llm_judge.npy", "llm_judge_exp4.npy"),
                          ("LLM-judge (Llama-3.3-70B, k=5)", "llama_frjudge.npy", "llama_exp4.npy")):
    RAW[name] = np.load(os.path.join(OUT, "cache", corp))
    i_, _, u_ = P.split3(np.load(os.path.join(OUT, "cache", probe)))
    IDENT[name], UNREL[name] = i_, u_

rng = np.random.default_rng(1105)
res = {}
for name in RAW:
    v, vi, vu = (np.asarray(a, float) for a in (RAW[name], IDENT[name], UNREL[name]))
    r_h, r_a = [], []
    for sd in SEEDS:
        _, _, te = make_split(len(PP), sd)
        ii = te if len(vi) == len(PP) else rng.choice(len(vi), len(te), replace=False)
        uu = rng.choice(len(vu), len(te), replace=False)
        r_h.append(su.pearson(v[te], y[te]))
        r_a.append(su.pearson(np.concatenate([v[te], vi[ii], vu[uu]]),
                              np.concatenate([y[te], np.full(len(te), 10.0), np.full(len(te), 1.0)])))
    res[name] = dict(r_human=float(np.mean(r_h)), r_aug=float(np.mean(r_a)),
                     gain=float(np.mean(np.array(r_a) - np.array(r_h))),
                     gain_sd=float(np.std(np.array(r_a) - np.array(r_h), ddof=1)))
json.dump(res, open(os.path.join(OUT, "exp11_aug_inflation.json"), "w"), indent=1)
for k, d in sorted(res.items(), key=lambda kv: -kv[1]["gain"]):
    print("%-34s r human %.3f  r augmented %.3f  gain %+.3f (sd %.3f)" % (k[:34], d["r_human"], d["r_aug"], d["gain"], d["gain_sd"]))
