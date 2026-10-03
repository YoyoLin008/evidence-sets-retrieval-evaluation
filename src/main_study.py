"""Frozen primary study; --limit permits bounded resumable record batches."""
from pathlib import Path
from dataclasses import asdict
from collections import Counter
import argparse,json,hashlib,datetime,time,shutil,platform,sys
from evidence import *

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def file_hash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def immutable_jsonl(path,rows):
    value="".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in rows)
    if path.exists() and path.read_text()!=value:raise ValueError(f"Changed immutable input {path}")
    if not path.exists():
        temp=path.with_suffix(".tmp");temp.write_text(value);temp.replace(path)

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--limit",type=int);args=parser.parse_args()
    out=ROOT/"outputs/main_v1";out.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/"configs/main_v1.json").read_text())
    freeze_path=ROOT/"logs/main_freeze.json"
    paths=[ROOT/p for p in ["src/evidence.py","src/dense.py","src/main_study.py",
           "configs/main_v1.json","planning/analysis_plan.md","planning/contribution_statement.md"]]
    hashes={str(p.relative_to(ROOT)):file_hash(p) for p in paths}
    input_hashes={p:file_hash(ROOT/p) for p in config["input_files"]}
    for rel,want in config["model_sha256"].items():
        if file_hash(ROOT/rel)!=want:raise ValueError("Pinned model content mismatch")
    if freeze_path.exists():
        old=json.loads(freeze_path.read_text())
        if hashes!=old["frozen_files"] or input_hashes!=old["input_files"]:raise ValueError("Frozen study changed")
    else:
        snapshot=ROOT/"logs/frozen_main_v1"
        for p in paths+list((ROOT/"tests").glob("test_*.py")):
            dest=snapshot/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        freeze={"utc":now(),"statement":"Local prospective freeze before QASPER test deserialization and SciFact dev scoring; not public preregistration.",
                "frozen_files":hashes,"input_files":input_hashes,"test_log":file_hash(ROOT/"logs/pre_main_tests_fixed.txt"),
                "python":sys.version,"platform":platform.platform()}
        freeze_path.write_text(json.dumps(freeze,indent=2)+"\n")
    start=time.monotonic();append_jsonl(ROOT/"logs/main_jobs.jsonl",{"event":"start","utc":now(),"limit":args.limit})
    # Main annotations are first deserialized only after successful freeze.
    q,qa=qasper_instances(ROOT/config["qasper_file"],"test")
    s,sa=scifact_instances(ROOT/config["scifact_claims"],ROOT/config["scifact_corpus"],"dev")
    instances=sorted(q+s,key=lambda x:(x.dataset,x.id))
    immutable_jsonl(out/"instances.jsonl",[asdict(x) for x in instances])
    immutable_jsonl(out/"audit.jsonl",qa+sa)
    print(json.dumps({"event":"cohort","n":dict(Counter(x.dataset for x in instances)),
          "clusters":{d:len({x.cluster for x in instances if x.dataset==d}) for d in ["qasper","scifact"]}}),flush=True)
    created=run_instances(instances,config,out/"rankings.jsonl",limit=args.limit)
    rows=load_jsonl(out/"rankings.jsonl")
    complete=len(rows)==len(instances)*len(config["methods"])
    if complete:
        from dense import get_encoder
        encoder=get_encoder();audit=[]
        for x in instances:
            meta=[encoder.info(t) for t in x.units]
            audit.append({"dataset":x.dataset,"id":x.id,"query":encoder.info(x.query),
              "truncated_units":[i for i,m in enumerate(meta) if m["truncated"]],
              "any_gold_truncated":any(meta[i]["truncated"] for e in x.gold for i in e)})
        immutable_jsonl(out/"dense_audit.jsonl",audit)
    summary={"event":"finish","utc":now(),"new_records":created,"records":len(rows),"expected_records":len(instances)*5,
             "complete":complete,"seconds":time.monotonic()-start}
    append_jsonl(ROOT/"logs/main_jobs.jsonl",summary)
    (out/"run_status.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary),flush=True)
if __name__=="__main__":main()
