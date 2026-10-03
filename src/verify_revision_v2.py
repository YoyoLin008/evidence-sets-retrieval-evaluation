"""Recheck saved original and exploratory results without rewriting them."""
from pathlib import Path
import json,hashlib,sys,argparse
import numpy as np,pandas as pd
from analyze import bootstrap_matrix,estimate
from evidence import score
from revision_analysis import category
R=Path(__file__).resolve().parents[1];O=R/'revisions/v2'
def close(a,b):assert np.allclose(a,b,rtol=2e-9,atol=6e-7,equal_nan=True),(a,b)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--fresh-reproduction',action='store_true',help='Recompute scientific checks without comparing new run metadata to historical bytes.');args=parser.parse_args()
 base=json.loads((O/'baseline_manifest.json').read_text())
 if not args.fresh_reproduction:
  for f,h in base['protected'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h,f
 raw=[json.loads(x) for x in (R/'outputs/main_v1/rankings.jsonl').read_text().splitlines()];instances={(x['dataset'],x['id']):x for x in [json.loads(x) for x in (R/'outputs/main_v1/instances.jsonl').read_text().splitlines()]}
 tables={n:pd.read_csv(R/'tables'/f'{n}.csv') for n in ['primary','costs','curve_estimates','independent_bootstrap','joint_sensitivity']};top=pd.read_csv(O/'tables/topology_disjoint.csv');count=0;direct=[]
 for d,k in [('qasper',5),('scifact',3)]:
  for method in ['bm25','tfidf','dense','lead','random']:
   rows=sorted([r for r in raw if r['dataset']==d and r['method']==method],key=lambda r:r['id']);clusters=[r['cluster'] for r in rows];boot=bootstrap_matrix(clusters)
   for name in ['primary','costs','curve_estimates']:
    source=tables[name];sub=source[(source.dataset==d)&(source.method==method)]
    for _,t in sub.iterrows():
     if t.metric=='saturated_fraction':values=[r['unit_count']<t.k for r in rows];close(np.mean(values),t['mean']);count+=1;continue
     vals=[r['costs'][t.metric] if name=='costs' else next(p[t.metric] for p in r['points'] if p['k']==t.k) for r in rows]
     m,ci=estimate(vals,boot);close([m[0],*ci[0]],[t['mean'],t.lo,t.hi]);count+=1
   if method=='bm25':
    for cat in range(4):
     ix=[i for i,r in enumerate(rows) if category(r['gold'])==cat];sb=bootstrap_matrix([clusters[i] for i in ix]) if ix else None
     for _,t in top[(top.dataset==d)&(top.method==method)&(top.category==cat)].iterrows():
      vals=[next(p[t.metric] for p in r['points'] if p['k']==k) if t.metric=='complete_without_union' else r['costs'][t.metric] for r in rows]
      if ix:
       m,ci=estimate([vals[i] for i in ix],sb);close([m[0],*ci[0]],[t['mean'],t.lo,t.hi])
      else:assert t.n==0 and pd.isna(t['mean'])
      m,ci=estimate([v if i in ix else 0 for i,v in enumerate(vals)],boot);close([m[0],*ci[0]],[t.contribution,t.contribution_lo,t.contribution_hi]);count+=1
    # A separate direct integer-cluster draw reproduces the earlier independent bootstrap.
    groups={}
    for r in rows:groups.setdefault(r['cluster'],[]).append([next(p[m] for p in r['points'] if p['k']==k) for m in ['hit_without_complete','complete_without_union']])
    arrays=[np.asarray(a) for a in groups.values()];sums=np.array([a.sum(0) for a in arrays]);sizes=np.array([len(a) for a in arrays]);rng=np.random.default_rng(91827);draw=rng.integers(0,len(arrays),size=(10000,len(arrays)));samples=sums[draw].sum(1)/sizes[draw].sum(1)[:,None];ci=np.quantile(samples,[.025,.975],axis=0)
    for j,m in enumerate(['hit_without_complete','complete_without_union']):
     t=tables['independent_bootstrap'].query('dataset==@d and metric==@m').iloc[0];close(ci[:,j],[t.lo,t.hi]);direct.append({'dataset':d,'metric':m,'lo':float(ci[0,j]),'hi':float(ci[1,j])})
  # Recompute joint sensitivity from references, retaining the original post-main definition.
  for method in ['bm25','tfidf','dense']:
   rows=sorted([r for r in raw if r['dataset']==d and r['method']==method and instances[d,r['id']]['metadata']['answer_agreement']],key=lambda r:r['id']);boot=bootstrap_matrix([r['cluster'] for r in rows]);pts=[]
   for r in rows:
    sets={frozenset(e) for e in r['gold']};minimal=[list(e) for e in sets if not any(z<e for z in sets)];pts.append(score(r['ranking'][:k],minimal))
   for _,t in tables['joint_sensitivity'].query('dataset==@d and method==@method').iterrows():
    m,ci=estimate([p[t.metric] for p in pts],boot);close([m[0],*ci[0]],[t['mean'],t.lo,t.hi]);count+=1
 gate=json.loads((O/'compute/feasibility.json').read_text());timing=[json.loads(x) for x in (O/'compute/timing_rows.jsonl').read_text().splitlines()];means=[np.mean([x['seconds'] for x in timing if x['bin']==b]) for b in range(4)];close(sum(n*m for n,m in zip(gate['bin_counts'],means))+gate['warmup_seconds']+gate['load_seconds'],gate['projected_seconds'])
 doc=json.loads((R/'paper/article.json').read_text());bib=(R/'paper/references.bib').read_text();assert all('{'+k+',' in bib for k in doc['references']);assert len(doc['references'])==26
 assert 'approval pending' not in json.dumps(doc).lower();assert not any(x==['figure','figure4_annotation_structure'] for x in doc['blocks'])
 result={'passed':True,'protected_files':0 if args.fresh_reproduction else len(base['protected']),'historical_byte_check':'not applicable to fresh reproduction; validate package before running' if args.fresh_reproduction else 'passed','estimate_rows_recomputed':count,'original_and_topology_cluster_intervals_recomputed':True,'independent_direct_bootstrap_reproduced':direct,'joint_post_main_recomputed':True,'qwen_timing_projection_reconstructed':True,'source_ledger_entries':26,'overlapping_headline_figure_removed':True,'no_original_output_changed':None if args.fresh_reproduction else True}
 (R/'revisions/final/analysis/numerical_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
