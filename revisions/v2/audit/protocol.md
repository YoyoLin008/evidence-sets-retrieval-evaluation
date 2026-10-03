# Revision-v2 exploratory ecosystem audit protocol
Frozen before inspection of additional implementation behavior. Search cutoff: 2026-10-03 UTC (2026-10-02 America/Chicago). This is post-main and not a preregistered confirmatory audit.

## Prior knowledge
The producing agent previously inspected the official QASPER and SciFact evaluators and knows that their relevant official objectives preserve alternative evidence sets. These are reference cases, not newly discovered findings or a random prevalence sample. Planning explored IR literature and the optional Qwen model card, but did not classify additional QASPER/SciFact implementations.

## Discovery
For benchmark in {QASPER, SciFact}, phrase in {dataset loader, evidence retrieval evaluation, qrels conversion, RAG benchmark}, and domain in {github.com, huggingface.co/datasets}, issue the sixteen exact neutral searches: site:DOMAIN BENCHMARK "PHRASE". Record returned order and first ten available results, including irrelevant results and fewer-than-ten returns. Search-engine results are bounded and not exhaustive. Record exact dates and queries. No searches favoring "flatten", "bug", or a desired conclusion.
If quoted searches return few results, retain that outcome; do not silently broaden or replace them. Original project implementations and their official dataset distributions are separate reference cases.

## Eligibility, sampling and unit
A candidate must expose public code or inspectable dataset structure that loads, converts, distributes, or evaluates QASPER or SciFact. Mere mention, tutorials without such artifacts, search navigation pages, and unrelated datasets are excluded with reason. Unavailable plausible candidates remain in the log as inaccessible/undetermined.
Unit: a canonical project lineage's benchmark-specific source-to-output pipeline. Multiple inspected files support a single unit; mirrored/forked identical implementation lineages are not independent cases. When a family exposes alternative pathways, classify the available outputs together, recording the distinction.
Identify candidates and source-level provenance before classifying behavior. Inspect all eligible downstream families up to fifteen per benchmark. If more qualify, select the fifteen smallest SHA-256 hashes of normalized canonical family identifiers separately by benchmark. Preserve unselected candidates in the ledger. Reference cases are not included in downstream counts.

## Classification
preserved: source evidence-family grouping can be recovered at the relevant unit granularity; nested lists suffice without explicit set IDs.
flat_only: output retains annotated unit membership at the same granularity but omits grouping required to recover original evidence sets.
both_exposed: both family-preserving and flat outputs are explicitly available within the inspected pipeline.
other_not_applicable: changed task/granularity, selected single reference, no relational input available, answer-only output, or another transformation not representing the defined same-granularity intervention.
undetermined: insufficient accessible code/data to trace the relevant operation.

Record whether all observed annotated units are preserved. Flat-only grouping loss with unit deletion is not an exact instance of the paper's union-preserving intervention. Distinguish paragraph/sentence relevance from document-level qrels; document-level SciFact conversions do not alone establish sentence-rationale flattening. A flat metric does not establish that its input loader discarded structure.

## Evidence and verification
For each unit record benchmark, canonical URL, version/commit, inspected file and line span or dataset schema, source/output granularity, conversion/evaluation path, class, retention of all annotated units, evidence summary, fixture status, limitations, and reviewer pass.
Pin sources to commits or retrieved bytes/SHA-256. Trace source→conversion→scoring when accessible. Run isolated minimal conversion fixtures when the relevant function can be exercised without executing an untrusted project. Verify remaining cases statically; mark that difference. A second code-reading pass rechecks the evidence; it is same-agent consistency checking, not independent annotation or inter-rater agreement.

## Reporting
Report counts and denominators for downstream families separately by benchmark, with five classes and reference cases separate. Show unknown/inapplicable cases explicitly. For the narrower union-preserving same-granularity intervention, report only cases directly supporting that condition. No population prevalence estimate or significance test is justified. Few/no flattening cases must remain visible and narrow practical claims.

## Other post-main additions
Topology uses four mutually exclusive groups: one distinct set; >1 distinct with one minimal; multiple minimal without strict supersets; multiple minimal with strict supersets. BM25 primary depths and existing cluster conventions remain fixed. Supplemental modifiers are singleton availability and QASPER normalized answer agreement. Empty cells are explicit; fewer than ten clusters are flagged sparse. No primary rankings or cohorts change.
Optional modern retriever: Qwen3-Embedding-0.6B only, pinned official revision, float32 CPU, 1024 dimensions, last-token pooling, normalized cosine, 8192 token cap, fixed instruction "Given a scientific question or claim, retrieve passages that provide evidence relevant to it". The feasibility trial is deterministic and label/score blind. Sample 32 texts by SHA-256 from each tokenizer-length quartile, plus the longest text in each quartile if absent; estimate full runtime with bin-wise mean time and full bin counts. Gate: projected full inference <=7200 seconds on the local CPU. Otherwise omit without substitute or selected partial effectiveness. Timing failures and resource limits are reported. The runtime configuration is frozen before the first timed inference.
