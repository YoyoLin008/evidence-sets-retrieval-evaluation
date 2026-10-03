from pathlib import Path
import json,urllib.request,hashlib,concurrent.futures,datetime,re
ROOT=Path(__file__).resolve().parents[1]/'revisions/v2/audit'
def get(url):
 return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'EvidenceRepresentationResearch/2.0'}),timeout=60).read()
def main():
 data=json.loads((ROOT/'candidate_metadata.json').read_text());sel=json.loads((ROOT/'selected_families.json').read_text());idx=[r['index'] for r in sel if r['selected']]+[107,124,136]
 def job(i):
  r=data[i];base=ROOT/r['directory'];result=dict(index=i,canonical=r['canonical'],directory=r['directory'],utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  try:
   if r['canonical'].startswith('github.com/'):
    repo=r['canonical'][11:];meta=json.loads(get('https://api.github.com/repos/'+repo));(base/'github_metadata.json').write_text(json.dumps(meta,indent=2))
    branch=meta['default_branch'];commit=json.loads(get('https://api.github.com/repos/'+repo+'/commits/'+branch));sha=commit['sha'];result.update(revision=sha,fork=meta['fork'],parent=meta.get('parent',{}).get('full_name'))
    tree=json.loads(get('https://api.github.com/repos/'+repo+'/git/trees/'+sha+'?recursive=1'));(base/'tree.json').write_text(json.dumps(tree,indent=2))
    paths=[x['path'] for x in tree.get('tree',[]) if x['type']=='blob'];result['tree_truncated']=tree.get('truncated',False);result['candidate_files']=[p for p in paths if re.search(r'qasper|scifact|dataset|loader|convert|evaluat|metric',p,re.I) and not re.search(r'\.(png|jpg|pdf|parquet|jsonl|csv|tsv|zip|gz|lock)$',p,re.I)][:300]
   else:
    result.update(revision=r.get('revision'),candidate_files=r.get('files',[]))
  except Exception as e:result['error']=str(e)
  (base/'pinned.json').write_text(json.dumps(result,indent=2));return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:out=list(pool.map(job,idx))
 (ROOT/'pins.json').write_text(json.dumps(out,indent=2));print(json.dumps([{k:r.get(k) for k in ['index','canonical','revision','fork','parent','error']} for r in out],indent=2))
if __name__=='__main__':main()
