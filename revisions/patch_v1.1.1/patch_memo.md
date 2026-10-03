# Final correction memo — v1.1.1

This is a reproduction-instruction and editorial patch to reviewed v1.1.0, not a scientific revision. Reviewed scientific source: `45c5c57e2de2fd45cb6691e7274bc600e731b5a0`; reviewed tag: `ff7f51142aa7bb253ed4a587309654ac5d6101e7`; working baseline: `d656c69217bd77ae600f09607486980cf9b6c6f8`.

## Four corrections

1. **Fresh encoder environment.** `revisions/v3/encoder/README.md` now creates a new pip-free, isolated CPython 3.12.14 macOS ARM64 target and populates the unchanged lock with an external pip `--python` installer. An ordinary venv installs pip, but the historical 36-distribution freeze omits it; the unchanged encoder compares the entire distribution dictionary, so the old instructions failed that guard. `src/encoder_dependency_preflight.py` calls the actual frozen `dependencies()` function without filtering. It reports missing, unexpected and version-mismatched packages, checks source hashes and isolation, and does not load the model or run inference. README and `docs/revision_v1.1_reproduction.md` point to the corrected route. No package was added to the freeze, no guard was weakened, and no system Python packages were changed.
2. **Exploratory chronology.** The authoritative `RevisionTiming` value in `src/revision_v3_manuscript.py` now says: “They are revision-added exploratory work, not part of the original frozen design.” Supplement Section 7 retains that v1.0.0 outcomes were already known.
3. **Topology caption.** `src/manuscript_revision_tables.py` now states: “Category denominators are reported in Table 7 of the main article.” The final main Table 7 contains the item/cluster n/g denominators. Supplement Table 11 remains Table 11; its preceding table is the SciFact case.
4. **Grammar.** `paper/article_blocks_2.json` changes `pruning yields a {QJointGap}-point gap` to `pruning yields an {QJointGap}-point gap`. Both manuscript formats inherit “an 8.2-point gap”; the value, interval and restricted-cohort interpretation are unchanged.

## Preserved record and regenerated artifacts

All protected sources, lock/freeze, protocols, input/model manifests, rankings, statistics, historical QA and original figures retain their baseline SHA-256 values. Full document-model comparison permits only those three textual corrections and current-version propagation. The rendering registry's sole change is the `RevisionTiming` prose entry; numerical values and all table data remain identical. Author-confirmed authorship, AI and funding wording is unchanged.

Regenerated: official IRRJ manuscript (21 pages), official supplement (12), cover letter (1), reading copy (20), their source/Markdown/display derivatives and v1.1.1 submission ZIP. These are actual new counts (54 PDF pages total), not a prescribed total. The native single-file editor still cannot resolve the adjacent journal style, but the established two-pass pdfLaTeX export succeeds with that unchanged style. Every exported page was rendered and inspected.

## Validation scope and publication

The fresh target began with zero distributions. External pip 26.2.1 installed the original lock; the target reports all 36 frozen distributions exactly, no target pip, no missing/unexpected/version differences, and preserved encoder/scorer hashes. This is **fresh-environment installation and dependency-preflight validation**, not full-inference replication. Two directly relevant existing manuscript tests passed. No Qwen inference, statistical recomputation or new scientific experiment ran for this patch. See `validation_report.md` and the machine-readable records.

Old v1.0.0/v1.1.0 tags and assets remain historical. New artifacts cite verified concept DOI `10.5281/zenodo.23122619` plus exact v1.1.1 tag. The actual new version DOI and downloaded-payload verification are added after automatic GitHub–Zenodo archiving, without moving the tag or replacing frozen artifacts. Formal journal submission is outside this work. The existing scientific limitations and bounded claims remain as reviewed.
