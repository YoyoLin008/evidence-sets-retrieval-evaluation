# Published v1.1.1 verification

Verified at 2026-10-03T19:22:49.202040+00:00. This is a **post-publication** record, separate from the bundled pre-publication validation. Formal IRRJ submission has not been made.

## Version and commit correspondence

- Scientific source: `45c5c57e2de2fd45cb6691e7274bc600e731b5a0`.
- Reviewed v1.1.0 tag: `ff7f51142aa7bb253ed4a587309654ac5d6101e7`; patch baseline: `d656c69217bd77ae600f09607486980cf9b6c6f8`.
- Correction/build commit: `e77374837ce5891b5ff38b932438f02491d6809e`.
- Immutable v1.1.1 tag and release commit: `25654c3cd12f358145b4f50ef4f97bb86101b53a`. The remote tag, local tag and archived source match.
- [Published GitHub release](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.1.1) (normal release, not draft), nine assets.
- [Published Zenodo version](https://zenodo.org/records/23126392); [version DOI 10.5281/zenodo.23126392](https://doi.org/10.5281/zenodo.23126392). The DOI returned HTTP 200 and resolved to the intended record.
- [Concept DOI 10.5281/zenodo.23122619](https://doi.org/10.5281/zenodo.23122619) retains the existing concept record 23122619.

The later documentation commit adds this record, landing links and current citation DOI; its identity is in Git history. No tag was moved and no frozen artifact was replaced to add the DOI.

## Actual downloaded payloads

All nine public GitHub assets were downloaded and matched local accepted bytes and SHA-256 hashes. The ZIP contains 22 files, each byte-identical to its final standalone file (`revisions/patch_v1.1.1/package_checks.json`).

| Public asset | Bytes | SHA-256 |
|---|---:|---|
| asset_manifest.json | 1289 | `3f3a6d0854659608e4868f77459b1daa85a8dcacc22577024d9efc73913c880a` |
| cover_letter.pdf | 46269 | `457e3e7095bebf07b0a28d60bd428f83f0aec4424ebefcf56693e8c76ca8ed94` |
| manuscript_official_style.pdf | 397755 | `b2044275325f8a1317ffc1a571d8b010f5d027b1a5aa39f4886516dc7707e580` |
| manuscript_reading_copy.pdf | 401633 | `3ef55e26ae7b8a4c27c73b02d61d1658581be8c4c2f16f8911e811e37667bf29` |
| patch_memo.md | 4056 | `0acd4d2589c99eed87f7c0a365623245b4d50c3538aba4de7aa758bdab74c291` |
| SHA256SUMS | 624 | `577434ae59602c289770bdeaff865a6cab45a9d8dee2218c1d6914cac829e49a` |
| submission-v1.1.1.zip | 1166535 | `f2ed4d64bc2fb0005130d41e01c72569d53541b3b8780b614c0b655b9b7da12d` |
| supplement_official_style.pdf | 305768 | `8478c6beb495f0f656f557708f5efda0f6b89567bbe1b6ed55750bd5a2ef11ad` |
| validation_report.md | 6495 | `4c562bc2c864f8f88041762c4326ed167ffd869aace9bc6f3f2542781c41b0c9` |

Zenodo's automatic integration archived **one tagged repository ZIP**, not nine independent GitHub attachments. Its 15,109,009-byte payload matches the record's MD5 `d41870b88f0a6cc35c8187f9dd7aec6c`; downloaded SHA-256 is `ec960f4340d2ba4aa620af60221a291fd96741224b22b1770d6e7eb78e66875e`. Every one of its **424 decompressed files** matched `git archive` of `25654c3cd12f358145b4f50ef4f97bb86101b53a` by path and bytes. This verifies the complete tagged tree, including all four PDFs, the v1.1.1 submission ZIP, code, saved results and manifests. Archive-wrapper bytes are not assumed equal across independently generated ZIPs. No duplicate manual Zenodo deposit was created.

## Preservation and scope

Remote v1.0.0 and v1.1.0 tag commits, release identities, publication times and every historical asset ID/name/size/digest/update timestamp match their pre-publication inventory. Protected scientific and historical files remain equal to the pre-edit baseline. Old release assets and archived records are unchanged.

The [machine-readable record](release_verification_v1.1.1.json) includes downloaded asset hashes, archive correspondence, exact version metadata and preserved historical inventories. The [patch validation](../revisions/patch_v1.1.1/validation_report.md) records the real fresh-install/dependency-preflight check (36 exact distributions), two relevant existing tests and 54 inspected PDF pages. It does not claim a new full-inference replication or statistical rerun.

All authorized patch publication and verification steps are complete. The formal manuscript, supplement and cover letter are ready for the author's journal upload; the reading copy remains a convenience version. No editor has been contacted.
