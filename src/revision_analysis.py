"""Exploratory post-main v2 topology analysis; frozen rankings are read-only."""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
import pandas as pd
from evidence import ROOT,Instance,load_jsonl,topology,score
from analyze import bootstrap_matrix,estimate
OUT=ROOT/'revisions/v2'
CATEGORIES=['One distinct set','Multiple sets, one minimal set','Multiple minimal sets, no supersets','Multiple minimal sets plus supersets']
def category(gold):
 t=topology(gold)
 if t['n_distinct_sets']==1:return 0
 if t['n_minimal_sets']==1:return 1
 return 2 if t['n_minimal_sets']==t['n_distinct_sets'] else 3
def summarize(values,clusters):
 if not values:return dict(n=0,clusters=0,mean=None,lo=None,hi=None,median=None,sparse=True)
 m,ci=estimate(values,bootstrap_matrix(clusters))
 return dict(n=len(values),clusters=len(set(clusters)),mean=float(m[0]),lo=float(ci[0,0]),hi=float(ci[0,1]),median=float(np.median(values)),sparse=len(set(clusters))<10)
def main():
 xs=[Instance(**r) for r in load_jsonl(ROOT/'outputs/main_v1/instances.jsonl')]
 raw=load_jsonl(ROOT/'outputs/main_v1/rankings.jsonl');rr={(r['dataset'],r['id'],r['method']):r for r in raw}
 tables=[];modifiers=[];items=[];checks={};panels=[]
 old=load_jsonl(ROOT/'outputs/main_v1/audit.jsonl')
 examples=json.loads((ROOT/'analysis/representative_examples.json').read_text())
 for d,k in [('qasper',5),('scifact',3)]:
  dx=sorted([x for x in xs if x.dataset==d],key=lambda x:x.id);n=len(dx);clusters=[x.cluster for x in dx];boot=bootstrap_matrix(clusters)
  cats=[category(x.gold) for x in dx];counts=[cats.count(c) for c in range(4)]
  assert counts==([403,187,243,42] if d=='qasper' else [124,0,85,0])
  checks[d]=dict(counts=counts,n=n,exhaustive=sum(counts)==n,disjoint=True)
  for x,c in zip(dx,cats):items.append(dict(dataset=d,id=x.id,cluster=x.cluster,category=c,category_label=CATEGORIES[c],singleton=any(len(e)==1 for e in x.gold),answer_agreement=x.metadata['answer_agreement']))
  for method in ['bm25','tfidf','dense','lead','random']:
   rows=[rr[d,x.id,method] for x in dx];points=[next(p for p in r['points'] if p['k']==k) for r in rows]
   data={'complete_without_union':[p['complete_without_union'] for p in points], 'depth_penalty':[r['costs']['depth_penalty'] for r in rows], 'tokens_penalty':[r['costs']['tokens_penalty'] for r in rows]}
   total=0.
   for c in range(4):
    ix=[i for i,v in enumerate(cats) if v==c];cs=[clusters[i] for i in ix]
    for metric,values in data.items():
     stats=summarize([values[i] for i in ix],cs)
     weighted=[v*int(cats[i]==c) for i,v in enumerate(values)]
     m,ci=estimate(weighted,boot)
     tables.append(dict(dataset=d,method=method,k=k,category=c,label=CATEGORIES[c],metric=metric,**stats,overall_n=n,weight=len(ix)/n,contribution=float(m[0]),contribution_lo=float(ci[0,0]),contribution_hi=float(ci[0,1]),status='exploratory_post_main'))
     if metric=='complete_without_union':total+=float(m[0])
    if method=='bm25':
     mods=['singleton']+(['answer_agreement'] if d=='qasper' else [])
     for mod in mods:
      for level in [False,True]:
       subset=[i for i in ix if (any(len(e)==1 for e in dx[i].gold) if mod=='singleton' else dx[i].metadata['answer_agreement'])==level]
       for metric,values in data.items():modifiers.append(dict(dataset=d,category=c,label=CATEGORIES[c],modifier=mod,level=level,metric=metric,**summarize([values[i] for i in subset],[clusters[i] for i in subset]),status='exploratory_post_main'))
   assert np.isclose(total,np.mean(data['complete_without_union']))
   checks[d][method+'_reconstructed_gap']=total
  # Retain the first already selected hash-ordered one-not-union example in each corpus.
  ex=next(e for e in examples if e['dataset']==d and e['category']=='one_not_union')
  x=next(x for x in dx if x.id==ex['id']);r=rr[d,x.id,'bm25'];prefix=r['ranking'][:k]
  def source_id(i):return (x.cluster+':paragraph:'+str(i) if d=='qasper' else str(x.metadata['doc_id'])+':sentence:'+str(i))
  panels.append(dict(**ex,scores=score(prefix,x.gold),unit_index_base=0,source_unit_ids={str(i):source_id(i) for i in sorted(set(prefix)|set(sum(x.gold,[])))},text={str(i):x.units[i] for i in sorted(set(prefix)|set(sum(x.gold,[])))},costs=r['costs'],status='exploratory_presentation_of_preselected_case'))
 for name,rows in [('topology_disjoint',tables),('topology_modifiers',modifiers),('topology_membership',items)]:pd.DataFrame(rows).to_csv(OUT/'tables'/(name+'.csv'),index=False,float_format='%.12g')
 (OUT/'analysis/topology_checks.json').write_text(json.dumps(checks,indent=2));(OUT/'analysis/case_panels.json').write_text(json.dumps(panels,ensure_ascii=False,indent=2))
 example={tuple(p):{k:v for k,v in score(p,[[0,1],[2]]).items() if k in ['hit','complete','union_complete']} for p in [[],[0],[0,1],[2],[0,2],[0,1,2],[3]]}
 (OUT/'analysis/concept_example.json').write_text(json.dumps([dict(prefix=list(p),**v) for p,v in example.items()],indent=2))
 manifest=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='exploratory_post_main',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rankings_sha256=hashlib.sha256((ROOT/'outputs/main_v1/rankings.jsonl').read_bytes()).hexdigest(),bootstrap=dict(replicates=10000,seed=20261002,unit='same connected clusters as primary; item-weighted',stratum='resample clusters represented within stratum',contribution='resample full cohort clusters, with non-category values zero'))
 (OUT/'analysis/manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps(checks,indent=2));print(pd.DataFrame(tables).query("method=='bm25' and metric=='complete_without_union'").to_string(index=False))
if __name__=='__main__':main()
