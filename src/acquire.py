"""Download research inputs with hashes and resumable per-file acquisition."""
from pathlib import Path
import urllib.request, json, hashlib, datetime, time, argparse
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 'literature/sources/qasper_card.md':'https://huggingface.co/datasets/allenai/qasper/raw/main/README.md',
 'literature/sources/qasper_loader.py.txt':'https://huggingface.co/datasets/allenai/qasper/raw/main/qasper.py',
 'literature/sources/scifact_license.md':'https://raw.githubusercontent.com/allenai/scifact/master/LICENSE.md',
 'literature/sources/scifact_data.md':'https://raw.githubusercontent.com/allenai/scifact/master/doc/data.md',
 'literature/sources/scifact_evaluation.md':'https://raw.githubusercontent.com/allenai/scifact/master/doc/evaluation.md',
 'literature/sources/scifact_evaluator.py.txt':'https://raw.githubusercontent.com/allenai/scifact-evaluator/master/evaluator/eval.py',
 'literature/sources/qasper_paper.pdf':'https://aclanthology.org/2021.naacl-main.365.pdf',
 'literature/sources/scifact_paper.pdf':'https://aclanthology.org/2020.emnlp-main.609.pdf',
 'literature/sources/qasper_heuristics.py.txt':'https://raw.githubusercontent.com/allenai/qasper-led-baseline/main/scripts/evidence_retrieval_heuristic_baselines.py',
 'literature/sources/scifact_annotation_guide.pdf':'https://scifact.s3-us-west-2.amazonaws.com/doc/evidence-annotation-instructions.pdf',
 'data/raw/scifact.tar.gz':'https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz',
 'literature/sources/irrj_submissions.html':'https://irrj.org/about/submissions',
 'literature/sources/irrj_about.html':'https://irrj.org/about',
 'literature/sources/information_research_submissions.html':'https://informationr.net/infres/about/submissions'
}
def acquire(sources=SOURCES):
 manifest_path=ROOT/'data/acquisition_manifest.json'
 manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
 for rel,url in sources.items():
  p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists() and rel in manifest and hashlib.sha256(p.read_bytes()).hexdigest()==manifest[rel].get('sha256'):
   print('cached',rel,flush=True);continue
  for attempt in range(3):
   try:
    req=urllib.request.Request(url,headers={'User-Agent':'AstraAcademicResearch/0.1 (public reproducibility study)'})
    with urllib.request.urlopen(req,timeout=60) as resp:
     content=resp.read(); final=resp.geturl(); status=resp.status
    tmp=p.with_suffix(p.suffix+'.part');tmp.write_bytes(content);tmp.replace(p)
    manifest[rel]={'url':url,'final_url':final,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'status':status}
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print('downloaded',rel,len(content),flush=True);break
   except Exception as e:
    print('failed',rel,attempt+1,repr(e),flush=True)
    with (ROOT/'logs/acquisition_failures.jsonl').open('a') as f:f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':url,'error':repr(e),'attempt':attempt+1})+'\n')
    if attempt<2:time.sleep(2)
if __name__=='__main__': acquire()
