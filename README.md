# When Evidence Sets Become Relevance Lists

**When Evidence Sets Become Relevance Lists: A Controlled Audit of Scientific Retrieval Evaluation**  
Yunya Lin · University of Illinois Urbana-Champaign

Reproducibility package **v1.1.1** for an IRRJ Normal Paper submission manuscript. This is not an accepted journal article. The contribution is an empirical measurement audit, building on established complete-set, sufficient-rank and group-versus-union evaluation.

- **H**: at least one annotated unit retrieved.
- **C**: every unit of at least one original annotated set retrieved.
- **A**: every unit in the union of original annotations retrieved.

Flat qrels support their intended relevance metrics. They do not automatically choose A, and membership alone cannot generally reconstruct C. Annotation completion is not independently certified semantic sufficiency or downstream answer quality.

## Original frozen study

The main cohorts are 875 QASPER questions (367 papers, within-paper paragraphs) and 209 SciFact claim–abstract pairs (164 connected claim/document clusters, within-abstract sentences). BM25, TF-IDF and MiniLM are retrievers; lead and seeded random are controls. Original cohorts, 5,420 complete rankings and 32,520 six-budget points remain unchanged.

| Primary BM25 outcome | QASPER, k=5 | SciFact, k=3 |
|---|---:|---:|
| H | 65.0% | 83.7% |
| C | 51.0% | 79.4% |
| A | 33.1% | 51.7% |
| C−A | 17.8 pp | 27.8 pp |
| Mean extra union depth | 6.65 paragraphs | 2.02 sentences |
| Median extra union depth | 0 | 0 |

No original primary F1 ranking reversal was observed. Zero extra depth occurs in 54.9% and 59.3% of items; costs are unevenly distributed.

## What v1.1 adds and narrows

- **Paired pruning versus cohort selection.** Among 195 exact normalized-answer-agreement questions in 149 papers, C−A is 12.3 points before pruning and 8.2 afterward; paired change −4.1 points (95% cluster interval −7.1 to −1.5). This is neither a full-cohort bound nor a causal estimate of answer disagreement. The 680-question complement is not synonymous with semantic conflict. The subsets share 119 papers.
- **A real converter and scorer.** Pinned sscc-rag-paper conversion and six actual relevance metrics were executed. All 875 main questions intersect the test export; 866 align exactly in union membership under an explicit normalized-text/candidate restriction. Nine exports omit 14 evidence-unit memberships owing to whitespace matching. Native candidates include abstracts and cross-paper distractors; controlled replay retains original normalized body-text units. Duplicate/abstract-ID mappings are disclosed. No whole downstream product was run, and no objective/implementation mismatch was established.
- **Uniform budgets.** For BM25 to complete 75% of QASPER items, C requires 14 paragraphs and A 27; SciFact requires 3 versus 6 sentences. All 50%, 75% and 90% unit/lexical thresholds and paired intervals are retained. These are annotation-defined population budgets, not mean individual costs or measured time.
- **Complete Qwen robustness.** Qwen's complete-cohort C−A gaps are 23.1 points in QASPER and 27.3 in SciFact. The sole predetermined new model completed all 1,084 eligible items using CPU float32, pinned weights/tokenizer, query-only instruction, last-token pooling and normalized 1,024-dimensional vectors. There were 0 truncated unique inputs. The old timing-gate omission remains a historical decision, superseded by this complete run.
- **Deterministic examples and narrower novelty.** The first SHA-ordered qualifying example from 16 candidates is retained even though one paragraph supports the question indirectly. No human semantic validation is claimed. Alt and Li precedents and recent related work are explicitly credited.

Combined original-plus-Qwen totals are 6,504 rankings and 39,024 points at the six original budgets. Added exact integer-budget threshold calculations are separate. All additions are post-main exploratory; no retrospective original preregistration is claimed.

## Reproduce and inspect

Start with [revision reproduction instructions](docs/revision_v1.1_reproduction.md). They provide saved-ranking reconstruction without source text/embeddings and separate source-based/full-inference routes. Python 3.12.14 on ARM64 macOS was used. `requirements.lock.txt`, the encoder lock and the pipeline requirements identify distinct environments. An existing `pdflatex` installation exports official-style PDFs; no TeX software is installed by the build.

```sh
.venv/bin/python src/revision_v3_statistics.py --rankings-only --qwen revisions/v3/encoder/rankings.jsonl
.venv/bin/python src/revision_v3_pipeline.py --summarize-saved
.venv/bin/python src/render_final.py
```

For original acquisition, use `src/prepare.py`; original source-based saved-ranking replay is `src/replay_saved.py` in an empty output directory. To infer original rankings instead, use a separate clean clone with `src/main_study.py`. Do not write into frozen historical outputs. The full analysis/replay, technical configuration and validation evidence are linked in the stream READMEs under `revisions/v3/`.

The editable sources are `paper/article_blocks_1.json`, `article_blocks_2.json` and `supplement_blocks.json`; references are generated from `literature/verified_references.json`. Official and reading versions share one scientific content model. **Use the official manuscript, official supplement and cover letter for submission; the reading copy is for convenience.** See [submission checklist](revisions/v3/submission_checklist.md).

## Files and provenance

`reference_outputs/`, `tables/` and `logs/frozen_main_v1/` retain original results and freeze evidence. `revisions/v2/` retains earlier post-main topology, audit and timing results. `revisions/v3/` contains new protocols, statistics, executed pipeline mappings, encoder rankings/fingerprints, examples, literature comparison, revision memo and QA. `release_artifacts/` contains the submission ZIP, asset manifest and SHA-256 list. `PACKAGE_MANIFEST.json` checks the public tree before reproduction modifies it.

The archive excludes full source corpora, model weights, virtual environments, downloaded project collections, full literature PDFs and private operational material. URLs and acquisition hashes identify those inputs. The local study freeze is not public preregistration; actual public Git history begins with submission preparation.

## Versions and citation

Current package: [v1.1.1 release](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.1.1). Frozen documents cite the verified [Zenodo concept DOI 10.5281/zenodo.23122619](https://doi.org/10.5281/zenodo.23122619) together with the exact tag. The concept DOI identifies the version family. The version-specific DOI is recorded in release notes and publication verification only after automatic archiving succeeds; frozen same-version files are not replaced to insert it.

Historical [v1.0.0](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.0.0), [DOI 10.5281/zenodo.23122620](https://doi.org/10.5281/zenodo.23122620), remains unchanged. Its tag commit is `ed2d6f6ca6f3e17b3b89c593bda5668c83b44e78`. Zenodo automatically archives the tagged source snapshot, not arbitrary GitHub assets; all four PDFs and the submission ZIP are therefore included in the new tag.

## Licensing and responsibility

Code and usage documentation: [MIT](LICENSE). Original scholarly materials and derived results: [CC BY 4.0](LICENSE-CONTENT). Third-party materials retain their own terms; see [LICENSES.md](LICENSES.md). These licenses do not relicense datasets, models, papers or the official journal style. See [CITATION.cff](CITATION.cff).

Author-confirmed authorship, AI and funding disclosures remain unchanged. The human author retains responsibility; no external funding or third-party computational resources were used. Contact: yoyolin2@illinois.edu. IRRJ formal submission has not been performed by this workflow.

## Final patch v1.1.1

This patch corrects the pip-free installation route for the strict frozen encoder environment and three editorial defects. It adds no experiment and preserves the original scientific sources, dependency lock/freeze, inputs, rankings and numerical outputs. The historical substantive revision is [v1.1.0](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.1.0), [DOI 10.5281/zenodo.23125121](https://doi.org/10.5281/zenodo.23125121).

Follow the corrected [encoder setup and read-only preflight](revisions/v3/encoder/README.md#commands). Create a new target without pip, install the unchanged lock from an external installer, and require the complete dependency dictionary to match. Keep analysis, pipeline and encoder environments separate. See the [patch memo](revisions/patch_v1.1.1/patch_memo.md), [patch validation](revisions/patch_v1.1.1/validation_report.md), and [current submission checklist](revisions/patch_v1.1.1/submission_checklist.md). Earlier revision memos and QA records describe their historical executions, not new patch test runs. Fresh installation/preflight does not constitute full-inference replication.

Current patch assets are in [release_artifacts/v1.1.1](release_artifacts/v1.1.1), including the submission ZIP, asset manifest and checksums. Files directly under `release_artifacts/` retain the older v1.1.0 release.

## Verified publication status

**v1.1.1 is published and its remote files are verified.** [GitHub release](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.1.1) · [Zenodo record](https://zenodo.org/records/23126392) · [version DOI 10.5281/zenodo.23126392](https://doi.org/10.5281/zenodo.23126392). All nine release assets match the accepted local files. All **424 files** in the automatic source archive match immutable tag `25654c3cd12f358145b4f50ef4f97bb86101b53a`. See [publication verification](docs/release_verification_v1.1.1.md). The [submission ZIP](release_artifacts/v1.1.1/submission-v1.1.1.zip) contains the final PDFs and patch evidence. Old v1.0.0/v1.1.0 tags/assets and frozen v1.1.1 files remain unchanged. Formal IRRJ submission remains an author action.
