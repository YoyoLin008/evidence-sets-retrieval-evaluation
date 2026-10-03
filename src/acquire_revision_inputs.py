"""Restore pinned revision audit evidence; optional Qwen files, never inference."""
from pathlib import Path
import argparse,json,hashlib,urllib.request
R=Path(__file__).resolve().parents[1];A=R/'revisions/v2/audit';C=R/'revisions/v2/compute'
def get(url,path,digest):
 if path.exists():
  assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,('existing checksum mismatch',path);return
 path.parent.mkdir(parents=True,exist_ok=True);req=urllib.request.Request(url,headers={'User-Agent':'EvidenceMeasurementResearch/2.0'});data=urllib.request.urlopen(req,timeout=180).read();assert hashlib.sha256(data).hexdigest()==digest,('download checksum mismatch',url);path.write_bytes(data)
def main():
 p=argparse.ArgumentParser();p.add_argument('--qwen',action='store_true');a=p.parse_args()
 manifest=json.loads((A/'file_manifest.json').read_text())
 for x in manifest:
  if x.get('sha256'):get(x['url'],A/x['local'],x['sha256'])
 x=json.loads((A/'mteb_schema_check.json').read_text());pin=next(r for r in json.loads((A/'pins.json').read_text()) if r['index']==112);get(x['url'],A/pin['directory']/'files/QASPER-corpus/test-00000-of-00001.parquet',x['sha256'])
 for x in json.loads((A/'openviking_lineage_check.json').read_text()):
  if x.get('sha256'):get(x['url'],A/'sources/b44f52925239d1a7/files'/x['path'],x['sha256'])
 if a.qwen:
  rev=json.loads((C/'runtime_freeze.json').read_text())['config']['revision']
  for f,h in json.loads((C/'model_manifest.json').read_text()).items():get('https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/resolve/'+rev+'/'+f,C/'model'/f,h)
 print('Pinned audit evidence verified; Qwen files', 'included' if a.qwen else 'not requested')
if __name__=='__main__':main()
