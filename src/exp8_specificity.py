"""Experiment 8: the specificity half of the dissociation (the 2x2 design).

LEXFLIP (exp4) fills one cell: high overlap, legal force changed. This adds the
two force-preserving cells on the same source sentences (specificity.py):

  neutral     high overlap, force preserved     155 sources
  paraphrase  low overlap,  force preserved     Llama rewrites that pass filters

For each scorer and cell we report the *drop fraction*

    (mean m(s,s) - mean m(s,x)) / (mean m(s,s) - mean m(u))

with the denominator taken over all 373 LEXFLIP sources and the unrelated
probes, i.e. exactly the denominator of the LEXFLIP margin, so the numbers sit
on one scale. A scorer reading legal meaning has drop ~0 on both new cells and
a large LEXFLIP margin. The *selectivity* on a cell is the LEXFLIP margin minus
that cell's drop, computed on the sources the two share (paired).

Intervals are percentile bootstraps (2000 draws) that resample source
sentences, keeping each source's identical/edited/control scores together, and
resample unrelated probes independently.
"""
import os, sys, json, pickle
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probes as P
import specificity as SP

OUT = os.path.join(P.ROOT, "results")
RAW = os.path.join(OUT, "exp8_raw.pkl")
B = 2000
LLAMA = "meta-llama/Llama-3.3-70B-Instruct"


def cells():
    NE = SP.neutral_edits(P.SOURCES)
    C = {"neutral": ([i for i, _, _ in NE],
                     [dict(original=P.SOURCES[i], simplification=e) for i, e, _ in NE],
                     [r for _, _, r in NE])}
    try:
        import gen_paraphrases as G
        PA = G.load()
        C["paraphrase"] = ([i for i, _ in PA],
                           [dict(original=P.SOURCES[i], simplification=p) for i, p in PA],
                           ["paraphrase"] * len(PA))
    except FileNotFoundError:
        print("  (no paraphrases yet; run gen_paraphrases.py)")
    return C


def metric_scores(pairs):
    import metrics_zoo as M
    import features as F
    S = {}
    S["BERTScore-CamemBERTv2"] = M.bertscore_f1(pairs, "almanach/camembertv2-base")
    S["BERTScore-CamemBERTv2-Recall"] = M.bertscore_recall(pairs, "almanach/camembertv2-base")
    S["BERTScore-FlauBERT"] = M.bertscore_f1(pairs, "flaubert/flaubert_base_cased")
    for nm, hf in [("LaBSE", "sentence-transformers/LaBSE"),
                   ("Sentence-CamemBERT", "dangvantuan/sentence-camembert-base"),
                   ("Para-mUSE-mpnet", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")]:
        S[nm] = M.sbert_cosine(pairs, hf)
    S["mE5-base"] = M.sbert_cosine(pairs, "intfloat/multilingual-e5-base", prefix="query: ")
    fwd, bwd, mn = M.nli_bidirectional(pairs)
    S["NLI-fwd (no hallucination)"], S["NLI-bwd (no omission)"], S["NLI-bidirectional (min)"] = fwd, bwd, mn
    X = np.array([F.featurize(d["original"], d["simplification"]) for d in pairs])
    S["surface: token Jaccard"] = X[:, F.FEATURE_NAMES.index("jaccard")]
    S["surface: -|len diff|"] = -X[:, F.FEATURE_NAMES.index("abs_len_diff")]
    return S


def judge_scores(pairs, tag, model):
    import llm_judge as J
    M = J.score_matrix(pairs, tag=tag, model=model)
    return np.nanmean(M, axis=1)


def main():
    C = cells()
    raw = pickle.load(open(RAW, "rb")) if os.path.exists(RAW) else {}
    base = pickle.load(open(os.path.join(OUT, "exp4_raw.pkl"), "rb"))
    base = dict(base)
    base["LLM-judge (deepseek-chat, k=5)"] = np.load(os.path.join(OUT, "cache", "llm_judge_exp4.npy"))
    use_llama = os.environ.get("SKIP_LLAMA") != "1"
    if use_llama:
        base["LLM-judge (Llama-3.3-70B, k=5)"] = judge_scores(P.ALL, "exp4", LLAMA)

    for cell, (idx, pairs, _) in C.items():
        have = raw.get(cell, {})
        if have.get("_n") != len(pairs):
            have = {"_n": len(pairs)}
        if "BERTScore-CamemBERTv2" not in have:
            have.update(metric_scores(pairs))
        have["LLM-judge (deepseek-chat, k=5)"] = judge_scores(pairs, "spec_" + cell, "deepseek-chat")
        if use_llama:
            have["LLM-judge (Llama-3.3-70B, k=5)"] = judge_scores(pairs, "spec_" + cell, LLAMA)
        raw[cell] = have
        pickle.dump(raw, open(RAW, "wb"))

    rng = np.random.default_rng(0)
    res = {}
    for name, v in base.items():
        i_, e_, u_ = P.split3(v)
        row = {}
        den = i_.mean() - u_.mean()
        boots_den = []
        for cell, (idx, pairs, rules) in C.items():
            if name not in raw[cell]:
                continue
            x = np.asarray(raw[cell][name], float)
            idx = np.asarray(idx)
            drop = (i_[idx].mean() - x.mean()) / den
            flip = (i_[idx] - e_[idx]).mean() / den
            bd, bs = [], []
            for _ in range(B):
                a = rng.integers(0, P.n, P.n); b = rng.integers(0, P.n, P.n)
                k = rng.integers(0, len(idx), len(idx))
                d_ = i_[a].mean() - u_[b].mean()
                bd.append((i_[idx[k]].mean() - x[k].mean()) / d_)
                bs.append(((i_[idx[k]] - e_[idx[k]]).mean() - (i_[idx[k]] - x[k]).mean()) / d_)
            per_rule = {}
            for r in sorted(set(rules)):
                m_ = np.array([rr == r for rr in rules])
                per_rule[r] = dict(n=int(m_.sum()),
                                   drop=float((i_[idx][m_].mean() - x[m_].mean()) / den))
            row[cell] = dict(n=len(idx), drop=float(drop), drop_ci=np.percentile(bd, [2.5, 97.5]).tolist(),
                             flip_margin_paired=float(flip), selectivity=float(flip - drop),
                             selectivity_ci=np.percentile(bs, [2.5, 97.5]).tolist(),
                             per_rule=per_rule)
        res[name] = row
    json.dump(dict(rows=res, cells={c: len(v[0]) for c, v in C.items()}),
              open(os.path.join(OUT, "exp8_specificity.json"), "w"), indent=2, default=float)

    print("\n%-32s" % "scorer" + "".join("  %-26s" % c for c in C))
    for name, row in sorted(res.items(), key=lambda kv: -kv[1].get("neutral", {}).get("selectivity", 0)):
        print("%-32s" % name[:32] + "".join(
            "  drop %6.3f sel %6.3f       " % (row[c]["drop"], row[c]["selectivity"]) if c in row else " " * 28
            for c in C))


if __name__ == "__main__":
    main()
