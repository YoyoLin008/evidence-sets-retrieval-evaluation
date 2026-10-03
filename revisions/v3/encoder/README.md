# Complete-cohort Qwen robustness experiment (revision v3)

This directory records a revision-added exploratory experiment. It is separate from the frozen original five-method results and the v2 timing-only omission. The v2 files and two-hour gate outcome remain historical records; this revision removes the artificial two-hour gate and runs the selected model for every original eligible item.

`technical_plan.md` is saved before technical sampling or any new effectiveness. `public_technical_summary.json` preserves every field and measurement of the hash-identified original `technical_results.json`, with only local diagnostic path prefixes normalized; the original raw log is retained locally. These records compare only embeddings, elapsed time and memory, without gold labels or retrieval metrics. `runtime_freeze.json` records the chosen configuration before any new effectiveness, including exact model, tokenizer, source and input hashes. `requirements.lock.txt` records the actual environment. Technical/reproduction checks performed by software are not independent human review.

The official Qwen model card documents query-only instructions, last-token pooling, left padding and normalization. The protocol retains the original fixed scientific-evidence instruction and 8,192-token cap. The model's tokenizer tokens are used only for inference/truncation diagnostics. Evaluation costs retain the paper's original lexical-token function. All 1,024 output dimensions are used. No quantization, fine-tuning, new training data or outcome-driven model selection is used.

## Commands

The reported run uses CPython 3.12.14 (see `execution_environment.json`). Run from the repository root. Acquire the original dataset inputs with the project's existing acquisition instructions. The dedicated helper below acquires only the pinned Qwen model, without requiring unrelated ecosystem-audit downloads. Do not run the old v2 timing script to reproduce v3.

The strict runtime compares **all** installed distributions with `runtime_freeze.json`. A default venv adds pip, which is absent from that frozen dictionary. Keep the original lock and guard unchanged: create a new target without pip and use an external installer. Do not install extra tools into the target (pytest already present in the historical lock must retain its locked version).

Select an existing **CPython 3.12.14 on macOS ARM64**. The commands below default to the analysis environment's `.venv/bin/python` only after checking its actual version/platform; set `ENCODER_PYTHON` to another installed interpreter if necessary. `INSTALLER_PYTHON` must be outside the target and have pip supporting `--python` (pip >=22.3); the recorded patch validation used `/opt/homebrew/bin/python3` with pip 26.2.1. These commands install nothing into that external interpreter or the system environment. Run from the repository root in a clean reproduction checkout.

```sh
ENCODER_PYTHON="${ENCODER_PYTHON:-.venv/bin/python}"
INSTALLER_PYTHON="${INSTALLER_PYTHON:-python3}"
"$ENCODER_PYTHON" -c 'import sys,platform; assert sys.version_info[:3] == (3,12,14); assert platform.system() == "Darwin" and platform.machine() == "arm64"; print(sys.version); print(platform.platform())'
"$INSTALLER_PYTHON" -m pip --version
"$INSTALLER_PYTHON" -m pip --help
if [ -e .venv-final-repro-v1.1.1 ]; then
  echo "Choose a new target directory; do not reuse an installed environment." >&2
  exit 1
fi
"$ENCODER_PYTHON" -m venv --without-pip .venv-final-repro-v1.1.1
"$INSTALLER_PYTHON" -m pip --python .venv-final-repro-v1.1.1 install -r revisions/v3/encoder/requirements.lock.txt
.venv-final-repro-v1.1.1/bin/python src/encoder_dependency_preflight.py
```

Before installing, confirm `--python` is listed in the external pip help. Do not enable `--system-site-packages`. The helper calls the frozen encoder's actual `dependencies()` function without filtering distributions and reports missing, unexpected and mismatched packages. It also checks the frozen encoder/scorer source hashes and virtual-environment isolation. It does not load weights, start inference, alter the freeze or write scientific outputs. Require `passed: true`, `exact_dictionary_match: true` and empty difference dictionaries. The supported platform matches `execution_environment.json`; other platforms are not validated by this check and may add platform-specific packages.

The approach follows [Python's pip-free venv option](https://docs.python.org/3.12/library/venv.html) and [pip's external-interpreter option](https://pip.pypa.io/en/stable/topics/python-option/). The actual fresh-install commands, identity and results are in `revisions/patch_v1.1.1/installation.json` and `dependency_preflight.json`. This validation is installation and dependency preflight, **not a new full inference replication**.

Only if intentionally reproducing the full experiment in a separate clean checkout, after obtaining original inputs and passing preflight, use:

```sh
.venv-final-repro-v1.1.1/bin/python src/revision_v3_encoder_acquire.py
.venv-final-repro-v1.1.1/bin/python src/revision_v3_encoder.py infer
.venv-final-repro-v1.1.1/bin/python src/revision_v3_encoder.py score
.venv-final-repro-v1.1.1/bin/python src/revision_v3_encoder.py validate
```


The `infer` command verifies the frozen configuration, environment and model and resumes atomic per-text checkpoints under `cache/<configuration hash>/`. Only this locally generated cache is excluded from Git; weights and source datasets are acquired under their respective terms. The published cache fingerprint manifest permits vector integrity checks without redistributing model weights. The cache namespace includes model/tokenizer file hashes, input data, instruction, length, pooling, precision, attention, backend, source and dependencies. A different environment/backend requires a separately labeled run rather than silently sharing this cache.

For a new result-blind technical replication on different hardware, preserve the released directory and use a separate checkout/output directory before `technical`; the command refuses to overwrite an existing freeze. The existing freeze describes the reported run, not a claim of cross-device bitwise reproducibility.

`score` requires a complete embedding manifest for every unique input. It writes `rankings.jsonl` only after all item rankings are assembled. Its schema follows the original rankings with method `qwen3`, retaining source unit indices, original annotations and cluster IDs, full cosine scores, source-index tie breaks, six original unit-budget points and per-item completion costs. `scoring_complete.json` records the complete item and point counts. `validate` checks every integer prefix, ranking permutation, source annotation hash, completion inequality, single-set equality and cost/score replay.

Statistics can be rebuilt without embeddings from the published `rankings.jsonl` using the revision-v3 statistics entry point documented in the repository README. Scientific outputs are labeled exploratory. The bounded paired method contrasts and bootstrap retain the original dependency structure; no causal interpretation is attached to observational model differences.

`src/revision_v3_encoder_report.py` produces the sanitized technical record and, after complete validation, `completion_report.json`. The latter reports execution counts, timing scope, truncation, fingerprints and validation status; scientific estimates are generated separately by the revision statistics code.

## Official documentation provenance

`official_sources.json` records the official model-card URL, pinned raw URL, SHA-256 and concise methodological reading notes. The third-party card is retained locally as `official_model_card.md` and excluded from the public release. To verify it, download the `pinned_raw_url` and compute SHA-256, comparing with `model_card.local_sha256`. The technical command does not require this separate full-text copy. Model acquisition separately provides the pinned model files (including the model directory README), whose hashes are checked against the original model manifest.

`src/revision_v3_encoder_acquire.py --verify-only` hashes all existing model/tokenizer files without networking. Acquisition is streamed to a temporary file and promoted only after its SHA-256 matches the historical manifest; an existing mismatch is retained and rejected. The successful local verification is recorded in `acquisition_verification.json`.
