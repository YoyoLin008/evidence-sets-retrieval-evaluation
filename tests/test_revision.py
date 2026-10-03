import json,sys,hashlib,os
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from evidence import score,topology
from revision_analysis import category,summarize

@pytest.mark.parametrize('gold,expected',[([[0,1]],0),([[0,1],[0,1]],0),([[0],[0,1]],1),([[0],[1]],2),([[0],[1],[0,2]],3)])
def test_disjoint_topology_edge_cases(gold,expected):assert category(gold)==expected

def test_empty_stratum_is_missing_not_zero():
 r=summarize([],[])
 assert r['n']==r['clusters']==0 and r['mean'] is None and r['lo'] is None and r['hi'] is None and r['sparse']

def test_flat_nonidentifiability():
 a,b=[[0,1],[2]],[[0],[1,2]]
 assert set(sum(a,[]))==set(sum(b,[]))
 x,y=score([0],a),score([0],b)
 assert x['hit']==y['hit']==1 and x['union_complete']==y['union_complete']==0
 assert x['complete']==0 and y['complete']==1

def test_duplicate_reference_and_prediction_invariance():
 a=score([0,1],[[0,1],[2]])
 b=score([0,0,1],[[0,1],[2],[0,1]])
 assert a==b

def test_nested_pruning_preserves_c_but_changes_union():
 for prefix in [[],[0],[1],[0,1]]:assert score(prefix,[[0],[0,1]])['complete']==score(prefix,[[0]])['complete']
 assert score([0],[[0],[0,1]])['union_complete']==0 and score([0],[[0]])['union_complete']==1

def test_all_original_protected_bytes_unchanged():
 if os.environ.get('ASTRA_FRESH_REPRODUCTION')=='1':pytest.skip('Fresh run: historical byte identity is checked on the package before reproduction, not new run metadata.')
 m=json.loads((ROOT/'revisions/v2/baseline_manifest.json').read_text())
 for p,h in m['protected'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p

def test_topology_exhaustive_and_weighted_reconstruction():
 m=pd.read_csv(ROOT/'revisions/v2/tables/topology_membership.csv');t=pd.read_csv(ROOT/'revisions/v2/tables/topology_disjoint.csv');p=pd.read_csv(ROOT/'tables/primary.csv');cost=pd.read_csv(ROOT/'tables/costs.csv')
 assert not m.duplicated(['dataset','id']).any()
 for d,ns in [('qasper',[403,187,243,42]),('scifact',[124,0,85,0])]:
  assert [sum((m.dataset==d)&(m.category==c)) for c in range(4)]==ns
  for method in ['bm25','tfidf','dense','lead','random']:
   for metric in ['complete_without_union','depth_penalty','tokens_penalty']:
    sub=t[(t.dataset==d)&(t.method==method)&(t.metric==metric)]
    original=p if metric=='complete_without_union' else cost
    expected=original[(original.dataset==d)&(original.method==method)&(original.metric==metric)].iloc[0]['mean']
    assert sum(sub.n)==sum(ns)
    raw=[json.loads(x) for x in (ROOT/"outputs/main_v1/rankings.jsonl").read_text().splitlines()]
    selected=[r for r in raw if r["dataset"]==d and r["method"]==method]
    exact=np.mean([next(v[metric] for v in r["points"] if v["k"]==(5 if d=="qasper" else 3)) if metric=="complete_without_union" else r["costs"][metric] for r in selected])
    assert np.isclose(sub.contribution.sum(),exact,rtol=1e-10,atol=1e-10)
    assert np.isclose(sub.contribution.sum(),expected,rtol=1e-9,atol=1e-6)
    assert np.allclose(sub.loc[sub.n>0,'contribution'],sub.loc[sub.n>0,'mean']*sub.loc[sub.n>0,'n']/sum(ns))

def test_six_conversion_fixture_results():
 rows=json.loads((ROOT/'revisions/v2/audit/fixture_results.json').read_text())
 assert len(rows)==6 and all(r['passed'] for r in rows)

def test_audit_sample_count_and_lineage():
 rows=json.loads((ROOT/'revisions/v2/audit/classification_ledger.json').read_text());sel=json.loads((ROOT/'revisions/v2/audit/selected_families_corrected.json').read_text());counts=json.loads((ROOT/'revisions/v2/audit/counts.json').read_text())['counts']
 assert len(rows)==30 and len({r['canonical'].lower() for r in rows})==30
 assert not any(r['index']==52 for r in rows)
 for d in ['QASPER','SciFact']:
  ids={r['index'] for r in sorted([r for r in sel if r['benchmark']==d],key=lambda r:r['selection_hash'])[:15]}
  assert ids=={r['index'] for r in rows if r['benchmark']==d}
  for c,n in counts[d].items():assert sum(r['benchmark']==d and r['classification']==c for r in rows)==n

def test_qwen_gate_omits_all_effectiveness():
 f=json.loads((ROOT/'revisions/v2/compute/feasibility.json').read_text());freeze=json.loads((ROOT/'revisions/v2/compute/runtime_freeze.json').read_text())
 assert not f['passed'] and f['projected_seconds']>7200 and not f['effectiveness_computed']
 assert not (ROOT/'revisions/v2/compute/inference_complete.json').exists()
 assert freeze['config']['source_sha256']==hashlib.sha256((ROOT/'src/qwen_revision.py').read_bytes()).hexdigest()
 assert f['sample_n']==132 and f['unique_inputs']==20112

def test_example_panels_against_frozen_rankings():
 cases=json.loads((ROOT/'revisions/v2/analysis/case_panels.json').read_text());raw=[json.loads(x) for x in (ROOT/'outputs/main_v1/rankings.jsonl').read_text().splitlines()]
 for x in cases:
  r=next(r for r in raw if r['dataset']==x['dataset'] and r['id']==x['id'] and r['method']=='bm25')
  assert x['retrieved']==r['ranking'][:x['k']] and x['scores']==score(x['retrieved'],r['gold']) and x['costs']==r['costs']
