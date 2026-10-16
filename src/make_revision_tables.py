"""Tables and numeric macros added in the JCLLT revision.

Reads the revision result files (exp3b, exp8, exp9, exp10) and writes
paper/numbers_rev.tex plus the new or replaced tables in paper/tables/. Any
result file that does not exist yet leaves its macros as a visible
placeholder, so a missing run can never pass silently into the PDF.
"""
import os, sys, json, re, difflib, datetime, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probes as P

ROOT = P.ROOT
RES = os.path.join(ROOT, "results")
TAB = os.path.join(ROOT, "paper", "tables")
N = {}
MISSING = r"\textbf{??}"
JUDGE = "LLM-judge (deepseek-chat, k=5)"
LLAMA = "LLM-judge (Llama-3.3-70B, k=5)"
NLI = "NLI-bidirectional (min)"
SIM = ["BERTScore-CamemBERTv2", "BERTScore-CamemBERTv2-Recall", "BERTScore-FlauBERT",
       "LaBSE", "Sentence-CamemBERT", "Para-mUSE-mpnet", "mE5-base"]


def load(name):
    p = os.path.join(RES, name)
    return json.load(open(p)) if os.path.exists(p) else None


def f3(x):
    return MISSING if x is None or (isinstance(x, float) and np.isnan(x)) else "%.3f" % x


def neg0(s):
    return s.replace("-0.000", "0.000")


def W(name, text):
    open(os.path.join(TAB, name), "w").write(text + "\n")


def esc(s):
    return (s.replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%")
            .replace("$", r"\$").replace("#", r"\#").replace("_", r"\_").replace("°", r"\textdegree{}")
            .replace("\u2014", "--"))


# --------------------------------------------------------------- examples --
EXAMPLES = [  # (source index into probes, rule label)
    (None, "modal_permission_to_obligation"), (43, "modal_obligation_to_permission"),
    (None, "negation_drop"), (None, "temporal_flip"), (168, "scope_all_to_some"),
    (305, "party_insurer_to_insured"), (301, "condition_unless_to_if")]
LABEL = {"modal_permission_to_obligation": r"\emph{peut} $\rightarrow$ \emph{doit}",
         "modal_obligation_to_permission": r"\emph{doit} $\rightarrow$ \emph{peut}",
         "negation_drop": r"drop \emph{ne \dots pas}",
         "temporal_flip": r"\emph{avant} $\leftrightarrow$ \emph{apr\`es}",
         "scope_all_to_some": r"\emph{tous les} $\rightarrow$ \emph{certains}",
         "party_insurer_to_insured": r"\emph{assureur} $\rightarrow$ \emph{assur\'e}",
         "condition_unless_to_if": r"\emph{sauf} $\rightarrow$ \emph{y compris}"}


def bold_diff(o, e):
    a, b = o.split(" "), e.split(" ")
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        seg = " ".join(b[j1:j2])
        if not seg:
            continue
        out.append(esc(seg) if op == "equal" else r"\textbf{" + esc(seg) + "}")
    return " ".join(out)


def tab_examples():
    rows = []
    used = set()
    for idx, rule in EXAMPLES:
        if idx is None:   # first item of the rule that is short enough
            idx = next(i for i, r in enumerate(P.RULES) if r == rule and len(P.SOURCES[i]) < 170
                       and i not in used)
        assert P.RULES[idx] == rule, (idx, rule, P.RULES[idx])
        used.add(idx)
        o, e = P.SOURCES[idx], P.edit[idx]["simplification"]
        t = "tier %d" % (1 if P.T1[idx] else 2)
        rows.append(LABEL[rule] + r" \hfill \emph{" + t + r"} \\[1pt]" + "\n"
                    + r"\footnotesize $o$: " + esc(o) + r" \\[1pt]" + "\n"
                    + r"\footnotesize $s'$: " + bold_diff(o, e) + r" \\")
    W("examples_rev.tex", "\\setlength{\\tabcolsep}{4pt}\n\\begin{tabular}{@{}p{0.97\\columnwidth}@{}}\n"
      "\\toprule\n" + "\n\\midrule\n".join(rows) + "\n\\bottomrule\n\\end{tabular}")


# --------------------------------------------------------------- glossary --
GLOSSARY = [
    ("Metric, scorer", "An automatic function that gives a number for how well a simplification $s$ keeps the meaning of an original $o$."),
    ("Legal force", "What a provision does in law: who it binds, whether it obliges or permits, what it covers, and how much."),
    ("Dissociation", "A test item in which two variables that usually move together are separated. Here, surface wording stays fixed and legal force changes, or the reverse."),
    ("Token Jaccard", "The share of distinct words two sentences have in common: $1$ for identical sentences, $0$ for no shared words."),
    ("Margin", "The share of a metric's own identical-to-unrelated range that it uses on a legally decisive edit. Higher is better."),
    ("Specificity drop", "The same quantity for an edit that keeps legal force. The ideal value is $0$."),
    ("Selectivity", "Margin minus specificity drop, on the same sentences."),
    ("NLI (bidirectional)", "Natural language inference: a model gives the probability that one sentence follows from another. We test both directions and keep the lower value."),
    ("Pearson $r$, Spearman $\\rho$", "Correlation of a metric with the human ratings: $1$ is perfect agreement, $0$ is none. $\\rho$ uses ranks only."),
    ("Human ceiling", "The correlation one annotator reaches with the mean of the other four. It shows how well a single expert agrees with the panel."),
    ("Isotonic calibration", "A monotone map from a metric's raw score to the $1$--$10$ scale, fitted on training data. It changes the scale and keeps the ranking."),
    ("Bootstrap interval", "A $95\\%$ range for a statistic, found by recomputing it on many resamples of the items."),
]


def tab_glossary():
    rows = ["%s & %s \\\\" % (t, d) for t, d in GLOSSARY]
    W("glossary.tex", "\\setlength{\\tabcolsep}{4pt}\n\\begin{tabular}{@{}p{0.27\\columnwidth}p{0.68\\columnwidth}@{}}\n"
      "\\toprule\nTerm & Meaning \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}")


# --------------------------------------------- challenge table, with CIs --
SHORTN = {"NLI-bidirectional (min)": "NLI-bidirectional (min)", "NLI-bwd (no omission)": "NLI-bwd (no omission)",
          "NLI-fwd (no hallucination)": "NLI-fwd (no hallucination)",
          JUDGE: "Judge: DeepSeek-chat ($K{=}5$)", LLAMA: "Judge: Llama-3.3-70B ($K{=}5$)",
          "surface: token Jaccard": "surface: token Jaccard", "surface: -|len diff|": r"surface: $-|\,|s|-|o|\,|$"}


def tab_challenge(A, E4):
    rows = []
    order = sorted(A, key=lambda k: -A[k]["margin"])
    for k in order:
        a = A[k]
        r4 = E4.get(k)
        if r4 is None and k == LLAMA:
            ident, edit, unrel = a["norm_ident"], float("nan"), a["norm_unrel"]
        name = SHORTN.get(k, esc(k))
        ci = "[%.3f, %.3f]" % tuple(a["margin_ci"])
        rows.append("%s & %.3f & %.3f & %.1f & %.1f & %.3f & %s & %.3f & %.3f \\\\" % (
            name, a["norm_ident"], a["norm_unrel"], 100 * a["discrim_strict"], 100 * a["ties"],
            a["margin"], ci, a["margin_t1"], a["margin_t2"]))
    W("challenge_rev.tex", "\\setlength{\\tabcolsep}{3.5pt}\n\\begin{tabular}{lrrrrrcrr}\n\\toprule\n"
      "Metric & ident. & unrel. & discrim.\\% & ties\\% & margin & $95\\%$ CI & tier 1 & tier 2 \\\\\n"
      "\\midrule\n" + "\n".join(neg0(r) for r in rows) + "\n\\bottomrule\n\\end{tabular}")


# --------------------------------------------------- rules x scorer family --
RULE_DISPLAY = {
    "modal_permission_to_obligation": r"\emph{peut} $\rightarrow$ \emph{doit}",
    "modal_obligation_to_permission": r"\emph{doit} $\rightarrow$ \emph{peut}",
    "scope_all_to_some": r"\emph{tous les} $\rightarrow$ \emph{certains}",
    "amount_x10": r"amount $\times 10$", "negation_drop": r"drop \emph{ne \dots pas}",
    "party_insurer_to_insured": r"\emph{assureur} $\rightarrow$ \emph{assur\'e}",
    "party_insured_to_insurer": r"\emph{assur\'e} $\rightarrow$ \emph{assureur}",
    "condition_unless_to_if": r"\emph{sauf (si)} $\rightarrow$ \emph{si}, \emph{y compris}",
    "temporal_flip": r"\emph{avant} $\leftrightarrow$ \emph{apr\`es}",
    "connective_and_to_or": r"\emph{et} $\rightarrow$ \emph{ou}",
    "connective_or_to_and": r"\emph{ou} $\rightarrow$ \emph{et}",
    "vehicle_class": r"\emph{automobile} $\leftrightarrow$ \emph{v\'ehicule}"}


def tab_rules(Bt, A):
    have_llama = any(LLAMA in r for r in Bt.values())
    rows1, rows2 = [], []
    for rule, r in sorted(Bt.items(), key=lambda kv: (kv[1]["tier"], -kv[1]["n"])):
        cells = [RULE_DISPLAY[rule], str(r["n"]), "%.3f" % r["similarity_mean"],
                 "%.3f" % r[NLI], "%.3f" % r[JUDGE]]
        if have_llama:
            cells.append("%.3f" % r[LLAMA] if LLAMA in r else "--")
        (rows1 if r["tier"] == 1 else rows2).append(" & ".join(cells) + r" \\")
    ncol = 6 if have_llama else 5
    head = "Rule & $n$ & similarity & NLI-bi & DeepSeek" + (" & Llama" if have_llama else "") + r" \\"
    def allrow(mask_name, label):
        c = [label, "", "", "", ""]
        return c
    t = ("\\setlength{\\tabcolsep}{3.5pt}\n\\begin{tabular}{l" + "r" * (ncol - 1) + "}\n\\toprule\n" + head +
         "\n\\midrule\n\\multicolumn{%d}{l}{\\emph{Tier 1}} \\\\\n" % ncol + "\n".join(neg0(r) for r in rows1) +
         "\n\\midrule\n\\multicolumn{%d}{l}{\\emph{Tier 2}} \\\\\n" % ncol + "\n".join(neg0(r) for r in rows2))
    tot = ["\\textbf{All}", str(P.n), "%.3f--%.3f" % (min(A[k]["margin"] for k in SIM), max(A[k]["margin"] for k in SIM)),
           "%.3f" % A[NLI]["margin"], "%.3f" % A[JUDGE]["margin"]]
    if have_llama:
        tot.append("%.3f" % A[LLAMA]["margin"] if LLAMA in A else "--")
    t += "\n\\midrule\n" + " & ".join(tot) + r" \\" + "\n\\bottomrule\n\\end{tabular}"
    W("rules_rev.tex", t)


# ------------------------------------------------------------ specificity --
def tab_specificity(S8):
    rows = S8["rows"]
    cells = list(S8["cells"])
    order = [NLI, "NLI-bwd (no omission)", "NLI-fwd (no hallucination)", JUDGE, LLAMA] + SIM + \
            ["surface: token Jaccard", "surface: -|len diff|"]
    out = []
    for k in order:
        if k not in rows:
            continue
        r = rows[k]
        flip = r.get("neutral", r.get(cells[0]))["flip_margin_paired"]
        c = [SHORTN.get(k, esc(k)), "%.3f" % flip]
        for cell in ("neutral", "paraphrase"):
            if cell in r:
                c += ["%.3f" % r[cell]["drop"], "%.3f" % r[cell]["selectivity"]]
            else:
                c += ["--", "--"]
        out.append(neg0(" & ".join(c) + r" \\"))
    W("specificity.tex", "\\setlength{\\tabcolsep}{3.5pt}\n\\begin{tabular}{lrrrrr}\n\\toprule\n"
      "& \\textsc{LexFlip} & \\multicolumn{2}{c}{neutral edit} & \\multicolumn{2}{c}{paraphrase} \\\\\n"
      "\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}\n"
      "Metric & margin & drop & select. & drop & select. \\\\\n\\midrule\n" + "\n".join(out) +
      "\n\\bottomrule\n\\end{tabular}")


# ---------------------------------------------------- judge configurations --
def tab_judge_configs(E7, E10, E5):
    c = E7["configs"]
    rows = [
        ("\\textbf{Headline}", "rubric, FR", "deepseek-chat", "5", "all", "yes", f3(E5["r"]) if E5 else MISSING, f3(E5["m"]) if E5 else MISSING),
        ("Redraw", "rubric, FR", "deepseek-chat", "5", "all", "yes", N.get("repRcalTwo", MISSING), N.get("repMarginTwo", MISSING)),
        ("Uncalibrated", "rubric, FR", "deepseek-chat", "5", "all", "no", N.get("judgeKfiveRaw", MISSING), "--"),
        ("Single sample", "rubric, FR", "deepseek-chat", "1", "sub", "yes", f3(c["chat (K=1)"]["r_cal_mean"]), f3(c["chat (K=1)"]["margin_frac"])),
        ("Reasoner", "rubric, FR", "deepseek-reasoner", "1", "sub", "yes", f3(c["reasoner (K=1)"]["r_cal_mean"]), f3(c["reasoner (K=1)"]["margin_frac"])),
        ("Prompt v1", "rubric, FR", "deepseek-chat", "2", "sub", "yes", f3(c["chat v1 (rubric, FR)"]["r_cal_mean"]), f3(c["chat v1 (rubric, FR)"]["margin_frac"])),
        ("Prompt v2", "rubric, EN", "deepseek-chat", "2", "sub", "yes", f3(c["chat v2 (rubric, EN)"]["r_cal_mean"]), f3(c["chat v2 (rubric, EN)"]["margin_frac"])),
        ("Prompt v3", "bare, FR", "deepseek-chat", "2", "sub", "yes", f3(c["chat v3 (no taxonomy)"]["r_cal_mean"]), f3(c["chat v3 (no taxonomy)"]["margin_frac"])),
    ]
    L = (E10 or {}).get("llama")
    rows.append(("Second family", "rubric, FR", "Llama-3.3-70B", "5", "all", "yes",
                 f3(L["r_cal"]) if L else MISSING, f3(L["margin"]) if L else MISSING))
    out = [" & ".join(r) + r" \\" for r in rows]
    W("judge_configs.tex", "\\setlength{\\tabcolsep}{3pt}\n\\begin{tabular}{lllcccrr}\n\\toprule\n"
      "Configuration & prompt & model & $K$ & items & cal. & $r$ & margin \\\\\n\\midrule\n"
      + "\n".join(out) + "\n\\bottomrule\n\\end{tabular}")


# ---------------------------------------------------------- in-distribution --
def tab_indist(E3b):
    rows = []
    names = [("JudgeBERT (repro)|vary=both", "Scalar"), ("JudgeBERT-DA (repro)|vary=both", "DA"),
             ("JudgeBERT-DA+LexFlip|vary=both", "DA+LexFlip")]
    for key, lab in names:
        recs = E3b.get(key, [])
        if not recs:
            continue
        def m(path):
            v = [r[path[0]][path[1]] for r in recs]
            v = [x for x in v if not (isinstance(x, float) and np.isnan(x))]
            return np.mean(v) if v else float("nan")
        def fmt(x, pct=False):
            return "--" if np.isnan(x) else ("%.0f" % (100 * x) if pct else "%.2f" % x)
        rows.append(" & ".join([lab, str(len(recs)),
                                fmt(m(("frjudge", "ident_mean"))), fmt(m(("frjudge", "unrel_mean"))),
                                fmt(m(("frjudge", "ident_pass_99")), True),
                                fmt(m(("frjudge", "ident_pass_9")), True), fmt(m(("frjudge", "margin_frac"))),
                                fmt(m(("statute", "ident_mean"))), fmt(m(("statute", "ident_pass_99")), True),
                                fmt(m(("statute", "ident_pass_9")), True), fmt(m(("statute", "margin_frac")))]) + r" \\")
    W("indist.tex", "\\setlength{\\tabcolsep}{3pt}\n\\begin{tabular}{lrrrrrrrrrr}\n\\toprule\n"
      "& & \\multicolumn{5}{c}{held-out \\textsc{FrJudge} originals} & \\multicolumn{4}{c}{statutory probes} \\\\\n"
      "\\cmidrule(lr){3-7}\\cmidrule(lr){8-11}\n"
      "Model & seeds & ident. & unrel. & $\\geq$9.9 & $\\geq$9 & margin & ident. & $\\geq$9.9 & $\\geq$9 & margin \\\\\n"
      "\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}")


# ---------------------------------------------------------------- prompts --
def tab_prompts():
    import llm_judge as J
    def block(t):
        t = t.replace("{original}", "<original>").replace("{simplification}", "<simplification>")
        t = t.replace("{{", "{").replace("}}", "}")
        raw = t.split("\n")     # rejoin the source's wrapped continuation lines
        merged = []
        for l in raw:
            if l.startswith("    ") and merged:
                merged[-1] += " " + l.strip()
            else:
                merged.append(l)
        lines = [esc(l).replace("<original>", r"\emph{[original clause]}").replace(
            "<simplification>", r"\emph{[simplified version]}") for l in merged]
        return r"\\ ".join(l if l.strip() else r"\phantom{x}" for l in lines)
    sys_fr, v1 = J.PROMPTS["v1"]
    _, v3 = J.PROMPTS["v3"]
    rows = [r"\textbf{System (v1, v3)} & " + esc(sys_fr) + r" \\",
            r"\midrule", r"\textbf{User, v1 (headline)} & \parbox[t]{0.80\textwidth}{\raggedright " + block(v1) + r"} \\",
            r"\midrule", r"\textbf{User, v3 (bare)} & \parbox[t]{0.80\textwidth}{\raggedright " + block(v3) + r"} \\",
            r"\midrule", r"\textbf{v2} & The v1 rubric translated into English, over the same French clauses (system prompt in English). Full text in the repository, \texttt{src/llm\_judge.py}. \\"]
    W("prompts.tex", "\\setlength{\\tabcolsep}{4pt}\n\\begin{tabular}{@{}p{0.15\\textwidth}p{0.81\\textwidth}@{}}\n\\toprule\n"
      + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}")


def tab_significance(D):
    import pickle
    rows = []
    cl = D["cluster"]
    for t in D["williams"]:
        k = t["metric"]
        c = cl[k]
        p = "$<$0.001" if t["p"] < 1e-3 else "%.3f" % t["p"]
        ph = "$<$0.001" if t["p_holm"] < 1e-3 else "%.3f" % t["p_holm"]
        rows.append("%s & %.3f & %.2f & %s & %s & [%.3f, %.3f] \\\\" % (
            esc(k), c["r"], t["t"], p, ph, *c["len_minus_m_ci_cluster"]))
    W("significance_rev.tex", "\\setlength{\\tabcolsep}{4pt}\n\\begin{tabular}{lrrrrc}\n\\toprule\n"
      "Neural metric $m$ & $r(m,h)$ & $t$ & $p$ & $p_{\\text{Holm}}$ & cluster CI \\\\\n\\midrule\n"
      + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}")


def audit_and_bugs():
    """Margins without the generator errors; the expert annotation summary."""
    import pickle
    S = dict(pickle.load(open(os.path.join(RES, "exp4_raw.pkl"), "rb")))
    S[JUDGE] = np.load(os.path.join(RES, "cache", "llm_judge_exp4.npy"))
    bugs = set(json.load(open(os.path.join(RES, "lexflip_generator_bugs.json"))))
    keep = np.array([i not in bugs for i in range(P.n)])
    shift = []
    for k, v in S.items():
        i_, e_, u_ = P.split3(v)
        den = i_.mean() - u_.mean()
        m0 = (i_ - e_).mean() / den
        m1 = (i_[keep] - e_[keep]).mean() / den
        shift.append(abs(m1 - m0))
        if k == NLI:
            N["nliMarginNoBug"] = "%.3f" % m1
    N["nBugs"] = str(len(bugs))
    N["maxBugShift"] = "%.3f" % max(shift)
    f = os.path.join(ROOT, "audit", "expert_labels.json")
    if os.path.exists(f):
        L = json.load(open(f))["labels"]
        def pct(a, b): return "%d" % round(100.0 * a / b) if b else "0"
        lex = [x for x in L if x["cell"] == "lexflip"]
        t1 = [x for x in lex if x["tier"] == "1"]; t2 = [x for x in lex if x["tier"] == "2"]
        neu = [x for x in L if x["cell"] == "neutral"]; par = [x for x in L if x["cell"] == "paraphrase"]
        N["expLexAgree"], N["expLexN"] = str(sum(x["agree"] for x in lex)), str(len(lex))
        N["expTOneAgree"], N["expTOneN"] = str(sum(x["agree"] for x in t1)), str(len(t1))
        N["expTTwoAgree"], N["expTTwoN"] = str(sum(x["agree"] for x in t2)), str(len(t2))
        N["expNeuAgree"], N["expNeuN"] = str(sum(x["agree"] for x in neu)), str(len(neu))
        N["expParAgree"], N["expParN"] = str(sum(x["agree"] for x in par)), str(len(par))
        N["expParChange"] = str(sum(x["q2"] == "Oui" for x in par))
        N["expParUncertain"] = str(sum(x["q2"] == "Incertain" for x in par))
        yes = [x for x in lex if x["q2"] == "Oui"]
        N["expReverse"], N["expYes"] = str(sum(x["q3"] == "Inverse la règle" for x in yes)), str(len(yes))
        N["expLexUnidiom"] = str(sum(x["q1"] <= 2 for x in lex))
        N["expCtrlUnidiom"] = str(sum(x["q1"] <= 2 for x in neu + par))
        N["expCtrlN"] = str(len(neu + par))
        N["expTotal"] = str(len(L))
        N["expBugsSample"] = str(sum(x["q3"] == "Autre" for x in lex))


def main():
    tab_examples(); tab_glossary(); tab_prompts()
    E4 = load("exp4_challenge.json")["rows"]
    E9 = load("exp9_revision_stats.json")
    A = E9["A_lexflip"]
    tab_challenge(A, E4)
    audit_and_bugs()
    tab_rules(E9["B_rules"], A)

    N["nSingular"] = str(E9["A_n_singular_scope"])
    N["maxSingularShift"] = "%.3f" % max(abs(a["margin_no_singular"] - a["margin"]) for a in A.values())
    N["nliMarginLo"], N["nliMarginHi"] = ["%.3f" % x for x in A[NLI]["margin_ci"]]
    N["judgeMarginLo"], N["judgeMarginHi"] = ["%.3f" % x for x in A[JUDGE]["margin_ci"]]
    N["nliMarginTone"], N["nliMarginTtwo"] = "%.3f" % A[NLI]["margin_t1"], "%.3f" % A[NLI]["margin_t2"]
    N["judgeMarginTtwo"] = "%.3f" % A[JUDGE]["margin_t2"]
    sim_t2 = [A[k]["margin_t2"] for k in SIM]
    N["simMarginTtwoLo"], N["simMarginTtwoHi"] = "%.3f" % min(sim_t2), "%.3f" % max(sim_t2)
    N["judgeTies"] = "%.1f" % (100 * A[JUDGE]["ties"])
    N["lenTies"] = "%.1f" % (100 * A["surface: -|len diff|"]["ties"])
    C = E9.get("C_unrelated_sensitivity", {})
    if NLI in C:
        N["nliUnrelLo"], N["nliUnrelHi"] = "%.3f" % C[NLI]["min"], "%.3f" % C[NLI]["max"]
        sims = [C[k] for k in SIM if k in C]
        N["simUnrelLo"] = "%.3f" % min(c["min"] for c in sims)
        N["simUnrelHi"] = "%.3f" % max(c["max"] for c in sims)
        N["nUnrelDraws"] = str(len(C[NLI]["margins"]) - 1)
    D = E9["D_frjudge"]
    tab_significance(D)
    N["holmMaxP"] = "%.3f" % max(t["p_holm"] for t in D["williams"])
    cl = D["cluster"]
    flau = cl["BERTScore-FlauBERT"]
    N["lenMinusFlau"] = "%.3f" % flau["len_minus_m"]
    N["lenMinusFlauLo"], N["lenMinusFlauHi"] = ["%.3f" % x for x in flau["len_minus_m_ci_cluster"]]
    ln = cl["surface: -|len diff|"]
    N["lenRclLo"], N["lenRclHi"] = ["%.2f" % x for x in ln["ci_cluster"]]
    N["lenRitLo"], N["lenRitHi"] = ["%.2f" % x for x in ln["ci_item"]]
    n_sig = sum(1 for k, v in cl.items() if k in SIM + [NLI, "NLI-fwd (no hallucination)", "NLI-bwd (no omission)"]
                and v["len_minus_m_ci_cluster"][0] > 0)
    N["nClusterSig"] = str(n_sig)
    Epw = E9["E_power"]
    N["powerRtwothree"] = "%.2f" % Epw["median_r_m_ell"]
    N["powerBelow"] = "%.2f" % Epw["largest_r_detectably_below_base"] if Epw.get("largest_r_detectably_below_base") == Epw.get("largest_r_detectably_below_base") else MISSING
    if "smallest_r_detectably_above_base" in Epw:
        N["powerAbove"] = "%.2f" % Epw["smallest_r_detectably_above_base"]
    F = E9["F_ceiling"]
    N["ceilTest"] = "%.3f" % F["ceiling_test_mean"]
    for k, mac in [("Surface-Ridge (supervised, 10 feats)", "ridgeRfour"), ("surface: -|len diff|", "lenRfour"),
                   (JUDGE, "judgeRfour"), ("BERTScore-FlauBERT", "flauRfour")]:
        N[mac] = "%.3f" % F["metrics"][k]["r4"]
    G = E9["G_buckets"]
    for nm in ("small", "medium", "large"):
        N["lenBucketLo" + nm.capitalize()], N["lenBucketHi" + nm.capitalize()] = \
            ["%.2f" % x for x in G["length"][nm]["ci"]]
    N["labseMedLo"], N["labseMedHi"] = ["%.2f" % x for x in G["LaBSE"]["medium"]["ci"]]
    N["flauMedLo"], N["flauMedHi"] = ["%.2f" % x for x in G["BERTScore-FlauBERT"]["medium"]["ci"]]

    # judge call ledger, from the cache files themselves
    calls = {"deepseek-chat": 0, "deepseek-reasoner": 0, "llama": 0}
    for f in glob.glob(os.path.join(RES, "llm_cache", "*.jsonl")):
        b = os.path.basename(f)
        if b.startswith(("smoke", "sanity")):
            continue
        n = sum(1 for l in open(f, encoding="utf-8") if l.strip())
        calls["deepseek-reasoner" if "reasoner" in b else ("llama" if "Llama" in b else "deepseek-chat")] += n
    N["judgeCallsTotal"] = "{:,}".format(calls["deepseek-chat"] + calls["deepseek-reasoner"]).replace(",", "{,}")
    N["llamaCalls"] = "{:,}".format(calls["llama"]).replace(",", "{,}")
    led = json.load(open(os.path.join(RES, "llm_cache", "spend_ledger.json")))
    N["judgeCostTotal"] = "%.2f" % led["_total"]
    N["judgeDateFirst"] = "3~September 2026"   # earliest DeepSeek cache write (git log, cache mtimes)
    N["judgeDateLast"] = "3~September 2026"
    N["judgeDateRev"] = datetime.date.today().strftime("%-d~%B %Y")

    S8 = load("exp8_specificity.json")
    if S8:
        tab_specificity(S8)
        R = S8["rows"]
        N["nNeutral"] = str(S8["cells"].get("neutral", 0))
        if "paraphrase" in S8["cells"]:
            N["nPara"] = str(S8["cells"]["paraphrase"])
        for k, mac in [(NLI, "nli"), (JUDGE, "judge"), (LLAMA, "llama")]:
            for cell, cm in [("neutral", "Neutral"), ("paraphrase", "Para")]:
                if k in R and cell in R[k]:
                    N[mac + cm + "Drop"] = neg0("%.3f" % R[k][cell]["drop"])
                    N[mac + cm + "Sel"] = neg0("%.3f" % R[k][cell]["selectivity"])
                    N[mac + cm + "SelLo"], N[mac + cm + "SelHi"] = [neg0("%.2f" % x) for x in R[k][cell]["selectivity_ci"]]
                    N[mac + cm + "DropLo"], N[mac + cm + "DropHi"] = [neg0("%.3f" % x) for x in R[k][cell]["drop_ci"]]
        for cell, cm in [("neutral", "Neutral"), ("paraphrase", "Para")]:
            d = [R[k][cell]["drop"] for k in SIM if cell in R.get(k, {})]
            if d:
                N["sim" + cm + "DropLo"], N["sim" + cm + "DropHi"] = "%.3f" % min(d), "%.3f" % max(d)
                s = [R[k][cell]["selectivity"] for k in SIM]
                N["sim" + cm + "SelLo"], N["sim" + cm + "SelHi"] = neg0("%.3f" % min(s)), neg0("%.3f" % max(s))
        if NLI in R and "neutral" in R[NLI]:
            N["nliNulNe"] = neg0("%.3f" % R[NLI]["neutral"]["per_rule"]["nul_ne"]["drop"])
    from augment import _tok
    import specificity as SP
    NE = SP.neutral_edits(P.SOURCES)
    J = [len(set(_tok(P.SOURCES[i])) & set(_tok(e))) / len(set(_tok(P.SOURCES[i])) | set(_tok(e))) for i, e, _ in NE]
    N["neutralJaccard"] = "%.2f" % np.mean(J)
    try:
        import gen_paraphrases as G
        PA = G.load()
        Jp = [len(set(_tok(P.SOURCES[i])) & set(_tok(p))) / len(set(_tok(P.SOURCES[i])) | set(_tok(p))) for i, p in PA]
        N["paraJaccard"] = "%.2f" % np.mean(Jp)
        N["nPara"] = str(len(PA))
    except FileNotFoundError:
        pass
    import csv
    ak = os.path.join(ROOT, "audit", "audit_key.csv")
    if os.path.exists(ak):
        N["nAudit"] = str(sum(1 for _ in csv.DictReader(open(ak))))

    E10 = load("exp10_judge_controls.json")
    if E10:
        for tag, mac in (("deepseek", "ds"), ("llama", "llama")):
            if tag not in E10:
                continue
            e = E10[tag]
            N[mac + "AsymFwdWeaken"] = "%.2f" % e["forward_asym"]["doit_to_peut"]
            N[mac + "AsymFwdStrengthen"] = "%.2f" % e["forward_asym"]["peut_to_doit"]
            N[mac + "AsymSwWeaken"] = "%.2f" % e["swapped_asym"]["doit_to_peut"]
            N[mac + "AsymSwStrengthen"] = "%.2f" % e["swapped_asym"]["peut_to_doit"]
            N[mac + "AsymFwdGap"] = "%.2f" % e["forward_asym"]["gap"]
            N[mac + "AsymSwGap"] = "%.2f" % e["swapped_asym"]["gap"]
            N[mac + "OrderR"] = "%.2f" % e["order_effect_r"]
            if tag == "llama":
                for k in ("r_cal", "margin", "identical", "lexflip", "unrelated", "mean_rating", "margin_t1"):
                    N["llama" + k.replace("_t1", "tone").replace("_", "").capitalize()] = ("%.2f" if k in ("identical", "lexflip", "unrelated", "mean_rating") else "%.3f") % e[k]
                N["llamaRcalSd"] = "%.3f" % e["r_cal_sd"]
                N["llamaTies"] = "%.1f" % (100 * e["ties"])
                N["llamaDiscrim"] = "%.1f" % (100 * e["discrim"])
    E5 = load("exp5_llm_judge.json")
    E7 = load("exp7_panel.json")
    num = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", open(os.path.join(ROOT, "paper", "numbers.tex")).read()))
    N.setdefault("repRcalTwo", num.get("repRcalTwo", MISSING)); N.setdefault("repMarginTwo", num.get("repMarginTwo", MISSING))
    N.setdefault("judgeKfiveRaw", num.get("judgeKfive", MISSING))
    E5h = dict(r=float(num["judgeR"]), m=float(num["judgeMargin"]))
    E5b = load("exp5b_replication.json")
    tab_judge_configs(E7, E10, E5h)

    E3b = load("exp3b_indist.json")
    if E3b:
        tab_indist(E3b)
        def mean(key, f):
            v = [f(r) for r in E3b.get(key, [])]
            v = [x for x in v if not (isinstance(x, float) and np.isnan(x))]
            return float(np.mean(v)) if v else float("nan")
        for key, mac in (("JudgeBERT (repro)|vary=both", "Scalar"), ("JudgeBERT-DA (repro)|vary=both", "Da"),
                         ("JudgeBERT-DA+LexFlip|vary=both", "Dalf")):
            N["ind" + mac + "Ident"] = "%.2f" % mean(key, lambda r: r["frjudge"]["ident_mean"])
            N["ind" + mac + "Unrel"] = "%.2f" % mean(key, lambda r: r["frjudge"]["unrel_mean"])
            N["ind" + mac + "Edit"] = "%.2f" % mean(key, lambda r: r["frjudge"]["edit_mean"])
            N["ind" + mac + "Margin"] = "%.2f" % mean(key, lambda r: r["frjudge"]["margin_frac"])
        for vary, mac in (("split", "Split"), ("init", "Init")):
            r = [x["r"] for x in E3b.get("JudgeBERT (repro)|vary=" + vary, [])]
            if len(r) >= 2:
                N["seedSd" + mac] = "%.3f" % np.std(r, ddof=1)
                N["seedN" + mac] = str(len(r))

    # every macro the revision uses must exist; unknown ones print as ??
    used = set(re.findall(r"\\([A-Za-z]+)", open(os.path.join(ROOT, "paper", "jcllt_revision.tex")).read()))
    expected = {"llamaIdentical", "llamaLexflip", "llamaMargin", "llamaRcal", "llamaRcalSd", "llamaUnrelated",
                "nUnrelDraws", "nliUnrelHi", "nliUnrelLo", "simUnrelHi", "simUnrelLo",
                "dsAsymFwdWeaken", "dsAsymFwdStrengthen", "dsAsymSwWeaken", "dsAsymSwStrengthen",
                "dsAsymFwdGap", "dsAsymSwGap", "nSingular", "maxSingularShift", "nNeutral", "neutralJaccard", "nPara", "paraJaccard", "nAudit",
                "judgeDateFirst", "judgeDateLast", "judgeDateRev", "judgeCallsTotal", "judgeCostTotal",
                "powerRtwothree", "powerBelow"}
    for k in sorted((used & expected) - set(N)):
        N[k] = MISSING
    with open(os.path.join(ROOT, "paper", "numbers_rev.tex"), "w") as f:
        for k, v in N.items():
            if k in num:          # already defined by numbers.tex
                continue
            f.write("\\newcommand{\\%s}{%s}\n" % (k, v))
    missing = [k for k, v in N.items() if v == MISSING]
    print("numbers_rev.tex: %d macros, %d missing: %s" % (len(N), len(missing), missing))


if __name__ == "__main__":
    main()
