"""Validate exact local release bytes before any reproduction modifies them."""
from pathlib import Path
import hashlib,json,argparse
R=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=R);a=p.parse_args();root=a.root.resolve()
 m=json.loads((root/'PACKAGE_MANIFEST.json').read_text());checked=0
 for rel,v in m['files'].items():
  f=root/rel;assert f.is_file(),('missing',rel);assert f.stat().st_size==v['bytes'],('size',rel);assert hashlib.sha256(f.read_bytes()).hexdigest()==v['sha256'],('hash',rel);checked+=1
 expected=set(m['files'])|{'PACKAGE_MANIFEST.json'};actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}
 extra=sorted(actual-expected)
 # Extra runtime files are reported, not hidden. Tracked release contents must still match.
 assert not (root/'data/raw').exists() and not (root/'revisions/v2/compute/model').exists(),'Unexpected acquired payload in clean release'
 print(json.dumps({'passed':True,'files_verified':checked,'extra_files':extra,'scope':'Exact delivered release bytes, before reproduction'},indent=2))
if __name__=='__main__':main()
