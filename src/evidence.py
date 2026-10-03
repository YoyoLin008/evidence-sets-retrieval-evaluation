"""Evidence-set representations, dataset adapters, and deterministic CPU retrieval.

Scores describe annotation coverage, not semantic correctness or answerability.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import Counter
import hashlib, json, math, re, random, string, os, datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[1]
def normalized(text): return " ".join(text.split())
def tokens(text): return re.findall(r"\w+", text.lower(), flags=re.UNICODE)
def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def hash_order(ids): return sorted(ids,key=lambda x:hashlib.sha256(str(x).encode()).hexdigest())
def answer_key(a):
    if a.get("extractive_spans"): value=", ".join(a["extractive_spans"])
    elif a.get("free_form_answer"): value=a["free_form_answer"]
    elif a.get("yes_no") is not None: value="yes" if a["yes_no"] else "no"
    else: value=""
    value=value.lower().translate(str.maketrans("","",string.punctuation))
    return " ".join(re.sub(r"\b(a|an|the)\b"," ",value).split())

@dataclass
class Instance:
    dataset:str
    split:str
    id:str
    cluster:str
    query:str
    units:list[str]
    gold:list[list[int]]
    metadata:dict

def qasper_instances(path:Path,split:str,paper_ids=None):
    data=json.loads(path.read_text()); instances=[]; audit=[]
    for paper_id,paper in data.items():
        if paper_ids is not None and paper_id not in paper_ids: continue
        paras=[normalized(p) for s in paper["full_text"] for p in s["paragraphs"] if normalized(p)]
        units=list(dict.fromkeys(paras)); lookup={p:i for i,p in enumerate(units)}
        for q in paper["qas"]:
            answers=[a["answer"] for a in q["answers"]]
            reasons=set(); gold=[]
            if not answers: reasons.add("no_annotations")
            for a in answers:
                ev=a.get("evidence",[])
                if a.get("unanswerable"): reasons.add("any_unanswerable")
                if not ev: reasons.add("any_empty_evidence")
                if any("FLOAT SELECTED" in e for e in ev): reasons.add("any_float_evidence")
                if any(normalized(e) not in lookup for e in ev if "FLOAT SELECTED" not in e):
                    reasons.add("any_unmapped_text")
                if all(normalized(e) in lookup for e in ev) and ev:
                    gold.append(sorted(set(lookup[normalized(e)] for e in ev)))
            if not units: reasons.add("empty_document")
            row={"dataset":"qasper","split":split,"id":q["question_id"],"paper_id":paper_id,
                 "included":not reasons,"reasons":sorted(reasons),"n_annotations":len(answers),
                 "duplicate_paragraphs":len(paras)-len(units)}
            audit.append(row)
            if reasons: continue
            if len(gold)!=len(answers): raise ValueError("Incomplete reference mapping")
            instances.append(Instance("qasper",split,q["question_id"],paper_id,q["question"],units,gold,
                {"n_annotations":len(answers),"answer_agreement":len({answer_key(a) for a in answers})==1,
                 "answer_keys":[answer_key(a) for a in answers],
                 "duplicate_paragraphs":len(paras)-len(units)}))
    return instances,audit

def scifact_instances(claims_path:Path,corpus_path:Path,split:str,claim_ids=None):
    corpus={str(x["doc_id"]):x for x in map(json.loads,corpus_path.read_text().splitlines())}
    instances=[];audit=[]
    for claim in map(json.loads,claims_path.read_text().splitlines()):
        if claim_ids is not None and claim["id"] not in claim_ids: continue
        if not claim["evidence"]:
            audit.append({"dataset":"scifact","split":split,"id":str(claim["id"]),"included":False,"reasons":["no_evidence_claim"]})
        for doc_id,ev in claim["evidence"].items():
            units=corpus[doc_id]["abstract"]; reasons=set()
            gold=[sorted(set(a["sentences"])) for a in ev]
            if not gold or any(not a for a in gold): reasons.add("empty_rationale")
            if any(i<0 or i>=len(units) for a in gold for i in a): reasons.add("invalid_sentence")
            if len({a["label"] for a in ev})!=1: reasons.add("conflicting_labels")
            ix=f"{claim['id']}:{doc_id}"
            audit.append({"dataset":"scifact","split":split,"id":ix,"included":not reasons,"reasons":sorted(reasons)})
            if reasons: continue
            instances.append(Instance("scifact",split,ix,doc_id,claim["claim"],units,gold,
                {"claim_id":claim["id"],"doc_id":doc_id,"label":ev[0]["label"],
                 "n_annotations":len(ev),"answer_agreement":True,
                 "duplicate_sentences":len(units)-len(set(map(normalized,units)))}))
    # Cluster all claim/doc pairs connected through either the claim or document.
    # This keeps shared abstracts and claim/negation families sharing a document together.
    parent={}
    def find(a):
        parent.setdefault(a,a)
        if parent[a]!=a: parent[a]=find(parent[a])
        return parent[a]
    def union(a,b): parent[find(a)]=find(b)
    for x in instances: union("c:"+str(x.metadata["claim_id"]),"d:"+x.metadata["doc_id"])
    comps={}
    for x in instances: comps.setdefault(find("d:"+x.metadata["doc_id"]),[]).append(x.id)
    labels={k:min(v) for k,v in comps.items()}
    for x in instances: x.cluster=labels[find("d:"+x.metadata["doc_id"])]
    return instances,audit

def score(predicted,gold):
    refs=[set(e) for e in gold]
    if not refs or any(not e for e in refs): raise ValueError("Gold references must be nonempty")
    r=set(predicted);u=set.union(*refs);hits=[len(r&e) for e in refs]
    f1=lambda h,n:2*h/(len(r)+n) if r else 0.
    complete=int(any(e<=r for e in refs)); union_complete=int(u<=r);hit=int(bool(u&r))
    out={"hit":hit,"complete":complete,"union_complete":union_complete,
         "union_recall":len(u&r)/len(u),"max_recall":max(h/len(e) for h,e in zip(hits,refs)),
         "max_f1":max(f1(h,len(e)) for h,e in zip(hits,refs)),"union_f1":f1(len(u&r),len(u)),
         "hit_without_complete":hit-complete,"complete_without_union":complete-union_complete}
    assert union_complete<=complete<=hit
    return out

def topology(gold):
    refs={frozenset(e) for e in gold}; union=set.union(*(set(e) for e in refs))
    minimal={e for e in refs if not any(other<e for other in refs)}
    return {"n_references":len(gold),"n_distinct_sets":len(refs),"n_minimal_sets":len(minimal),
            "union_size":len(union),"min_set_size":min(map(len,refs)),
            "max_set_size":max(map(len,refs)),"union_to_min_size":len(union)/min(map(len,refs)),
            "has_alternatives":int(len(minimal)>1),"has_compound_requirement":int(all(len(e)>1 for e in refs))}

def bm25(query,units,k1=1.2,b=.75):
    bags=[Counter(tokens(p)) for p in units];n=len(bags); lengths=[sum(p.values()) for p in bags]
    avg=sum(lengths)/n if n else 0
    if not avg:return [0.]*n
    df=Counter(w for p in bags for w in p)
    scores=[]
    for bag,dl in zip(bags,lengths):
        value=0.
        for w in sorted(set(tokens(query))):
            f=bag[w]
            if not f:continue
            idf=math.log(1+(n-df[w]+.5)/(df[w]+.5))
            value+=idf*(f*(k1+1))/(f+k1*(1-b+b*dl/avg))
        scores.append(value)
    return scores

def rank(instance,method,seed=20261002):
    units=instance.units
    if method=="bm25": scores=bm25(instance.query,units)
    elif method=="tfidf":
        vectorizer=TfidfVectorizer(tokenizer=tokens,token_pattern=None,lowercase=False)
        if not any(tokens(u) for u in units): scores=[0.]*len(units)
        else:
            matrix=vectorizer.fit_transform(units)
            scores=(matrix@vectorizer.transform([instance.query]).T).toarray().ravel().tolist()
    elif method=="dense":
        from dense import dense_scores
        scores=dense_scores(instance.query,units)
    elif method=="lead": scores=[float(-i) for i in range(len(units))]
    elif method=="random":
        rng=random.Random(digest([seed,instance.dataset,instance.id]))
        scores=[rng.random() for _ in units]
    else: raise ValueError(method)
    order=sorted(range(len(units)),key=lambda i:(-scores[i],i))
    return order,scores

def completion_costs(order,gold,units):
    pos={u:i+1 for i,u in enumerate(order)}
    cumulative=np.cumsum([max(1,len(tokens(units[i]))) for i in order]).tolist()
    depths=[max(pos[i] for i in e) for e in gold]
    d_any=min(depths);d_union=max(depths)
    return {"depth_complete":d_any,"depth_union":d_union,
            "depth_penalty":d_union-d_any,"tokens_complete":cumulative[d_any-1],
            "tokens_union":cumulative[d_union-1],"tokens_penalty":cumulative[d_union-1]-cumulative[d_any-1]}

def load_jsonl(path): return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def recover_jsonl(path):
    """Drop only an uncommitted final line; quarantine bytes before truncation."""
    raw=path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        boundary=raw.rfind(b"\n")+1
        tail=raw[boundary:]
        quarantine=path.with_suffix(path.suffix+".interrupted-"+hashlib.sha256(tail).hexdigest()[:12])
        quarantine.write_bytes(tail)
        with path.open("r+b") as f:f.truncate(boundary)
    return load_jsonl(path)  # Interior corruption must fail loudly.

def pipeline_hash():
    files=[Path(__file__),Path(__file__).with_name("dense.py")]
    return digest({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files})

def append_jsonl(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a") as f: f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n"); f.flush(); os.fsync(f.fileno())

def run_instances(instances,config,output_path,limit=None):
    cfg_hash=digest(config); source_hash=pipeline_hash()
    previous=recover_jsonl(output_path) if output_path.exists() else []
    wanted={(x.dataset,x.id) for x in instances}
    hashes={(x.dataset,x.id):digest(asdict(x)) for x in instances}
    if any(r["config_hash"]!=cfg_hash or r["source_hash"]!=source_hash for r in previous):
        raise ValueError("Resume configuration/source mismatch: choose a new run directory")
    if any((r["dataset"],r["id"]) not in wanted for r in previous): raise ValueError("Unexpected prior item")
    if any(r["instance_hash"]!=hashes[(r["dataset"],r["id"])] for r in previous): raise ValueError("Resume input mismatch")
    keys=[(r["dataset"],r["id"],r["method"]) for r in previous]
    if len(keys)!=len(set(keys)):raise ValueError("Duplicate resume records")
    done=set(keys);created=0
    for x in instances:
        for method in config["methods"]:
            key=(x.dataset,x.id,method)
            if key in done:continue
            if limit is not None and created>=limit:return created
            order,scores=rank(x,method,config["seed"])
            points=[]
            for k in config["ks"]:
                p=order[:k];points.append({"k":k,"retrieved_n":len(p),**score(p,x.gold)})
            row={"dataset":x.dataset,"split":x.split,"id":x.id,"cluster":x.cluster,"method":method,
                 "instance_hash":digest(asdict(x)),"config_hash":cfg_hash,"source_hash":source_hash,
                 "ranking":order,"retrieval_scores":scores,"gold":x.gold,"unit_count":len(x.units),
                 "metadata":x.metadata,"topology":topology(x.gold),"costs":completion_costs(order,x.gold,x.units),"points":points}
            append_jsonl(output_path,row);created+=1
            if created%100==0:print(json.dumps({"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"new_records":created,"last":key}),flush=True)
    return created
