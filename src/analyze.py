"""Analyze frozen rankings without changing the retrieval pipeline."""
from pathlib import Path
from collections import Counter
import json,hashlib,itertools
import numpy as np
import pandas as pd
from evidence import ROOT,Instance,load_jsonl,score,tokens,digest,topology,hash_order

SEED=20261002;B=10000
METRICS=["hit","complete","union_complete","hit_without_complete","complete_without_union","max_recall","union_recall","max_f1","union_f1"]
def bootstrap_matrix(clusters,seed=SEED,b=B):
    labels=sorted(set(clusters));ix={x:i for i,x in enumerate(labels)}
    ids=np.array([ix[x] for x in clusters]);counts=np.bincount(ids,minlength=len(labels))
    rng=np.random.default_rng(seed)
    w=rng.multinomial(len(labels),np.full(len(labels),1/len(labels)),size=b)
    return ids,counts,w
def estimate(values,boot):
    values=np.asarray(values,dtype=float)
    if values.ndim==1:values=values[:,None]
    ids,counts,w=boot
    totals=np.zeros((len(counts),values.shape[1]));np.add.at(totals,ids,values)
    samples=(w@totals)/(w@counts)[:,None]
    return values.mean(axis=0),np.quantile(samples,[.025,.975],axis=0).T
def estimates(rows,metrics,boot):
    m,ci=estimate([[r[k] for k in metrics] for r in rows],boot)
    return [{"metric":k,"mean":float(v),"lo":float(bounds[0]),"hi":float(bounds[1])} for k,v,bounds in zip(metrics,m,ci)]
def save_csv(name,rows):
    pd.DataFrame(rows).to_csv(ROOT/"tables"/name,index=False,float_format="%.10g")
def main():
    out=ROOT/"outputs/main_v1"
    status=json.loads((out/"run_status.json").read_text())
    if not status["complete"]:raise ValueError("Refusing incomplete main run")
    raw=load_jsonl(out/"rankings.jsonl")
    xs=[Instance(**r) for r in load_jsonl(out/"instances.jsonl")]
    inst={(x.dataset,x.id):x for x in xs}
    dense={(r["dataset"],r["id"]):r for r in load_jsonl(out/"dense_audit.jsonl")}
    audit=load_jsonl(out/"audit.jsonl")
    cfg=json.loads((ROOT/"configs/main_v1.json").read_text())
    methods=cfg["methods"];ks=cfg["ks"]
    summary=[];primary=[];costs=[];structure=[];flow=[];robust=[];topo=[];tokenrows=[];examples=[];contrasts=[];one_refs=[]
    for d,kprimary in [("qasper",5),("scifact",3)]:
        dx=sorted([x for x in xs if x.dataset==d],key=lambda x:x.id);ids=[x.id for x in dx]
        n=len(dx);clusters=[x.cluster for x in dx];boot=bootstrap_matrix(clusters)
        rr={(r["method"],r["id"]):r for r in raw if r["dataset"]==d}
        if len(rr)!=n*len(methods):raise ValueError("Missing or duplicate rows")
        ds_audit=[r for r in audit if r["dataset"]==d]
        reasons=Counter(r for a in ds_audit for r in a["reasons"])
        exclusive=Counter("included" if a["included"] else a["reasons"][0] for a in ds_audit)
        flow.append({"dataset":d,"audit_units":len(ds_audit),"included":n,"clusters":len(set(clusters)),
                     "excluded":sum(not x["included"] for x in ds_audit),"exclusion_reason_counts":json.dumps(reasons),"exclusive_flow":json.dumps(exclusive),
                     "audit_grain":"question" if d=="qasper" else "evidence-bearing pair or no-evidence claim"})
        ts=[topology(x.gold) for x in dx]
        for key in ts[0]:
            vals=[t[key] for t in ts]
            structure.append({"dataset":d,"variable":key,"n":n,"mean":np.mean(vals),"median":np.median(vals),"counts":json.dumps(dict(sorted(Counter(vals).items())))})
        structure.append({"dataset":d,"variable":"answer_agreement","n":n,"mean":np.mean([x.metadata["answer_agreement"] for x in dx]),"counts":json.dumps(Counter(x.metadata["answer_agreement"] for x in dx))})
        structure.append({"dataset":d,"variable":"units_per_item","n":n,"mean":np.mean([len(x.units) for x in dx]),"median":np.median([len(x.units) for x in dx])})
        structure.append({"dataset":d,"variable":"any_gold_truncated","n":n,"mean":np.mean([dense[(d,x.id)]["any_gold_truncated"] for x in dx])})
        for method in methods:
            rows=[rr[method,i] for i in ids]
            for k in ks:
                points=[next(p for p in r["points"] if p["k"]==k) for r in rows]
                est=estimates(points,METRICS,boot)
                for e in est:
                    result={"dataset":d,"method":method,"k":k,"n":n,"clusters":len(set(clusters)),**e}
                    summary.append(result)
                    if k==kprimary:primary.append(result)
                summary.append({"dataset":d,"method":method,"k":k,"n":n,"clusters":len(set(clusters)),
                                "metric":"saturated_fraction","mean":np.mean([r["unit_count"]<k for r in rows])})
            cost=[r["costs"] for r in rows]
            for e in estimates(cost,["depth_complete","depth_union","depth_penalty","tokens_complete","tokens_union","tokens_penalty"],boot):
                a=np.array([r[e["metric"]] for r in cost])
                costs.append({"dataset":d,"method":method,"n":n,**e,"median":np.median(a),"q25":np.quantile(a,.25),"q75":np.quantile(a,.75),"zero_fraction":np.mean(a==0)})
            points=[next(p for p in r["points"] if p["k"]==kprimary) for r in rows]
            # Explicit denominator-preserving topology strata.
            for key,labels in [("n_minimal_sets",["1","2+"]),("min_set_size",["1","2+"]),("n_distinct_sets",["1","2+"])]:
                for label in labels:
                    chosen=[i for i,t in enumerate(ts) if (t[key]==1 if label=="1" else t[key]>=2)]
                    if not chosen:continue
                    sb=bootstrap_matrix([clusters[i] for i in chosen])
                    for e in estimates([points[i] for i in chosen],["hit_without_complete","complete_without_union"],sb):
                        topo.append({"dataset":d,"method":method,"k":kprimary,"stratum":key,"level":label,"n":len(chosen),**e})
            if method in ["bm25","tfidf","dense"]:
                variants={"answer_agreement":[i for i,x in enumerate(dx) if x.metadata["answer_agreement"]],
                          "no_gold_truncation":[i for i,x in enumerate(dx) if not dense[d,x.id]["any_gold_truncated"]]}
                for v,chosen in variants.items():
                    sb=bootstrap_matrix([clusters[i] for i in chosen])
                    for e in estimates([points[i] for i in chosen],["complete","hit_without_complete","complete_without_union"],sb):
                        robust.append({"dataset":d,"method":method,"variant":v,"n":len(chosen),"k":kprimary,**e})
                # Minimal reference pruning preserves C but may shrink union of nested sets.
                pruned=[]
                for x,r in zip(dx,rows):
                    unique={frozenset(e) for e in x.gold}
                    minimum=[list(e) for e in unique if not any(z<e for z in unique)]
                    p=score(r["ranking"][:kprimary],minimum);pruned.append(p)
                    assert p["complete"]==score(r["ranking"][:kprimary],x.gold)["complete"]
                for e in estimates(pruned,["complete","hit_without_complete","complete_without_union"],boot):
                    robust.append({"dataset":d,"method":method,"variant":"minimal_reference_pruning","n":n,"k":kprimary,**e})
                # One-reference diagnostic: 100 independently seeded deterministic selections.
                samples=[]
                for rep in range(100):
                    srows=[]
                    for x,r in zip(dx,rows):
                        choice=int(digest([SEED,"one-reference",rep,d,x.id]),16)%len(x.gold)
                        srows.append(score(r["ranking"][:kprimary],[x.gold[choice]]))
                    samples.append([np.mean([z[k] for z in srows]) for k in ["complete","hit_without_complete","complete_without_union"]])
                a=np.asarray(samples)
                for j,m in enumerate(["complete","hit_without_complete","complete_without_union"]):
                    one_refs.append({"dataset":d,"method":method,"k":kprimary,"metric":m,"n":n,"selections":100,
                                     "selection_mean":a[:,j].mean(),"selection_min":a[:,j].min(),"selection_max":a[:,j].max(),
                                     "note":"Selection variability; not confidence interval"})
            for budget in [64,128,256,512,1024,2048]:
                points=[]
                for x,r in zip(dx,rows):
                    p=[];used=0
                    for u in r["ranking"]:
                        cost=max(1,len(tokens(x.units[u])))
                        if used+cost>budget:break
                        used+=cost;p.append(u)
                    points.append(score(p,x.gold))
                for e in estimates(points,["hit","complete","union_complete","hit_without_complete","complete_without_union"],boot):
                    tokenrows.append({"dataset":d,"method":method,"lexical_token_budget":budget,"n":n,**e})
            if method=="bm25":
                categories={}
                for x,p,r in zip(dx,points if False else [next(p for p in r["points"] if p["k"]==kprimary) for r in rows],rows):
                    cat=("no_hit" if not p["hit"] else "partial" if not p["complete"] else "one_not_union" if not p["union_complete"] else "union")
                    categories.setdefault(cat,[]).append(x.id)
                for category,available in categories.items():
                    for item_id in hash_order(available)[:3]:
                        x=inst[d,item_id];r=rr[method,item_id]
                        examples.append({"dataset":d,"id":item_id,"cluster":x.cluster,"category":category,"category_n":len(available),"query":x.query,
                                         "gold":x.gold,"retrieved":r["ranking"][:kprimary],"k":kprimary,"topology":topology(x.gold),
                                         "answer_agreement":x.metadata["answer_agreement"],"selection":"First 3 IDs ordered by SHA256 within BM25 category"})
        # Paired method differences; do not infer reversals from independent interval overlap.
        for a,b in itertools.combinations(["bm25","tfidf","dense"],2):
            for metric in ["complete","union_complete","max_f1","union_f1"]:
                values=[]
                for i in ids:
                    pa=next(p for p in rr[a,i]["points"] if p["k"]==kprimary)
                    pb=next(p for p in rr[b,i]["points"] if p["k"]==kprimary)
                    values.append(pa[metric]-pb[metric])
                m,ci=estimate(values,boot)
                contrasts.append({"dataset":d,"k":kprimary,"method_a":a,"method_b":b,"metric":metric,"n":n,"mean_difference":m[0],"lo":ci[0,0],"hi":ci[0,1],
                                  "note":"Exploratory pointwise interval; no multiplicity-controlled significance claim"})
    for filename,rows in [("curve_estimates.csv",summary),("primary.csv",primary),("costs.csv",costs),("structure.csv",structure),
      ("cohort_flow.csv",flow),("robustness.csv",robust),("topology.csv",topo),("token_budget.csv",tokenrows),("method_contrasts.csv",contrasts),
      ("one_reference.csv",one_refs)]:save_csv(filename,rows)
    (ROOT/"analysis/representative_examples.json").write_text(json.dumps(examples,indent=2,ensure_ascii=False)+"\n")
    manifest={"input_sha256":hashlib.sha256((out/"rankings.jsonl").read_bytes()).hexdigest(),"analysis_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "bootstrap":"item-weighted percentile connected-cluster bootstrap","replicates":B,"seed":SEED,
              "tables":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/"tables").glob("*.csv")}}
    (ROOT/"analysis/analysis_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(pd.DataFrame(primary).query("method=='bm25' and metric in ['hit','complete','union_complete','hit_without_complete','complete_without_union']").to_string(index=False))
if __name__=="__main__":main()
