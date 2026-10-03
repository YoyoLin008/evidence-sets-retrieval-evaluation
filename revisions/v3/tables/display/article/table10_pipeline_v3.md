# Table 10. Revision-added real converter/scorer replay on 866 questions in 364 papers, with exact union membership under the stated text mapping and original candidate restriction. Actual Recall/nDCG are conventional relevance measures; C/A are separate completion targets at k=5. The paired gap uses paper-cluster 95% intervals. This is not native pooled-retrieval performance.

| Method | Recall@5 (%) | nDCG@10 (%) | C (%) | A (%) | C−A, pp [CI] |
| --- | --- | --- | --- | --- | --- |
| BM25 | 46.4 | 42.3 | 51.4 | 33.5 | 17.9 [15.4, 20.5] |
| TF-IDF | 44.4 | 42.1 | 49.0 | 31.5 | 17.4 [14.9, 20.0] |
| MiniLM | 48.8 | 46.7 | 55.1 | 33.7 | 21.4 [18.6, 24.3] |
| Lead | 14.2 | 13.9 | 18.1 | 7.4 | 10.7 [8.5, 13.1] |
| Random | 14.0 | 15.5 | 16.3 | 6.7 | 9.6 [7.6, 11.7] |
