# Table 9. Exploratory case panel: QASPER. Preselected BM25 example; all unit indices are zero-based and refer to the released source mapping.

| Field | Recorded example |
| --- | --- |
| Source IDs | Paper 1909.12208; question 14fdc8087f2a62baea9d50c4aa3a3f8310b38d17 |
| Question / claim | What supports the claim that enhancement in training is advisable as long as enhancement in test is at least as strong as in training? |
| Evidence family | E1={17,22,23,34}; E2={23} |
| Exact retrieved prefix | [34,1,2,23,3] at k=5 |
| Scores | H=1; C=1; A=0 |
| Completion depths | dC=4; dA=23; extra depth=19 |
| Interpretation | Paragraph 23 alone completes a selected annotation. The longer reference also contains 17, 22, and 34. Answers disagree under normalization; this case illustrates nesting and should not be read as agreement-free alternative support. |
