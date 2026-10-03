import sys,json,math,random,importlib.util
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evidence import *

def inst():
    return Instance("fixture","pilot","1","g","alpha beta",["alpha","beta alpha","gamma"],[[0],[1]],{})

def test_and_or_distinction():
    assert score([0],[[0,1],[2,3]])["complete"]==0
    assert score([0,2],[[0,1],[2,3]])["union_recall"]==.5
    assert score([0,2],[[0,1],[2,3]])["complete"]==0
    r=score([0,1],[[0,1],[2,3]])
    assert r["complete"]==1 and r["union_complete"]==0 and r["union_recall"]==.5
    assert score([0,1,2,3],[[0,1],[2,3]])["union_complete"]==1

def test_empty_and_duplicate_predictions():
    r=score([],[[1]])
    assert r["complete"]==r["hit"]==0
    assert score([1,1],[[1]])==score([1],[[1]])
    with pytest.raises(ValueError):score([1],[[]])
    with pytest.raises(ValueError):score([1],[])

def test_flat_nonidentifiability():
    # Same union and retrieved set; different annotation-level completion.
    a=score([0],[[0],[1]]);b=score([0],[[0,1]])
    assert a["union_f1"]==b["union_f1"]
    assert a["complete"]==1 and b["complete"]==0

def test_nested_references():
    assert topology([[0],[0,1],[0]])["n_minimal_sets"]==1
    assert topology([[0],[0,1],[0]])["n_distinct_sets"]==2
    assert topology([[0],[0,1],[0]])["union_to_min_size"]==2

def test_bm25_independent_small_example():
    units=["a a","a b","c"]
    n=3;avg=5/3;k1=1.2;b=.75
    expected=[math.log(1+1.5/2.5)*2*2.2/(2+1.2*(.25+.75*2/avg)),
              math.log(1+1.5/2.5)*1*2.2/(1+1.2*(.25+.75*2/avg)),0.]
    assert bm25("a",units)==pytest.approx(expected)
    assert bm25("a",["",""])==[0,0]

@pytest.mark.parametrize("method",["bm25","tfidf","lead","random"])
def test_rank_is_deterministic_permutation(method):
    a,s=rank(inst(),method);b,_=rank(inst(),method)
    assert a==b and sorted(a)==[0,1,2] and len(s)==3

def test_tie_break_and_unicode():
    x=inst();x.query="absent"
    assert rank(x,"bm25")[0]==[0,1,2]
    assert rank(x,"tfidf")[0]==[0,1,2]
    assert tokens("CAFÉ α β_2")==["café","α","β_2"]

def test_completion_costs():
    x=completion_costs([2,0,1],[[0],[1]],["a a","b","c c c"])
    assert x=={"depth_complete":2,"depth_union":3,"depth_penalty":1,
               "tokens_complete":5,"tokens_union":6,"tokens_penalty":1}

def test_resume(tmp_path):
    config={"methods":["bm25","tfidf"],"ks":[1,2],"seed":2}
    out=tmp_path/"records.jsonl"
    assert run_instances([inst()],config,out,limit=1)==1
    assert run_instances([inst()],config,out)==1
    original=out.read_bytes()
    assert run_instances([inst()],config,out)==0 and out.read_bytes()==original
    with pytest.raises(ValueError):run_instances([inst()],{**config,"seed":3},out)

def test_qasper_rejects_incomplete_mapping(tmp_path):
    a={"unanswerable":False,"evidence":["a","missing"],"yes_no":True}
    p={"p":{"full_text":[{"paragraphs":["a","a","b"]}],"qas":[{"question_id":"q","question":"x","answers":[{"answer":a}]}]}}
    f=tmp_path/"q.json";f.write_text(json.dumps(p))
    xs,audit=qasper_instances(f,"fixture")
    assert not xs and "any_unmapped_text" in audit[0]["reasons"]
    a["evidence"]=["a"];f.write_text(json.dumps(p));xs,audit=qasper_instances(f,"fixture")
    assert xs[0].gold==[[0]] and len(xs[0].units)==2
    assert xs[0].metadata["duplicate_paragraphs"]==1

def test_scorer_identities_exhaustive_small():
    import itertools
    refs=[[0,1],[2]]
    for k in range(5):
        for r in itertools.combinations(range(4),k):
            x=score(r,refs)
            assert x["union_complete"]<=x["complete"]<=x["hit"]
            assert (x["max_recall"]==1)==bool(x["complete"])

def load_official(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_qasper_official_f1_parity():
    path=ROOT/"data/raw/qasper-test-and-evaluator-v0/qasper_evaluator.py"
    m=load_official(path,"official_qasper")
    for predicted in [[],[0],[0,1],[0,2],[0,1,2,3]]:
        refs=[[0,1],[2]]
        expected=max(m.paragraph_f1_score(predicted,g) for g in refs)
        assert score(predicted,refs)["max_f1"]==pytest.approx(expected)

def test_scifact_official_containment_parity():
    # Read downloaded official code without needing to import non-Python extension.
    ns={};exec((ROOT/"literature/sources/scifact_evaluator.py.txt").read_text(),ns)
    contains=ns["Evaluator"].contains_evidence
    for predicted in [[],[0],[0,2],[0,1],[0,1,2,3]]:
        refs=[{0,1},{2,3}]
        assert bool(score(predicted,refs)["complete"])==contains(refs,set(predicted))

def test_resume_rejects_changed_input(tmp_path):
    config={"methods":["bm25"],"ks":[1],"seed":2};p=tmp_path/"r.jsonl"
    x=inst();run_instances([x],config,p)
    x.query="different"
    with pytest.raises(ValueError,match="input mismatch"):run_instances([x],config,p)

def test_resume_partial_tail_and_interior_corruption(tmp_path):
    p=tmp_path/"r.jsonl";cfg={"methods":["bm25","tfidf"],"ks":[1],"seed":2}
    run_instances([inst()],cfg,p,limit=1)
    with p.open("ab") as f:f.write(b'{"unfinished":')
    assert run_instances([inst()],cfg,p)==1
    assert len(load_jsonl(p))==2 and len(list(tmp_path.glob("*.interrupted-*")))==1
    p.write_text(p.read_text()+"invalid interior\n")
    with pytest.raises(json.JSONDecodeError):run_instances([inst()],cfg,p)

def test_bm25_order_independent_query_terms():
    assert bm25("a b c",["a b","b c"])==bm25("c b a",["a b","b c"])
