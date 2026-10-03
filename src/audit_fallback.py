from pathlib import Path
import json,subprocess,concurrent.futures,re
ROOT=Path(__file__).resolve().parents[1]/'revisions/v2/audit'
def main():
 rs=json.loads((ROOT/'pins.json').read_text())
 def job(r):
  if not r.get('error') or not r['canonical'].startswith('github.com/'):return r
  base=ROOT/r['directory'];repo=base/'git_snapshot'
  try:
   if not repo.exists():subprocess.run(['git','clone','--depth','1','--filter=blob:none','--no-checkout','https://'+r['canonical']+'.git',str(repo)],check=True,capture_output=True,timeout=180)
   sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();paths=subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'],cwd=repo,text=True).splitlines()
   r.update(revision=sha,candidate_files=[p for p in paths if re.search('qasper|scifact|dataset|loader|convert|eval|metric|download',p,re.I) and not re.search(r'\.(pdf|png|jpg|csv|jsonl|tsv|zip|gz|parquet)$',p,re.I)][:300],fallback='partial Git clone; original API rate-limit error retained')
   (base/'git_paths.json').write_text(json.dumps(paths,indent=2))
  except Exception as e:r['fallback_error']=str(e)
  (base/'pinned.json').write_text(json.dumps(r,indent=2));return r
 with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:rs=list(pool.map(job,rs))
 (ROOT/'pins.json').write_text(json.dumps(rs,indent=2))
 for r in rs:
  if r.get('error'):print(r['index'],r['canonical'],r.get('revision'),r.get('fallback_error',''),r.get('candidate_files'))
if __name__=='__main__':main()
