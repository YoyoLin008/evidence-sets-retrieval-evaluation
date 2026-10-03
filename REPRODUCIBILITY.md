# Reproduction guide

The [README](README.md) provides the complete environment, acquisition, saved-ranking replay, fresh retrieval, analysis, test, and rendering commands. Choose either replay or fresh retrieval in a separate clean copy; do not mix their output directories.

`src/check_release.py` verifies the exact tracked release files against `PACKAGE_MANIFEST.json` before reproduction. Regeneration intentionally changes derived presentation/validation files, so archive verification precedes it. `docs/reproduction_status.md` records what was actually exercised for this release.

For optional Qwen helper validation, create a separate Python 3.12.14 environment with `revisions/v2/compute/requirements.lock.txt`, then run `src/verify_qwen_pool.py`. This checks pooling only; it does not compute effectiveness or reopen the completed feasibility decision.
