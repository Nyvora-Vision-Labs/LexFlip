"""Specificity controls for LEXFLIP: edits that must NOT move a legal metric.

LEXFLIP holds surface form fixed and moves legal force. On its own it cannot
tell a metric that reads the law from one that drops on any edit at all. The
revision adds the two missing cells of the 2x2 design, both built on the same
LEXFLIP source sentences so every comparison is paired:

  neutral     high overlap, force PRESERVED   a single legally inert rewrite
  paraphrase  low overlap,  force PRESERVED   a plain-language rewrite of the
                                              whole sentence (generated on the
                                              cluster, see gen_paraphrases.py)

A metric that reads legal meaning should leave both near the identical pair. A
metric that reacts to any edit will drop on `neutral`; a metric that reads
overlap will drop on `paraphrase`.

The neutral rules below are restricted to substitutions that Quebec statutory
drafting treats as equivalent: subordinators (lorsque / quand), connective
adverbs, deictic self-reference (le present article / cet article), numerals
written out, and two rewrites that touch an obligation or prohibition marker
without changing its force (est tenu de / doit, nul ne peut / personne ne peut).
The last two are flagged as `modal_touching`: they move a token NLI training
data associates with modality, so they are the hardest test of whether a
metric reacts to the token or to the force.
"""
import re, random

_NUM = {1: "un", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq", 6: "six",
        7: "sept", 8: "huit", 9: "neuf", 10: "dix", 12: "douze", 14: "quatorze",
        15: "quinze", 20: "vingt", 21: "vingt et un", 30: "trente",
        45: "quarante-cinq", 60: "soixante", 90: "quatre-vingt-dix"}


def _num_words(s):
    m = re.search(r"\b(\d{1,2}) (jours|mois|ans)\b", s)
    if not m or int(m.group(1)) not in _NUM:
        return None
    w = _NUM[int(m.group(1))]
    if int(m.group(1)) == 1:            # "un jour", not "un jours"
        return None
    return s[:m.start()] + w + " " + m.group(2) + s[m.end():]


def _case(rep):
    """Replacement that keeps the capitalisation of the matched text."""
    def f(m):
        t = m.expand(rep)
        return t[0].upper() + t[1:] if m.group(0)[0].isupper() else t
    return f


# (name, modal_touching, [(pattern, replacement), ...]); first matching
# pattern of a rule is applied once.
NEUTRAL_RULES = [
    ("subordinator", False, [(r"\blorsqu['’]", "quand "), (r"\blorsque\b", "quand")]),
    ("deictic", False, [
        (r"\bdu présent (article|code|chapitre|paragraphe|titre)\b", r"de ce \1"),
        (r"\bau présent (article|code|chapitre|paragraphe|titre)\b", r"à ce \1"),
        (r"\ble présent (article|code|chapitre|paragraphe|titre)\b", r"ce \1"),
        (r"\b(du|au|le) présent alinéa\b", None),       # elision: handled below
        (r"\bde la présente (loi|section|sous-section|partie)\b", r"de cette \1"),
        (r"\bà la présente (loi|section|sous-section|partie)\b", r"à cette \1"),
        (r"\bla présente (loi|section|sous-section|partie)\b", r"cette \1")]),
    ("en_vertu", False, [(r"\ben vertu (de|du|des|d['’])", r"aux termes \1")]),
    ("toutefois", False, [(r"\btoutefois\b", "cependant")]),
    ("au_moins", False, [(r"\bau moins\b(?=\s+(?:\d|un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix)\b)",
                         "au minimum")]),
    ("conformement", False, [(r"\bconformément aux\b", "selon les"),
                             (r"\bconformément au\b", "selon le"),
                             (r"\bconformément à\b", "selon")]),
    ("en_outre", False, [(r"\ben outre\b(?!\s+(?:de|des|du|d['\u2019]))", "de plus")]),
    ("afin", False, [(r"\bafin d['’]", "pour "), (r"\bafin de\b", "pour"),
                     (r"\bafin que\b", "pour que")]),
    ("cas_suivants", False, [(r"\bdans les cas suivants\b", "dans les situations suivantes")]),
    ("il_y_a_lieu", False, [(r"\bs['’]il y a lieu\b", "le cas échéant")]),
    ("tenu_de", True, [(r"\bsont tenue?s d['’]", "doivent "), (r"\bsont tenue?s de\b", "doivent"),
                       (r"\best tenue? d['’]", "doit "), (r"\best tenue? de\b", "doit")]),
    ("nul_ne", True, [(r"\bnul ne\b", "personne ne")]),
]
MODAL_TOUCHING = {name for name, mt, _ in NEUTRAL_RULES if mt}


def neutral_candidates(s):
    out = []
    for name, _, subs in NEUTRAL_RULES:
        for pat, rep in subs:
            if rep is None:
                continue
            if re.search(pat, s, flags=re.IGNORECASE):
                new = re.sub(pat, _case(rep), s, count=1, flags=re.IGNORECASE)
                if new != s:
                    out.append((new, name))
                break
    w = _num_words(s)
    if w:
        out.append((w, "numeral"))
    return out


def neutral_edits(sentences, seed=11):
    """One legally inert edit per sentence where one applies.

    Returns a list of (index_into_sentences, edited, rule). Uses the same
    well-formedness filter as LEXFLIP so the two cells are held to one
    standard.
    """
    from augment import _wellformed
    rng = random.Random(seed)
    out = []
    for i, s in enumerate(sentences):
        c = [(n, r) for n, r in neutral_candidates(s) if _wellformed(n)]
        if c:
            n, r = rng.choice(c)
            out.append((i, n, r))
    return out


if __name__ == "__main__":
    import sys, os, collections
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import probes as P
    from augment import _tok
    NE = neutral_edits(P.SOURCES)
    print("neutral edits: %d / %d sources" % (len(NE), P.n))
    print(collections.Counter(r for _, _, r in NE).most_common())
    J = [len(set(_tok(P.SOURCES[i])) & set(_tok(e))) / len(set(_tok(P.SOURCES[i])) | set(_tok(e)))
         for i, e, _ in NE]
    print("mean Jaccard %.3f  min %.3f" % (sum(J) / len(J), min(J)))
    seen = set()
    for i, e, r in NE:
        if r in seen:
            continue
        seen.add(r)
        print("\n[%s]\n  - %s\n  + %s" % (r, P.SOURCES[i][:160], e[:160]))
