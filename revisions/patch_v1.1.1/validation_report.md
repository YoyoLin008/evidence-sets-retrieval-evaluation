# Pre-publication validation — v1.1.1

This report records only checks executed for the final patch on 3 October 2026 UTC. Earlier v1.1.0 test/replay totals remain historical. It does not claim a new full-inference replication or statistical rerun. Post-publication downloads and DOI verification belong in `docs/release_verification_v1.1.1.md`, added later.

## Fresh installation and dependency preflight: passed

Actual compatible target: CPython 3.12.14, macOS 15.2 ARM64, `.venv-final-repro-v1.1.1`. The directory did not exist before creation. Initial distributions: zero; system site packages and user-site inheritance disabled. External interpreter: `/opt/homebrew/bin/python3`; external pip: 26.2.1, with `--python` support. This follows the documented [pip-free venv](https://docs.python.org/3.12/library/venv.html) and [external pip interpreter](https://pip.pypa.io/en/stable/topics/python-option/) options.

Commands actually executed from the repository root:

```sh
.venv/bin/python -m venv --without-pip .venv-final-repro-v1.1.1
/opt/homebrew/bin/python3 -m pip --python .venv-final-repro-v1.1.1 install -r revisions/v3/encoder/requirements.lock.txt
.venv-final-repro-v1.1.1/bin/python src/encoder_dependency_preflight.py
```

Interpreter/version assertions and the initially empty distribution check are recorded in `installation.json`. The unchanged encoder's actual `dependencies()` returned the complete frozen 36-distribution dictionary. Missing, unexpected and version-mismatched distributions: none. Target pip: absent. Encoder and scorer source hashes: match. See `dependency_preflight.json`. No filtering/subset comparison was used. Nothing was installed into the external/system interpreter. Compatibility outside this macOS ARM64 setup is not established. No model load, inference, encoder scoring or statistical analysis was launched.

## Scientific integrity and source diff: passed

`baseline.json` records all 406 tracked baseline files before editing and five external scientific-tree hash inventories. The final comparison in `scientific_integrity.json` found 381 unchanged tracked files and exactly 25 intended edits before packaging. The later package manifest is a necessary metadata change, not a scientific output. All protected experiment sources, lock/freeze, manifests, protocols, rankings, numeric statistics and historical records are unchanged. All 20,184 files across raw inputs, MiniLM model files, Qwen model files, original outputs and the 20,112-file Qwen embedding cache also match their baseline hashes. No cache identifier or source fingerprint was regenerated.

All source-linked rendering values and complete article/supplement models compare exactly after only the three requested text fixes and v1.1.0-to-v1.1.1 availability changes. All table rows and numeric values are unchanged; only the `RevisionTiming` prose entry changes in the rendering registry. All author/AI/funding declaration strings remain exact. Preserved rounded checkpoints include 875/209 original items, Qwen gaps 23.1/27.3 points, BM25 75% budgets 14/27 and 3/6, zero extra-depth medians, stable reported primary F1 ordering, and the 866-question converter/scorer scope with its explicit restrictions. These are preservation checks against saved output, not recomputed estimates.

## Build, tests and page checks: passed

Executed `.venv/bin/python src/revision_v3_release_docs.py`, then `src/render_final.py` using the analysis environment. The existing renderer assembled the manuscript from saved outputs and used two passes of the installed pdfLaTeX for each formal document. No TeX installation was required. Native-editor compilation was attempted and reported missing adjacent `irrj2e.sty`; this single-file-editor limitation does not affect the successful official-style export. The editable source remains available.

Executed `.venv/bin/python -m pytest -q tests/test_revision_v3_manuscript.py`: **2 passed in 0.33 seconds**. These existing checks cover source-denominator guards, protected content and saved-output manuscript integration. No historical full-suite count is presented as a new execution; there is no repository CI configuration requiring a broader run.

Rendered with `.venv/bin/python src/qa_final_documents.py --output-dir revisions/patch_v1.1.1/qa/rendered`. Official main: **21 pages**; supplement: **12**; reading copy: **20**; cover letter: **1**. Every page was visually inspected, including references, tables and figures. No clipping, missing glyphs, broken references, unexpected blank pages or pagination changes were found. Compiler logs contain no undefined-reference, missing-character or overfull-box warnings. `qa/document_checks.json` records the new hashes and inspection timestamps.

Full extracted old/new PDF text matches only the requested corrections and current-version changes after layout whitespace/hyphenation normalization; complete JSON-model equality separately prevents that normalization from hiding content changes (`qa/text_comparison.json`). Direct checks locate the grammar correction in both main formats (page 13), corrected chronology in supplement Section 7 (page 5), and corrected Table 11 caption (page 10). Main Table 7 (page 12) is the topology table with the verified n/g counts. Exploratory status, restricted-cohort interpretation, annotation-defined completion and bounded converter/scorer language are unchanged.

## Packaging gate and scope

`src/package_final_patch.py` checks the accepted PDF hashes, creates the patch-only ZIP under `release_artifacts/v1.1.1/`, rereads every internal file and requires byte equality with its standalone source. It writes `package_checks.json` outside the ZIP after that check. The asset manifest and SHA256SUMS are computed after the archive; PACKAGE_MANIFEST excludes itself and uses the explicit Git index allowlist. Old release artifacts are never overwritten. Temporary environments, caches, raw corpora, weights, credentials and private logs are excluded. The public tag archives the complete reproducibility tree; the submission ZIP is the smaller journal-oriented package.

The bundled report describes pre-publication validation only. A later public-download verification record reports the actual release/tag, assigned version DOI and complete decompressed Zenodo archive comparison. Passing this patch's gates does not add an independent replication or change the manuscript's scientific claims. Formal IRRJ submission has not been performed.
