## v1.1.0 — empirical revision and submission package

This release revises *When Evidence Sets Become Relevance Lists: A Controlled Audit of Scientific Retrieval Evaluation*. It preserves the original 875 QASPER questions, 209 SciFact pairs, 5,420 rankings and frozen primary results. Historical [v1.0.0](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.0.0) and [its Zenodo record](https://zenodo.org/records/23122620) remain unchanged.

### What changed

- Corrected the 8.2-point sensitivity interpretation and added paired pruning estimates for answer-agreement, complement and full cohorts. This is neither a full-cohort bound nor a causal decomposition.
- Executed a pinned real QASPER converter and actual scorer. Exact mapped union membership holds for 866 questions under an explicit normalized-text/candidate restriction; nine exports omit evidence memberships. Conventional scorer objectives remain appropriate: no objective/implementation mismatch was established.
- Added exact uniform 50/75/90% completion budgets. At 75%, BM25 needs 14 versus 27 QASPER paragraphs and 3 versus 6 SciFact sentences under C versus A.
- Completed the sole added Qwen3-Embedding-0.6B experiment across both full cohorts. C−A is 23.1 points for QASPER and 27.3 for SciFact; median extra depth remains zero. Fixed primary comparisons show no new F1 ranking reversal.
- Expanded primary-source positioning, retained an imperfect deterministically selected real case, updated all prose/data models and bibliography, and produced synchronized official PDFs and reproducibility records.

All new analyses are revision-added exploratory work. Original BM25 gaps (17.8 and 27.8 points), zero extra-depth medians and stable original primary F1 ordering remain. The claim is measurement sensitivity under annotation-defined targets; it is not a new completion criterion, semantic sufficiency, measured user effort or an ecosystem-wide defect estimate.

### Files and reproduction

Use `manuscript_official_style.pdf`, `supplement_official_style.pdf` and `cover_letter.pdf` for submission review. `manuscript_reading_copy.pdf` is for convenient reading. `submission-v1.1.0.zip` includes final documents and supporting submission materials. The source tag additionally contains reproducible code, plans, saved rankings, machine-readable results and audits; source corpora and model weights are acquired separately.

Start with [the revision reproduction guide](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/blob/v1.1.0/docs/revision_v1.1_reproduction.md), `revision_memo.md`, `validation_report.md`, `asset_manifest.json` and `SHA256SUMS`. Main tests: 55 passed/1 optional-dependency skip; that scorer is exercised in its separate environment (10 pipeline/example tests passed). Encoder tests: 8 passed. Isolated saved-ranking replay reproduces 20 table/source files and the four PDFs' page counts/text. Every page of all four final PDFs was visually checked. These are automated local checks, not independent human review or external replication.

### Archiving and scope

The verified [Zenodo concept DOI](https://doi.org/10.5281/zenodo.23122619) identifies the version family; exact tag **v1.1.0** identifies these frozen files. GitHub–Zenodo automatic archiving is enabled. It archives the tag source snapshot, which includes the four final PDFs and submission ZIP; it does not automatically archive arbitrary release attachments. The actual new version DOI and downloaded-content verification will be appended to this landing description after the automatic record exists. Frozen same-version PDFs, ZIP and tag will not be replaced to insert that DOI.

MIT covers original code and CC BY 4.0 covers original scholarly materials, with third-party exclusions retained. The author-confirmed authorship, AI and funding statements are unchanged. This release does not submit the manuscript to IRRJ or predict acceptance.
