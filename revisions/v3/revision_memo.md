# Revision memo — v1.1.0

This memo responds to internal revision requests, not to purported IRRJ reviewer comments. The editable baseline is commit `faf730ea4c25161b6b2dc350ff9890e344bc3524`; all four author-specified reference PDFs matched its corresponding project files byte for byte. The original title and protected declarations are retained.

## 1. Positioning and novelty

**Issue:** Complete evidence sets and sufficient stopping depth have precedents. **Change:** Full original Alt et al. (2026) and Li et al. (2025) papers were read; the related-work and methods sections now state C/MSR and group-versus-union precedents explicitly. A bounded recent search adds relevant coverage/sufficiency work and labels September preprints. **Evidence:** `literature/novelty_matrix.md`, `claim_source_ledger.json`, source hashes and verified bibliography. **Limit:** The contribution remains a controlled empirical extension, not a new mathematical completion criterion.

## 2. The 8.2-point sensitivity

**Issue:** A subset-plus-pruning observation was susceptible to being read as a bound or causal explanation. **Change:** Abstract, introduction, results, conclusion and cover letter distinguish subgroup selection from same-item transformation. **Evidence:** 195 questions/149 papers: original 24/195=12.3%, pruned 16/195=8.2%; paired change −4.1 points [−7.1,−1.5]. Complement 680/337: 132/680→87/680; full 875/367: 156/875→103/875. The mutually exclusive question subsets reconstruct the full mean; 119 papers are shared. **Limit:** Exact strings are not semantic agreement; the complement is not semantic conflict. See `statistics/agreement_pruning.csv` and the main paired table.

## 3. Executed conversion and scoring

**Issue:** Isolated fixtures alone did not show an actual workflow. **Change:** A pinned upstream QASPER loader/converter and actual `ir_measures` scorer were executed, with unchanged native dev-loader/data-wrapper parity, real test export, ID mapping and six-metric parity. **Evidence:** 875 main questions intersect; 866 exact membership-aligned under explicit normalized-text/candidate restriction; nine exports omit 14 evidence-unit memberships owing to whitespace-handling differences. All 4,330 original-method aligned rankings were scored. BM25 at k=5 gives C=51.4%, A=33.5%, gap=17.9 points and original R@5=46.4%. **Limit:** Native export expands the candidate pool and paragraph occurrence representation. Ninety aligned questions have duplicate/normalized-equivalent export IDs; eight canonical mappings include identical abstract text. Original metrics are appropriate; no target/implementation mismatch or entire downstream product rerun is claimed. See `pipeline/report.json`, mapping records, score tables and README.

## 4. Explicit budget decision

**Issue:** Mean per-item extra depth does not directly answer a population-budget question. **Change:** Added exact minimum uniform budgets for 50/75/90% completion, lexical whole-prefix counterparts, paired cluster intervals and affected-item distributions. **Evidence:** BM25 QASPER C budgets 5/14/30 versus A 11/27/44; SciFact 2/3/6 versus 3/6/9. At 75% QASPER, the paired unit-budget difference is 13 [10,15]. All thresholds and bootstrap replicates attain completion in the full rankings. **Limit:** These are annotation-defined costs, not reading time or guaranteed inference savings; median individual extra depth remains zero. See `statistics/budget_thresholds.csv`, `cost_distributions.csv` and protocol.

## 5. Modern encoder and cases

**Issue:** The earlier timing omission limited robustness, and the original QASPER case involved nesting/disagreement. **Change:** Completed the predetermined Qwen3-Embedding-0.6B on all original eligible items, plus deterministic same-answer/no-superset case selection. **Evidence:** 20,112 unique inputs, maximum 4,826 model tokens, 0 truncations, CPU float32 and pinned revision; qwen's complete-cohort c−a gaps are 23.1 points in qasper and 27.3 in scifact. The original 5,420 rankings remain unchanged. Sixteen examples qualified and the first SHA-ordered ID was kept. **Limit:** The new example includes an indirect fluency-context paragraph, which is disclosed; no human semantic sufficiency check was invented. One additional model does not establish broad model-family generality. See `encoder/completion_report.json`, `statistics/method_contrasts.csv`, `examples/panels.json`.

## Materials, validation and outstanding boundaries

Original primary, previous post-main and present revision-added analyses remain separate. Source-backed prose models prevent regenerated PDFs from reverting edits. The official style is unchanged; the reading copy shares the main content model. The accompanying QA report records actual tests, numeric replay, all-page visual inspection and artifact hashes. Package construction preserves old v1.0.0 and uses concept DOI plus exact tag in frozen documents; publication verification subsequently records the new real version DOI without replacing frozen files.

No independent human semantic annotation, external independent replication, deployment-cost study or ecosystem-wide prevalence estimate was performed. These remain scientific limits, not missing tasks required by this revision. Formal IRRJ submission and any new journal terms remain author actions. The [reviewer-risk table](reviewer_risks.md) covers eight concerns; authorship/disclosure was explicitly excluded from this revision's editing scope.
