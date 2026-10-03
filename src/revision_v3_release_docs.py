"""Generate release-facing research prose from completed revision result files."""
from pathlib import Path
import json
import pandas as pd
R=Path(__file__).resolve().parents[1]
def put(rel,text):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n')
def main():
 from revision_v3_manuscript import Revision
 Revision(R, require_qwen=True)
 val=json.loads((R/'revisions/v3/statistics/validation.json').read_text())
 assert val['ranking_rows']==6504 and 'qwen3' in val['methods'],'Complete six-method statistics required'
 completion=json.loads((R/'revisions/v3/encoder/completion_report.json').read_text())
 p=pd.read_csv(R/'revisions/v3/statistics/primary.csv')
 def v(d,m,metric):
  a=p[(p.dataset==d)&(p.method==m)&(p.metric==metric)];assert len(a)==1;return float(a.iloc[0]['mean'])
 qgap=v('qasper','qwen3','complete_without_union')*100;sgap=v('scifact','qwen3','complete_without_union')*100
 qline=f"Qwen's complete-cohort C−A gaps are {qgap:.1f} points in QASPER and {sgap:.1f} in SciFact"
 protected=json.loads((R/'revisions/v3/protected_declarations.json').read_text())
 declaration='I am the sole author and consent to review by IRRJ. The manuscript has not been published in an archival journal or conference, is not under concurrent archival review, and has no separate overlapping paper or preprint. I am not aware of conflicts with IRRJ editorial-board members or other relevant competing interests. No external funding or third-party computational resources were received or used; all experiments ran locally on my personal computer.'
 old=(R/'paper/cover_letter.md').read_text();assert declaration in old and protected['ai_disclosure'] in old
 put('paper/cover_letter.md',f'''3 October 2026

Dear Editors of Information Retrieval Research,

Please consider “When Evidence Sets Become Relevance Lists: A Controlled Audit of Scientific Retrieval Evaluation” as a Normal Paper. The study asks how choosing an annotation-completion target changes retrieval measurements and uniform budgets while candidates and rankings remain fixed.

The frozen cohorts comprise 875 QASPER questions and 209 SciFact claim–abstract pairs. Primary BM25 gaps between completing one evidence set (C) and its union (A) are 17.8 and 27.8 percentage points; both extra-depth medians are zero, and original primary F1 ordering remains stable. Within 195 exact-answer-agreement questions, pruning changes the gap from 12.3 to 8.2 points, a restricted descriptive result rather than a bound or causal decomposition.

Revision-added exploratory evidence includes a pinned real conversion/scoring path, uniform completion budgets and full-cohort Qwen3-Embedding-0.6B rankings. At 75% QASPER completion, BM25 needs 14 paragraphs for C and 27 for A. The real export preserves union membership for 866 aligned questions after explicit text/candidate restrictions; nine omit evidence memberships. Its ordinary relevance objectives remain appropriate. {qline}. These results quantify target sensitivity without claiming semantic sufficiency, measured reading time or widespread evaluator defects.

Alt et al. (2026) and Li et al. (2025) establish important precedents for complete-set success, Minimal Sufficient Rank and group/union comparisons. Our contribution is a bounded paired measurement audit, structural decomposition, executed representation tracing and uniform-budget interpretation. This empirical focus on evaluation validity fits IRRJ’s scope.

The reproducibility repository is https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation, exact version v1.1.0; its verified Zenodo version family is https://doi.org/10.5281/zenodo.23122619. The tag includes final PDFs, source, frozen plans, code, saved rankings and revision evidence. Data and weights are acquired separately. Historical v1.0.0 remains unchanged.

{protected['ai_disclosure']}

{declaration}

Sincerely,  
Yunya Lin  
University of Illinois Urbana-Champaign  
yoyolin2@illinois.edu''')
 put('README.md',f'''# When Evidence Sets Become Relevance Lists

**When Evidence Sets Become Relevance Lists: A Controlled Audit of Scientific Retrieval Evaluation**  
Yunya Lin · University of Illinois Urbana-Champaign

Reproducibility package **v1.1.0** for an IRRJ Normal Paper submission manuscript. This is not an accepted journal article. The contribution is an empirical measurement audit, building on established complete-set, sufficient-rank and group-versus-union evaluation.

- **H**: at least one annotated unit retrieved.
- **C**: every unit of at least one original annotated set retrieved.
- **A**: every unit in the union of original annotations retrieved.

Flat qrels support their intended relevance metrics. They do not automatically choose A, and membership alone cannot generally reconstruct C. Annotation completion is not independently certified semantic sufficiency or downstream answer quality.

## Original frozen study

The main cohorts are 875 QASPER questions (367 papers, within-paper paragraphs) and 209 SciFact claim–abstract pairs (164 connected claim/document clusters, within-abstract sentences). BM25, TF-IDF and MiniLM are retrievers; lead and seeded random are controls. Original cohorts, 5,420 complete rankings and 32,520 six-budget points remain unchanged.

| Primary BM25 outcome | QASPER, k=5 | SciFact, k=3 |
|---|---:|---:|
| H | 65.0% | 83.7% |
| C | 51.0% | 79.4% |
| A | 33.1% | 51.7% |
| C−A | 17.8 pp | 27.8 pp |
| Mean extra union depth | 6.65 paragraphs | 2.02 sentences |
| Median extra union depth | 0 | 0 |

No original primary F1 ranking reversal was observed. Zero extra depth occurs in 54.9% and 59.3% of items; costs are unevenly distributed.

## What v1.1 adds and narrows

- **Paired pruning versus cohort selection.** Among 195 exact normalized-answer-agreement questions in 149 papers, C−A is 12.3 points before pruning and 8.2 afterward; paired change −4.1 points (95% cluster interval −7.1 to −1.5). This is neither a full-cohort bound nor a causal estimate of answer disagreement. The 680-question complement is not synonymous with semantic conflict. The subsets share 119 papers.
- **A real converter and scorer.** Pinned sscc-rag-paper conversion and six actual relevance metrics were executed. All 875 main questions intersect the test export; 866 align exactly in union membership under an explicit normalized-text/candidate restriction. Nine exports omit 14 evidence-unit memberships owing to whitespace matching. Native candidates include abstracts and cross-paper distractors; controlled replay retains original normalized body-text units. Duplicate/abstract-ID mappings are disclosed. No whole downstream product was run, and no objective/implementation mismatch was established.
- **Uniform budgets.** For BM25 to complete 75% of QASPER items, C requires 14 paragraphs and A 27; SciFact requires 3 versus 6 sentences. All 50%, 75% and 90% unit/lexical thresholds and paired intervals are retained. These are annotation-defined population budgets, not mean individual costs or measured time.
- **Complete Qwen robustness.** {qline}. The sole predetermined new model completed all 1,084 eligible items using CPU float32, pinned weights/tokenizer, query-only instruction, last-token pooling and normalized 1,024-dimensional vectors. There were {completion['truncated_unique_inputs']} truncated unique inputs. The old timing-gate omission remains a historical decision, superseded by this complete run.
- **Deterministic examples and narrower novelty.** The first SHA-ordered qualifying example from 16 candidates is retained even though one paragraph supports the question indirectly. No human semantic validation is claimed. Alt and Li precedents and recent related work are explicitly credited.

Combined original-plus-Qwen totals are 6,504 rankings and 39,024 points at the six original budgets. Added exact integer-budget threshold calculations are separate. All additions are post-main exploratory; no retrospective original preregistration is claimed.

## Reproduce and inspect

Start with [revision reproduction instructions](docs/revision_v1.1_reproduction.md). They provide saved-ranking reconstruction without source text/embeddings and separate source-based/full-inference routes. Python 3.12.14 on ARM64 macOS was used. `requirements.lock.txt`, the encoder lock and the pipeline requirements identify distinct environments. An existing `pdflatex` installation exports official-style PDFs; no TeX software is installed by the build.

```sh
.venv/bin/python src/revision_v3_statistics.py --rankings-only --qwen revisions/v3/encoder/rankings.jsonl
.venv/bin/python src/revision_v3_pipeline.py --summarize-saved
.venv/bin/python src/render_final.py
```

For original acquisition, use `src/prepare.py`; original source-based saved-ranking replay is `src/replay_saved.py` in an empty output directory. To infer original rankings instead, use a separate clean clone with `src/main_study.py`. Do not write into frozen historical outputs. The full analysis/replay, technical configuration and validation evidence are linked in the stream READMEs under `revisions/v3/`.

The editable sources are `paper/article_blocks_1.json`, `article_blocks_2.json` and `supplement_blocks.json`; references are generated from `literature/verified_references.json`. Official and reading versions share one scientific content model. **Use the official manuscript, official supplement and cover letter for submission; the reading copy is for convenience.** See [submission checklist](revisions/v3/submission_checklist.md).

## Files and provenance

`reference_outputs/`, `tables/` and `logs/frozen_main_v1/` retain original results and freeze evidence. `revisions/v2/` retains earlier post-main topology, audit and timing results. `revisions/v3/` contains new protocols, statistics, executed pipeline mappings, encoder rankings/fingerprints, examples, literature comparison, revision memo and QA. `release_artifacts/` contains the submission ZIP, asset manifest and SHA-256 list. `PACKAGE_MANIFEST.json` checks the public tree before reproduction modifies it.

The archive excludes full source corpora, model weights, virtual environments, downloaded project collections, full literature PDFs and private operational material. URLs and acquisition hashes identify those inputs. The local study freeze is not public preregistration; actual public Git history begins with submission preparation.

## Versions and citation

Current package: [v1.1.0 release](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.1.0). Frozen documents cite the verified [Zenodo concept DOI 10.5281/zenodo.23122619](https://doi.org/10.5281/zenodo.23122619) together with the exact tag. The concept DOI identifies the version family. The version-specific DOI is recorded in release notes and publication verification only after automatic archiving succeeds; frozen same-version files are not replaced to insert it.

Historical [v1.0.0](https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.0.0), [DOI 10.5281/zenodo.23122620](https://doi.org/10.5281/zenodo.23122620), remains unchanged. Its tag commit is `ed2d6f6ca6f3e17b3b89c593bda5668c83b44e78`. Zenodo automatically archives the tagged source snapshot, not arbitrary GitHub assets; all four PDFs and the submission ZIP are therefore included in the new tag.

## Licensing and responsibility

Code and usage documentation: [MIT](LICENSE). Original scholarly materials and derived results: [CC BY 4.0](LICENSE-CONTENT). Third-party materials retain their own terms; see [LICENSES.md](LICENSES.md). These licenses do not relicense datasets, models, papers or the official journal style. See [CITATION.cff](CITATION.cff).

Author-confirmed authorship, AI and funding disclosures remain unchanged. The human author retains responsibility; no external funding or third-party computational resources were used. Contact: yoyolin2@illinois.edu. IRRJ formal submission has not been performed by this workflow.
''')
 put('revisions/v3/revision_memo.md',f'''# Revision memo — v1.1.0

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

**Issue:** The earlier timing omission limited robustness, and the original QASPER case involved nesting/disagreement. **Change:** Completed the predetermined Qwen3-Embedding-0.6B on all original eligible items, plus deterministic same-answer/no-superset case selection. **Evidence:** {completion['unique_inputs']:,} unique inputs, maximum {completion['max_model_tokens']:,} model tokens, {completion['truncated_unique_inputs']} truncations, CPU float32 and pinned revision; {qline.lower()}. The original 5,420 rankings remain unchanged. Sixteen examples qualified and the first SHA-ordered ID was kept. **Limit:** The new example includes an indirect fluency-context paragraph, which is disclosed; no human semantic sufficiency check was invented. One additional model does not establish broad model-family generality. See `encoder/completion_report.json`, `statistics/method_contrasts.csv`, `examples/panels.json`.

## Materials, validation and outstanding boundaries

Original primary, previous post-main and present revision-added analyses remain separate. Source-backed prose models prevent regenerated PDFs from reverting edits. The official style is unchanged; the reading copy shares the main content model. The accompanying QA report records actual tests, numeric replay, all-page visual inspection and artifact hashes. Package construction preserves old v1.0.0 and uses concept DOI plus exact tag in frozen documents; publication verification subsequently records the new real version DOI without replacing frozen files.

No independent human semantic annotation, external independent replication, deployment-cost study or ecosystem-wide prevalence estimate was performed. These remain scientific limits, not missing tasks required by this revision. Formal IRRJ submission and any new journal terms remain author actions. The [reviewer-risk table](reviewer_risks.md) covers eight concerns; authorship/disclosure was explicitly excluded from this revision's editing scope.
''')
 cff=(R/'CITATION.cff').read_text().replace('version: 1.0.0','version: 1.1.0').replace('doi: "10.5281/zenodo.23122620"','doi: "10.5281/zenodo.23122619"')
 if 'url:' not in cff:cff+='url: "https://github.com/YoyoLin008/evidence-sets-retrieval-evaluation/releases/tag/v1.1.0"\n'
 (R/'CITATION.cff').write_text(cff)
 landing=R/'docs/release_landing_v1.1.md'
 if landing.exists():
  readme=R/'README.md';readme.write_text(readme.read_text()+'\n'+landing.read_text())
 print('Generated README, cover research prose, revision memo and citation metadata from complete results.')
if __name__=='__main__':main()
