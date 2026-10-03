import ast, dataclasses, importlib.util, json, sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from revision_v3_pipeline import (ROOT, FILES, membership_category, conventional, load_upstream, convert_supplied, normalized_alignment)
from evidence import Instance, score


def test_membership_axis_does_not_hide_missing_or_extra_units():
 assert membership_category({'a','b'},{'a','b'})=='exact_union_membership'
 assert membership_category({'a','b'},{'a'})=='missing_or_filtered_membership'
 assert membership_category({'a'},{'a','b'})=='additional_membership'
 assert membership_category({'a'},{'b'})=='changed_membership'
 assert membership_category({'a'},{'a'},False)=='undetermined_source_correspondence'


def test_flat_scorer_cannot_identify_group_completion():
 relevant={'a','b'};ranking=['a','x','b']
 actual=conventional(ranking,relevant,1)
 assert actual['recall']==.5 and actual['success']==1
 assert score(['a'],[['a'],['b']])['complete']==1
 assert score(['a'],[['a','b']])['complete']==0
 assert score(['a'],[['a'],['b']])['union_complete']==0
 # Ordinary recall does not claim union completion.
 assert actual['recall']!=score(['a'],[['a'],['b']])['union_complete']


def test_alignment_keeps_scope_and_duplicate_id_evidence():
 x=Instance('qasper','test','q','p','query',['a b','c'],[[0],[1]],{})
 mapping,ambiguous=normalized_alignment(x,{'p::0::0':'abstract','p::1::0':'a  b','p::1::1':'a b','p::1::2':'c','other::1::0':'a b'})
 assert mapping=={0:'p::1::0',1:'p::1::2'}
 assert ambiguous=={0:['p::1::0','p::1::1']}
 # A different normalized-equivalent output ID must not be called exact union.
 assert membership_category(mapping.values(),{'p::1::1','p::1::2'})=='changed_membership'


def upstream():
 cache=ROOT/'revisions/v3/pipeline/source_cache/upstream'
 if not all((cache/p).exists() for p in FILES):pytest.skip('Acquire pinned upstream source with revision_v3_pipeline.py')
 return load_upstream(cache)


def test_real_converter_wrapper_matches_native_file_and_preserves_filtering(tmp_path):
 dataset,loader,metrics=upstream()
 answer=lambda evidence: {'answer':{'evidence':evidence,'free_form_answer':'yes','unanswerable':False}}
 papers={'p':{'abstract':'abstract','full_text':[{'paragraphs':['alpha beta','gamma']}],
  'qas':[{'question_id':'q','question':'question','answers':[answer(['alpha beta']),answer(['gamma'])]},
         {'question_id':'whitespace','question':'question','answers':[answer(['alpha  beta']),answer(['gamma'])]}]}}
 (tmp_path/'qasper-dev-v0.3.json').write_text(json.dumps(papers))
 original=loader.load_qasper(split='validation',max_papers=None,cache_dir=tmp_path)
 wrapped=convert_supplied(loader,papers)
 assert dataclasses.asdict(original)==dataclasses.asdict(wrapped)
 assert original.qrels['q']=={'p::1::0':1,'p::1::1':1}
 assert original.qrels['whitespace']=={'p::1::1':1}
 assert original.examples[0].answers==('yes',)
 # The class holds answers and qrels but no answer-to-evidence membership.
 assert set(dataclasses.asdict(original))=={'name','examples','corpus','qrels'}


def test_real_ir_scorer_parity_with_formula_and_saturated_prefix():
 pytest.importorskip('ir_measures');dataset,loader,metrics=upstream()
 qrels={'q':{'a':1,'b':1},'short':{'s':1}}
 run={'q':{'x':5.,'a':4.,'y':3.,'b':2.},'short':{'s':1.}}
 for k in [1,3,10]:
  for measure,key in [(f'R@{k}','recall'),(f'Success@{k}','success'),(f'nDCG@{k}','ndcg'),(f'RR@{k}','rr')]:
   actual=metrics.retrieval_metrics_per_query(qrels,run,measure)
   for q in qrels:
    ranking=sorted(run[q],key=lambda d:-run[q][d])
    assert actual[q]==pytest.approx(conventional(ranking,qrels[q],k)[key],abs=1e-12)


def test_saved_real_mapping_equality_and_incomplete_cases_visible():
 p=ROOT/'revisions/v3/pipeline/main_cohort_alignment.json'
 if not p.exists():pytest.skip('Run the real replay first')
 rows=json.loads(p.read_text());assert len(rows)==875 and len({r['id'] for r in rows})==875
 for r in rows:
  eq=set(r['mapped_source_union'])==set(r['export_membership'])
  assert eq==(r['membership_category']=='exact_union_membership')
  if not eq:
   assert r['missing_membership_evidence']
   assert not any(e['any_stripped_evidence_exactly_matches_export_text'] for e in r['missing_membership_evidence'])


def test_saved_summary_rejects_changed_public_score_input(tmp_path):
 from revision_v3_pipeline import summarize_saved
 (tmp_path/'per_query_scores.csv').write_text('id,paper_id,method,k\nmodified,p,bm25,5\n')
 (tmp_path/'manifest.json').write_text(json.dumps({'outputs_sha256':{'per_query_scores.csv':'0'*64}}))
 with pytest.raises(ValueError,match='differ from execution manifest'):
  summarize_saved(tmp_path)
 assert not (tmp_path/'score_summary.csv').exists()
