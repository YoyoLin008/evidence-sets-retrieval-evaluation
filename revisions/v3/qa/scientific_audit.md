# Completed automated scientific and code audit

Scientific/code scope completed on 2026-10-03T17:18:23.161080+00:00. This is an additional automated review, not independent human review or external replication. The reviewer differs from statistics/manuscript implementers and produced the converter/example implementation, so the latter is a self-check.

## Actual checks

- All 6,504 complete rankings, 39,024 original-grid points and 351,216 score values recomputed through direct set operations.
- Every one of 261,852 integer prefixes checked for pruning invariance/direction; all depth and lexical costs reconstructed from source text. Best-reference F1 is explicitly excluded from invariance, with the existing counterexample retained.
- All 648 curve means, 72 cost means, 144 threshold endpoints and 36 subgroup means checked. Thresholds attain the target at k and fail at k−1, retaining all eligible items.
- Cluster resampling code and explicit multiplicity/unattained-replicate tests reviewed. These intervals are paired, item-weighted and exploratory; no long bootstrap or full inference rerun was repeated for this review.
- Original source instances/rankings match frozen hashes. All 13 pipeline public output hashes, current source, plan and input provenance agree. Changed saved-score inputs are rejected by an executed test.
- The complete manuscript helper instantiated successfully and generates the four fixed Qwen comparison rows from validated complete output; no partial effectiveness enters this path.

## Main interpretation safeguards

The QASPER agreement and complement distinguish sample selection from paired target pruning: BM25 24→16/195, 132→87/680 and 156→103/875. Shared papers are not treated as independent groups. The 8.2-point result is neither a formal bound nor a causal decomposition; exact normalized answer strings do not establish semantic agreement.

The converter covers 875 original questions, but exact union-membership alignment applies to 866 under the stated normalized-text/candidate restriction. Nine exports omit 14 annotated memberships. Within the matched subset, 90 have duplicate/normalized-equivalent candidates (four involving gold); eight canonical mappings use identical abstract text (one involving gold). These disclosed equivalences preclude calling the full native task pure grouping-only loss. Ordinary relevance metrics remain separate from C/A, and no stated-objective mismatch is established.

Complete Qwen3 rankings yield QASPER H/C/A=78.2/65.0/41.9%, C−A=23.1 [20.2, 26.0] points, and mean extra depth 5.89 (median 0); SciFact H/C/A=90.4/86.6/59.3%, C−A=27.3 [20.9, 33.9] points, and mean extra depth 1.61 (median 0). The revision contains 6,504 full rankings and 39,024 points across the six original unit budgets when the historical and new methods are counted together; the original block remains unchanged.

QASPER Qwen3−BM25 differences are 14.1 points under C and 8.8 under A; SciFact Qwen3−BM25 differences are 7.2 points under C and 7.7 under A. The fixed revision-added exploratory comparisons show no new primary F1 ranking reversal. The supplement reports every primary paired comparison against BM25 and MiniLM; all six budgets and all fixed metrics remain in the machine-readable results. These are exploratory pointwise comparisons.

## Release-code and public scope review

The release validator now checks the public copies of historical frozen outputs even when source text is absent, author/affiliation and protected disclosure values, current complete manifests, unchanged official style and intended-public file scope. The release-prose generator reuses the final completion/hash guard. All three earlier wording/provenance recommendations were adopted. Complete third-party model-card text is excluded; source/hash attribution remains.

PDF visual verification, remote publication/DOI/file checks and the isolated source-free reproduction are separate root-managed checks. Their exclusion here is a scope boundary, not an unresolved scientific calculation. No new human semantic annotation or acceptance probability is claimed. See independent_six_method_checks.json for exact inputs and check totals.
