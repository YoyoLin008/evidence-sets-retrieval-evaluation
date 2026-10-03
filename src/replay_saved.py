"""Restore source annotations and saved rankings for analysis-only replay."""
from pathlib import Path
from dataclasses import asdict
import json,hashlib,shutil
from evidence import ROOT,qasper_instances,scifact_instances
from main_study import immutable_jsonl

def main():
 out=ROOT/'outputs/main_v1'
 if out.exists() and any(out.iterdir()):raise SystemExit('Use a clean copy: outputs/main_v1 must be empty.')
 freeze=json.loads((ROOT/'logs/main_freeze.json').read_text())
 for p,h in {**freeze['frozen_files'],**freeze['input_files']}.items():
  assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 cfg=json.loads((ROOT/'configs/main_v1.json').read_text())
 q,qa=qasper_instances(ROOT/cfg['qasper_file'],'test')
 s,sa=scifact_instances(ROOT/cfg['scifact_claims'],ROOT/cfg['scifact_corpus'],'dev')
 out.mkdir(parents=True,exist_ok=True)
 immutable_jsonl(out/'instances.jsonl',[asdict(x) for x in sorted(q+s,key=lambda x:(x.dataset,x.id))])
 expected=json.loads((ROOT/'revisions/v2/baseline_manifest.json').read_text())['protected']['outputs/main_v1/instances.jsonl']
 assert hashlib.sha256((out/'instances.jsonl').read_bytes()).hexdigest()==expected
 for name in ['rankings.jsonl','audit.jsonl','dense_audit.jsonl','run_status.json']:
  shutil.copy2(ROOT/'reference_outputs/main_v1'/name,out/name)
 print(json.dumps({'mode':'saved-ranking replay; no new retrieval','qasper':len(q),'scifact':len(s),'reconstructed_instances_match_frozen_hash':True}))
if __name__=='__main__':main()
