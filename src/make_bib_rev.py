"""Write paper/bib_jcllt_rev.tex: the revision's reference list in APA form,
ordered by first citation in jcllt_revision.tex (the first work cited is [1]).

Existing entries are carried over from bib_jcllt.tex, with the corrections the
reviewers asked for; new entries were each verified against their source record
(see paper/references_revision.md)."""
import os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paper")
old = open(os.path.join(ROOT, "bib_jcllt.tex"), encoding="utf-8").read()
E = dict(re.findall(r"\\bibitem\{([^}]*)\}\s*%?\s*\n(.*?)(?=\n\\bibitem|\n\\end\{thebibliography\})", old, re.S))

E["zhang2019bertscore"] = r"""Zhang, T., Kishore, V., Wu, F., Weinberger, K. Q., \& Artzi, Y. (2020).
BERTScore: Evaluating text generation with BERT. In \textit{International
Conference on Learning Representations}."""
E["krippendorff2004content"] = r"""Krippendorff, K. (2019). \textit{Content analysis: An introduction to its
methodology}. SAGE. \url{https://doi.org/10.4135/9781071878781}"""
# Crossref, doi:10.52202/085713-0590: NeurIPS 38 is the 2025 volume.
E["bean2025construct"] = r"""Bean, A. M., Kearns, R. O., Romanou, A., Hafner, F. S., Mayne, H., Batzner, J.,
Foroutan Eghlidi, N., et al. (2025). Measuring what matters: Construct validity
in large language model benchmarks. \textit{Advances in Neural Information
Processing Systems}, \textit{38}, 19868--19949."""
# Crossref, doi:10.1109/ICCV.2019.00971.
E["peterson2019human"] = r"""Peterson, J. C., Battleday, R. M., Griffiths, T. L., \& Russakovsky, O. (2019).
Human uncertainty makes classification more robust. In \textit{Proceedings of
the IEEE/CVF International Conference on Computer Vision (ICCV)}
(pp.~9616--9625)."""
NEW = {
"moffatt2024": r"""\textit{Moffatt v.\ Air Canada}, 2024 BCCRT 149 (British Columbia Civil
Resolution Tribunal, 14 February 2024).""",
"interpretationact": r"""\textit{Interpretation Act}, CQLR c I-16, s 51 (Quebec).""",
"alvamanchego2021unsuitability": r"""Alva-Manchego, F., Scarton, C., \& Specia, L. (2021). The (un)suitability of
automatic evaluation metrics for text simplification. \textit{Computational
Linguistics}, \textit{47}(4), 861--889. \url{https://doi.org/10.1162/coli_a_00418}""",
"garimella2022legalsimp": r"""Garimella, A., Sancheti, A., Aggarwal, V., Ganesh, A., Chhaya, N., \&
Kambhatla, N. (2022). Text simplification for legal domain: Insights and
challenges. In \textit{Proceedings of the Natural Legal Language Processing
Workshop 2022} (pp.~296--304).""",
"gardner2020contrast": r"""Gardner, M., Artzi, Y., Basmov, V., Berant, J., Bogin, B., Chen, S., Dasigi, P.,
et al. (2020). Evaluating models' local decision boundaries via contrast sets.
In \textit{Findings of the Association for Computational Linguistics: EMNLP
2020} (pp.~1307--1323).""",
"ribeiro2020checklist": r"""Ribeiro, M. T., Wu, T., Guestrin, C., \& Singh, S. (2020). Beyond accuracy:
Behavioral testing of NLP models with CheckList. In \textit{Proceedings of the
58th Annual Meeting of the Association for Computational Linguistics}
(pp.~4902--4912).""",
"zhang2019paws": r"""Zhang, Y., Baldridge, J., \& He, L. (2019). PAWS: Paraphrase adversaries from
word scrambling. In \textit{Proceedings of the 2019 Conference of the North
American Chapter of the Association for Computational Linguistics: Human
Language Technologies} (pp.~1298--1308).""",
"naik2018stress": r"""Naik, A., Ravichander, A., Sadeh, N., Rose, C., \& Neubig, G. (2018). Stress test
evaluation for natural language inference. In \textit{Proceedings of the 27th
International Conference on Computational Linguistics} (pp.~2340--2353).""",
"hossain2020negation": r"""Hossain, M. M., Kovatchev, V., Dutta, P., Kao, T., Wei, E., \& Blanco, E.
(2020). An analysis of natural language inference benchmarks through the lens
of negation. In \textit{Proceedings of the 2020 Conference on Empirical Methods
in Natural Language Processing} (pp.~9106--9118).""",
"sai2021perturbation": r"""Sai, A. B., Dixit, T., Sheth, D. Y., Mohan, S., \& Khapra, M. M. (2021).
Perturbation CheckLists for evaluating NLG evaluation metrics. In
\textit{Proceedings of the 2021 Conference on Empirical Methods in Natural
Language Processing} (pp.~7219--7234).""",
"he2023blindspots": r"""He, T., Zhang, J., Wang, T., Kumar, S., Cho, K., Glass, J., \& Tsvetkov, Y.
(2023). On the blind spots of model-based evaluation metrics for text
generation. In \textit{Proceedings of the 61st Annual Meeting of the
Association for Computational Linguistics (Volume 1: Long Papers)}
(pp.~12067--12097).""",
"goebel2024coliee": r"""Goebel, R., Kano, Y., Kim, M.-Y., Rabelo, J., Satoh, K., \& Yoshioka, M. (2024).
Overview and discussion of the Competition on Legal Information,
Extraction/Entailment (COLIEE) 2023. \textit{The Review of Socionetwork
Strategies}, \textit{18}(1), 27--47.""",
"koreeda2021contractnli": r"""Koreeda, Y., \& Manning, C. (2021). ContractNLI: A dataset for document-level
natural language inference for contracts. In \textit{Findings of the
Association for Computational Linguistics: EMNLP 2021} (pp.~1907--1919).""",
"guha2023legalbench": r"""Guha, N., Nyarko, J., Ho, D. E., R\'e, C., Chilton, A., Narayana, A.,
Chohlas-Wood, A., et al. (2023). LegalBench: A collaboratively built benchmark
for measuring legal reasoning in large language models. \textit{Advances in
Neural Information Processing Systems}, \textit{36} (Datasets and Benchmarks
Track).""",
"zheng2023judging": r"""Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z.,
et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena.
\textit{Advances in Neural Information Processing Systems}, \textit{36}.""",
"steiger1980tests": r"""Steiger, J. H. (1980). Tests for comparing elements of a correlation matrix.
\textit{Psychological Bulletin}, \textit{87}(2), 245--251.""",
"plank2022variation": r"""Plank, B. (2022). The ``problem'' of human label variation: On ground truth in
data, modeling and evaluation. In \textit{Proceedings of the 2022 Conference on
Empirical Methods in Natural Language Processing} (pp.~10671--10682).""",
"kaushik2020counterfactual": r"""Kaushik, D., Hovy, E., \& Lipton, Z. C. (2020). Learning the difference that
makes a difference with counterfactually-augmented data. In
\textit{International Conference on Learning Representations}.""",
"huang2020counterfactual": r"""Huang, W., Liu, H., \& Bowman, S. R. (2020). Counterfactually-augmented SNLI
training data does not yield better generalization than unaugmented data. In
\textit{Proceedings of the First Workshop on Insights from Negative Results in
NLP} (pp.~82--87).""",
}
E.update(NEW)
tex = open(os.path.join(ROOT, "jcllt_revision.tex"), encoding="utf-8").read()
tex = re.sub(r"(?m)^%.*$", "", tex)
keys = []
for m in re.finditer(r"\\cite\{([^}]*)\}", tex):
    for k in m.group(1).split(","):
        k = k.strip()
        if k not in keys:
            keys.append(k)
missing = [k for k in keys if k not in E]
assert not missing, missing
out = ["%% Revision reference list (src/make_bib_rev.py). APA form, in order of first",
       "%% citation, so the first work cited is [1]. paper/references_revision.md",
       "%% records how each added entry was verified.", "", r"\begin{thebibliography}{99}", ""]
for k in keys:
    out += [r"\bibitem{%s} %%" % k, E[k].strip(), ""]
out.append(r"\end{thebibliography}")
open(os.path.join(ROOT, "bib_jcllt_rev.tex"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("%d references written" % len(keys))
