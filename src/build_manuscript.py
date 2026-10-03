
"""Build the journal source and document model directly from verified numeric tables."""
from pathlib import Path
import json,re,hashlib,datetime,argparse
import pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[1]
def main(require_qwen=True):
 from revision_v3_manuscript import Revision,source_denominators
 revision=Revision(ROOT,require_qwen=require_qwen)
 source_counts=source_denominators(ROOT)
 p=pd.read_csv(ROOT/"tables/primary.csv");c=pd.read_csv(ROOT/"tables/costs.csv")
 rob=pd.read_csv(ROOT/"tables/robustness.csv");joint=pd.read_csv(ROOT/"tables/joint_sensitivity.csv")
 flow=pd.read_csv(ROOT/"tables/cohort_flow.csv").set_index("dataset");structure=pd.read_csv(ROOT/"tables/structure.csv")
 topo=pd.read_csv(ROOT/"tables/topology.csv");one=pd.read_csv(ROOT/"tables/one_reference.csv")
 independent=pd.read_csv(ROOT/"tables/independent_bootstrap.csv")
 diag=json.loads((ROOT/"analysis/diagnostics.json").read_text())
 raw=[json.loads(s) for s in (ROOT/"reference_outputs/main_v1/rankings.jsonl").read_text().splitlines()]
 refs=json.loads((ROOT/"literature/verified_references.json").read_text())
 v={};provenance={}
 def add(key,value,source):v[key]=str(value);provenance[key]={"value":str(value),"source":source}
 def row(table,**where):
  for key,value in where.items():table=table[table[key]==value]
  assert len(table)==1,(where,len(table))
  return table.iloc[0]
 def counts(d,key):
  return {str(k):val for k,val in json.loads(row(structure,dataset=d,variable=key)["counts"]).items()}
 for d,prefix in [("qasper","Q"),("scifact","S")]:
  for metric,short in [("hit","H"),("complete","C"),("union_complete","A"),("hit_without_complete","HC"),("complete_without_union","CA")]:
   a=row(p,dataset=d,method="bm25",metric=metric)
   for field,suffix in [("mean",""),("lo","lo"),("hi","hi")]:add(prefix+short+suffix,f"{a[field]*100:.1f}",f"tables/primary.csv:{d}/bm25/{metric}/{field}")
  for method in ["dense"]:
   for metric,short in [("complete","C"),("union_complete","A")]:
    a=row(p,dataset=d,method=method,metric=metric);add(prefix+method+short,f"{a['mean']*100:.1f}","tables/primary.csv")
  for metric,short in [("max_f1","Fmax"),("union_f1","FUnion")]:
   add(prefix+short,f"{row(p,dataset=d,method='bm25',metric=metric)['mean']:.3f}","tables/primary.csv")
  a=row(c,dataset=d,method="bm25",metric="depth_penalty")
  for field,suffix in [("mean",""),("lo","Lo"),("hi","Hi")]:add(prefix+"Depth"+suffix,f"{a[field]:.2f}","tables/costs.csv")
  add(prefix+"Zero",f"{a.zero_fraction*100:.1f}","tables/costs.csv")
  add(prefix+"Tokens",f"{row(c,dataset=d,method='bm25',metric='tokens_penalty')['mean']:.1f}","tables/costs.csv")
  add(prefix+"n",int(flow.loc[d,"included"]),"tables/cohort_flow.csv")
  add(prefix+"clusters",int(flow.loc[d,"clusters"]),"tables/cohort_flow.csv")
  add(prefix+"distinct",int(diag[d]["distinct_evidence_multiset_items"]),"analysis/diagnostics.json")
  m=counts(d,"n_minimal_sets");add(prefix+"minimal",sum(val for k,val in m.items() if int(k)>1),"tables/structure.csv")
  add(prefix+"singleminimal",m["1"],"tables/structure.csv")
  m=counts(d,"min_set_size");add(prefix+"compound",sum(val for k,val in m.items() if int(k)>1),"tables/structure.csv")
  for level,short in [("1","SingleGap"),("2+","AltGap")]:
   add(prefix+short,f"{row(topo,dataset=d,method='bm25',stratum='n_minimal_sets',level=level,metric='complete_without_union')['mean']*100:.1f}","tables/topology.csv")
  add(prefix+"OneC",f"{row(one,dataset=d,method='bm25',metric='complete')['selection_mean']*100:.1f}","tables/one_reference.csv")
  m={"NoHitN":0,"PartialN":0,"OneN":0,"AllN":0}
  for record in raw:
   if record["dataset"]!=d or record["method"]!="bm25":continue
   point=next(x for x in record["points"] if x["k"]==(5 if d=="qasper" else 3))
   key="NoHitN" if not point["hit"] else "PartialN" if not point["complete"] else "OneN" if not point["union_complete"] else "AllN"
   m[key]+=1
  for k,num in m.items():add(prefix+k,num,"reference_outputs/main_v1/rankings.jsonl:BM25 primary taxonomy")
 add("Qtotal",int(flow.loc["qasper","audit_units"]),"tables/cohort_flow.csv")
 assert source_counts["Qtotal"]==int(v["Qtotal"])
 add("Qpapers",source_counts["Qpapers"],"revisions/v3/statistics/source_denominators.json:hash-verified QASPER source")
 add("Qexcluded",int(flow.loc["qasper","excluded"]),"tables/cohort_flow.csv")
 reason=json.loads(flow.loc["qasper","exclusion_reason_counts"])
 for k,source in [("Qfloat","any_float_evidence"),("Qempty","any_empty_evidence"),("Qunanswerable","any_unanswerable"),("Qunmapped","any_unmapped_text")]:add(k,reason[source],"tables/cohort_flow.csv")
 for key in ["Sclaims","Sevidenceclaims","Snoevidence"]:add(key,source_counts[key],"revisions/v3/statistics/source_denominators.json:hash-verified SciFact source")
 add("Smaxrefs",max(map(int,counts("scifact","n_references"))),"tables/structure.csv")
 freeze=json.loads((ROOT/"logs/main_freeze.json").read_text());add("FreezeTime",freeze["utc"].split(".")[0]+" UTC","logs/main_freeze.json")
 add("RankRecords",len(raw),"reference_outputs/main_v1/rankings.jsonl")
 add("ScorePoints",sum(len(r["points"]) for r in raw),"reference_outputs/main_v1/rankings.jsonl")
 first=[json.loads(s) for s in (ROOT/"logs/main_jobs.jsonl").read_text().splitlines() if '"finish"' in s][0]
 add("RunSeconds",f"{first['seconds']:.1f}","logs/main_jobs.jsonl")
 for metric,short in [("complete","C"),("union_complete","A")]:
  val=row(p,dataset="qasper",method="dense",metric=metric)["mean"]-row(p,dataset="qasper",method="bm25",metric=metric)["mean"]
  add("QdenseAdv"+short,f"{val*100:.1f}","tables/primary.csv:paired point estimate")
 for variant,short in [("answer_agreement","AgreeGap"),("minimal_reference_pruning","PrunedGap"),("no_gold_truncation","NoTruncGap")]:
  method="dense" if variant=="no_gold_truncation" else "bm25"
  a=row(rob,dataset="qasper",method=method,variant=variant,metric="complete_without_union")
  add("Q"+short,f"{a['mean']*100:.1f}","tables/robustness.csv")
  add("QNoTruncN" if variant=="no_gold_truncation" else "QagreeN" if variant=="answer_agreement" else "QPrunedN",int(a.n),"tables/robustness.csv")
 a=row(joint,dataset="qasper",method="bm25",metric="complete_without_union")
 for field,key in [("mean","QJointGap"),("lo","QJointLo"),("hi","QJointHi")]:add(key,f"{a[field]*100:.1f}","tables/joint_sensitivity.csv")
 add("QJointClusters",int(a.clusters),"tables/joint_sensitivity.csv")
 add("QAnyTrunc",diag["qasper"]["any_unit_truncated_items"],"analysis/diagnostics.json")
 add("QGoldTrunc",diag["qasper"]["gold_truncated_items"],"analysis/diagnostics.json")
 add("QEligiblePct",f"{100*int(v['Qn'])/int(v['Qtotal']):.1f}","tables/cohort_flow.csv")
 delta=[]
 for _,r in independent.iterrows():
  a=row(p,dataset=r.dataset,method="bm25",metric=r.metric);delta += [abs(r.lo-a.lo),abs(r.hi-a.hi)]
 add("BootstrapMaxDiff",f"{100*max(delta):.2f}","tables/independent_bootstrap.csv vs primary.csv")
 tok=pd.read_csv(ROOT/"tables/token_budget.csv")
 for d,prefix,budget in [("qasper","Q",512),("scifact","S",64)]:
  for metric,short in [("complete","C"),("union_complete","A")]:
   a=row(tok,dataset=d,method="bm25",lexical_token_budget=budget,metric=metric)
   add(prefix+"Token"+short,f"{a['mean']*100:.1f}","tables/token_budget.csv")
 revision.populate(add)
 blocks=json.loads((ROOT/"paper/article_blocks_1.json").read_text())+json.loads((ROOT/"paper/article_blocks_2.json").read_text())
 def replace(text):
  return re.sub(r"\{([A-Za-z][A-Za-z0-9]+)\}",lambda m:v[m[1]] if m[1] in v else m[0],text)
 abstract=revision.abstract(v)
 tables={}
 def estimate(a,scale=100,digits=1):
  return f"{a['mean']*scale:.{digits}f} [{a.lo*scale:.{digits}f}, {a.hi*scale:.{digits}f}]"
 tables["cohort"]={"caption":"Source and analysis denominators. QASPER exclusion reasons overlap; SciFact claims and claim-abstract pairs are different units.","headers":["Quantity","QASPER test","SciFact dev"],"rows":[
 ["Source questions / claims",v["Qtotal"],v["Sclaims"]],
 ["Source papers",v["Qpapers"],"Known abstract supplied"],
 ["Eligible questions / pairs",v["Qn"],v["Sn"]],
 ["Resampling clusters",v["Qclusters"],v["Sclusters"]],
 ["Multiple distinct evidence sets",v["Qdistinct"],v["Sdistinct"]],
 ["Multiple minimal evidence sets",v["Qminimal"],v["Sminimal"]],
 ["No singleton reference",v["Qcompound"],v["Scompound"]],
 ["Exact answer agreement",v["QagreeN"],"Consistent rationale labels"]],
 "widths":[216,108,108]}
 rows=[]
 for d,k in [("qasper",5),("scifact",3)]:
  for method in ["bm25","tfidf","dense","lead","random"]:
   rows.append([f"{d.upper()} / {k}",{"bm25":"BM25","tfidf":"TF-IDF","dense":"MiniLM","lead":"Lead","random":"Random"}[method]]+
    [f"{row(p,dataset=d,method=method,metric=m)['mean']*100:.1f}" for m in ["hit","complete","union_complete"]]+
    [estimate(row(p,dataset=d,method=method,metric="complete_without_union"))])
 tables["primary"]={"caption":"Fixed-budget outcomes on the full eligible cohorts. H: any annotated hit; C: one completed set; A: completed union. C−A uses paired 95% cluster intervals. Lead and random are controls.","headers":["Corpus / k","Method","H (%)","C (%)","A (%)","C−A, pp [95% interval]"],"rows":rows,"widths":[77,54,42,42,42,175]}
 rows=[]
 for d in ["qasper","scifact"]:
  for method in ["bm25","tfidf","dense"]:
   a=row(c,dataset=d,method=method,metric="depth_penalty");b=row(c,dataset=d,method=method,metric="tokens_penalty")
   rows.append([d.upper(),method.upper() if method!="dense" else "MiniLM",estimate(a,1,2),f"{a['median']:.0f} [{a.q25:.0f}, {a.q75:.0f}]",estimate(b,1,1)])
 tables["costs"]={"caption":"Extra fixed-ranking prefix budget required for the union instead of one original reference. Means have 95% cluster intervals; depth medians have interquartile ranges. Lexical tokens are not encoder wordpieces.","headers":["Corpus","Method","Extra units: mean [CI]","Median [IQR]","Extra tokens: mean [CI]"],"rows":rows,"widths":[61,53,112,79,127]}
 rows=[]
 for variant,label in [("answer_agreement","Exact answer agreement"),("minimal_reference_pruning","Minimal-reference pruning"),("no_gold_truncation","MiniLM: no gold truncation")]:
  method="dense" if variant=="no_gold_truncation" else "bm25";a=row(rob,dataset="qasper",method=method,variant=variant,metric="complete_without_union")
  rows.append([label,str(int(a.n)),estimate(a)])
 a=row(joint,dataset="qasper",method="bm25",metric="complete_without_union")
 rows.append(["Agreement + minimal sets (exploratory)",str(int(a.n)),estimate(a)])
 tables["robustness"]={"caption":"QASPER union-gap sensitivities at k=5. Rows use BM25 unless indicated. The joint restriction is post-main and exploratory.","headers":["Restriction","n","C−A, pp [95% interval]"],"rows":rows,"widths":[250,42,140]}
 captions={
 "figure1_completion_curves":"BM25 completion curves. Shaded bands are 95% cluster-bootstrap intervals. The same prefixes are scored under all three definitions. Units are paragraphs for QASPER and sentences for SciFact; large k saturates at document length.",
 "figure2_paired_gaps":"Paired score gaps at the primary budgets: QASPER k=5 and SciFact k=3. Whiskers show 95% cluster intervals. The definitions guarantee nonnegative gaps; their magnitudes are the empirical quantities.",
 "figure4_annotation_structure":"BM25 union gaps stratified by the number of minimal observed evidence sets. Whiskers are 95% cluster intervals; labels give item counts. Original unions retain nested references, explaining the nonzero one-minimal-set QASPER stratum.",
 "figure3_extra_depth":"Empirical cumulative distributions of extra ranked units for union completion. Horizontal axes are transformed by log(1+extra units), with corpus-specific ranges. The large mass at zero and the tail must be considered together."
 }
 doc={"title":"When Evidence Sets Become Relevance Lists: A Controlled Audit of Scientific Retrieval Evaluation",
      "author":"Yunya Lin","affiliation":"University of Illinois Urbana-Champaign","abstract":abstract,
      "keywords":"retrieval evaluation; evidence sets; scientific information; measurement validity; reproducibility",
      "blocks":[[kind,replace(value)] for kind,value in blocks],"tables":tables,"captions":captions,"references":refs,
      "render_note":"The PDF reading copy is generated from this shared document model. The manuscript.tex source loads the separate unmodified official IRRJ style; official PDFs are exported from a clean directory."}
 from manuscript_revision_tables import enrich
 doc=enrich(doc)
 doc=revision.enrich(doc)
 doc["abstract"]=revision.abstract(v)
 for table in doc["tables"].values():
  table["caption"]=table["caption"].replace("SCIFACT","SciFact")
  table["rows"]=[[cell.replace("SCIFACT","SciFact") for cell in row] for row in table["rows"]]
 (ROOT/"paper/article.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n")
 supplement=dict(doc)
 supplement.update(title="Supplementary material: "+doc["title"],abstract=revision.supplement_abstract(),blocks=[[kind,replace(value)] for kind,value in json.loads((ROOT/"paper/supplement_blocks.json").read_text())],references={k:refs[k] for k in ["alt2026","li2025","qwen"]})
 (ROOT/"paper/supplement.json").write_text(json.dumps(supplement,ensure_ascii=False,indent=2)+"\n")
 (ROOT/"analysis/manuscript_numbers.json").write_text(json.dumps(provenance,indent=2)+"\n")
 (ROOT/"analysis/manuscript_values.json").write_text(json.dumps(v,indent=2)+"\n")
 revision.save_provenance()
 print("Built manuscript model with",len(blocks),"blocks,",len(v),"source-linked values,",len(refs),"verified references.")
if __name__=="__main__":
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--draft-without-qwen",action="store_true",help="Internal layout draft only; final builds require the complete validated encoder run")
 args=parser.parse_args()
 main(require_qwen=not args.draft_without_qwen)
