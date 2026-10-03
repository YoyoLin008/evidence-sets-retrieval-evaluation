# Real annotation panels

Revision-added exploratory presentation. Unit indexes are zero-based. Short quotations reproduce annotation-source text; full passages are not republished. All other evidence discussion is paraphrase. No new human semantic annotation was performed.

The new QASPER selection had 16 eligible questions. The first SHA-256 ID was retained, with known original outcomes and no substitution.

## retained preselected qasper case

Source: 14fdc8087f2a62baea9d50c4aa3a3f8310b38d17 / 1909.12208.
Question/claim: What supports the claim that enhancement in training is advisable as long as enhancement in test is at least as strong as in training?
Answers/label: ['Paraphrase: an extensive experimental evaluation on difficult CHiME-5 dinner-party data.', 'Paraphrase: training enhancement improves accuracy provided it is no stronger than test enhancement.']
Original evidence family: [[17, 22, 23, 34], [23]]; exact BM25 prefix at k=5: [34, 1, 2, 23, 3].
H/C/A = 1/1/0; d_C=4, d_A=23.

- 1909.12208:paragraph:17: “Experiments were performed using the CHiME-5 data.”
- 1909.12208:paragraph:22: “An extensive set of experiments”
- 1909.12208:paragraph:23: “the recognition accuracy improves monotonically”
- 1909.12208:paragraph:34: “CHiME-5 dinner party data”

The singleton {23} is nested within {17,22,23,34}; completing the singleton makes C=1 before the full union is covered. The two recorded normalized answers differ. This illustrates annotation nesting and answer-text variation, not same-answer alternative sufficient evidence.

## new agreement/no-superset hash-selected case

Source: 0bde3ecfdd7c4a9af23f53da2cda6cd7a8398220 / 1804.07445.
Question/claim: what language was the data in?
Answers/label: ['English', 'English ', 'English']
Original evidence family: [[24], [20], [24]]; exact BM25 prefix at k=5: [27, 29, 20, 26, 0].
H/C/A = 1/1/0; d_C=3, d_A=16.

- 1804.07445:paragraph:20: “aligned complex-simple sentence pairs from English Wikipedia”
- 1804.07445:paragraph:24: “the output is grammatical English”

All three recorded answers normalize to English; duplicate {24} leaves two distinct singleton alternatives, {20} and {24}, with no nesting. Paragraph 20 describes English Wikipedia pairs, whereas paragraph 24 mentions grammatical English as a fluency criterion. The selected first case is retained despite this difference in how directly the paragraphs support the question. It demonstrates annotation-defined same-answer alternatives; no independent human judgment establishes semantic sufficiency of either singleton.

## retained preselected scifact case

Source: 873:1180972 / 1180972.
Question/claim: Obesity is determined solely by environmental factors.
Answers/label: CONTRADICT
Original evidence family: [[3, 4], [6], [7]]; exact BM25 prefix at k=3: [7, 0, 1].
H/C/A = 1/1/0; d_C=1, d_A=8.

- 1180972:sentence:3: “body mass index (kg/m2) significantly increased”
- 1180972:sentence:4: “a steady but weaker increase”
- 1180972:sentence:6: “a striking, significant increase”
- 1180972:sentence:7: “influenced by genetic factors independent of sex”

The gold label is CONTRADICT and the family contains the two-sentence set {3,4} plus alternatives {6} and {7}. The retrieved prefix completes {7}, while {6} and {3,4} remain incomplete. This is an annotation-defined alternative-rationale control; completion is not a new semantic validation.
