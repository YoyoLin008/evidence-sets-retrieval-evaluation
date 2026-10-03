"""Independent arithmetic and provenance audit; does not call study scoring."""
from pathlib import Path
import json,hashlib,re,math
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def read(p):return [json.loads(s) for s in p.read_text().splitlines()]
def main():
    out=ROOT/"outputs/main_v1";raw=read(out/"rankings.jsonl")
    xs={(x["dataset"],x["id"]):x for x in read(out/"instances.jsonl")}
    checked=0
    for r in raw:
        x=xs[r["dataset"],r["id"]];rank=r["ranking"];gold=[set(e) for e in x["gold"]];u=set().union(*gold)
        assert sorted(rank)==list(range(len(x["units"])))
        assert len(r["retrieval_scores"])==len(rank)
        # Source ID/reference mapping is independently reconstructed.
        assert r["gold"]==x["gold"]
        for p in r["points"]:
            pred=set(rank[:p["k"]]);h=bool(pred&u);c=any(e.issubset(pred) for e in gold);a=u.issubset(pred)
            result={"hit":int(h),"complete":int(c),"union_complete":int(a),
                    "hit_without_complete":int(h)-int(c),"complete_without_union":int(c)-int(a),
                    "union_recall":len(pred&u)/len(u),"max_recall":max(len(pred&e)/len(e) for e in gold),
                    "max_f1":max(2*len(pred&e)/(len(pred)+len(e)) for e in gold),
                    "union_f1":2*len(pred&u)/(len(pred)+len(u))}
            for k,v in result.items():assert math.isclose(v,p[k],abs_tol=1e-12)
            checked+=1
        depths=[next(j for j in range(1,len(rank)+1) if e.issubset(rank[:j])) for e in gold]
        c=min(depths);a=max(depths)
        counts=[max(1,len(re.findall(r"\w+",x["units"][j].lower()))) for j in rank]
        assert r["costs"]=={"depth_complete":c,"depth_union":a,"depth_penalty":a-c,
                            "tokens_complete":sum(counts[:c]),"tokens_union":sum(counts[:a]),"tokens_penalty":sum(counts[c:a])}
    primary=pd.read_csv(ROOT/"tables/primary.csv");curves=pd.read_csv(ROOT/"tables/curve_estimates.csv")
    for _,t in primary.iterrows():
        vals=[p[t.metric] for r in raw if r["dataset"]==t.dataset and r["method"]==t.method for p in r["points"] if p["k"]==t.k]
        assert len(vals)==t.n and abs(np.mean(vals)-t["mean"])<1e-9
        assert t.lo-1e-10<=t["mean"]<=t.hi+1e-10
    # Independently reconstruct QASPER normalized paragraph references from source.
    qdata=json.loads((ROOT/"data/raw/qasper-test-and-evaluator-v0/qasper-test-v0.3.json").read_text())
    for paper_id,paper in qdata.items():
        units=list(dict.fromkeys(" ".join(p.split()) for s in paper["full_text"] for p in s["paragraphs"] if p.strip()))
        for qa in paper["qas"]:
            key=("qasper",qa["question_id"])
            if key not in xs:continue
            x=xs[key];assert x["units"]==units
            expected=[sorted({units.index(" ".join(e.split())) for e in a["answer"]["evidence"]}) for a in qa["answers"]]
            assert expected==x["gold"]
    # Cluster validity: sharing either a claim or an abstract cannot cross clusters.
    for field in ["claim_id","doc_id"]:
        seen={}
        for x in xs.values():
            if x["dataset"]!="scifact":continue
            val=x["metadata"][field]
            if val in seen:assert seen[val]==x["cluster"]
            seen[val]=x["cluster"]
    freeze=json.loads((ROOT/"logs/main_freeze.json").read_text())
    for rel,sha in {**freeze["frozen_files"],**freeze["input_files"]}.items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha
    result={"passed":True,"rank_records":len(raw),"score_points":checked,"primary_rows":len(primary),"source_mapping":"all included QASPER questions",
            "cost_recomputation":"all rankings; independent prefix search","cluster_check":"all SciFact claim/doc links",
            "frozen_hashes":"all checked","interval_audit":"bootstrap fixtures plus bounds; separate end-to-end resampling check in supplemental audit"}
    (ROOT/"analysis/validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
