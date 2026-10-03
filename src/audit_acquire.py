from pathlib import Path
import json,urllib.request,urllib.error,concurrent.futures,hashlib,re,datetime
ROOT=Path(__file__).resolve().parents[1]/'revisions/v2/audit'
def fetch(url):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'EvidenceRepresentationResearch/2.0'}),timeout=25) as f:return f.read(),f.geturl(),None
 except Exception as e:return None,url,str(e)
def main():
 rows=json.loads((ROOT/'discovery_all.json').read_text());projects={};out=[]
 for r in rows:
  m=re.match(r'https://(github.com)/([^/]+)/([^/?#]+)',r['url']) or re.match(r'https://(huggingface.co)/datasets/([^/]+)/([^/?#]+)',r['url'])
  if not m:continue
  domain,user,repo=m.groups();key=domain+'/'+user+'/'+repo
  projects.setdefault(key,[]).append(r)
 def job(pair):
  key,rs=pair;domain,user,repo=key.split('/');folder=ROOT/'sources'/hashlib.sha256(key.lower().encode()).hexdigest()[:16];folder.mkdir(exist_ok=True)
  result=dict(canonical=key,directory=str(folder.relative_to(ROOT)),queries=sorted(set(r['query_index'] for r in rs)),benchmark_queries=sorted(set(r['benchmark'] for r in rs)),urls=sorted(set(r['url'] for r in rs)),acquired_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  if domain=='huggingface.co':
   blob,url,error=fetch(f'https://huggingface.co/api/datasets/{user}/{repo}')
   if blob:
    (folder/'metadata.json').write_bytes(blob);meta=json.loads(blob);result['revision']=meta.get('sha');result['files']=[v['rfilename'] for v in meta.get('siblings',[])];branch=meta.get('sha','main')
   else: result['metadata_error']=error;branch='main'
   urls=[f'https://huggingface.co/datasets/{user}/{repo}/resolve/{branch}/README.md']
  else:urls=[f'https://raw.githubusercontent.com/{user}/{repo}/{b}/{f}' for b in ['main','master'] for f in ['README.md','README.rst']]
  for url in urls:
   blob,final,error=fetch(url)
   if blob:
    (folder/'README.source').write_bytes(blob);text=blob.decode(errors='replace');result.update(readme_url=final,readme_sha256=hashlib.sha256(blob).hexdigest(),readme_size=len(blob),benchmark_lines=[s[:500] for s in text.splitlines() if re.search('qasper|scifact',s,re.I)][:20],opening=text[:1000]);break
  else:result['readme_error']=error
  (folder/'provenance.json').write_text(json.dumps(result,indent=2));return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
  for r in pool.map(job,projects.items()):out.append(r)
 (ROOT/'candidate_metadata.json').write_text(json.dumps(out,indent=2))
 for r in out:print(json.dumps({k:r.get(k) for k in ['canonical','queries','benchmark_lines','readme_error']}))
if __name__=='__main__':main()
