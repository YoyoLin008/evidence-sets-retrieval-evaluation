# Reproduce the v1.1 scientific revision with setup patch v1.1.1

These are revision-added exploratory analyses, planned after the original study and v1.0.0 results were known. The primary cohorts and five original rankings per item remain unchanged. Use a clean clone or copy; do not regenerate historical records in a working archive.

## Saved-ranking route (no source text or inference)

Install the original analysis environment from `requirements.lock.txt` into `.venv` (Python 3.12.14 was used). Then run:

```sh
.venv/bin/python src/revision_v3_statistics.py --rankings-only --qwen revisions/v3/encoder/rankings.jsonl
.venv/bin/python src/revision_v3_pipeline.py --summarize-saved
.venv/bin/python src/revision_v3_release_docs.py
.venv/bin/python src/render_final.py
.venv/bin/python src/qa_final_documents.py --output-dir revisions/patch_v1.1.1/qa/rendered
```

The statistics entry point verifies complete rankings, source-instance hashes, groups, cluster assignments, scores, depth costs, pruning properties, subgroup reconstruction and all fixed budget thresholds. In this route, saved lexical completion costs are derived inputs; source text is not re-tokenized. All original five-method rows retain their original-study role. Qwen contributes 1,084 new rankings and 6,504 points at the six original budgets; combined totals are 6,504 rankings and 39,024 points. Integer-budget threshold analysis is separate from those point totals.

The pipeline summary replay uses the released per-query results from the real scorer. It does not claim to rerun the converter or scorer. Public mapping records and hashes document the original execution. The controlled 866-question comparison uses original normalized body-text units, not the entire native exported task. Ninety questions have duplicate/normalized-equivalent export candidates; four involve gold units. Eight canonical mappings include identical abstract text IDs, one involving gold. These are disclosed mappings under the original normalized-text representation, not evidence of physical paragraph-identity preservation.

`render_final.py` regenerates manuscript/supplement models, bibliography, display tables, editable TeX, official PDFs and the reading copy from the shared prose models. It requires an existing `pdflatex` runtime and the unchanged official `paper/irrj2e.sty`. It installs no TeX software. The native editor remains an editable source/preview route. The reading copy is not the IRRJ upload document. After rebuilding, inspect every rendered page; the automatic document check intentionally leaves visual status pending.

## Source-based verification and new inference

Acquire original inputs using `src/prepare.py`, which checks pinned hashes. `src/replay_saved.py` reconstructs original instances and copies saved original rankings into a new, empty `outputs/main_v1`. Then use the source-text mode:

```sh
.venv/bin/python src/prepare.py
.venv/bin/python src/replay_saved.py
.venv/bin/python src/verify_reproduction.py
.venv/bin/python src/revision_v3_statistics.py --qwen revisions/v3/encoder/rankings.jsonl
.venv/bin/python src/verify_revision_v2.py
```

Source-text mode independently recomputes lexical costs and verifies the original annotation mapping. The historical main retrieval route, if desired, is `src/main_study.py` in a separate clean copy before any saved-ranking replay; keep its cache distinct.

The v1.1.1 patch preserves the scientific outputs and frozen encoder implementation. Its fresh-environment validation checks installation and the exact dependency preflight only; it does not rerun inference or statistics. Create the strict encoder target without pip and install the unchanged lock through an external installer, then run `src/encoder_dependency_preflight.py` with that target interpreter. Do not install analysis/build extras into it. For the tested commands, supported CPython 3.12.14 macOS ARM64 setup, Qwen acquisition and optional full inference, follow `revisions/v3/encoder/README.md` and its exact locked environment. Model/tokenizer revision, query instruction, pooling, normalization, dtype, batch policy and the technical freeze define the run. Use the encoder's documented acquisition, input, technical and inference commands; do not reinterpret the old two-hour gate as a new stopping rule. Cache fingerprints bind text, model/configuration and vectors, and resumption is permitted only for identical frozen inputs/configuration. Its CPU float32 backend follows a failed pre-effectiveness MPS consistency test. Model tokens (limit 8,192) and historical lexical budget tokens are different quantities.

For the real converter/scorer route, follow `revisions/v3/pipeline/README.md`, install its separate `requirements.txt`, and execute `src/revision_v3_pipeline.py`. The script acquires hash-pinned source files and runs the upstream conversion and six actual `ir_measures` objectives. It verifies unchanged dev-loader/wrapper parity before applying the converter to the original test data. Full source exports, downloaded code and environment remain excluded. It does not execute the complete upstream retrieval/generation product.

## Validation and limits

Run the main test suite with the analysis environment; run encoder tests in the separately locked encoder environment and the real-scorer test in the pipeline environment. A skipped optional-dependency test is not reported as a passed scorer execution. Historical release QA reports identify their original executions; current patch checks are recorded separately in `revisions/patch_v1.1.1/validation_report.md`.

Frozen data/code hashes, acquisition hashes, original bootstrap settings (10,000 replicates, seed 20261002), protected declarations, and the original official-style hash must remain unchanged. The added analysis uses paired cluster resampling and item weights; 119 QASPER papers span both answer subgroups. No unobserved/infinite bootstrap outcome is silently dropped. All completed full rankings attain all three specified thresholds here.

Public output files contain derived quantities, unit IDs, minimal licensed quotations and source hashes. Source corpora, weights, full literature PDFs, credentials and virtual environments are excluded. This local replay is not independent replication, human semantic validation or a cross-platform test. Future availability of third-party sources is not guaranteed.
