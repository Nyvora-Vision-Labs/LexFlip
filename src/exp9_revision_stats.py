"""Experiment 9: the statistical additions requested in review.

Everything here re-analyses scores that are already cached; nothing is
retrained and no API is called, except section C, which scores redrawn
unrelated probes with the untrained metrics (cached to exp9_unrel_raw.pkl).

  A  LEXFLIP margins with bootstrap intervals, per tier, tie rates, and the
     margin with the singular tout/toute -> certain(e) items removed
  B  margin per rule for each scorer family (the per-rule table)
  C  sensitivity of the margin to the unrelated probe set
  D  FrJudge: Holm-corrected Williams tests, and correlations with intervals
     from a cluster bootstrap that resamples source forms, not items
  E  power for a dependent-correlation comparison at the test-split size
  F  a like-for-like human ceiling: same 89-item test splits, same kind of
     target (a held-out rater against the other four, and each metric against
     those same four-rater means)
  G  bootstrap intervals for the within-tercile correlations (Table 9)
  H  the prompted-judge call ledger: every request actually issued
"""
import os, sys, json, pickle, glob, re, collections, datetime
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probes as P
import stats_utils as su
from data import load_pairs, ANNOTATORS
from splits import make_split, SEEDS

OUT = os.path.join(P.ROOT, "results")
RNG = np.random.default_rng(2026)
B = 2000
SIM = ["BERTScore-CamemBERTv2", "BERTScore-CamemBERTv2-Recall", "BERTScore-FlauBERT",
       "LaBSE", "Sentence-CamemBERT", "Para-mUSE-mpnet", "mE5-base"]
JUDGE = "LLM-judge (deepseek-chat, k=5)"
LLAMA = "LLM-judge (Llama-3.3-70B, k=5)"
R = {}


def probe_scores():
    S = dict(pickle.load(open(os.path.join(OUT, "exp4_raw.pkl"), "rb")))
    S[JUDGE] = np.load(os.path.join(OUT, "cache", "llm_judge_exp4.npy"))
    q = os.path.join(OUT, "cache", "llama_exp4.npy")
    if os.path.exists(q):
        S[LLAMA] = np.load(q)
    import features as F
    X = np.array([F.featurize(d["original"], d["simplification"]) for d in P.ALL])
    S["surface: token Jaccard"] = X[:, F.FEATURE_NAMES.index("jaccard")]
    S["surface: -|len diff|"] = -X[:, F.FEATURE_NAMES.index("abs_len_diff")]
    return S


def margin(i_, e_, u_):
    return float((i_ - e_).mean() / (i_.mean() - u_.mean()))


def boot_margin(i_, e_, u_, mask=None):
    idx = np.arange(len(i_)) if mask is None else np.flatnonzero(mask)
    out = []
    for _ in range(B):
        a = RNG.choice(idx, len(idx)); b = RNG.integers(0, len(u_), len(u_))
        c = RNG.integers(0, len(i_), len(i_))
        out.append((i_[a] - e_[a]).mean() / (i_[c].mean() - u_[b].mean()))
    return np.percentile(out, [2.5, 97.5]).tolist()


# ------------------------------------------------------------------------ A --
S = probe_scores()
singular = np.array([r == "scope_all_to_some" and
                     re.search(r"\b(certain|certaine)\b", e["simplification"]) is not None
                     for r, e in zip(P.RULES, P.edit)])
A = {}
for name, v in S.items():
    i_, e_, u_ = P.split3(v)
    allv = np.asarray(v, float); lo, hi = allv.min(), allv.max()
    A[name] = dict(
        margin=margin(i_, e_, u_), margin_ci=boot_margin(i_, e_, u_),
        margin_t1=float((i_[P.T1] - e_[P.T1]).mean() / (i_.mean() - u_.mean())),
        margin_t2=float((i_[~P.T1] - e_[~P.T1]).mean() / (i_.mean() - u_.mean())),
        margin_t1_ci=boot_margin(i_, e_, u_, P.T1),
        margin_t2_ci=boot_margin(i_, e_, u_, ~P.T1),
        margin_no_singular=float((i_[~singular] - e_[~singular]).mean() / (i_.mean() - u_.mean())),
        discrim_strict=float((i_ > e_).mean()), ties=float((i_ == e_).mean()),
        discrim_ties_half=float((i_ > e_).mean() + 0.5 * (i_ == e_).mean()),
        # where the probe means sit after min-max over all 3n item scores
        norm_ident=float((i_.mean() - lo) / (hi - lo)), norm_unrel=float((u_.mean() - lo) / (hi - lo)),
        frac_ident_below_max=float((i_ < hi - 1e-9).mean()))
R["A_lexflip"] = A
R["A_n_singular_scope"] = int(singular.sum())

# ------------------------------------------------------------------------ B --
Bt = {}
for rule in sorted(set(P.RULES), key=lambda r: -P.RULES.count(r)):
    m_ = np.array([r == rule for r in P.RULES])
    row = dict(n=int(m_.sum()), tier=1 if P.T1[m_][0] else 2)
    def rm(name):
        i_, e_, u_ = P.split3(S[name])
        return float((i_[m_] - e_[m_]).mean() / (i_.mean() - u_.mean()))
    row["similarity_mean"] = float(np.mean([rm(k) for k in SIM]))
    row["similarity_range"] = [float(min(rm(k) for k in SIM)), float(max(rm(k) for k in SIM))]
    for k in ["NLI-bidirectional (min)", JUDGE, LLAMA, "surface: token Jaccard"]:
        if k in S:
            row[k] = rm(k)
            i_, e_, u_ = P.split3(S[k])
            row[k + " ci"] = boot_margin(i_, e_, u_, m_)
    row["all13_mean"] = float(np.mean([rm(k) for k in S if k != LLAMA]))
    Bt[rule] = row
R["B_rules"] = Bt

# ------------------------------------------------------------------------ C --
from augment import unrelated_pairs
UC = os.path.join(OUT, "exp9_unrel_raw.pkl")
draws = [("seed", s, 0.25) for s in (78, 79, 80, 81, 82)] + [("rouge", 77, t) for t in (0.10, 0.15, 0.35)]
cache = pickle.load(open(UC, "rb")) if os.path.exists(UC) else {}
if os.environ.get("SKIP_UNREL") != "1":
    import metrics_zoo as M
    import features as F
    for kind, sd, th in draws:
        key = "%s_%d_%.2f" % (kind, sd, th)
        if key in cache:
            continue
        pr = [dict(original=a, simplification=b) for a, b in unrelated_pairs(P.n, seed=sd, max_rouge=th)]
        sc = {}
        sc["BERTScore-CamemBERTv2"] = M.bertscore_f1(pr, "almanach/camembertv2-base")
        sc["BERTScore-CamemBERTv2-Recall"] = M.bertscore_recall(pr, "almanach/camembertv2-base")
        sc["BERTScore-FlauBERT"] = M.bertscore_f1(pr, "flaubert/flaubert_base_cased")
        for nm, hf in [("LaBSE", "sentence-transformers/LaBSE"),
                       ("Sentence-CamemBERT", "dangvantuan/sentence-camembert-base"),
                       ("Para-mUSE-mpnet", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")]:
            sc[nm] = M.sbert_cosine(pr, hf)
        sc["mE5-base"] = M.sbert_cosine(pr, "intfloat/multilingual-e5-base", prefix="query: ")
        f_, b_, m_ = M.nli_bidirectional(pr)
        sc["NLI-fwd (no hallucination)"], sc["NLI-bwd (no omission)"], sc["NLI-bidirectional (min)"] = f_, b_, m_
        X = np.array([F.featurize(d["original"], d["simplification"]) for d in pr])
        sc["surface: token Jaccard"] = X[:, F.FEATURE_NAMES.index("jaccard")]
        sc["surface: -|len diff|"] = -X[:, F.FEATURE_NAMES.index("abs_len_diff")]
        sc["_n"] = len(pr)
        cache[key] = sc
        pickle.dump(cache, open(UC, "wb"))
        print("  unrelated draw %s scored (%d pairs)" % (key, len(pr)), flush=True)
C = {}
for name in S:
    i_, e_, u_ = P.split3(S[name])
    ms = {"submitted": margin(i_, e_, u_)}
    for key, sc in cache.items():
        if name in sc:
            ms[key] = float((i_ - e_).mean() / (i_.mean() - np.mean(sc[name])))
    if len(ms) > 1:
        vals = list(ms.values())
        C[name] = dict(margins=ms, min=float(min(vals)), max=float(max(vals)))
R["C_unrelated_sensitivity"] = C

# ------------------------------------------------------------------------ D --
PP = load_pairs()
y = np.array([p["label"] for p in PP])
src = np.array([p["source"] for p in PP])
forms = sorted(set(src))
RAW = dict(pickle.load(open(os.path.join(OUT, "raw_metric_scores.pkl"), "rb")))
RAW[JUDGE] = np.load(os.path.join(OUT, "cache", "llm_judge.npy"))
import features as F
X = F.matrix(PP)
ell = -X[:, F.FEATURE_NAMES.index("abs_len_diff")]
r_ref = su.pearson(ell, y)
tests = []
for k in [k for k in RAW if k != JUDGE]:
    v = np.asarray(RAW[k], float)
    t, df, p = su.williams_test(r_ref, su.pearson(v, y), su.pearson(v, ell), len(y))
    tests.append([k, t, p])
order = np.argsort([p for _, _, p in tests])
m = len(tests); run = 0.0
for rank, j in enumerate(order):
    run = max(run, min(1.0, (m - rank) * tests[j][2]))
    tests[j].append(run)                                  # Holm step-down
D = dict(williams=[dict(metric=k, t=t, p=p, p_holm=ph) for k, t, p, ph in tests])

def cluster_boot(fn):
    out = []
    by = {f: np.flatnonzero(src == f) for f in forms}
    for _ in range(B):
        pick = RNG.choice(forms, len(forms))
        idx = np.concatenate([by[f] for f in pick])
        out.append(fn(idx))
    return np.percentile(out, [2.5, 97.5]).tolist()

def item_boot(fn):
    out = [fn(RNG.integers(0, len(y), len(y))) for _ in range(B)]
    return np.percentile(out, [2.5, 97.5]).tolist()

D["cluster"] = {}
for k, v in list(RAW.items()) + [("surface: -|len diff|", ell)]:
    v = np.asarray(v, float)
    fn = lambda idx, v=v: su.pearson(v[idx], y[idx])
    dfn = lambda idx, v=v: su.pearson(ell[idx], y[idx]) - su.pearson(v[idx], y[idx])
    D["cluster"][k] = dict(r=su.pearson(v, y), ci_item=item_boot(fn), ci_cluster=cluster_boot(fn),
                           len_minus_m=su.pearson(ell, y) - su.pearson(v, y),
                           len_minus_m_ci_cluster=cluster_boot(dfn))
D["n_forms"] = len(forms)
D["form_sizes"] = sorted(collections.Counter(src).values(), reverse=True)
R["D_frjudge"] = D

# ------------------------------------------------------------------------ E --
def williams_power(r12, r13, r23, n, reps=4000, rng=np.random.default_rng(5)):
    C_ = np.array([[1, r12, r13], [r12, 1, r23], [r13, r23, 1]])
    hit = 0
    for _ in range(reps):
        Z = rng.multivariate_normal(np.zeros(3), C_, size=n)
        a, b, c = Z[:, 0], Z[:, 1], Z[:, 2]
        _, _, p = su.williams_test(np.corrcoef(a, b)[0, 1], np.corrcoef(a, c)[0, 1],
                                   np.corrcoef(b, c)[0, 1], n)
        hit += p < 0.05
    return hit / reps

r23s = [su.pearson(np.asarray(RAW[k], float), ell) for k in RAW if k != JUDGE]
r23 = float(np.median(r23s))
grid = np.round(np.concatenate([np.arange(0.0, 0.46, 0.02), np.arange(0.48, 0.92, 0.02)]), 2)
pw = {float(r13): williams_power(0.46, float(r13), r23, 89, reps=1500) for r13 in grid}
below = max([r for r, p in pw.items() if r < 0.46 and p >= 0.8], default=float("nan"))
above = min([r for r, p in pw.items() if r > 0.46 and p >= 0.8], default=float("nan"))
R["E_power"] = dict(r_base=0.46, n=89, median_r_m_ell=r23, power_by_r=pw,
                    largest_r_detectably_below_base=below, smallest_r_detectably_above_base=above,
                    independent_formula=su.min_detectable_r_diff(0.46, 89))

# ------------------------------------------------------------------------ F --
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
Mx = np.array([[p["ratings"][a] for a in ANNOTATORS] for p in PP], float)
F_ = {"ceiling_loo": [], "metrics": collections.defaultdict(lambda: dict(r5=[], r4=[]))}
for sd in SEEDS:
    tr, va, te = make_split(len(PP), sd)
    fit = np.concatenate([tr, va])
    loo = [su.pearson(Mx[te, k], np.delete(Mx[te], k, axis=1).mean(1)) for k in range(5)]
    F_["ceiling_loo"].append(float(np.mean(loo)))
    cands = {k: np.asarray(v, float) for k, v in RAW.items()}
    cands["surface: -|len diff|"] = ell
    for k, v in cands.items():
        iso = IsotonicRegression(out_of_bounds="clip").fit(v[tr], y[tr])
        pr = iso.predict(v[te])
        F_["metrics"][k]["r5"].append(su.pearson(pr, y[te]))
        F_["metrics"][k]["r4"].append(float(np.mean(
            [su.pearson(pr, np.delete(Mx[te], j, axis=1).mean(1)) for j in range(5)])))
    ss = StandardScaler().fit(X[fit])
    rg = RidgeCV(alphas=np.logspace(-3, 3, 25)).fit(ss.transform(X[fit]), y[fit])
    pr = rg.predict(ss.transform(X[te]))
    F_["metrics"]["Surface-Ridge (supervised, 10 feats)"]["r5"].append(su.pearson(pr, y[te]))
    F_["metrics"]["Surface-Ridge (supervised, 10 feats)"]["r4"].append(float(np.mean(
        [su.pearson(pr, np.delete(Mx[te], j, axis=1).mean(1)) for j in range(5)])))
R["F_ceiling"] = dict(
    ceiling_test_mean=float(np.mean(F_["ceiling_loo"])), ceiling_test_sd=float(np.std(F_["ceiling_loo"])),
    metrics={k: dict(r5=float(np.mean(v["r5"])), r4=float(np.mean(v["r4"])), r4_sd=float(np.std(v["r4"])))
             for k, v in F_["metrics"].items()})

# ------------------------------------------------------------------------ G --
d_ = X[:, F.FEATURE_NAMES.index("abs_len_diff")]
q = np.quantile(d_, [1 / 3, 2 / 3]); bucket = np.digitize(d_, q)
G = {}
for k, v in [("length", ell)] + [(k, np.asarray(RAW[k], float)) for k in
                                 ("BERTScore-FlauBERT", "LaBSE", "NLI-bidirectional (min)")]:
    row = {}
    for b, nm in enumerate(["small", "medium", "large"]):
        idx = np.flatnonzero(bucket == b)
        row[nm] = dict(n=len(idx), r=su.pearson(v[idx], y[idx]),
                       ci=np.percentile([su.pearson(v[j], y[j]) for j in
                                         (RNG.choice(idx, len(idx)) for _ in range(B))], [2.5, 97.5]).tolist())
    G[k] = row
R["G_buckets"] = G

# ------------------------------------------------------------------------ H --
H = collections.Counter(); first, last = {}, {}
for f in glob.glob(os.path.join(OUT, "llm_cache", "*.jsonl")):
    base = os.path.basename(f)
    if base.startswith(("smoke", "sanity")):
        continue
    model = "deepseek-reasoner" if "reasoner" in base else ("llama" if "Llama" in base else "deepseek-chat")
    n_ok = sum(1 for l in open(f, encoding="utf-8") if l.strip())
    H[model] += n_ok
    H[base] = n_ok
    t = datetime.datetime.fromtimestamp(os.path.getmtime(f)).date().isoformat()
    last[base] = t
R["H_calls"] = dict(per_file=dict(H), last_modified=last)

json.dump(R, open(os.path.join(OUT, "exp9_revision_stats.json"), "w"), indent=1, default=float)
print("wrote results/exp9_revision_stats.json")
for k in ["NLI-bidirectional (min)", JUDGE, "BERTScore-CamemBERTv2", "surface: -|len diff|"]:
    a = A[k]
    print("%-32s margin %.3f [%.3f, %.3f]  t1 %.3f t2 %.3f  no-singular %.3f  ties %.3f  norm id %.3f un %.3f"
          % (k, a["margin"], *a["margin_ci"], a["margin_t1"], a["margin_t2"], a["margin_no_singular"],
             a["ties"], a["norm_ident"], a["norm_unrel"]))
print("singular scope items:", R["A_n_singular_scope"])
print("Holm:", [(t["metric"][:14], round(t["p"], 4), round(t["p_holm"], 4)) for t in D["williams"]])
print("power: below", R["E_power"]["largest_r_detectably_below_base"], "above", R["E_power"]["smallest_r_detectably_above_base"], "indep formula", R["E_power"]["independent_formula"])
print("ceiling test-split: %.3f" % R["F_ceiling"]["ceiling_test_mean"])
for k, v in R["F_ceiling"]["metrics"].items():
    print("   %-36s r5 %.3f  r4 %.3f" % (k[:36], v["r5"], v["r4"]))
print("calls:", {k: v for k, v in H.items() if not k.endswith(".jsonl")})
