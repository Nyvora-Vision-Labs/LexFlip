"""Extend the audit sample from 117 to 200 items (Q118-Q200), drawing only
items not sampled before. Appends to audit/audit_key.csv and writes the new
items to audit/audit_extension.json (same fields as the workbook)."""
import os, sys, csv, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probes as P, specificity as SP, gen_paraphrases as G
from make_audit_sheet import context
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
key = list(csv.DictReader(open(os.path.join(ROOT, "audit", "audit_key.csv"))))
used = {(r["cell"], int(r["source_index"])) for r in key}
rng = random.Random(1205002)
ALLOC = {"modal_permission_to_obligation": 8, "modal_obligation_to_permission": 6, "scope_all_to_some": 5,
         "connective_and_to_or": 3, "connective_or_to_and": 3, "amount_x10": 3, "negation_drop": 3,
         "party_insurer_to_insured": 3, "condition_unless_to_if": 3, "vehicle_class": 3, "temporal_flip": 3}
new = []
for rule, k in ALLOC.items():
    pool = [i for i, r in enumerate(P.RULES) if r == rule and ("lexflip", i) not in used]
    rng.shuffle(pool)
    for i in pool[:k]:
        new.append(dict(cell="lexflip", rule=rule, tier=1 if P.T1[i] else 2, src=i,
                        original=P.SOURCES[i], edited=P.edit[i]["simplification"]))
NE = [(i, e, r) for i, e, r in SP.neutral_edits(P.SOURCES) if ("neutral", i) not in used]
rng.shuffle(NE)
new += [dict(cell="neutral", rule=r, tier="", src=i, original=P.SOURCES[i], edited=e) for i, e, r in NE[:20]]
PA = [(i, p) for i, p in G.load() if ("paraphrase", i) not in used]
rng.shuffle(PA)
new += [dict(cell="paraphrase", rule="paraphrase", tier="", src=i, original=P.SOURCES[i], edited=p) for i, p in PA[:20]]
rng.shuffle(new)
for k, d in enumerate(new, 118):
    d["item"] = "Q%03d" % k
    d["law"], d["article"], d["article_text"] = context(d["original"])
with open(os.path.join(ROOT, "audit", "audit_key.csv"), "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for d in new:
        w.writerow([d["item"], d["cell"], d["rule"], d["tier"], d["src"], bool(d["article"])])
json.dump([{k: d[k] for k in ("item", "law", "article", "article_text", "original", "edited")} for d in new],
          open(os.path.join(ROOT, "audit", "audit_extension.json"), "w"), ensure_ascii=False, indent=1)
import collections
print(len(new), "new items:", dict(collections.Counter(d["cell"] for d in new)))
