# Table 10. Exploratory annotation case: SciFact. Unit indices are zero-based in the released mapping; source-unit IDs use paper:paragraph:index or abstract:sentence:index. Brief excerpts are from the identified source. No new human semantic validation is claimed.

| Field | Recorded example |
| --- | --- |
| Source IDs | 1180972; item 873:1180972 |
| Question / claim | Obesity is determined solely by environmental factors. |
| Answer / label | CONTRADICT |
| Evidence family | E1={3,4}; E2={6}; E3={7} |
| Exact prefix | [7,0,1] at k=3 |
| Completion | H=1, C=1, A=0; dC=1, dA=8 |
| Brief unit excerpts | 3: “body mass index (kg/m2) significantly increased”; 4: “a steady but weaker increase”; 6: “a striking, significant increase”; 7: “influenced by genetic factors independent of sex” |
| Interpretation | The gold label is CONTRADICT and the family contains the two-sentence set {3,4} plus alternatives {6} and {7}. The retrieved prefix completes {7}, while {6} and {3,4} remain incomplete. This is an annotation-defined alternative-rationale control; completion is not a new semantic validation. |
