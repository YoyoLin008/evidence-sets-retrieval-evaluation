3 October 2026

Dear Editors of Information Retrieval Research,

Please consider “When Evidence Sets Become Relevance Lists: A Controlled Audit of Scientific Retrieval Evaluation” as a Normal Paper. The study asks how choosing an annotation-completion target changes retrieval measurements and uniform budgets while candidates and rankings remain fixed.

The frozen cohorts comprise 875 QASPER questions and 209 SciFact claim–abstract pairs. Primary BM25 gaps between completing one evidence set (C) and its union (A) are 17.8 and 27.8 percentage points; both extra-depth medians are zero, and original primary F1 ordering remains stable. Within 195 exact-answer-agreement questions, pruning changes the gap from 12.3 to 8.2 points, a restricted descriptive result rather than a bound or causal decomposition.

Revision-added exploratory evidence includes a pinned real conversion/scoring path, uniform completion budgets and full-cohort Qwen3-Embedding-0.6B rankings. At 75% QASPER completion, BM25 needs 14 paragraphs for C and 27 for A. The real export preserves union membership for 866 aligned questions after explicit text/candidate restrictions; nine omit evidence memberships. Its ordinary relevance objectives remain appropriate. Qwen's complete-cohort C−A gaps are 23.1 points in QASPER and 27.3 in SciFact. These results quantify target sensitivity without claiming semantic sufficiency, measured reading time or widespread evaluator defects.

Alt et al. (2026) and Li et al. (2025) establish important precedents for complete-set success, Minimal Sufficient Rank and group/union comparisons. Our contribution is a bounded paired measurement audit, structural decomposition, executed representation tracing and uniform-budget interpretation. This empirical focus on evaluation validity fits IRRJ’s scope.

The reproducibility repository is https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation, exact version v1.1.1; its verified Zenodo version family is https://doi.org/10.5281/zenodo.23122619. The tag includes final PDFs, source, frozen plans, code, saved rankings and revision evidence. Data and weights are acquired separately. Historical v1.0.0 remains unchanged.

Generative AI tools (OpenAI Codex) supported grammar checking, language refinement, clarity, and organization. The author conceived the study, made the substantive methodological and interpretive decisions, conducted and verified the research, and wrote the substantive content. Under the author’s direction, tool assistance also supported code edits, reruns, numerical and reference checks, and preparation of figures and manuscript files. The author reviewed AI-assisted material and takes responsibility for the final work. AI is not an author.

I am the sole author and consent to review by IRRJ. The manuscript has not been published in an archival journal or conference, is not under concurrent archival review, and has no separate overlapping paper or preprint. I am not aware of conflicts with IRRJ editorial-board members or other relevant competing interests. No external funding or third-party computational resources were received or used; all experiments ran locally on my personal computer.

Sincerely,  
Yunya Lin  
University of Illinois Urbana-Champaign  
yoyolin2@illinois.edu
