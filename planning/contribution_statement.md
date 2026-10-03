# Contribution freeze
Created 2026-10-02, after the explicitly separated pilot and before main test scoring. Timestamp/hash recorded with the analysis-plan freeze.

Existing research has established that relevance, answer utility, and complete supporting evidence are different evaluation targets, and that multiple valid evidence sets should be handled as alternatives in established benchmarks.

The examined literature has not provided the particular cross-benchmark decomposition proposed here: with retrieved rankings held fixed, quantify loss of within-set conjunction versus loss of between-set alternatives, then measure the resulting extra ranked units and token cost and variation by annotation structure. This is a bounded novelty assessment, not proof no related work exists.

This gap matters because reducing a set of sets to a single relevance list discards relationships that distinguish completing a justification from finding a fragment or exhausting all justifications.

We investigate it through controlled rescoring of frozen CPU lexical and dense rankings on QASPER scientific QA and SciFact claim–abstract rationale selection, with retained source annotations and clustered uncertainty.

The contribution is an empirical measurement-validity analysis, a formal counterexample demonstrating non-identifiability from flat labels, and a reproducible protocol retaining annotation structure. It is not a new retrieval model or newly invented completeness metric.

If material differences exist, flattening would change the operational question answered by a retrieval score and potentially its budget requirements. If differences are small, the study would bound practical sensitivity in these datasets. We do not require ranking reversals, downstream answer effects, or significant p-values to tell that story.
