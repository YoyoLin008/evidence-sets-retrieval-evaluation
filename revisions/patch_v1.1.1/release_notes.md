# v1.1.1 — final reproduction and editorial patch

This patch preserves all scientific results and frozen experiment implementations from v1.1.0. It fixes the strict Qwen environment instructions (new pip-free target populated through external pip), supplement exploratory-design wording, the supplement Table 11 reference to main Table 7, and “an 8.2-point gap” in both manuscript formats.

A genuinely fresh CPython 3.12.14 macOS ARM64 installation passed the unchanged encoder's complete 36-distribution dependency comparison with no missing, unexpected or mismatched packages. **This is installation/dependency-preflight validation, not a new full-inference replication.** No inference or statistical recomputation ran. Two relevant existing manuscript tests passed; all 54 exported PDF pages were inspected and full text/source preservation checked.

For journal upload use the official manuscript (21 pages), official supplement (12) and cover letter (1); the 20-page reading copy is for convenience. The submission ZIP contains the accepted files and patch evidence. Asset manifest/SHA256SUMS identify the final downloads. Old releases remain unchanged.

Scientific source: `45c5c57e2de2fd45cb6691e7274bc600e731b5a0`; reviewed v1.1.0 release: `ff7f51142aa7bb253ed4a587309654ac5d6101e7`; patch baseline: `d656c69217bd77ae600f09607486980cf9b6c6f8`. Correction/build and release commits are recorded separately in the patch build provenance and release metadata.

[Verified concept DOI 10.5281/zenodo.23122619](https://doi.org/10.5281/zenodo.23122619) identifies the existing version family. The exact v1.1.1 tag identifies the frozen artifacts. Automatic GitHub–Zenodo integration archives the tag repository snapshot, including the PDFs and ZIP tracked there; it does not separately archive arbitrary release attachments. The actual patch DOI and public-download verification are appended after archiving succeeds. No journal submission has been made.
