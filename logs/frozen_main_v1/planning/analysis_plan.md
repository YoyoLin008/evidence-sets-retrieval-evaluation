# Main analysis plan, version 1
Date: 2026-10-02 America/Chicago. Frozen after pilot, before reading QASPER test or scoring SciFact dev. Exact timestamp, file/config hashes and code snapshot go in logs/main_freeze.json. Local prospective plan, NOT a public preregistration. Pilot measurements are not confirmatory results.

## Questions
RQ1: At fixed retrieval budgets, how far apart are any evidence hit, completion of at least one original annotation, and completion of the flattened union?
RQ2: How much deeper in a fixed ranking must one go to retrieve the union rather than one original annotated set, and how does this vary with annotation structure?
RQ3 (exploratory): Do numerical scores and system comparisons change under max-reference versus union aggregation?

## Design and units
One controlled rescoring experiment. Rankings and source annotations stay fixed across scoring rules; thus differences have a deterministic interpretation conditional on this benchmark. No claim about real-world prevalence of erroneous evaluation implementations.
QASPER: questions within papers; main split test v0.3. Use all eligible items.
SciFact: evidence-bearing claim–abstract pairs, official development split. Known evidence abstract supplied; this is rationale retrieval, not whole-corpus claim verification. Bootstrap connected components linking pairs that share a claim or document.
Do not pool the two corpora into a single headline effect. A paragraph and a sentence differ as units.

## Eligibility and reference handling
Retain pilot criteria exactly: QASPER must have all answer annotations answerable, nonempty, text-only, and wholly mappable. Collapse identical normalized paragraph strings to a single content unit. Do not drop bad pieces inside a reference. Retain duplicate and nested reference sets, but report distinct/minimal-set counts. Primary QASPER interpretation permits differing answers; robustness restricts to normalized answer agreement. Do not equate reference coverage with true semantic sufficiency.
SciFact rationales must be nonempty, in-range, and consistently labelled within a pair. Log overlapping sets or duplicated sentences; do not silently alter sentence identifiers.
Exclusion audit includes all applicable reasons, so reason counts may overlap. Also provide a mutually exclusive hierarchy for cohort flow.

## Frozen retrievers
BM25 k1=1.2 b=.75; word TF-IDF cosine (smoothed IDF and L2 normalization, scikit-learn defaults); MiniLM-L6-v2 mean-pooled masked token embeddings, normalized cosine, pinned official ONNX revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41; lead-position and deterministic random controls.
Lexical tokenization is lowercase Unicode word sequences, no stop-word removal. Tie-break by original unit order. Encoder limit 256 wordpieces including special tokens, batch size 16, CPU two threads; truncation recorded. Encoder's training corpus may overlap these old scientific corpora, so this is not an uncontaminated generalization benchmark.
No training, prompt tuning, stochastic decoding, generation model, or LLM ground-truth judgment.
Seed 20261002. Random control is illustrative; no inference about all random permutations.

## Outcomes and primary comparisons
For references E_1,...,E_m, union U, retrieved units R:
H=1[R intersects U]; C=1[exists j:E_j subset R]; A=1[U subset R].
Primary estimands are mean H-C and mean C-A for BM25 at k=5 QASPER and k=3 SciFact, and corresponding raw H,C,A rates. These inequalities are guaranteed; test effect magnitude, not a tautological null.
Report same outcomes for dense and TF-IDF as robustness and lead/random as controls.
Secondary: union recall |R intersect U|/|U|; max-reference recall; union and max-reference F1; depth d_C=min_j max_{e in E_j} rank(e), d_A=max_{e in U} rank(e); extra units d_A-d_C and lexical-token prefix cost difference.
Report k=1,2,3,5,10 for curves, with long-list k=20 only if preconfigured now. Use k=1,2,3,5,10,20 for main. Values beyond document length saturate and are marked.
Supplementary token-budget prefix curves: 64,128,256,512,1024,2048 lexical tokens. A prefix includes only complete units fitting before the first over-budget unit; do not skip or truncate units. Clearly distinguish lexical tokens from encoder wordpieces. No cross-corpus budget equality claim.

## Statistical analysis
95% percentile cluster bootstrap with 10000 replicates; seed 20261002. Sample clusters with replacement, retain all constituent items and all paired scoring rules/methods. The target is item-weighted means, calculated as summed cluster totals divided by summed cluster sizes. Intervals describe resampling stability within the benchmark's observed cluster structure, not representativeness of all scientific queries.
For cost distributions report mean, median, IQR, and bootstrap interval for mean extra units/tokens.
Do not produce p-values for H>=C>=A. Exploratory method-pair contrasts for C and F1 may use paired cluster sign-flip tests (10000 permutations) and Holm correction across the predeclared family of non-control methods and both datasets; report all, not only reversals. Reversals are descriptive unless both relevant paired differences survive correction. If no tests are needed, report intervals and no claims of statistical significance.
Sample size: census of eligible held-out benchmark items, chosen for feasible coverage, not powered from the pilot effect. No optional stopping or post-result expansion to obtain significance.

## Three robustness families
1. Representation/annotation: QASPER exact normalized answer agreement; distinct/minimal sets; one-reference resampling (100 deterministic selections) to expose dependence on annotation count. The latter deliberately changes reference coverage and is a diagnostic, not a gold replacement.
2. Retrieval/budget: lexical vs dense family, unit vs lexical-token budget, exclude instances whose gold evidence is encoder-truncated for dense sensitivity.
3. Corpus/dependence: per-corpus results; cluster vs item bootstrap sensitivity if needed; alternative observed split replication may be added only as a declared post-main amendment, not silently combined.

## Error analysis and validation
Deterministic categories: no-hit, partial-without-completion, completed-one-not-union, completed-union. Examples selected by stable ID hash within category, not dramatic appearance. Display source IDs and annotation sets; do not reproduce lengthy copyrighted paragraphs.
Cross-check scorer against official functions where definitions match. Verify reported counts and all manuscript values from machine-readable result tables. Investigate annotation version discrepancies before interpretation.
Resumption must validate input/config/code hashes and handle an interrupted final checkpoint. Stop on interior corruption. Preserve original pilot code, all failed checks, and amendments.

## Planned figures and tables
Figures: completion curves by corpus; paired primary gaps and intervals across non-control retrievers; distribution of extra completion depth; topology-stratified differences.
Tables: dataset flow and structure; main outcomes and intervals; completion cost; robustness.
Budget and rank contrasts are secondary and fully disclosed. End when main questions, three robustness families, implementation checks and skeptical reviews are complete; expand only to resolve a concrete flaw.
