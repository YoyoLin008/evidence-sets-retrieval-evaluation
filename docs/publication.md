# Release and archive identification

Version v1.1.0 is the substantive revision of v1.0.0. Frozen PDFs identify exact tag v1.1.0 and verified concept DOI 10.5281/zenodo.23122619. The concept DOI denotes the version family. The release protocol is `revisions/v3/release_protocol.md`.

GitHub release assets comprise four PDFs, submission ZIP, revision memo, validation report, asset manifest and SHA-256 list. These files are attached and checked while the release is a draft before publication. The existing GitHub–Zenodo integration automatically archives the tagged repository snapshot; it does not automatically archive arbitrary release attachments. All final PDFs and the ZIP are therefore included in the tag.

After publication, the release landing notes and subsequent verification document record the actual new version DOI and download comparison. No frozen same-version PDF, ZIP or tag is replaced to insert a DOI that did not exist when files were frozen. Source commit and tag/release commit are separately recorded to avoid self-hash cycles.

Historical v1.0.0 remains at commit ed2d6f6ca6f3e17b3b89c593bda5668c83b44e78 and DOI 10.5281/zenodo.23122620. Existing `docs/archive_verification.json` describes that historical version; it is not evidence for the new version.
