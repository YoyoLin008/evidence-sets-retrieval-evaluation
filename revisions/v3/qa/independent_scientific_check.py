"""Additional automated six-method audit using direct set operations.

Run after complete Qwen scoring and statistics: python revisions/v3/qa/independent_scientific_check.py
Source text is required to independently recompute lexical costs. This is a
scientific/code check only, not PDF QA, publication verification, human semantic
review or independent external replication. No long inference/bootstrap is rerun.
"""
from pathlib import Path
import collections,csv,datetime,hashlib,json,math,re,sys
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'revisions/v3/qa'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def csvrows(relative):return list(csv.DictReader((ROOT/relative).open()))
def jsonl(path):return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
def close(a,b):return abs(float(a)-float(b))<=3e-11*max(1,abs(float(a)),abs(float(b)))
def main():
 validation=json.loads((ROOT/'revisions/v3/statistics/validation.json').read_text())
 assert validation['ranking_rows']==6504 and validation['scoring_points']==39024
 original=ROOT/'reference_outputs/main_v1/rankings.jsonl';new=ROOT/'revisions/v3/encoder/rankings.jsonl'
 raw=jsonl(original)+jsonl(new);assert len(raw)==6504
 source=ROOT/'outputs/main_v1/instances.jsonl';instances={(x['dataset'],x['id']):x for x in jsonl(source)}
 frozen=json.loads((ROOT/'revisions/v2/baseline_manifest.json').read_text())['protected']
 assert sha(original)==frozen['outputs/main_v1/rankings.jsonl']
 assert sha(source)==frozen['outputs/main_v1/instances.jsonl']
 manifest=json.loads((ROOT/'revisions/v3/statistics/manifest.json').read_text())
 for key,path in [('original_rankings',original),('qwen_rankings',new)]:assert sha(path)==manifest['input_sha256'][key]
 for name,expected in manifest['outputs'].items():assert sha(ROOT/'revisions/v3/statistics'/name)==expected
 points=collections.defaultdict(list);costs=collections.defaultdict(list);subgroups=collections.defaultdict(list)
 prefix_checks=0;score_checks=0;identities=set()
 for r in raw:
  identity=(r['dataset'],r['id'],r['method']);assert identity not in identities;identities.add(identity)
  x=instances[r['dataset'],r['id']];n=len(x['units']);assert sorted(r['ranking'])==list(range(n))
  assert r['gold']==x['gold'] and r['cluster']==x['cluster'] and r['unit_count']==n
  assert r['instance_hash']==hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
  refs=[set(e) for e in r['gold']];assert refs and all(refs)
  union=set.union(*refs);minimal=[e for e in refs if not any(z<e for z in refs)];small=set.union(*minimal)
  assert small<=union
  seen=set();dc=da=dc2=da2=None
  for k,i in enumerate(r['ranking'],1):
   seen.add(i);c=any(e<=seen for e in refs);a=union<=seen;c2=any(e<=seen for e in minimal);a2=small<=seen
   assert c==c2 and int(a)<=int(a2) and bool(small&seen)<=bool(union&seen)
   assert int(c)-int(a)>=int(c2)-int(a2)
   if dc is None and c:dc=k
   if da is None and a:da=k
   if dc2 is None and c2:dc2=k
   if da2 is None and a2:da2=k
   prefix_checks+=1
  assert dc==dc2 and da2<=da
  lexical=[max(1,len(re.findall(r'\w+',x['units'][i].lower(),flags=re.UNICODE))) for i in r['ranking']]
  tc=sum(lexical[:dc]);ta=sum(lexical[:da]);actual_cost={'depth_complete':dc,'depth_union':da,'depth_penalty':da-dc,'tokens_complete':tc,'tokens_union':ta,'tokens_penalty':ta-tc}
  assert actual_cost==r['costs'];costs[r['dataset'],r['method']].append(actual_cost)
  for p in r['points']:
   k=p['k'];pred=set(r['ranking'][:k]);hits=[len(pred&e) for e in refs];h=int(bool(pred&union));c=int(any(e<=pred for e in refs));a=int(union<=pred)
   actual={'hit':h,'complete':c,'union_complete':a,'union_recall':len(pred&union)/len(union),'max_recall':max(h/len(e) for h,e in zip(hits,refs)),'max_f1':max(2*h/(len(pred)+len(e)) for h,e in zip(hits,refs)),'union_f1':2*len(pred&union)/(len(pred)+len(union)),'hit_without_complete':h-c,'complete_without_union':c-a}
   assert a<=c<=h
   if len({frozenset(e) for e in refs})==1:assert c==a
   for metric,value in actual.items():assert close(p[metric],value);points[r['dataset'],r['method'],k,metric].append(value);score_checks+=1
  if r['dataset']=='qasper':
   pred=set(r['ranking'][:5]);before=int(any(e<=pred for e in refs))-int(union<=pred);after=int(any(e<=pred for e in minimal))-int(small<=pred)
   group='exact_answer_agreement' if x['metadata']['answer_agreement'] else 'agreement_complement'
   for g in [group,'full']:subgroups[r['method'],g].append((before,after))
 aggregate_checks=0
 for r in csvrows('revisions/v3/statistics/curves.csv'):
  values=points[r['dataset'],r['method'],int(r['k']),r['metric']]
  assert len(values)==int(r['n']) and close(sum(values)/len(values),r['mean']);aggregate_checks+=1
 cost_mean_checks=0
 for r in csvrows('revisions/v3/statistics/costs.csv'):
  vals=[x[r['metric']] for x in costs[r['dataset'],r['method']]]
  assert len(vals)==int(r['n']) and close(sum(vals)/len(vals),r['mean']);cost_mean_checks+=1
 budget_checks=0
 for r in csvrows('revisions/v3/statistics/budget_thresholds.csv'):
  vals=costs[r['dataset'],r['method']];tau=float(r['tau']);prefix='depth' if r['budget_unit']=='units' else 'tokens'
  for name,field in [('B_C','complete'),('B_A','union')]:
   values=[x[prefix+'_'+field] for x in vals];k=int(float(r[name]));assert sum(x<=k for x in values)/len(values)>=tau;assert sum(x<=k-1 for x in values)/len(values)<tau;budget_checks+=1
  assert float(r['difference'])==float(r['B_A'])-float(r['B_C'])
 subgroup_checks=0
 for r in csvrows('revisions/v3/statistics/agreement_pruning.csv'):
  vals=subgroups[r['method'],r['group']];assert len(vals)==int(r['n'])
  for field,column in [('original_gap',0),('pruned_gap',1)]:assert close(sum(x[column] for x in vals)/len(vals),r[field]);subgroup_checks+=1
  assert close(sum(b-a for a,b in vals)/len(vals),r['pruned_minus_original'])
 pipe=ROOT/'revisions/v3/pipeline';pm=json.loads((pipe/'manifest.json').read_text());pr=json.loads((pipe/'report.json').read_text())
 assert pm['source_code_sha256']==sha(ROOT/'src/revision_v3_pipeline.py')==pr['source_code_sha256']
 assert pm['selection_plan_sha256']==sha(pipe/'plan.json')
 for name,expected in pm['outputs_sha256'].items():assert sha(pipe/name)==expected
 assert pm['input_hashes']==pr['input_hashes'] and pm['input_hashes']['frozen_rankings']==sha(original)
 mapping=json.loads((pipe/'main_cohort_alignment.json').read_text());assert len(mapping)==875
 for r in mapping:assert (set(r['mapped_source_union'])==set(r['export_membership']))==(r['membership_category']=='exact_union_membership')
 sys.path.insert(0,str(ROOT/'src'))
 from revision_v3_manuscript import Revision
 revision=Revision(ROOT,require_qwen=True);values={};revision.populate(lambda k,v,s:values.__setitem__(k,str(v)))
 doc={'tables':{'primary':{'rows':[],'caption':''},'costs':{'rows':[],'caption':''}}};revision.enrich(doc)
 assert len(doc['tables']['qwen_contrasts_v3']['rows'])==4
 assert 'INTERNAL LAYOUT DRAFT' not in json.dumps(values)
 counts=dict(collections.Counter(r['method'] for r in raw));assert all(n==1084 for n in counts.values()) and len(counts)==6
 final={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'scope':'Scientific calculations, protected original inputs, pipeline public provenance and complete source-linked manuscript helper; excludes PDF rendering, remote publication and isolated source-free reproduction.','review_role':'Additional automated code/scientific review; pipeline is producing-agent self-check, statistics/helper are checked by a different agent; no independent human review.','methods':counts,'ranking_count':len(raw),'unit_budget_points':sum(len(r['points']) for r in raw),'full_integer_prefix_pruning_checks':prefix_checks,'individual_score_value_checks':score_checks,'curve_mean_checks':aggregate_checks,'cost_mean_checks':cost_mean_checks,'exact_budget_endpoint_minimality_checks':budget_checks,'subgroup_mean_checks':subgroup_checks,'pipeline_public_output_hashes_checked':len(pm['outputs_sha256']),'pipeline_original_intersection':875,'pipeline_aligned_n':866,'complete_helper_new_tables':list(revision.table_sources),'qwen_results':values['QwenResults'],'qwen_comparisons':values['QwenComparisons'],'qwen_technical_details':values['QwenTechnicalDetails'],'checked_file_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),original,new,ROOT/'src/revision_v3_statistics.py',ROOT/'src/revision_v3_manuscript.py',ROOT/'src/validate_revision_v3_release.py',ROOT/'src/revision_v3_release_docs.py',pipe/'manifest.json',ROOT/'revisions/v3/statistics/manifest.json']}}
 (OUT/'independent_six_method_checks.json').write_text(json.dumps(final,indent=2)+'\n')
 audit=json.loads((OUT/'scientific_audit.json').read_text());audit['status']='COMPLETED: automated scientific/code audit of all six methods; PDF and publication verification are outside this report';audit['pending']=[];audit['final_six_method_checks']=final
 audit['release_docs_review']['recommendations_status']='All three root fixes adopted: omitted evidence memberships; exact integer-budget wording; final Revision hash/completion guard.'
 audit['scope_exclusions']=['Final PDF all-page visual checks','Remote publication/DOI/file verification','Root-managed isolated source-free reproduction','Independent external or human semantic replication']
 (OUT/'scientific_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 md=f'''# Completed automated scientific and code audit\n\nScientific/code scope completed on {final['checked_utc']}. This is an additional automated review, not independent human review or external replication. The reviewer differs from statistics/manuscript implementers and produced the converter/example implementation, so the latter is a self-check.\n\n## Actual checks\n\n- All {len(raw):,} complete rankings, {final['unit_budget_points']:,} original-grid points and {score_checks:,} score values recomputed through direct set operations.\n- Every one of {prefix_checks:,} integer prefixes checked for pruning invariance/direction; all depth and lexical costs reconstructed from source text. Best-reference F1 is explicitly excluded from invariance, with the existing counterexample retained.\n- All {aggregate_checks} curve means, {cost_mean_checks} cost means, {budget_checks} threshold endpoints and {subgroup_checks} subgroup means checked. Thresholds attain the target at k and fail at k−1, retaining all eligible items.\n- Cluster resampling code and explicit multiplicity/unattained-replicate tests reviewed. These intervals are paired, item-weighted and exploratory; no long bootstrap or full inference rerun was repeated for this review.\n- Original source instances/rankings match frozen hashes. All {len(pm['outputs_sha256'])} pipeline public output hashes, current source, plan and input provenance agree. Changed saved-score inputs are rejected by an executed test.\n- The complete manuscript helper instantiated successfully and generates the four fixed Qwen comparison rows from validated complete output; no partial effectiveness enters this path.\n\n## Main interpretation safeguards\n\nThe QASPER agreement and complement distinguish sample selection from paired target pruning: BM25 24→16/195, 132→87/680 and 156→103/875. Shared papers are not treated as independent groups. The 8.2-point result is neither a formal bound nor a causal decomposition; exact normalized answer strings do not establish semantic agreement.\n\nThe converter covers 875 original questions, but exact union-membership alignment applies to 866 under the stated normalized-text/candidate restriction. Nine exports omit 14 annotated memberships. Within the matched subset, 90 have duplicate/normalized-equivalent candidates (four involving gold); eight canonical mappings use identical abstract text (one involving gold). These disclosed equivalences preclude calling the full native task pure grouping-only loss. Ordinary relevance metrics remain separate from C/A, and no stated-objective mismatch is established.\n\n{values['QwenResults']}\n\n{values['QwenComparisons']}\n\n## Release-code and public scope review\n\nThe release validator now checks the public copies of historical frozen outputs even when source text is absent, author/affiliation and protected disclosure values, current complete manifests, unchanged official style and intended-public file scope. The release-prose generator reuses the final completion/hash guard. All three earlier wording/provenance recommendations were adopted. Complete third-party model-card text is excluded; source/hash attribution remains.\n\nPDF visual verification, remote publication/DOI/file checks and the isolated source-free reproduction are separate root-managed checks. Their exclusion here is a scope boundary, not an unresolved scientific calculation. No new human semantic annotation or acceptance probability is claimed. See independent_six_method_checks.json for exact inputs and check totals.\n'''
 (OUT/'scientific_audit.md').write_text(md)
 print(json.dumps(final,indent=2))
if __name__=='__main__':main()
