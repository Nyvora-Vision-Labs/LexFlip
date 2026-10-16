"""Experiment 3b: why do the trained models fail the identical-pair check?

Section 4.6 of the submitted version reads the 0% identical pass as a failure to
generalise across source documents (statutory probes, FrJudge training pairs).
Two simpler explanations were not excluded, and this experiment separates them:

  scale compression   a regressor shrunk toward the label mean rarely reaches
                      the 9.9 pass bar, whatever the document. Test: the same
                      check on identical pairs built from held-out FrJudge
                      originals, plus relaxed criteria (>= 9, and the share of
                      identical pairs placed above the model's own 95th
                      percentile on real test pairs).
  document shift      the explanation in the paper. Test: the margin fraction
                      on LexFlip-style edits of held-out FrJudge originals,
                      against the same quantity on the statutory probes.

Held-out means: in the test split AND absent from every augmentation pool the
model saw. The submitted DA pools drew identical pairs and edit negatives from
all 297 originals; here they are drawn from the training split only, which is
also reported as a change to the DA configurations themselves.

It also separates the two sources of seed variance the submitted grid conflated:
`--vary split` keeps initialisation fixed and redraws the split, `--vary init`
keeps the split fixed and redraws initialisation.
"""
import argparse, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import load_pairs
from splits import make_split
from augment import unrelated_pairs, lexflip_edits, tier, _sents
from train import train_one, predict
import stats_utils as su
import exp3_train as E

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", os.environ.get("EXP3B_OUT", "exp3b_indist.json"))
P = E.P


def aug_items_trainonly(kind, seed, n, tr):
    """exp3's augmentation, restricted to training-split originals."""
    out = []
    orig = [P[i]["original"] for i in tr]
    if kind in ("da", "da+edit"):
        rng = np.random.default_rng(seed)
        for i in rng.choice(len(orig), size=min(n, len(orig)), replace=False):
            out.append(dict(text_a=orig[i], text_b=orig[i], mean=10.0, ratings=[10] * 5, aux=-1))
        for a, b in unrelated_pairs(n, seed=seed):
            out.append(dict(text_a=a, text_b=b, mean=1.0, ratings=[1] * 5, aux=-1))
    if kind == "da+edit":
        ed = lexflip_edits(orig, seed=seed, per_sentence=1)
        rng = np.random.default_rng(seed + 1)
        for j in rng.choice(len(ed), size=min(n, len(ed)), replace=False):
            o, pert, _ = ed[j]
            out.append(dict(text_a=o, text_b=pert, mean=1.0, ratings=[1] * 5, aux=-1))
    return out


def probes_frjudge(te, seed):
    """In-distribution probes from held-out (test) FrJudge originals."""
    orig = [P[i]["original"] for i in te]
    ident = [(o, o) for o in orig]
    rng = np.random.default_rng(3000 + seed)
    perm = rng.permutation(len(orig))
    unrel = [(orig[i], orig[j]) for i, j in zip(range(len(orig)), perm) if i != j]
    ed = lexflip_edits(orig, seed=seed, per_sentence=1)
    return ident, unrel, ed


def probes_statute(seed):
    """exp3's own statutory probes (same construction, same seeds)."""
    rng = np.random.default_rng(1000 + seed)
    ref = _sents("A-25.jsonl") + _sents("code_securite_routiere.jsonl")
    ridx = rng.choice(len(ref), size=min(297, len(ref)), replace=False)
    ident = [(ref[i], ref[i]) for i in ridx]
    unrel = [(a, b) for a, b in unrelated_pairs(297, seed=5000 + seed)]
    ed = lexflip_edits([ref[i] for i in ridx], seed=seed, per_sentence=1)
    return ident, unrel, ed


def diag(m, btc, ident, unrel, ed, test_preds):
    si = predict(m, btc, ident)
    su_ = predict(m, btc, unrel)
    so = predict(m, btc, [(o, o) for o, _, _ in ed])
    se = predict(m, btc, [(o, p) for o, p, _ in ed])
    p95 = float(np.percentile(test_preds, 95))
    rng_ = float(so.mean() - su_.mean())
    return dict(
        ident_mean=float(si.mean()), unrel_mean=float(su_.mean()),
        ident_pass_99=float((si >= 9.9).mean()), ident_pass_9=float((si >= 9.0).mean()),
        ident_above_p95=float((si >= p95).mean()),
        unrel_pass_11=float((su_ <= 1.1).mean()), unrel_pass_2=float((su_ <= 2.0).mean()),
        edit_mean=float(se.mean()),
        margin_frac=(float((so - se).mean() / rng_) if rng_ >= 1.0 else float("nan")),
        working_range=rng_, n_edit=len(ed),
        test_pred_sd=float(np.std(test_preds)), test_p95=p95)


def run(name, aug, seeds, vary):
    items = E.base_items()
    y = np.array([it["mean"] for it in items])
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    key = "%s|vary=%s" % (name, vary)
    done = {r["seed"] for r in res.get(key, [])}
    for sd in seeds:
        if sd in done:
            continue
        t0 = time.time()
        split_seed = sd if vary == "split" else 42
        init_seed = 42 if vary == "split" else sd
        if vary == "both":
            split_seed = init_seed = sd
        tr, va, te = make_split(len(P), split_seed)
        tri = [items[i] for i in tr]
        if aug:
            tri = tri + aug_items_trainonly(aug, split_seed, len(tr), tr)
        m, btc, eps = train_one(tri, [items[i] for i in va], head="scalar",
                                seed=init_seed, verbose=False)
        pr = predict(m, btc, [(items[i]["text_a"], items[i]["text_b"]) for i in te])
        rec = dict(seed=sd, split_seed=split_seed, init_seed=init_seed, epochs=eps,
                   r=su.pearson(pr, y[te]), rmse=su.rmse(pr, y[te]),
                   frjudge=diag(m, btc, *probes_frjudge(te, split_seed), pr),
                   statute=diag(m, btc, *probes_statute(split_seed), pr),
                   secs=time.time() - t0)
        res.setdefault(key, []).append(rec)
        json.dump(res, open(OUT, "w"), indent=2, default=float)
        f, s = rec["frjudge"], rec["statute"]
        print(f"[{key}] seed={sd} r={rec['r']:.3f} | FrJ id>=9.9 {f['ident_pass_99']:.2f} "
              f">=9 {f['ident_pass_9']:.2f} mean {f['ident_mean']:.2f} margin {f['margin_frac']:.3f} | "
              f"stat id>=9.9 {s['ident_pass_99']:.2f} mean {s['ident_mean']:.2f} "
              f"margin {s['margin_frac']:.3f} ({rec['secs']:.0f}s)", flush=True)
        del m
        import torch, gc; gc.collect()
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
        elif torch.cuda.is_available():
            torch.cuda.empty_cache()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="scalar", choices=["scalar", "da", "da+edit"])
    ap.add_argument("--seeds", default="42,43,44,45,46")
    ap.add_argument("--vary", default="both", choices=["both", "split", "init"])
    a = ap.parse_args()
    names = {"scalar": "JudgeBERT (repro)", "da": "JudgeBERT-DA (repro)",
             "da+edit": "JudgeBERT-DA+LexFlip"}
    run(names[a.config], None if a.config == "scalar" else a.config,
        [int(s) for s in a.seeds.split(",")], a.vary)
