# When Evidence Sets Become Relevance Lists

**When Evidence Sets Become Relevance Lists: A Controlled Audit of Scientific Retrieval Evaluation**  
Yunya Lin · University of Illinois Urbana-Champaign

Reproducibility materials for a manuscript prepared for Information Retrieval Research (IRRJ), Normal Paper. The controlled study rescores unchanged rankings and annotated units under three targets. It does not measure semantic sufficiency, downstream answer quality, or ecosystem-wide prevalence of evaluation errors.

- **H**: at least one annotated evidence unit is retrieved.
- **C**: every unit in at least one original annotated evidence set is retrieved.
- **A**: every unit in the union of all annotations is retrieved.

Flat qrels remain valid for their intended metrics. Flattening does not require choosing A; it removes grouping needed to recover C from membership alone.

## Study and findings

The frozen primary cohorts contain 875 QASPER test questions (paragraph retrieval within known papers) and 209 SciFact development claim–abstract pairs (sentence retrieval within known evidence abstracts). BM25, TF-IDF, and all-MiniLM-L6-v2 are the retrieval methods; lead and seeded random rankings are controls. All 5,420 rankings are saved.

| Primary BM25 outcome | QASPER, k=5 | SciFact, k=3 |
|---|---:|---:|
| H | 65.0% | 83.7% |
| C | 51.0% | 79.4% |
| A | 33.1% | 51.7% |
| C−A | 17.8 pp | 27.8 pp |
| Mean extra union depth | 6.65 paragraphs | 2.02 sentences |
| Median extra union depth | 0 | 0 |

No primary F1 ranking reversal occurred. The post-main joint QASPER sensitivity gives an 8.2-point gap. Annotation-topology decomposition, the bounded implementation audit, and the Qwen timing gate are exploratory. Qwen exceeded the prespecified two-hour projection and was omitted without effectiveness scoring. See [analysis status](docs/analysis_status.md) and the manuscript for limits and prior work.

## Repository contents

- `paper/`: editable prose models, conventional IRRJ LaTeX source, bibliography, and rendered manuscript/supplement. `irrj2e.sty` is the separate unmodified official style.
- `src/`, `tests/`, `configs/`: acquisition, frozen retrieval, scoring, validation, and artifact generation.
- `reference_outputs/`: source-text-free saved rankings, eligibility and truncation audits.
- `tables/`, `figures/`, `analysis/`: primary results and source-linked presentation values.
- `logs/frozen_main_v1/`, `planning/`: prospective local plan/source snapshots and the post-main amendment.
- `revisions/v2/`: exploratory topology, implementation audit, and timing-gate evidence.
- `revisions/final/literature/`: final claim-to-source ledger and bibliography verification.
- `docs/`: reproduction status, licenses, and interpretation of the frozen records.

Raw corpora, model weights, caches, downloaded implementation collections, and literature PDFs are excluded. Their stable acquisition URLs and SHA-256 hashes are retained. The historical local study freeze is not public preregistration; public Git history begins with submission preparation.

## Environment and acquisition

Run from the repository root. The demonstrated environment is Python 3.12.14 on ARM64 macOS, CPU only. `requirements.lock.txt` records the observed environment; portability to other platforms is not established. With an existing [uv](https://docs.astral.sh/uv/) installation:

```sh
uv venv --python 3.12.14 .venv
uv pip sync --python .venv/bin/python requirements.lock.txt
.venv/bin/python src/check_release.py
.venv/bin/python src/prepare.py
```

An existing Python 3.12.14 environment can install the same lock with pip. `prepare.py` checks every required input against `configs/acquisition_expected.json` before extraction. A changed or unavailable source is an error: do not substitute different data or update a hash while claiming the same study. Full literature acquisition is optional, not required for reproduction. See [third-party terms](LICENSES.md).

## Replay saved rankings

Use a clean copy for this route. It restores annotation text from the acquired public sources and copies the released saved rankings; it performs no new retrieval.

```sh
.venv/bin/python src/replay_saved.py
.venv/bin/python src/verify_reproduction.py
.venv/bin/python src/validate_results.py
.venv/bin/python src/verify_revision_v2.py
.venv/bin/python -m pytest -q
```

`replay_saved.py` refuses a nonempty live output directory and verifies that reconstructed annotations match the frozen hash. The checks cover all 32,520 score points, every ranked cost, shared SciFact clusters, topology reconstruction, and 804 estimate/interval rows. Do not resume new retrieval into this replay directory: it lacks the historical dense embedding cache.

## Recompute rankings and analyses

Use a separate clean clone with acquired inputs, without running `replay_saved.py`:

```sh
.venv/bin/python src/main_study.py
.venv/bin/python src/verify_reproduction.py
.venv/bin/python src/analyze.py
.venv/bin/python src/supplemental.py
.venv/bin/python src/revision_analysis.py
.venv/bin/python src/validate_results.py
.venv/bin/python src/verify_revision_v2.py --fresh-reproduction
ASTRA_FRESH_REPRODUCTION=1 .venv/bin/python -m pytest -q
```

The historical main retrieval run took 626.5 seconds; downloads, tests, bootstrap analysis, and PDF generation add time. Runtime depends on hardware and software. `main_study.py --limit 250` supports bounded resumable batches; retain `outputs/embedding_cache` with the live run. The comparator requires identical ranking IDs and outcomes and reports floating-score differences separately. A fresh run naturally changes timing metadata; the environment flag skips only historical output-byte comparison, not scientific checks.

The primary cluster bootstrap uses 10,000 replicates (seed 20261002), with QASPER paper clusters and SciFact connected claim/document clusters. The separate direct-resampling audit uses seed 91827. Exact answer agreement is implemented by `answer_key` in `src/evidence.py`; its complete operations and answer-field precedence are described in the supplement. It is a textual, not semantic, equivalence test.

## Regenerate tables, figures, and PDFs

After either replay or full retrieval:

```sh
.venv/bin/python src/figures.py
.venv/bin/python src/revision_figures.py
.venv/bin/python src/render_final.py
.venv/bin/python src/qa_final_documents.py
```

The prose sources are `paper/article_blocks_1.json`, `paper/article_blocks_2.json`, and `paper/supplement_blocks.json`; citation metadata are in `literature/verified_references.json`. Edit those models before regeneration. Eleven display tables are regenerated under `revisions/final/tables/display`; frozen empirical tables remain separate. An existing `pdflatex` installation is needed for official PDF export. No software is installed by the rendering script. Each TeX build starts in a clean temporary directory containing source and the unmodified style. The labeled reading copy uses a separate renderer and is not the official-style submission PDF. Visual inspection must follow any new rendering; automated checks alone do not establish layout quality.

## Exploratory implementation and encoder evidence

The bounded implementation audit retains the full query log, selection rule, inaccessible results, pinned code locations, five-way classification, and material selection corrections under `revisions/v2/audit/`. Official evaluators/distributions are reference cases outside the fifteen downstream families per corpus. A second consistency pass is not independent human annotation. `src/acquire_revision_inputs.py` restores pinned audit inputs; `src/finalize_audit_v2.py` contains the isolated conversion fixtures and classification calculations; its historical inputs and execution scope are documented in `docs/analysis_status.md`. No complete downstream model pipeline was executed.

Qwen3-Embedding-0.6B was the sole additional candidate. Its independent environment and 132-input timing sample project 10,568.9 seconds for 20,112 inputs, above the 7,200-second gate. `revisions/v2/compute/` retains the configuration, tokenizer/weight hashes, timing rows, and projection. No full Qwen effectiveness result exists. The pooling check can run in the recorded separate environment using `src/verify_qwen_pool.py`; downloading or retiming Qwen is unnecessary for the saved-result replay.

## Licensing, responsibility, and citation

Original software and usage documentation: [MIT](LICENSE). Original scholarly text, figures, and derived results: [CC BY 4.0](LICENSE-CONTENT). Third-party sources retain their own terms; these grants do not relicense the source corpora, model weights, journal style, or cited papers.

The manuscript and supplement disclose generative-AI editing and technical assistance under the author's direction; the human author retains intellectual authorship and responsibility. No external funding or third-party computational resources were used; experiments ran on the author's personal computer.

Use [CITATION.cff](CITATION.cff) to cite the reproduction package. The manuscript is a submission manuscript, not an accepted or published journal article. Contact: yoyolin2@illinois.edu.

## Archived submission release

The submission-time package is [v1.0.0](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.0.0), archived at [Zenodo DOI 10.5281/zenodo.23122620](https://doi.org/10.5281/zenodo.23122620) on 3 October 2026. This version DOI identifies the immutable package at commit `ed2d6f6ca6f3e17b3b89c593bda5668c83b44e78`.

The current branch adds the verified DOI to the manuscript, supplement and citation documentation after archiving. The v1.0.0 snapshot is retained unchanged; its manuscript files necessarily precede that DOI insertion. The scientific code, saved rankings and empirical results are identical. The published archive was downloaded and all 238 files were checked against the release commit.

Suggested citation: Lin, Y. (2026). *When Evidence Sets Become Relevance Lists: A Controlled Audit of Scientific Retrieval Evaluation* (v1.0.0) [Software and reproducibility package]. Zenodo. https://doi.org/10.5281/zenodo.23122620
