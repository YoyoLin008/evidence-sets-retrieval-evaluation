# Complete-cohort Qwen robustness experiment (revision v3)

This directory records a revision-added exploratory experiment. It is separate from the frozen original five-method results and the v2 timing-only omission. The v2 files and two-hour gate outcome remain historical records; this revision removes the artificial two-hour gate and runs the selected model for every original eligible item.

`technical_plan.md` is saved before technical sampling or any new effectiveness. `public_technical_summary.json` preserves every field and measurement of the hash-identified original `technical_results.json`, with only local diagnostic path prefixes normalized; the original raw log is retained locally. These records compare only embeddings, elapsed time and memory, without gold labels or retrieval metrics. `runtime_freeze.json` records the chosen configuration before any new effectiveness, including exact model, tokenizer, source and input hashes. `requirements.lock.txt` records the actual environment. Technical/reproduction checks performed by software are not independent human review.

The official Qwen model card documents query-only instructions, last-token pooling, left padding and normalization. The protocol retains the original fixed scientific-evidence instruction and 8,192-token cap. The model's tokenizer tokens are used only for inference/truncation diagnostics. Evaluation costs retain the paper's original lexical-token function. All 1,024 output dimensions are used. No quantization, fine-tuning, new training data or outcome-driven model selection is used.

## Commands

The reported run uses CPython 3.12.14 (see `execution_environment.json`). Run from the repository root. Acquire the original dataset inputs with the project's existing acquisition instructions. The dedicated helper below acquires only the pinned Qwen model, without requiring unrelated ecosystem-audit downloads. Do not run the old v2 timing script to reproduce v3.

```sh
python -m venv .venv-revision
.venv-revision/bin/python src/revision_v3_encoder_acquire.py
.venv-revision/bin/python -m pip install -r revisions/v3/encoder/requirements.lock.txt
.venv-revision/bin/python src/revision_v3_encoder.py infer
.venv-revision/bin/python src/revision_v3_encoder.py score
.venv-revision/bin/python src/revision_v3_encoder.py validate
```

The `infer` command verifies the frozen configuration, environment and model and resumes atomic per-text checkpoints under `cache/<configuration hash>/`. Only this locally generated cache is excluded from Git; weights and source datasets are acquired under their respective terms. The published cache fingerprint manifest permits vector integrity checks without redistributing model weights. The cache namespace includes model/tokenizer file hashes, input data, instruction, length, pooling, precision, attention, backend, source and dependencies. A different environment/backend requires a separately labeled run rather than silently sharing this cache.

For a new result-blind technical replication on different hardware, preserve the released directory and use a separate checkout/output directory before `technical`; the command refuses to overwrite an existing freeze. The existing freeze describes the reported run, not a claim of cross-device bitwise reproducibility.

`score` requires a complete embedding manifest for every unique input. It writes `rankings.jsonl` only after all item rankings are assembled. Its schema follows the original rankings with method `qwen3`, retaining source unit indices, original annotations and cluster IDs, full cosine scores, source-index tie breaks, six original unit-budget points and per-item completion costs. `scoring_complete.json` records the complete item and point counts. `validate` checks every integer prefix, ranking permutation, source annotation hash, completion inequality, single-set equality and cost/score replay.

Statistics can be rebuilt without embeddings from the published `rankings.jsonl` using the revision-v3 statistics entry point documented in the repository README. Scientific outputs are labeled exploratory. The bounded paired method contrasts and bootstrap retain the original dependency structure; no causal interpretation is attached to observational model differences.

`src/revision_v3_encoder_report.py` produces the sanitized technical record and, after complete validation, `completion_report.json`. The latter reports execution counts, timing scope, truncation, fingerprints and validation status; scientific estimates are generated separately by the revision statistics code.

## Official documentation provenance

`official_sources.json` records the official model-card URL, pinned raw URL, SHA-256 and concise methodological reading notes. The third-party card is retained locally as `official_model_card.md` and excluded from the public release. To verify it, download the `pinned_raw_url` and compute SHA-256, comparing with `model_card.local_sha256`. The technical command does not require this separate full-text copy. Model acquisition separately provides the pinned model files (including the model directory README), whose hashes are checked against the original model manifest.

`src/revision_v3_encoder_acquire.py --verify-only` hashes all existing model/tokenizer files without networking. Acquisition is streamed to a temporary file and promoted only after its SHA-256 matches the historical manifest; an existing mismatch is retained and rejected. The successful local verification is recorded in `acquisition_verification.json`.
