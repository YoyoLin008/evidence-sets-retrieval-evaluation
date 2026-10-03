# Revision-added exploratory statistics

These analyses were specified after the v1.0.0 results were known. The saved `protocol.md` precedes this revision's new calculations; it is not an original-study preregistration. Historical rankings and outputs are read-only inputs.

## Reproduction

From the repository root, with the existing Python analysis environment:

```sh
python src/revision_v3_statistics.py --rankings-only
```

This reconstructs all original-method statistics from `reference_outputs/main_v1/rankings.jsonl`, including its saved complete rankings, group membership, cluster labels, normalized-answer metadata, and lexical completion costs. It does not require article text, embeddings, or model weights. Source-text lexical costs are used as archived derived inputs in this mode and are explicitly not claimed to have been re-tokenized.

After acquiring/reconstructing the original `outputs/main_v1/instances.jsonl`, omit `--rankings-only` to independently recompute every score and lexical completion cost from text. Both modes must produce byte-identical CSV tables. A complete new encoder run can be included using:

```sh
python src/revision_v3_statistics.py --rankings-only --qwen revisions/v3/encoder/rankings.jsonl
```

The script rejects a partial Qwen run. Its full ranking file must contain exactly 1,084 valid permutations with the original instance hashes, IDs, groups, and clusters. The primary scoring budgets remain six original k values. The original five-method block contains 5,420 rankings and 32,520 points; a completed six-method block contains 6,504 rankings and 39,024 points. The new encoder alone has 1,084 rankings and 6,504 points. The additional continuous integer-budget threshold analysis is not included in these six-budget point totals.

Tests: `python -m pytest tests/test_revision_v3_statistics.py -q`.

## Tables and definitions

- `agreement_pruning.csv`: QASPER at k=5, for each method and each of exact normalized answer agreement, its complement, and the full cohort. `original_gap` and `pruned_gap` are proportions; `pruned_minus_original` is the paired transformation difference, not a between-cohort contrast. `_lo/_hi` are pointwise 95% cluster percentile intervals. `topology_0_n` through `topology_3_n` follow the existing four mutually exclusive categories. Questions partition the cohort; papers do not (119 papers occur in both subsets). Rates reconstruct by item weighting. Strict string agreement does not prove semantic agreement; its complement does not prove semantic conflict. Neither subgroup estimate is a mathematical bound or causal effect.
- `budget_thresholds.csv`: all prespecified methods, both corpora, unit and lexical-token budgets, and all three thresholds 0.50/0.75/0.90. `B_C`, `B_A`, and `difference=B_A−B_C` are exact minimum uniform integer budgets. The empirical completion CDF changes only at individual completion costs; searching those event costs is mathematically equivalent to testing every integer budget. These population thresholds differ from the mean individual `depth_penalty` or `tokens_penalty`.
- `costs.csv`: original completion-depth/token-cost definitions, with mean intervals, medians, quantiles, maxima, and zero shares.
- `cost_distributions.csv`: all items and positive-cost items for each additional-cost metric; the latter has its own item/represented-cluster denominator. The original population zero fraction and interval remain visible in both rows. These are annotation-defined retrieval costs, not measured reading time or deployed model-token charges.
- `curves.csv`, `primary.csv`: replayed H/C/A, gap, recall and F1 summaries, with original six k values and cluster intervals. The original method results retain their historical provenance; these CSVs repackage them alongside any completed revision-added Qwen results without rewriting original outputs.
- `method_contrasts.csv`: all prespecified paired comparisons (MiniLM−BM25, Qwen3−BM25, Qwen3−MiniLM, where available), all six k values, and all fixed metrics. `C_advantage_minus_A_advantage` equals the gap contrast algebraically and is labeled explicitly. Intervals are descriptive and pointwise; there is no multiplicity-controlled declaration or significance-based search for reversals.
- `item_completion_costs.csv` and `cohort_membership.csv`: item-level audit inputs for the published summary tables, containing identifiers and derived quantities, not source text.
- `validation.json`: actual cohort, historical-category, topology, original-score/cost, invariance, complete-ranking and threshold checks. The F1 counterexample demonstrates why removing strict supersets can lower best-reference F1 despite preserving C.
- `manifest.json`: source/protocol/input/output hashes, execution times, and the precise replay mode.

## Resampling and attainment

All analyses retain the original seed 20261002 and 10,000 replicates. QASPER resamples paper clusters; SciFact resamples original connected claim/document components. Whole clusters are sampled with replacement and means remain item weighted. Subset intervals resample clusters represented in that subset; the same cluster draw pairs original and pruned values. Sharing papers between the two answer subsets is explicitly retained in the metadata, and no independent-groups causal interpretation is made.

For each full-cohort threshold bootstrap replicate, the same cluster multiplicities and resulting item denominator are applied to C and A completion costs. The minimum cost whose weighted empirical CDF reaches the threshold is selected; their difference is calculated within the replicate. Short documents saturate at their complete prefix while all eligible items remain in the denominator. Lexical budgets stop before the first unit that would exceed the budget; no unit is truncated or skipped. The lexical cost of every unit remains `max(1, number of historical lexical tokens)`.

Percentile endpoints use the original linear interpolation convention and can be fractional even though point budget estimates are integers. A nonattained threshold is represented internally by positive infinity and is never extrapolated. CSV blank budget/interval fields are accompanied by explicit attainment flags and counts. Endpoint intervals preserve infinite endpoints; if any paired gap replicate is undefined because an endpoint is unattained, its ordinary paired interval is not reported rather than silently conditioning on attained draws. All complete rankings here attain all three thresholds in all 10,000 replicates.

The affected-item distributions are descriptive conditional distributions. Their mean intervals use clusters represented among affected items; they are not population-wide average burdens. Empty subsets are retained with zero denominators and blank estimates, and fewer than ten represented clusters is flagged sparse.
