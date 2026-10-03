# v1.1.0 published release verification

**PUBLISHED AND VERIFIED** at 2026-10-03T17:38:00.873250+00:00. This is a post-publication record on the landing branch. It is intentionally outside the frozen v1.1.0 tag and source archive.

- Scientific source commit: `45c5c57e2de2fd45cb6691e7274bc600e731b5a0`.
- Revision branch: `revision/practical-evidence-v1.1`; normally fast-forwarded into main and pushed.
- Exact release tag: `v1.1.0` → `ff7f51142aa7bb253ed4a587309654ac5d6101e7`.
- GitHub repository: https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation .
- Public release: https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.1.0 .
- Zenodo record: https://zenodo.org/records/23125121 .
- Version DOI: https://doi.org/10.5281/zenodo.23125121 (public resolution returned HTTP 200).
- Concept DOI: https://doi.org/10.5281/zenodo.23122619 (the version family).

## Actual remote checks

All nine explicit release assets were attached and hash-checked while the release was a draft, then downloaded again from their public URLs after publication. Names, sizes and SHA-256 values match the locally accepted files. The GitHub page also shows two platform-generated source downloads; those are separate from the nine uploaded assets.

Zenodo's automatic archive contains **403 files**, including all four PDFs and the submission ZIP. Every decompressed path and byte matches a local `git archive` of the verified release commit. Its archive download is 13,869,496 bytes; platform MD5 and a local SHA-256 were checked. ZIP-container metadata can differ between services, so comparison used the decompressed content. No duplicate manual deposit was created.

The preserved v1.0.0 tag still resolves to `ed2d6f6ca6f3e17b3b89c593bda5668c83b44e78` and retains DOI 10.5281/zenodo.23122620. The new DOI is added only to mutable landing records; final PDFs, submission ZIP and release tag remain unchanged. Zenodo displays MIT for the software archive; the description and repository license documents retain the CC BY 4.0 scholarly-materials split and third-party exclusions.

## Frozen asset correspondence

| File | Bytes | SHA-256 |
|---|---:|---|
| `paper/manuscript_official_style.pdf` | 397758 | `453b9d6dee8433b7d7b2eccf772ec97aaea74cbb3fe6961bdf9c762a2f04b12a` |
| `paper/supplement_official_style.pdf` | 305757 | `3256005b3206db9fbccc48aa4732b2051fc37ff8089916f5e84b66b2bb07d7d2` |
| `paper/cover_letter.pdf` | 46270 | `178ea207485d92f5f35ce2f27753985f0757bada47bc0e513835d326150cc297` |
| `paper/manuscript_reading_copy.pdf` | 401633 | `5c1f9b11ba218bc524b869254f2c9aef6d34da43a0cf96db01503ad40fd4ca6d` |
| `release_artifacts/submission-v1.1.0.zip` | 1118416 | `7ac7526746c4481bcaafea4811883b0c202adccf5babca0d02b89b8e776869f0` |
| `revisions/v3/revision_memo.md` | 5507 | `b067481c2a1c33cc9482998a2309bbc3dabe205cd7c3dfc92cc08f0676d286fa` |
| `revisions/v3/qa/validation_report.md` | 6422 | `38e2c6710cbaf8cf474697cc244921ce28008c54323d7fcb6bcf8009b555b9ab` |

## Submission choice and remaining scope

Use `paper/manuscript_official_style.pdf` (21 pages), `paper/supplement_official_style.pdf` (12 pages), and `paper/cover_letter.pdf` (1 page). The 20-page reading copy is for convenience. `release_artifacts/submission-v1.1.0.zip` groups the final files and supporting materials. All 54 PDF pages were visually inspected. See the frozen `revisions/v3/qa/validation_report.md` for scientific tests and the isolated replay; `revisions/v3/revision_memo.md` and `reviewer_risks.md` describe narrowed claims.

The scientific revision, code/document synchronization, release, archiving and downloadable package are complete. **Formal IRRJ submission was not performed**, as explicitly instructed; the author must review and upload the three official files and complete journal-specific forms and terms. There is no unresolved publication/access blocker. The native standalone editor cannot resolve the adjacent style; actual official PDFs were successfully exported and checked using the existing local compiler.

Independent human semantic annotation, external/cross-platform replication and a full downstream product run are not claimed. The remaining review risks concern incremental novelty, annotation-defined rather than semantic completion, cohort selection, bounded implementation evidence and one additional encoder. No acceptance probability is assigned.

Machine-readable evidence: `release_verification_v1.1.json`. This report does not hash itself or retroactively change the archived release.
