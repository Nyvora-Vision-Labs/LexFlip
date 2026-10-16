# References added or corrected in the JCLLT revision (manuscript #12050)

Every entry below was checked on 2026-10-16 against its source record (ACL
Anthology BibTeX, arXiv API, Crossref, CanLII) rather than a search snippet.
Each note says which reviewer asked for it and which claim in the revised paper
it supports. Entries that could not be fetched from a source record are not
listed and are not cited.

## Corrections to existing entries

**BERTScore (was arXiv preprint, now ICLR 2020).** Zhang, T., Kishore, V., Wu,
F., Weinberger, K. Q., & Artzi, Y. (2020). BERTScore: Evaluating text
generation with BERT. *International Conference on Learning Representations.*
Source: arXiv 1904.09675v3, author comment "To appear in ICLR2020". Asked by
Reviewer A.

**Krippendorff (was 1996, publisher "TPB").** Krippendorff, K. (2019). *Content
analysis: An introduction to its methodology.* SAGE.
https://doi.org/10.4135/9781071878781. Source: Crossref record for that DOI
(SAGE Publications, issued 2019, ISBN 9781506395661). Asked by Reviewers A
(edition) and D (publisher). Supports the ordinal-alpha computation in the
ceiling section.

**Reference [15] for the rubric.** The ten-point, deduct-per-error rubric is
the FrJudge annotation protocol, so the prompted-judge section now cites
Beauchemin et al. (2025) [JudgeBERT] for it, and keeps Enguehard et al. (2025)
[LeMAJ] only for the general idea of a legal LLM-as-a-judge. Asked by Reviewer D.

**Reference [20] (the arXiv preprint of this article) removed from the list.**
The prior posting is still disclosed in the Acknowledgement, with its arXiv
identifier written out, which satisfies the journal's prior-publication policy
without a self-citation in the reference list. Asked by Reviewers A and D.

## New entries: behavioural testing, minimal pairs, metric blind spots

**Ribeiro, M. T., Wu, T., Guestrin, C., & Singh, S. (2020).** Beyond accuracy:
Behavioral testing of NLP models with CheckList. *Proceedings of the 58th
Annual Meeting of the ACL*, 4902–4912. https://doi.org/10.18653/v1/2020.acl-main.442.
Introduces minimum-functionality, invariance and directional tests. LexFlip is
a directional test; the new neutral cell is an invariance test. Reviewers A, D.

**Gardner, M., Artzi, Y., Basmov, V., … Zhou, B. (2020).** Evaluating models'
local decision boundaries via contrast sets. *Findings of EMNLP 2020*,
1307–1323. https://doi.org/10.18653/v1/2020.findings-emnlp.117. Small,
label-changing manual perturbations of test items. LexFlip is a contrast set
for legal force, built by rule rather than by hand. Reviewers A, D.

**Zhang, Y., Baldridge, J., & He, L. (2019).** PAWS: Paraphrase adversaries
from word scrambling. *Proceedings of NAACL-HLT 2019*, 1298–1308.
https://doi.org/10.18653/v1/N19-1131. High-overlap non-paraphrases; the
nearest precedent for holding overlap fixed while meaning moves. Reviewer D.

**Naik, A., Ravichander, A., Sadeh, N., Rose, C., & Neubig, G. (2018).**
Stress test evaluation for natural language inference. *Proceedings of COLING
2018*, 2340–2353. NLI stress tests including negation and antonymy; bears on
the limitation that NLI may know the *form* of these edits. Reviewer D.

**Sai, A. B., Dixit, T., Sheth, D. Y., Mohan, S., & Khapra, M. M. (2021).**
Perturbation CheckLists for evaluating NLG evaluation metrics. *Proceedings of
EMNLP 2021*, 7219–7234. https://doi.org/10.18653/v1/2021.emnlp-main.575.
Criterion-specific perturbations for generation metrics; closest prior work to
Section 4.1's finding. Reviewer A.

**He, T., Zhang, J., Wang, T., Kumar, S., Cho, K., Glass, J., & Tsvetkov, Y.
(2023).** On the blind spots of model-based evaluation metrics for text
generation. *Proceedings of ACL 2023 (Long Papers)*, 12067–12097.
https://doi.org/10.18653/v1/2023.acl-long.674. Embedding-based metrics
insensitive to negation and similar errors. Reviewer A.

## New entries: counterfactual augmentation and NLI

**Kaushik, D., Hovy, E., & Lipton, Z. C. (2020).** Learning the difference that
makes a difference with counterfactually-augmented data. *International
Conference on Learning Representations.* Source: arXiv 1909.12434v2, comment
"Published at ICLR 2020". Supports the discussion of DA+LexFlip. Reviewer A, D.

**Huang, W., Liu, H., & Bowman, S. R. (2020).** Counterfactually-augmented SNLI
training data does not yield better generalization than unaugmented data.
*Proceedings of the First Workshop on Insights from Negative Results in NLP*,
82–87. https://doi.org/10.18653/v1/2020.insights-1.13. The negative result our
DA+LexFlip finding echoes. Reviewer A.

**Hossain, M. M., Kovatchev, V., Dutta, P., Kao, T., Wei, E., & Blanco, E.
(2020).** An analysis of natural language inference benchmarks through the
lens of negation. *Proceedings of EMNLP 2020*, 9106–9118.
https://doi.org/10.18653/v1/2020.emnlp-main.732. Negation is underrepresented
in NLI benchmarks; bears on the familiarity limitation. Reviewer A.

## New entries: legal NLP, legal NLI, legal simplification

**Koreeda, Y., & Manning, C. (2021).** ContractNLI: A dataset for
document-level natural language inference for contracts. *Findings of EMNLP
2021*, 1907–1919. https://doi.org/10.18653/v1/2021.findings-emnlp.164. Legal
NLI; notes that negation by exception makes contracts hard. Reviewers A, D.

**Goebel, R., Kano, Y., Kim, M.-Y., Rabelo, J., Satoh, K., & Yoshioka, M.
(2024).** Overview and discussion of the Competition on Legal Information,
Extraction/Entailment (COLIEE) 2023. *The Review of Socionetwork Strategies*,
18, 27–47. https://doi.org/10.1007/s12626-023-00152-0. Source: Crossref. The
statute-entailment task. Reviewer A.

**Garimella, A., Sancheti, A., Aggarwal, V., Ganesh, A., Chhaya, N., &
Kambhatla, N. (2022).** Text simplification for legal domain: Insights and
challenges. *Proceedings of the Natural Legal Language Processing Workshop
2022*, 296–304. https://doi.org/10.18653/v1/2022.nllp-1.28. Legal text
simplification, the application that motivates the paper. Reviewers A, C.

**Guha, N., Nyarko, J., Ho, D. E., Ré, C., Chilton, A., … (2023).** LegalBench:
A collaboratively built benchmark for measuring legal reasoning in large
language models. *arXiv:2308.11462.* Source: arXiv API (40 authors). LLM legal
evaluation, for the broader legal-NLP context Reviewer C asked for. Cited as
the arXiv record because that is the record verified here.

## New entries: simplification evaluation, LLM judges, disagreement, statistics

**Alva-Manchego, F., Scarton, C., & Specia, L. (2021).** The (un)suitability of
automatic evaluation metrics for text simplification. *Computational
Linguistics*, 47(4), 861–889. https://doi.org/10.1162/coli_a_00418. Reviewer D.

**Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z.,
… (2023).** Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. *Advances
in Neural Information Processing Systems, 36* (Datasets and Benchmarks Track).
Source: arXiv 2306.05685v4 comment and the NeurIPS proceedings listing.
Position and verbosity biases of LLM judges; supports the pair-order control.
Reviewer D.

**Plank, B. (2022).** The "problem" of human label variation: On ground truth
in data, modeling and evaluation. *Proceedings of EMNLP 2022*, 10671–10682.
https://doi.org/10.18653/v1/2022.emnlp-main.731. Supports the distributional
and annotator-aware targets. Reviewer D.

**Steiger, J. H. (1980).** Tests for comparing elements of a correlation matrix.
*Psychological Bulletin*, 87(2), 245–251. https://doi.org/10.1037/0033-2909.87.2.245.
Source: Crossref. The original reference for the Williams test as used here.
Reviewer D.

## Legal sources

**Moffatt v. Air Canada, 2024 BCCRT 149.** British Columbia Civil Resolution
Tribunal, decided 14 February 2024, Tribunal Member Christopher C. Rivers.
Source: CanLII. The tribunal found Air Canada liable in negligent
misrepresentation for its chatbot's statement of the bereavement-fare policy
("It should be obvious to Air Canada that it is responsible for all the
information on its website. It makes no difference whether the information
comes from a static page or a chatbot."). Reviewers A and D asked for the full
citation and for "held" to be used with a tribunal in mind.

**Interpretation Act, CQLR c I-16, s 51.** Source: CanLII consolidation. "Whenever
it is provided that a thing 'shall' be done or 'must' be done, the obligation is
imperative; but if it is provided that a thing 'may' be done, its accomplishment
is permissive." Supports the definitional label of the modality rule (doit /
peut), which is 193 of the 373 LexFlip items. Reviewer D asked for it to be
verified and cited.

## Second check of the full list (2026-10-16, afternoon)

All 38 entries were re-checked. 34 were resolved through doi.org/Crossref or
their ACL Anthology record, the two arXiv-only entries (Xu & Jurgens
2601.09065, Yang et al. 2605.01048) and Pacchiardi et al. (2410.11672) through
arXiv, the Interpretation Act s. 51 through CanLII ("Whenever it is provided
that a thing 'shall' be done or 'must' be done, the obligation is imperative;
but if it is provided that a thing 'may' be done, its accomplishment is
permissive."), and Moffatt v. Air Canada (decided 14 February 2024) through
case reports. Authors, titles, venues, volumes and pages matched, with three
corrections:

- **Bean et al.** Year corrected from 2026 to 2025 and pages 19868--19949
  added. NeurIPS 38 is the 2025 proceedings (doi:10.52202/085713-0590).
- **Guha et al. (LegalBench).** Was cited as an arXiv preprint. Now cited as
  published, NeurIPS 36 (2023), Datasets and Benchmarks Track.
- **Peterson et al.** Pages 9616--9625 added (doi:10.1109/ICCV.2019.00971).
