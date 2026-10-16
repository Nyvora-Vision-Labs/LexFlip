"""Figures for the paper.

Every figure is drawn at the size it is printed at, so that \\includegraphics
never rescales it. A figure authored at 6in and dropped into a 3in column has
its type shrunk to half the requested point size, which is why the panel text
used to come out smaller than the caption underneath it. The two widths below
are the ACL a4 geometry (\\columnwidth and \\textwidth) in inches; keeping the
figsize equal to one of them makes width=\\columnwidth a no-op scale of 1.0.
"""
import json, os, sys, collections
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import load_pairs, ANNOTATORS

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "paper", "figs"); os.makedirs(FIG, exist_ok=True)
RES = os.path.join(ROOT, "results")

# \columnwidth = 219.086pt, \textwidth = 455.244pt under acl.sty on a4.
COL_W, FULL_W = 219.086 / 72, 455.244 / 72

# The body font is Times at 10pt and captions at 10pt, so panel text sits at
# 6.5--8pt: small enough to read as figure furniture, large enough to read.
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 7,
    "axes.titlesize": 7.5,
    "axes.labelsize": 7.5,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "xtick.major.pad": 2,
    "ytick.major.pad": 2,
    "axes.labelpad": 2.5,
    "grid.linewidth": 0.5,
    "grid.color": "#dddddd",
    "legend.handletextpad": 0.4,
    "legend.columnspacing": 1.0,
    "legend.borderpad": 0.2,
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "pdf.fonttype": 42,
})

C_STRICT, C_LEN, C_NLI = "#B4432A", "#2A6FB4", "#1F7A5A"
C_GREY, C_FAINT = "#555555", "#999999"


def save(fig, name):
    """Write at exactly the requested figsize; no tight-bbox trim, so the
    LaTeX-side scale factor stays 1.0 and type sizes survive to the page."""
    fig.savefig(os.path.join(FIG, name))
    if os.environ.get("FIG_PNG"):          # 300 dpi copies for the Word build
        os.makedirs(os.path.join(FIG, "png"), exist_ok=True)
        fig.savefig(os.path.join(FIG, "png", name.replace(".pdf", ".png")), dpi=300)
    plt.close(fig)
    print("wrote", name)


# Long metric names are what makes a dot plot outgrow a column, and the tables
# carry the unabbreviated ones, so the figures use short forms throughout.
SHORT = {
    "NLI-bidirectional (min)": "NLI-bidirectional",
    "NLI-fwd (no hallucination)": "NLI-fwd",
    "NLI-bwd (no omission)": "NLI-bwd",
    "LLM-judge (deepseek-chat, k=5)": "LLM-judge",
    "surface: token Jaccard": "token Jaccard",
    "surface: -|len diff|": "$-|\\,|s|-|o|\\,|$",
    "BERTScore-CamemBERTv2-Recall": "BERTScore-CmBv2-R",
    "BERTScore-CamemBERTv2": "BERTScore-CmBv2",
    "Sentence-CamemBERT": "Sent-CamemBERT",
}


def fig_disagreement():
    P = load_pairs()
    M = np.array([[p["ratings"][a] for a in ANNOTATORS] for p in P], float)
    means = M.mean(0)
    fig, ax = plt.subplots(1, 3, figsize=(FULL_W, 1.95), layout="constrained")
    # (a) per-annotator rating histograms
    for i, a in enumerate(ANNOTATORS):
        c = C_LEN if means[i] > 6 else C_STRICT
        h = np.bincount(M[:, i].astype(int), minlength=11)[1:]
        ax[0].plot(range(1, 11), h, marker="o", ms=2.5, lw=1.0, color=c, alpha=.85,
                   label=f"{a} ({means[i]:.1f})")
    ax[0].set_xlabel("legal meaning rating"); ax[0].set_ylabel("items")
    ax[0].set_title("(a) two annotator populations")
    ax[0].set_xticks([2, 4, 6, 8, 10])
    ax[0].legend(fontsize=6, frameon=False, ncol=2, loc="upper center",
                 handlelength=1.2, labelspacing=.25, borderaxespad=.1)
    ax[0].margins(y=.22)
    # (b) spread per item
    rng = np.sort(M.max(1) - M.min(1))
    ax[1].fill_between(np.arange(len(rng)) / len(rng) * 100, rng, step="pre",
                       color="#bbbbbb", lw=0)
    ax[1].axhline(6, ls="--", lw=.9, color=C_STRICT)
    ax[1].set_xlabel("percentile of items"); ax[1].set_ylabel("max $-$ min rating")
    ax[1].set_title("(b) within-item disagreement")
    ax[1].set_xlim(0, 100); ax[1].set_ylim(0, rng.max() + 1.4)
    ax[1].text(2, 6.35, f"{(rng>=6).mean()*100:.0f}% span $\\geq$6 pts",
               fontsize=6.2, color=C_STRICT, va="bottom")
    # (c) ceiling vs reported
    e = json.load(open(os.path.join(RES, "exp1_ceiling.json")))
    loo = [v["r"] for v in e["leave_one_annotator_out"].values()]
    sb = np.sqrt(e["spearman_brown_reliability_k5"])
    vals = [e["ceiling_r"], e["best_human_pair"]["r"]]
    ax[2].barh(["single annotator\n(ceiling)", "best annotator\npair"], vals,
               color="#bbbbbb", height=.45)
    ax[2].errorbar([e["ceiling_r"]], [0],
                   xerr=[[e["ceiling_r"] - min(loo)], [max(loo) - e["ceiling_r"]]],
                   fmt="none", ecolor="#333333", capsize=2, lw=.8)
    # the two reference lines the section argues should both be reported
    ax[2].axvline(0.74, color=C_STRICT, lw=1.2)
    ax[2].axvline(sb, color=C_GREY, lw=1.0, ls=(0, (3, 2)))
    ax[2].set_ylim(-0.55, 2.15)
    ax[2].text(0.725, 1.5, "JudgeBERT\nreported 0.74", fontsize=6, color=C_STRICT,
               ha="right", va="center", linespacing=1.3)
    ax[2].text(sb + 0.02, 1.5, "aggregate\nallows %.2f" % sb, fontsize=6, color=C_GREY,
               ha="left", va="center", linespacing=1.3)
    for j, v in enumerate(vals):
        ax[2].text(0.02, j, f"{v:.3f}", fontsize=6.2, color="#222222", va="center",
                   ha="left")
    ax[2].set_xlim(0, 1.0); ax[2].set_xlabel("Pearson $r$ with consensus")
    ax[2].set_title("(c) the human ceiling")
    ax[2].tick_params(axis="y", length=0)
    for a in ax:
        a.spines["left"].set_color("#666666"); a.spines["bottom"].set_color("#666666")
    save(fig, "disagreement.pdf")


def fig_challenge():
    f = os.path.join(RES, "exp4_challenge.json")
    if not os.path.exists(f):
        print("skip challenge fig"); return
    c = json.load(open(f))["rows"]
    order = sorted(c, key=lambda k: -c[k]["margin_frac"])
    # one row per metric plus fixed furniture: legend, axis label, margin header
    fig, ax = plt.subplots(figsize=(COL_W, 0.175 * len(order) + 0.90),
                           layout="constrained")
    yy = np.arange(len(order))
    for j, k in enumerate(order):
        v = c[k]
        ax.plot([v["unrelated"], v["identical"]], [j, j], color="#d5d5d5", lw=2.4,
                zorder=1, solid_capstyle="round")
        ax.scatter(v["unrelated"], j, s=11, color="#444444", zorder=3)
        ax.scatter(v["identical"], j, s=11, color=C_LEN, zorder=3)
        ax.scatter(v["lexflip"], j, s=24, marker="D", color=C_STRICT, zorder=4,
                   edgecolor="white", linewidth=.5)
    # margin value in a gutter to the right of the plotting range
    for j, k in enumerate(order):
        ax.text(1.10, j, f"{c[k]['margin_frac']:.2f}", fontsize=6, va="center",
                ha="left", color="#222222",
                fontweight="bold" if c[k]["margin_frac"] > 0.2 else "normal")
    ax.text(1.10, -0.95, "margin", fontsize=6, va="center", ha="left", style="italic",
            color=C_GREY)

    # separate the family that reacts to the edit from the family that does not
    cut = sum(1 for k in order if c[k]["margin_frac"] > 0.2)
    if 0 < cut < len(order):
        # The rule alone carries the split. An inline caption for it has to sit
        # in a 12pt gap between two rows whose markers run the width of the
        # axes, and at any size that fits it lands on one of them; the caption
        # names the two families instead.
        ax.axhline(cut - 0.5, color=C_FAINT, lw=.7, ls=(0, (4, 3)), zorder=2, xmax=.79)

    ax.set_yticks(yy)
    ax.set_yticklabels([SHORT.get(k, k) for k in order], fontsize=6.2)
    ax.invert_yaxis(); ax.set_xlabel("normalised score")
    ax.set_xlim(-0.03, 1.30)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.spines["bottom"].set_bounds(0, 1.0)
    ax.tick_params(axis="y", length=0)
    ax.scatter([], [], s=11, color=C_LEN, label="identical")
    ax.scatter([], [], s=24, marker="D", color=C_STRICT, label="legal edit")
    ax.scatter([], [], s=11, color="#444444", label="unrelated")
    ax.legend(fontsize=6.2, frameon=False, loc="lower center", bbox_to_anchor=(.42, 1.0),
              ncol=3, handletextpad=.2, columnspacing=.9, borderaxespad=.1)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#666666")
    save(fig, "challenge.pdf")


def fig_dissociation(revision=False):
    """Corpus correlation against LexFlip margin.

    The paper's central new claim is that these two orderings come apart, so it
    deserves a picture: every metric is a point, and the axes are the two things
    a practitioner might select a metric on.
    """
    cf = os.path.join(RES, "exp4_challenge.json")
    bf = os.path.join(RES, "exp2_baselines.json")
    if not (os.path.exists(cf) and os.path.exists(bf)):
        print("skip dissociation fig"); return
    C = json.load(open(cf))["rows"]; B = json.load(open(bf))
    ALIAS = {"surface: token Jaccard": "surface: jaccard",
             "surface: -|len diff|": "surface: abs_len_diff"}
    LABEL = {"NLI-bidirectional (min)": "NLI-bidirectional",
             "NLI-fwd (no hallucination)": "NLI-fwd",
             "NLI-bwd (no omission)": "NLI-bwd",
             "LLM-judge (deepseek-chat, k=5)": "LLM-judge",
             "surface: token Jaccard": "token Jaccard",
             "surface: -|len diff|": "$-|\\,|s|-|o|\\,|$"}
    # where to put each label relative to its point, so none lands on another
    # and none lands in the upper-right quadrant the caption points at
    NUDGE = {"NLI-bidirectional": ("left", "center", (7, 0)),
             "NLI-fwd": ("left", "center", (7, 0)),
             "NLI-bwd": ("right", "center", (-7, 0)),
             "LLM-judge": ("right", "center", (-7, 0)),
             "token Jaccard": ("center", "bottom", (0, 6)),
             "$-|\\,|s|-|o|\\,|$": ("center", "bottom", (0, 7))}

    def family(k):
        if "LLM-judge" in k:
            return "judge"
        if "NLI" in k:
            return "nli"
        return "surface" if k.startswith("surface") else "sim"

    pts = []
    for k, v in C.items():
        b = B.get(ALIAS.get(k, k))
        if not b:
            continue
        r = float(np.mean([d["r"] for d in b["per_seed_cal"]]))
        pts.append((k, r, v["margin_frac"], family(k)))
    extra = []
    if revision:
        # Configurations from the judge section that the reviewers asked to see
        # here: the bare-prompt judge (100-edit subsample) and the judge-NLI
        # blend, plus the second judge family when its run exists.
        P7 = json.load(open(os.path.join(RES, "exp7_panel.json")))["configs"]["chat v3 (no taxonomy)"]
        extra.append(("judge, bare prompt", P7["r_cal_mean"], P7["margin_frac"], "open"))
        H = json.load(open(os.path.join(RES, "exp6_hybrid.json")))
        hb = H["run1"]["weighted w*judge+(1-w)*NLI"]
        extra.append(("judge + NLI blend", hb["r_cal_mean"], hb["margin_frac"], "open"))
        e10 = os.path.join(RES, "exp10_judge_controls.json")
        if os.path.exists(e10) and "llama" in json.load(open(e10)):
            L = json.load(open(e10))["llama"]
            pts.append(("Llama judge", L["r_cal"], L["margin"], "judge"))
            LABEL["Llama judge"] = "Llama judge"
            NUDGE["Llama judge"] = ("left", "center", (7, 0))
            # two judges now share the plot, so name each by its family
            LABEL["LLM-judge (deepseek-chat, k=5)"] = "DeepSeek judge"
            NUDGE["DeepSeek judge"] = NUDGE["LLM-judge"]

    COL = {"nli": C_NLI, "sim": C_LEN, "surface": C_STRICT, "judge": "#7A4FA3"}
    MARK = {"nli": "o", "sim": "o", "surface": "o", "judge": "D"}
    LBL = {"sim": "embedding / BERTScore", "surface": "surface feature",
           "nli": "entailment", "judge": "prompted LLM judge"}
    fig, ax = plt.subplots(figsize=(COL_W, 2.65), layout="constrained")
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)
    for fam in ("sim", "surface", "nli", "judge"):
        xs = [p[1] for p in pts if p[3] == fam]; ys = [p[2] for p in pts if p[3] == fam]
        ax.scatter(xs, ys, s=22, color=COL[fam], label=LBL[fam], zorder=3,
                   marker=MARK[fam], edgecolor="white", linewidth=.6)
    if revision:
        ceil = json.load(open(os.path.join(RES, "exp1_ceiling.json")))
        cr = ceil.get("ceiling_r", ceil.get("ceiling", {}).get("r")) if isinstance(ceil, dict) else None
        cr = 0.597 if cr is None else cr
        ax.axvline(cr, color=C_FAINT, lw=.7, ls="--", zorder=1)
        ax.axhline(0.5, color=C_FAINT, lw=.7, ls="--", zorder=1)
        ax.text(cr + .005, -.01, "human ceiling", fontsize=5.6, color=C_GREY, rotation=90,
                va="bottom", ha="left")
        for name, r, m, _ in extra:
            ax.scatter([r], [m], s=22, facecolor="white", edgecolor="#7A4FA3", linewidth=.9,
                       marker="D", zorder=4)
            ax.annotate(name, (r, m), fontsize=6.0, color="#222222", ha="right", va="center",
                        xytext=(-6, 0), textcoords="offset points")

    # Label the points that carry the argument individually. The seven
    # embedding metrics sit on top of each other along the floor, so they are
    # bracketed as a group rather than labelled into an unreadable pile.
    for k, r, m, fam in pts:
        if k not in LABEL:
            continue
        t = LABEL[k]
        ha, va, off = NUDGE[t]
        ax.annotate(t, (r, m), fontsize=6.2, color="#222222", ha=ha, va=va,
                    xytext=off, textcoords="offset points")
    sim = [(r, m) for _, r, m, f in pts if f == "sim"]
    x0, x1 = min(p[0] for p in sim), max(p[0] for p in sim)
    ax.annotate("", xy=(x0 - .012, -.055), xytext=(x1 + .012, -.055),
                arrowprops=dict(arrowstyle="-", color=C_FAINT, lw=.8,
                                shrinkA=0, shrinkB=0))
    for xx in (x0 - .012, x1 + .012):
        ax.plot([xx, xx], [-.055, -.040], color=C_FAINT, lw=.8, zorder=1)
    ax.text((x0 + x1) / 2, -.072,
            f"{len(sim)} embedding / BERTScore metrics\n"
            f"margin {min(p[1] for p in sim):.2f}–{max(p[1] for p in sim):.2f}",
            fontsize=6, color=C_GREY, ha="center", va="top", style="italic",
            linespacing=1.25)

    ax.set_xlabel("Pearson $r$ with the human label (calibrated)")
    ax.set_ylabel("LexFlip margin")
    ax.set_ylim(-0.21, 0.76); ax.set_xlim(0.18, 0.82)
    ax.set_yticks([0, .2, .4, .6])
    ax.set_xticks([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    ax.spines["bottom"].set_bounds(0.18, 0.82)
    ax.spines["left"].set_bounds(0.0, 0.70)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#666666")
    ax.legend(fontsize=6.2, frameon=False, loc="lower left", ncol=2,
              bbox_to_anchor=(-0.02, 1.0), handletextpad=.2, labelspacing=.3,
              columnspacing=.8, borderaxespad=0)
    save(fig, "dissociation_rev.pdf" if revision else "dissociation.pdf")


# The teaser example. Selected by matching the source text rather than by index
# so that it survives a regeneration of the edit set, and chosen because its
# three scores all sit within 0.6 SD of the mean over the 373 edits: it is a
# typical item, not the most flattering one.
TEASER_SRC = ("L\u2019agent de la paix doit remettre le certificat au "
              "conducteur d\u00e8s qu\u2019il l\u2019a examin\u00e9.")


def _teaser_scores():
    """Per-item and corpus-mean scores for the teaser example.

    Rebuilds exp4's probe pool under the same seed, so the row order of the
    cached score arrays is the one exp4 wrote them in.
    """
    import pickle
    from augment import lexflip_edits, _sents
    ref = _sents("A-25.jsonl") + _sents("code_securite_routiere.jsonl")
    rng = np.random.default_rng(7)
    pool = [ref[i] for i in rng.choice(len(ref), size=400, replace=False)]
    ED = lexflip_edits(pool, seed=7, per_sentence=1)
    n = len(ED)
    idx = [i for i, (o, _, _) in enumerate(ED) if o == TEASER_SRC]
    if not idx:
        raise KeyError("teaser source sentence not in the edit set")
    i = idx[0]
    S = pickle.load(open(os.path.join(RES, "exp4_raw.pkl"), "rb"))
    j = os.path.join(RES, "cache", "llm_judge_exp4.npy")
    if os.path.exists(j):
        S["LLM-judge"] = np.load(j)
    out = {}
    for k, v in S.items():
        v = np.asarray(v, float)
        out[k] = dict(pair=float(v[n + i]), edit=float(v[n:2 * n].mean()),
                      ident=float(v[:n].mean()), unrel=float(v[2 * n:].mean()))
    return ED[i], n, out


def fig_teaser(revision=False):
    """Page-one teaser: one edit, three metrics, two verdicts.

    Drawn in sans on a flat card palette rather than in the body serif the
    other figures use, because it is read as a diagram of an example and not
    as a plot. The face is DejaVu Sans, which ships with matplotlib and is
    free to embed, so the figure regenerates identically anywhere.
    """
    (src, edited, _rule), nedit, S = _teaser_scores()
    import features as F
    from matplotlib.patches import FancyBboxPatch
    jac = F.featurize(src, edited)[F.FEATURE_NAMES.index("jaccard")]

    # Both clauses sit on the same card and both labels on the same slate
    # chip, so nothing but the highlighted word and the scores distinguishes
    # the edit from its source, which is the figure's whole point. Orange is
    # kept for the change itself and for a metric that misses it, green for
    # the one that catches it.
    CARD, SLATE = "#DCE6F3", "#33404A"
    ORANGE, GREEN, INK, MUTED = "#E8712E", "#3E8E68", "#111111", "#6E6A6A"
    SANS = ["DejaVu Sans"]

    # The judge rates on the ten-point rubric scale. Dividing through by that
    # range is the min-max normalisation Table 1 applies to every scorer, and
    # puts all three numbers on one scale the reader can compare.
    def scaled(key, field):
        v = S[key][field]
        return (v - 1.0) / 9.0 if key == "LLM-judge" else v

    ROWS = [("BERTScore-CamemBERTv2", "BERTScore", False),
            ("LLM-judge", "LLM-judge", False),
            ("NLI-bidirectional (min)", "NLI", True)]
    ROWS = [r for r in ROWS if r[0] in S]

    # Laid out in inches measured down from the top edge; xlim is the figure
    # width in inches, so one data unit is one inch and a text extent in
    # pixels converts by the figure dpi.
    W, H = COL_W, 2.83
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(0, W); ax.set_ylim(0, H)
    TOP = 0.06                       # room between the frame and the first chip
    Y = lambda v: H - v - TOP
    rend = fig.canvas.get_renderer()
    X0, X1 = 0.10, W - 0.10          # card edges
    TX = X0 + 0.11                   # text inset

    def card(y0, y1, face, x0=X0, x1=X1, z=1, radius=0.055, edge="none",
             lw=0.0):
        ax.add_patch(FancyBboxPatch((x0, Y(y1)), x1 - x0, y1 - y0,
                                    boxstyle="round,pad=0,rounding_size=%g" % radius,
                                    facecolor=face, edgecolor=edge, lw=lw,
                                    zorder=z))

    def _mk(x, y, txt, size, color, kw, z):
        return ax.text(x, Y(y), txt, fontsize=size + kw.get("dsize", 0.0),
                       va="center", ha="left",
                       zorder=z, color=kw.get("color", color), fontfamily=SANS,
                       fontweight=kw.get("weight", "normal"),
                       style=kw.get("style", "normal"))

    def run(x, y, segs, size, color=INK, z=3, fit=None):
        """Draw one line as a sequence of styled runs, left to right.

        A single text call cannot mix weights, and the one word the edit
        changes is what the figure exists to point at, so the line is measured
        piece by piece and the pieces are placed by hand. With `fit` the whole
        line is measured first and the size stepped down until it fits.
        """
        segs = [(s[0], s[1] if len(s) > 1 else {}) for s in segs]
        while fit is not None:
            w, probe = 0.0, []
            for txt, kw in segs:
                t = _mk(0, y, txt, size, color, kw, z)
                w += t.get_window_extent(renderer=rend).width / fig.dpi
                w += kw.get("pad", 0.0)
                probe.append(t)
            for t in probe:
                t.remove()
            if w <= fit or size <= 5.4:
                break
            size -= 0.15
        spans = {}
        for txt, kw in segs:
            t = _mk(x, y, txt, size, color, kw, z)
            w = t.get_window_extent(renderer=rend).width / fig.dpi
            spans[txt] = (x, x + w)
            x += w + kw.get("pad", 0.0)
        return x, spans

    CL, GL = 7.0, 6.2                # clause and gloss sizes
    SP = 0.028                       # an inter-run space at the clause size
    AVAIL = X1 - TX - 0.05

    # A frame around the whole figure, inset from the edge so the rounded
    # corner is not clipped by the crop.
    ax.add_patch(FancyBboxPatch((0.025, 0.025), W - 0.05, H - 0.05,
                                boxstyle="round,pad=0,rounding_size=0.075",
                                facecolor="none", edgecolor="#B7C0CA", lw=0.8,
                                zorder=6))

    def pill(span, y, h=0.145):
        """A white slot behind the one word the two clauses differ in."""
        card(y - h / 2, y + h / 2, "white", x0=span[0] - 0.035,
             x1=span[1] + 0.035, z=2, radius=0.03)

    def chip(y, label):
        """A slate label sitting above the card it names."""
        _, sp = run(TX, y + 0.11, [(label, dict(weight="bold"))], 6.2, "white",
                    z=4)
        card(y, y + 0.22, SLATE, x1=sp[label][1] + 0.13, z=3, radius=0.045)

    # -- the source clause -------------------------------------------------
    chip(0.04, "QUEBEC HIGHWAY SAFETY CODE")
    card(0.32, 0.78, CARD)
    _, sp = run(TX, 0.45, [("L’agent de la paix", dict(pad=SP * 1.9)),
                           ("doit", dict(weight="bold", pad=SP * 2.1)),
                           ("remettre le certificat",)], CL, fit=AVAIL)
    pill(sp["doit"], 0.45)
    run(TX, 0.615, [("au conducteur dès qu’il l’a examiné.",)], CL, fit=AVAIL)
    run(TX, 0.885, [("The peace officer must return the certificate to the",
                     dict(style="italic"))], GL, MUTED, fit=AVAIL)
    run(TX, 0.995, [("driver as soon as they have examined it.",
                     dict(style="italic"))], GL, MUTED, fit=AVAIL)

    # -- the edit ----------------------------------------------------------
    ax.annotate("", xy=(0.30, Y(1.28)), xytext=(0.30, Y(1.10)),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.1,
                                shrinkA=0, shrinkB=0), zorder=4)
    run(0.42, 1.19, [("one word replaced; token Jaccard %.2f" % jac,)], GL,
        ORANGE)

    chip(1.36, "LEGAL FORCE CHANGED" if revision else "LEGAL FORCE REVERSED")
    card(1.64, 2.10, CARD)
    _, sp = run(TX, 1.77, [("L’agent de la paix", dict(pad=SP * 1.9)),
                           ("peut", dict(weight="bold", color=ORANGE,
                                         pad=SP * 2.1)),
                           ("remettre le certificat",)], CL, fit=AVAIL)
    pill(sp["peut"], 1.77)
    run(TX, 1.935, [("au conducteur dès qu’il l’a examiné.",)], CL, fit=AVAIL)
    run(TX, 2.205, [("The officer may return it: the duty has become a",
                     dict(style="italic"))], GL, MUTED, fit=AVAIL)
    run(TX, 2.315, [("discretion, so the clause no longer states the same rule." if revision else
                     "discretion and the clause states the opposite law.",
                     dict(style="italic"))], GL, MUTED, fit=AVAIL)

    # -- what the metrics say ----------------------------------------------
    segs = []
    for i, (key, label, good) in enumerate(ROWS):
        last = i == len(ROWS) - 1
        segs += [(("%s %.3f" if revision else "%s %.2f") % (label, scaled(key, "pair")),
                  dict(weight="bold", pad=SP)),
                 ("✓" if good else "✗",
                  dict(weight="bold", dsize=1.4,
                       color=GREEN if good else ORANGE,
                       pad=0.0 if last else SP * 2.4))]
    run(TX, 2.50, segs, 6.7, fit=AVAIL)
    run(TX, 2.635, [("mean over all %d edits: %s" % (
        nedit, ", ".join(("%.3f" if revision else "%.2f") % scaled(k, "edit") for k, _, _ in ROWS)),)],
        5.9, MUTED, fit=AVAIL)
    save(fig, "teaser_rev.pdf" if revision else "teaser.pdf")


# ------------------------------------------------------------------- driver --
if __name__ == "__main__":
    for fn in (fig_teaser, fig_disagreement, fig_challenge, fig_dissociation):
        try:
            fn()
        except Exception as ex:
            print("skip", fn.__name__, type(ex).__name__, ex)
