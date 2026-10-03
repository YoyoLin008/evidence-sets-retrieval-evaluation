# Table 8. Exploratory annotation case: QASPER. Unit indices are zero-based in the released mapping; source-unit IDs use paper:paragraph:index or abstract:sentence:index. Brief excerpts are from the identified source. No new human semantic validation is claimed.

| Field | Recorded example |
| --- | --- |
| Source IDs | 1804.07445; item 0bde3ecfdd7c4a9af23f53da2cda6cd7a8398220 |
| Question / claim | what language was the data in? |
| Answer / label | English; English ; English |
| Evidence family | E1={24}; E2={20}; E3={24} |
| Exact prefix | [27,29,20,26,0] at k=5 |
| Completion | H=1, C=1, A=0; dC=3, dA=16 |
| Brief unit excerpts | 20: “aligned complex-simple sentence pairs from English Wikipedia”; 24: “the output is grammatical English” |
| Interpretation | All three recorded answers normalize to English; duplicate {24} leaves two distinct singleton alternatives, {20} and {24}, with no nesting. Paragraph 20 describes English Wikipedia pairs, whereas paragraph 24 mentions grammatical English as a fluency criterion. The selected first case is retained despite this difference in how directly the paragraphs support the question. It demonstrates annotation-defined same-answer alternatives; no independent human judgment establishes semantic sufficiency of either singleton. |
