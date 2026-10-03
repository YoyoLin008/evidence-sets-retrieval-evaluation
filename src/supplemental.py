"""Post-main joint annotation sensitivity and independent resampling audit."""
import json,datetime,hashlib
import numpy as np,pandas as pd
from evidence import *
from analyze import bootstrap_matrix,estimates,save_csv
def main():
    plan=ROOT/"planning/amendment_01.md";freeze=ROOT/"analysis/amendment_01_freeze.json"
    if not freeze.exists():freeze.write_text(json.dumps({"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"plan_sha256":hashlib.sha256(plan.read_bytes()).hexdigest()},indent=2)+"\n")
    xs=[Instance(**r) for r in load_jsonl(ROOT/"outputs/main_v1/instances.jsonl")]
    raw=load_jsonl(ROOT/"outputs/main_v1/rankings.jsonl");lookup={(r["dataset"],r["id"],r["method"]):r for r in raw}
    extra=[];validation=[];diagnostics={}
    for d,k in [("qasper",5),("scifact",3)]:
        dx=sorted([x for x in xs if x.dataset==d],key=lambda x:x.id)
        chosen=[x for x in dx if x.metadata["answer_agreement"]]
        boot=bootstrap_matrix([x.cluster for x in chosen])
        for method in ["bm25","tfidf","dense"]:
            points=[]
            for x in chosen:
                sets={frozenset(e) for e in x.gold};minimal=[list(e) for e in sets if not any(z<e for z in sets)]
                r=lookup[d,x.id,method];points.append(score(r["ranking"][:k],minimal))
            for e in estimates(points,["hit","complete","union_complete","hit_without_complete","complete_without_union"],boot):
                extra.append({"dataset":d,"method":method,"n":len(chosen),"clusters":len(set(x.cluster for x in chosen)),"k":k,"variant":"joint_agreement_minimal","status":"exploratory post-main",**e})
        # Separate direct cluster draw, without the production multinomial matrix.
        groups={}
        for x in dx:groups.setdefault(x.cluster,[]).append(lookup[d,x.id,"bm25"])
        arrays=[]
        for group in groups.values():
            arrays.append(np.array([[next(p for p in r["points"] if p["k"]==k)[m] for m in ["hit_without_complete","complete_without_union"]] for r in group]))
        rng=np.random.default_rng(91827);dist=[]
        for _ in range(10000):
            sample=rng.integers(0,len(arrays),len(arrays))
            totals=np.sum([arrays[j].sum(axis=0) for j in sample],axis=0)
            dist.append(totals/sum(len(arrays[j]) for j in sample))
        ci=np.quantile(dist,[.025,.975],axis=0)
        for j,m in enumerate(["hit_without_complete","complete_without_union"]):
            validation.append({"dataset":d,"metric":m,"lo":ci[0,j],"hi":ci[1,j],"replicates":10000,"seed":91827,"implementation":"direct cluster draw and loop aggregation"})
        diagnostics[d]={"items":len(dx),"unique_clusters":len(groups),"largest_cluster":max(map(len,groups.values())),
                        "overlapping_distinct_refs":sum(any(a&b for i,a in enumerate([set(e) for e in x.gold]) for b in [set(e) for e in x.gold][i+1:] if a!=b) for x in dx),
                        "duplicate_unit_items":sum(x.metadata.get("duplicate_paragraphs",0)>0 or x.metadata.get("duplicate_sentences",0)>0 for x in dx),
                        "distinct_evidence_multiset_items":sum(topology(x.gold)["n_distinct_sets"]>1 for x in dx)}
    da=load_jsonl(ROOT/"outputs/main_v1/dense_audit.jsonl")
    for d in diagnostics:
        ds=[x for x in da if x["dataset"]==d]
        diagnostics[d]["query_truncated_items"]=sum(x["query"]["truncated"] for x in ds)
        diagnostics[d]["any_unit_truncated_items"]=sum(bool(x["truncated_units"]) for x in ds)
        diagnostics[d]["gold_truncated_items"]=sum(x["any_gold_truncated"] for x in ds)
    save_csv("joint_sensitivity.csv",extra);save_csv("independent_bootstrap.csv",validation)
    (ROOT/"analysis/diagnostics.json").write_text(json.dumps(diagnostics,indent=2)+"\n")
    print(pd.DataFrame(extra).query("method=='bm25'").to_string(index=False));print(diagnostics)
if __name__=="__main__":main()
