# Real conversion and scoring replay

Revision-added exploratory analysis. Read `plan.json` before results.

Run `python src/revision_v3_pipeline.py --summarize-saved` to rebuild statistics from public per-query scores without raw data, model weights, upstream source or ir_measures.

Run `python src/revision_v3_pipeline.py` after acquiring the original data and installing `requirements.txt`. It fetches three hash-pinned upstream source files into ignored `source_cache/`; full source-text exports stay there. Public outputs contain source IDs, text hashes, qrels, mappings, frozen-rank scorer inputs and derived results. The unchanged native dev loader and the injected data-only wrapper produce identical structures. The same converter then consumes the real frozen test input.

The upstream dataset module is isolated by dropping two unused imports for indexing types; its dataclasses and file loader, and the converter and scorer functions, are executed without body changes. The original upstream `load_jsonl` reloads the actual export exactly. The source scorer uses ir_measures/pytrec_eval; all six measures agree with direct formulas. Retrieval score ties are replaced by strictly decreasing rank values to preserve original deterministic order.

The upstream task pools abstracts and body paragraphs across papers. Controlled replay uses the normalized-text images of original paper-body units and the five saved rankings. The first matching export ID is canonical: 8 of 866 aligned questions map at least one body text to an identical abstract text ID (one involves gold); 90 have duplicate or normalized-equivalent export texts (four involve gold). This is an explicit quotient by original normalized text, not a one-to-one match to raw paragraph occurrences. Abstract-only text and other-paper distractors remain outside the controlled rankings. This scope change is explicit for every item. Exact source-union/qrels membership is a separate axis and must not be confused with identical full task semantics. No whole downstream system, generation, or original published performance is reproduced.

The upstream code documents standard relevance objectives; flat qrels are not A. C/A and overlap scores here are additional annotation-defined contrasts. Lack of grouped output prevents generally reconstructing C, while the implemented original relevance measures remain appropriate to their stated target.
