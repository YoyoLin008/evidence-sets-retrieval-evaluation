## Final patch v1.1.1

This patch corrects the pip-free installation route for the strict frozen encoder environment and three editorial defects. It adds no experiment and preserves the original scientific sources, dependency lock/freeze, inputs, rankings and numerical outputs. The historical substantive revision is [v1.1.0](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.1.0), [DOI 10.5281/zenodo.23125121](https://doi.org/10.5281/zenodo.23125121).

Follow the corrected [encoder setup and read-only preflight](revisions/v3/encoder/README.md#commands). Create a new target without pip, install the unchanged lock from an external installer, and require the complete dependency dictionary to match. Keep analysis, pipeline and encoder environments separate. See the [patch memo](revisions/patch_v1.1.1/patch_memo.md), [patch validation](revisions/patch_v1.1.1/validation_report.md), and [current submission checklist](revisions/patch_v1.1.1/submission_checklist.md). Earlier revision memos and QA records describe their historical executions, not new patch test runs. Fresh installation/preflight does not constitute full-inference replication.

Current patch assets are in [release_artifacts/v1.1.1](release_artifacts/v1.1.1), including the submission ZIP, asset manifest and checksums. Files directly under `release_artifacts/` retain the older v1.1.0 release.
