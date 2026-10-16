"""Experiment 10: controls on the prompted judges.

  order swap   every LEXFLIP edit is scored again with the two sentences
               exchanged: the edited sentence presented as the original and
               the source as the simplification. A doit->peut item then reads
               as peut->doit. If the asymmetry the submitted version read as
               "legal severity" follows the direction of change *as presented*,
               the swap reverses it; if it follows the items, it does not.
  second judge the same probes, FrJudge corpus and prompts under
               Llama-3.3-70B-Instruct (exp4/frjudge tags), so the judge results
               no longer rest on one model family.

Both judges use the rubric-faithful prompt (v1) at K=5, as in exp5.
"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probes as P
import llm_judge as J
import stats_utils as su
from data import load_pairs
from splits import make_split, SEEDS

OUT = os.path.join(P.ROOT, "results")
LLAMA = "meta-llama/Llama-3.3-70B-Instruct"
MODELS = [m for m in os.environ.get("JUDGES", "deepseek-chat," + LLAMA).split(",") if m]
MODAL = {"modal_obligation_to_permission": "doit->peut", "modal_permission_to_obligation": "peut->doit"}


def asym(scores):
    s = np.asarray(scores, float)
    r = np.array(P.RULES)
    a = s[r == "modal_obligation_to_permission"].mean()
    b = s[r == "modal_permission_to_obligation"].mean()
    return dict(doit_to_peut=float(a), peut_to_doit=float(b), gap=float(b - a))


def margin(i_, e_, u_):
    return float((i_ - e_).mean() / (i_.mean() - u_.mean()))


def calibrated_r(v, y):
    from sklearn.isotonic import IsotonicRegression
    rs = []
    for sd in SEEDS:
        tr, va, te = make_split(len(y), sd)
        iso = IsotonicRegression(out_of_bounds="clip").fit(v[tr], y[tr])
        rs.append(su.pearson(iso.predict(v[te]), y[te]))
    return float(np.mean(rs)), float(np.std(rs))


res = json.load(open(os.path.join(OUT, "exp10_judge_controls.json"))) \
    if os.path.exists(os.path.join(OUT, "exp10_judge_controls.json")) else {}
swapped = [dict(original=e["simplification"], simplification=e["original"]) for e in P.edit]
PP = load_pairs()
y = np.array([p["label"] for p in PP])

for model in MODELS:
    tag = "deepseek" if model.startswith("deepseek") else "llama"
    R = res.get(tag, {})
    # forward scores: the cached exp4 run for deepseek, a fresh run for llama
    fwd = np.nanmean(J.score_matrix(P.ALL, tag="exp4", model=model), axis=1)
    i_, e_, u_ = P.split3(fwd)
    if tag == "llama":
        np.save(os.path.join(OUT, "cache", "llama_exp4.npy"), fwd)
        corp = np.nanmean(J.score_matrix(PP, tag="frjudge", model=model), axis=1)
        np.save(os.path.join(OUT, "cache", "llama_frjudge.npy"), corp)
        r_cal, r_sd = calibrated_r(corp, y)
        R.update(r_full=su.pearson(corp, y), r_cal=r_cal, r_cal_sd=r_sd,
                 mean_rating=float(corp.mean()),
                 identical=float(i_.mean()), lexflip=float(e_.mean()), unrelated=float(u_.mean()),
                 margin=margin(i_, e_, u_),
                 margin_t1=float((i_[P.T1] - e_[P.T1]).mean() / (i_.mean() - u_.mean())),
                 discrim=float((i_ > e_).mean()), ties=float((i_ == e_).mean()))
    sw = np.nanmean(J.score_matrix(swapped, tag="swap", model=model), axis=1)
    R["forward_asym"] = asym(e_)
    R["swapped_asym"] = asym(sw)
    ok = np.isfinite(sw)   # an item whose k samples were all unusable has no score
    R["swapped_edit_mean"] = float(sw[ok].mean())
    R["forward_edit_mean"] = float(e_.mean())
    R["order_effect_r"] = su.pearson(e_[ok], sw[ok])
    R["swap_n_scored"] = int(ok.sum())
    res[tag] = R
    json.dump(res, open(os.path.join(OUT, "exp10_judge_controls.json"), "w"), indent=1, default=float)
    print("[%s] forward doit->peut %.2f  peut->doit %.2f | swapped (as presented) doit->peut items %.2f  "
          "peut->doit items %.2f" % (tag, R["forward_asym"]["doit_to_peut"], R["forward_asym"]["peut_to_doit"],
                                      R["swapped_asym"]["doit_to_peut"], R["swapped_asym"]["peut_to_doit"]))
    if tag == "llama":
        print("[llama] r_cal %.3f (sd %.3f)  margin %.3f  ident %.2f edit %.2f unrel %.2f"
              % (R["r_cal"], R["r_cal_sd"], R["margin"], R["identical"], R["lexflip"], R["unrelated"]))
