"""Data-linked revision-v2 manuscript tables; no changes to frozen estimates."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def enrich(doc):
 out=ROOT/'revisions/v2';tables=doc['tables'];t=pd.read_csv(out/'tables/topology_disjoint.csv');provenance={}
 def fmt(r,scale=1,digits=1):
  if pd.isna(r['mean']):return '—'
  return f"{r['mean']*scale:.{digits}f} [{r['lo']*scale:.{digits}f}, {r['hi']*scale:.{digits}f}]"
 tables['representations']={'caption':'Representations and the targets they directly support. The distinction is informational, not a claim of metric invalidity or formal novelty.','headers':['Representation','Documented target','What is still needed for C?'],'rows':[
 ['Flat binary/graded qrels','Recall, AP, nDCG, MRR under their relevance and judgment conventions; H/A from binary union membership.','Accepted combinations cannot generally be recovered from membership alone.'],
 ['Intent or subtopic labels','Intent-weighted utility and coverage of distinct subtopics.','A rule linking labels/units to accepted evidence combinations.'],
 ['Nugget labels and weights','Coverage/importance of information units and redundancy-sensitive gain.','A mapping from semantic coverage to accepted source-evidence combinations.'],
 ['Structured evidence families','H, C, A, and best-reference/union variants, once the target is chosen.','Source validity and semantic sufficiency still require separate evidence.']], 'widths':[107,164,161]}
 examples=json.loads((out/'analysis/concept_example.json').read_text());letters={0:'a',1:'b',2:'c',3:'d'}
 tables['concept']={'caption':'Illustrative family E1={a,b}, E2={c}. Brackets denote retrieved order; d is unannotated.','headers':['Retrieved prefix','H','C','A'],'rows':[['['+','.join(letters[i] for i in r['prefix'])+']',str(r['hit']),str(r['complete']),str(r['union_complete'])] for r in examples],'widths':[237,65,65,65]}
 names=['One distinct set','Multiple sets, one minimal','Multiple minimal, no supersets','Multiple minimal plus supersets'];rows=[];costs=[]
 for d in ['qasper','scifact']:
  for cat,label in enumerate(names):
   sub=t[(t.dataset==d)&(t.method=='bm25')&(t.category==cat)];r=sub[sub.metric=='complete_without_union'].iloc[0];dep=sub[sub.metric=='depth_penalty'].iloc[0];tok=sub[sub.metric=='tokens_penalty'].iloc[0]
   rows.append([d.upper()+': '+label,str(int(r.n))+'/'+str(int(r.clusters)),fmt(r,100),f"{r.contribution*100:.2f} [{r.contribution_lo*100:.2f}, {r.contribution_hi*100:.2f}]" if r.n else '0 (empty)'])
   if r.n:costs.append([d.upper()+': '+label,fmt(dep,1,2),fmt(tok,1,1)])
 tables['topology_gaps']={'caption':'Exploratory post-main, mutually exclusive topology strata at BM25 primary budgets. n/g gives items/represented clusters. Gap and full-cohort contribution are percentage points with 95% cluster intervals; represented clusters can overlap across strata. Empty categories are shown explicitly.','headers':['Corpus and category','n/g','C−A, pp [CI]','Contribution, pp [CI]'],'rows':rows,'widths':[153,49,115,115]}
 tables['topology_costs']={'caption':'Exploratory post-main completion costs in each populated topology category. Values are mean additional ranked units and lexical tokens with 95% cluster intervals. Units are QASPER paragraphs or SciFact sentences; category denominators are in the preceding table.','headers':['Corpus and category','Extra units [CI]','Extra lexical tokens [CI]'],'rows':costs,'widths':[173,117,142]}
 audit=json.loads((out/'audit/counts.json').read_text());classes=[('preserved','Preserved'),('flat_only','Flat only'),('both_exposed','Both exposed'),('other_not_applicable','Other / not applicable'),('undetermined','Undetermined')]
 tables['ecosystem']={'caption':'Exploratory bounded downstream implementation sample. Counts describe fifteen selected families per benchmark, not population prevalence. The two official evaluator reference families are excluded and retain alternatives for their relevant objectives.','headers':['Representation class','QASPER','SciFact'],'rows':[[label,str(audit['counts']['QASPER'][k]),str(audit['counts']['SciFact'][k])] for k,label in classes]+[['Total inspected','15','15']], 'widths':[244,94,94]}
 panels=json.loads((out/'analysis/case_panels.json').read_text())
 for x in panels:
  d=x['dataset'];gold='; '.join('E'+str(j+1)+'={'+','.join(map(str,e))+'}' for j,e in enumerate(x['gold']));s=x['scores'];cost=x['costs']
  interpretation=('Paragraph 23 alone completes a selected annotation. The longer reference also contains 17, 22, and 34. Answers disagree under normalization; this case illustrates nesting and should not be read as agreement-free alternative support.' if d=='qasper' else 'Sentence 7 alone is a complete annotated rationale. The other observed rationales contain {3,4} and {6}. The source statement concerns genetic influences on obesity; completion is not an endorsement of the claim’s wording.')
  source=('Paper 1909.12208; question '+x['id'] if d=='qasper' else 'Claim 873; abstract 1180972')
  tables['case_'+d]={'caption':'Exploratory case panel: '+d.upper()+'. Preselected BM25 example; all unit indices are zero-based and refer to the released source mapping.','headers':['Field','Recorded example'],'rows':[
   ['Source IDs',source],['Question / claim',x['query']],['Evidence family',gold],['Exact retrieved prefix','['+','.join(map(str,x['retrieved']))+'] at k='+str(x['k'])],['Scores',f"H={s['hit']}; C={s['complete']}; A={s['union_complete']}"],['Completion depths',f"dC={cost['depth_complete']}; dA={cost['depth_union']}; extra depth={cost['depth_penalty']}"],['Interpretation',interpretation]],'widths':[98,334]}
 # Retain artifact roles separately: reading copy and official native source.
 doc['abstract']+=' An exploratory bounded implementation audit distinguishes unavailable evidence grouping from preserved alternatives and deliberate changes of retrieval task.'
 doc['analysis_status']='Topology and implementation audit are exploratory and post-main'
 provenance={'tables':{'topology_gaps':'revisions/v2/tables/topology_disjoint.csv','topology_costs':'revisions/v2/tables/topology_disjoint.csv','ecosystem':'revisions/v2/audit/counts.json','concept':'revisions/v2/analysis/concept_example.json','case_qasper':'revisions/v2/analysis/case_panels.json','case_scifact':'revisions/v2/analysis/case_panels.json','representations':'Primary-source definitions in revisions/v2/literature/claim_source_ledger.json'},'abstract':'Original numeric registry plus exploratory audit summary','analysis_status':doc['analysis_status']}
 (ROOT/'revisions/final/analysis/manuscript_table_provenance.json').write_text(json.dumps(provenance,indent=2))
 return doc
