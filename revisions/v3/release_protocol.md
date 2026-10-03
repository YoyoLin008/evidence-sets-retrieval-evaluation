# Release strategy fixed for revision v1.1.0

Historical v1.0.0 remains unchanged at tag commit ed2d6f6ca6f3e17b3b89c593bda5668c83b44e78. Current revision starts from faf730ea4c25161b6b2dc350ff9890e344bc3524 on revision/practical-evidence-v1.1.

Use the already enabled GitHub–Zenodo automatic integration only. The verified concept DOI is 10.5281/zenodo.23122619; historical version DOI 10.5281/zenodo.23122620 identifies v1.0.0, not this revision. Frozen v1.1.0 PDFs and sources cite concept DOI plus exact tag/release URL. The new version DOI is not known before publication and will be added to mutable release notes and subsequent verification documentation only.

Zenodo automatically archives the tag source ZIP, not an assumed set of GitHub release assets. Include all four final PDFs, editable sources, permitted results and reproducibility files in that snapshot. The submission ZIP is a separately verified GitHub asset; it is not claimed as an extra file in the automatic archive. Prepare a draft release, attach all assets and checksums, verify the draft, then publish. Do not replace PDFs, ZIPs or tag to insert the later DOI.

Check current branch rules before ordinary merge/push; do not bypass required review. Verify published assets by downloading and hashing. Compare unpacked Zenodo files with the tag, since source ZIP containers may differ.

Official docs checked 2026-10-03 UTC: https://developers.zenodo.org/ and https://support.zenodo.org/help/en-gb/24-github-integration/73-can-i-pre-reserved-a-doi-before-a-github-release . The latter states that pre-reserving a DOI is unavailable through automatic GitHub integration. IRRJ guidelines checked: https://irrj.org/about/submissions . Actual IRRJ submission remains an author action.
