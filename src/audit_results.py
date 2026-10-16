"""Score the expert audit against the definitional labels.

Reads the labels exported from the audit page's store (one directory per
labeller: audit/<uid>.json profile, audit/<uid>/items/<Q>.json answers; the
ArtifactData tool's `out_dir` export writes exactly this layout) and the
blind key audit/audit_key.csv. Writes results/audit_results.json and the
macros the manuscript uses (appended to paper/numbers_rev.tex by
make_revision_tables.py).

Definitional label: a LEXFLIP item changes legal force ("Oui"); a neutral or
paraphrase control does not ("Non"). "Incertain" counts as disagreement.
"""
import os, sys, json, csv, glob, collections
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
EXP = os.path.join(ROOT, "audit", "export")
KEY = {r["item"]: r for r in csv.DictReader(open(os.path.join(ROOT, "audit", "audit_key.csv")))}


def load():
    labellers = {}
    for prof in glob.glob(os.path.join(EXP, "audit", "*.json")):
        uid = os.path.basename(prof)[:-5]
        p = json.load(open(prof))
        p = p.get("data", p)
        items = {}
        for f in glob.glob(os.path.join(EXP, "audit", uid, "items", "*.json")):
            d = json.load(open(f))
            items[os.path.basename(f)[:-5]] = d.get("data", d)
        labellers[uid] = dict(profile=p, items=items)
    return labellers


def main():
    L = load()
    out = dict(labellers={}, n_items=len(KEY))
    rows = []
    for uid, d in L.items():
        for q, a in d["items"].items():
            k = KEY[q]
            want = "Oui" if k["cell"] == "lexflip" else "Non"
            rows.append(dict(uid=uid, item=q, cell=k["cell"], rule=k["rule"], tier=k["tier"],
                             q2=a.get("q2"), q3=a.get("q3"), q4=a.get("q4"), q1=a.get("q1"),
                             agree=a.get("q2") == want))
        out["labellers"][uid] = dict(role=d["profile"].get("role"), background=d["profile"].get("background"),
                                     n=len(d["items"]))
    if not rows:
        print("no labels yet"); return
    def agg(sel):
        s = [r for r in rows if sel(r)]
        if not s:
            return None
        return dict(n=len(s), agree=float(np.mean([r["agree"] for r in s])),
                    uncertain=float(np.mean([r["q2"] == "Incertain" for r in s])),
                    reverse=float(np.mean([r["q3"] == "Inverse la règle" for r in s if r["q2"] == "Oui"])) if any(r["q2"] == "Oui" for r in s) else None,
                    severity=float(np.mean([r["q4"] for r in s if r["q4"] is not None])),
                    language=float(np.mean([r["q1"] for r in s if r["q1"] is not None])),
                    language_le2=float(np.mean([r["q1"] <= 2 for r in s if r["q1"] is not None])))
    out["by_cell"] = {c: agg(lambda r, c=c: r["cell"] == c) for c in ("lexflip", "neutral", "paraphrase")}
    out["lexflip_by_tier"] = {t: agg(lambda r, t=t: r["cell"] == "lexflip" and r["tier"] == t) for t in ("1", "2")}
    out["lexflip_by_rule"] = {ru: agg(lambda r, ru=ru: r["cell"] == "lexflip" and r["rule"] == ru)
                              for ru in sorted({r["rule"] for r in rows if r["cell"] == "lexflip"})}
    # agreement between labellers, where at least two labelled an item
    if len(L) >= 2:
        import krippendorff
        items = sorted(KEY)
        uids = sorted(L)
        code = {"Oui": 1, "Non": 0, "Incertain": np.nan}
        M = np.array([[code.get(L[u]["items"].get(q, {}).get("q2"), np.nan) for q in items] for u in uids], float)
        S = np.array([[L[u]["items"].get(q, {}).get("q4", np.nan) or np.nan for q in items] for u in uids], float)
        out["alpha_q2_nominal"] = float(krippendorff.alpha(reliability_data=M, level_of_measurement="nominal"))
        out["alpha_q4_ordinal"] = float(krippendorff.alpha(reliability_data=S, level_of_measurement="ordinal"))
    json.dump(out, open(os.path.join(ROOT, "results", "audit_results.json"), "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("labellers", "by_cell", "lexflip_by_tier")}, indent=1))
    for ru, v in out["lexflip_by_rule"].items():
        print("  %-34s n=%2d agree=%.2f reverse=%s sev=%.2f lang=%.2f" % (
            ru, v["n"], v["agree"], "%.2f" % v["reverse"] if v["reverse"] is not None else "-", v["severity"], v["language"]))


if __name__ == "__main__":
    main()
