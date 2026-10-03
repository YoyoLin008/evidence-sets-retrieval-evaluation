import json, sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from evidence import ROOT, Instance, score
from revision_v3_examples import eligible, select, source_positions


def item(gold,agreement=True):
 return Instance('qasper','test','q','p','query',['a','b','c','d','e','f'],gold,{'answer_agreement':agreement})


def test_selection_keeps_same_answer_distinct_minimal_alternatives_only():
 order=[0,2,3,4,5,1]
 assert eligible(item([[0],[1],[0]]),order)
 assert not eligible(item([[0],[0,1]]),order)
 assert not eligible(item([[0],[1]],False),order)
 assert not eligible(item([[0]]),order)
 assert not eligible(item([[0],[1]]),[0,1,2,3,4,5])
 assert select([], {})==[]


def test_source_positions_keep_all_duplicate_occurrences():
 paper={'full_text':[{'section_name':'A','paragraphs':['alpha  beta','','x']},{'section_name':'B','paragraphs':['alpha beta']}]}
 p=source_positions(paper,'alpha beta')
 assert [(r['section_index'],r['paragraph_index'],r['nonempty_body_ordinal']) for r in p]==[(0,0,0),(1,0,2)]


def test_panels_match_actual_prefix_and_preserve_selection():
 f=ROOT/'revisions/v3/examples/panels.json'
 if not f.exists():pytest.skip('Generate actual panels first')
 data=json.loads(f.read_text());candidates=data['new_candidate_ids_hash_order']
 assert candidates==sorted(candidates,key=lambda r:r['sha256'])
 assert data['selected_new_id']==candidates[0]['id']
 assert data['selected_first_without_substitution']
 for p in data['panels']:
  assert p['scores']==score(p['ranking_prefix'],p['gold'])
  assert p['completed_reference_sets']==[e for e in p['gold'] if set(e)<=set(p['ranking_prefix'])]
  assert p['quoted_evidence_word_count']<=25
  assert not p['human_semantic_validation']
  assert p['costs']['depth_complete']<=p['k']<p['costs']['depth_union']
 assert data['panels'][-1]['completed_reference_sets']==[[7]]
