# Table 1. Representations and the targets they directly support. The distinction is informational, not a claim of metric invalidity or formal novelty.

| Representation | Documented target | What is still needed for C? |
| --- | --- | --- |
| Flat binary/graded qrels | Recall, AP, nDCG, MRR under their relevance and judgment conventions; H/A from binary union membership. | Accepted combinations cannot generally be recovered from membership alone. |
| Intent or subtopic labels | Intent-weighted utility and coverage of distinct subtopics. | A rule linking labels/units to accepted evidence combinations. |
| Nugget labels and weights | Coverage/importance of information units and redundancy-sensitive gain. | A mapping from semantic coverage to accepted source-evidence combinations. |
| Structured evidence families | H, C, A, and best-reference/union variants, once the target is chosen. | Source validity and semantic sufficiency still require separate evidence. |
