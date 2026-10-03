# Prospective pilot plan
Created before scoring, 2026-10-02 America/Chicago. Local timestamp/hash will be recorded in logs/plan_freezes.jsonl. Not publicly preregistered.

## Candidate and estimand
Candidate A: loss of evidence-set structure in retrieval evaluation. Ground truth is released annotated sets, not actual semantic sufficiency. A retrieved set R completes a reference if at least one nonempty gold set E is contained in R. Flat hit means intersection with union(E) is nonempty; union completion means union(E) is contained in R. These inequalities are mathematical, not hypotheses requiring significance tests.

## Pilot scope
QASPER: first 30 development papers sorted by SHA256(paper ID), all eligible questions within them.
SciFact: first 50 training claims sorted by SHA256(claim ID), all gold claim–abstract pairs.
Held-out main: QASPER test (do not read until configuration frozen) and SciFact development. The latter was inspected only for schema and annotation counts, not scored.

## Eligibility
QASPER questions: reject if any answer is unanswerable, if any evidence list is empty, if any annotation requires FLOAT SELECTED, or if any evidence paragraph cannot be uniquely mapped after whitespace normalization. Keep complete reference lists; never remove a difficult piece to make a set easier. Canonicalize identical paragraph text to one content identity; count and report duplicates. Preserve answer variants for later sensitivity.
SciFact: evidence-bearing claim–abstract pairs with nonempty, in-range, consistently labelled sentence sets. Work within known relevant abstracts to isolate rationale selection; no claim of open-corpus retrieval performance.

## Retrieval and scoring
BM25 (k1=1.2,b=.75); word TF-IDF cosine; leading-position and seeded random controls. Lexical tokenization: Unicode word tokens, lower case. Deterministic content-order tie break. Primary pilot k: 1,2,3,5,10 units clipped to available units. No generator, prompts, decoding, or paid API.
For each R compute any-hit, max-reference recall, union recall, max-reference F1, union F1, any-reference completion, union completion, and the minimal depth in the full ranking to complete one reference versus the union.
Retain per-instance rankings, raw scores, evidence IDs, exclusions, timings, configuration hash, and completion records. Exclude pilot items from any later confirmatory use of their splits.

## Tests before pilot
Hand-computed empty/partial/complete/alternative sets; duplicate content; Unicode tokenization; mapping failures; deterministic tie order; resume idempotence; BM25 against an independent small calculation; scorer comparison with official QASPER/SciFact relevant functions where definitions match.
Pilot purpose: validate acquisition, parsing, runtime, score identities, and detect artefacts. No hypothesis selection by preferred result. Main plan must freeze after repairs and before test evaluation.
