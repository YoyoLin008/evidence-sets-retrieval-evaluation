# Table 5. Extra fixed-ranking prefix budget required for the union instead of one original reference. Means have 95% cluster intervals; depth medians have interquartile ranges. Lexical tokens are not encoder wordpieces. Qwen3 is revision-added exploratory.

| Corpus | Method | Extra units: mean [CI] | Median [IQR] | Extra tokens: mean [CI] |
| --- | --- | --- | --- | --- |
| QASPER | BM25 | 6.65 [5.69, 7.70] | 0 [0, 7] | 540.9 [463.7, 624.0] |
| QASPER | TFIDF | 6.61 [5.67, 7.63] | 0 [0, 8] | 540.9 [463.7, 623.8] |
| QASPER | MiniLM | 6.22 [5.41, 7.09] | 0 [0, 8] | 509.3 [440.3, 581.4] |
| QASPER | Qwen3 | 5.89 [5.15, 6.67] | 0 [0, 8] | 474.2 [414.2, 537.9] |
| SciFact | BM25 | 2.02 [1.48, 2.63] | 0 [0, 3] | 58.5 [43.0, 76.3] |
| SciFact | TFIDF | 2.04 [1.51, 2.63] | 0 [0, 3] | 59.5 [43.9, 77.0] |
| SciFact | MiniLM | 1.87 [1.33, 2.53] | 0 [0, 3] | 54.6 [39.4, 72.7] |
| SciFact | Qwen3 | 1.61 [1.20, 2.05] | 0 [0, 2] | 47.6 [35.7, 60.7] |
