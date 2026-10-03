# Data dictionary and provenance
Raw sources and their URLs, UTC acquisition times, byte sizes, and SHA-256 hashes are in data/acquisition_manifest.json. configs/acquisition_expected.json records the expected bytes for reproduction. QASPER is v0.3; SciFact's URL is named latest, so its hash, not the mutable label, identifies this study's release.

## Analysis units
QASPER: question nested in paper, scientific paper paragraphs from full_text. Identical whitespace-normalized paragraphs collapse to one content ID. Every answer annotation must be answerable with nonempty textual evidence wholly matching the paper. FLOAT SELECTED annotations, missing evidence, and unmapped paragraphs cause whole-question exclusion. Reasons overlap; the mutually exclusive flow uses alphabetically first reason.

SciFact: evidence-bearing claim–abstract pair. Candidate units are all abstract sentences, preserving original zero-based IDs. Labels must agree within a pair. Gold abstract is supplied: this is rationale retrieval, not abstract discovery or verdict prediction. No-evidence claims are excluded, and they are a different audit grain from evidence pairs. Cluster IDs denote connected components sharing claim or document.

## Processed schemas
outputs/main_v1/instances.jsonl: dataset, split, id, cluster, query, units, gold (list of lists of zero-based unit IDs), metadata.
outputs/main_v1/audit.jsonl: eligibility and all exclusion reasons.
outputs/main_v1/rankings.jsonl: full deterministic ranking, scores aligned to original unit order, references, topology, completion costs, all k outcomes, config/source/instance hashes.
outputs/main_v1/dense_audit.jsonl: query truncation, unit indices truncated at 256 wordpieces including special tokens, any annotated unit truncated.
tables/*.csv: numeric estimates, denominators, 95% percentile cluster intervals, token budgets, strata and sensitivity variants.

## Licenses and sharing
QASPER release declares CC BY 4.0. SciFact declares CC BY 4.0 for claims/annotations, ODC-By 1.0 for the abstract corpus, and Apache 2.0 for its code; see saved official license. The MiniLM model card declares Apache 2.0. Cite the source papers and retain the original license notices. The local workspace keeps acquired source text for reproducibility. The shareable code package uses acquisition scripts and derived IDs/scores rather than redistributing entire source papers, literature PDFs, or pretrained weights. No public upload has occurred.
