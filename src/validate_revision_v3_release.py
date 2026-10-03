"""Validate current manuscript provenance, protected records and public export scope."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess
from revision_v3_manuscript import Revision
R=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 revision=Revision(R,require_qwen=True)
 docs={stem:json.loads((R/f'paper/{stem}.json').read_text()) for stem in ['article','supplement']}
 numbers=json.loads((R/'analysis/manuscript_values.json').read_text())
 protected=json.loads((R/'revisions/v3/protected_declarations.json').read_text())
 freeze=json.loads((R/'revisions/v2/baseline_manifest.json').read_text())
 historical_checked=[]; unavailable=[]
 for name,expected in freeze['protected'].items():
  candidate=R/name
  if name.startswith('outputs/main_v1/') and Path(name).name!='instances.jsonl':
   public=R/'reference_outputs/main_v1'/Path(name).name
   assert public.is_file() and sha(public)==expected,('Public frozen copy mismatch',name)
  if candidate.exists():
   assert sha(candidate)==expected,name;historical_checked.append(name)
  elif name=='outputs/main_v1/instances.jsonl':unavailable.append(name)
  elif name.startswith('outputs/main_v1/'):
   historical_checked.append(name+' verified via reference_outputs')
  else:raise AssertionError(('Missing protected file',name))
 # Frozen public code/input manifests are available even in a source-free clone.
 main_freeze=json.loads((R/'logs/main_freeze.json').read_text())
 for name,expected in main_freeze['frozen_files'].items():assert sha(R/name)==expected,name
 assert sha(R/'paper/irrj2e.sty')=='5952d152ce89b9446587f8e4182da420f8228a8a85248a692b83d52962fd2910'
 for stem,doc in docs.items():
  text=json.dumps(doc,ensure_ascii=False)
  for key in ['author','affiliation']:assert doc[key]==protected[key],(stem,key)
  assert 'INTERNAL LAYOUT DRAFT' not in text and 'pending' not in doc['abstract'].lower()
  for key in numbers:assert '{'+key+'}' not in text,(stem,key)
  paragraphs=[v for k,v in doc['blocks'] if k=='p']
  for key in ['ai_disclosure','funding']:assert protected[key] in paragraphs,(stem,key)
  assert '10.5281/zenodo.23122620' not in text,(stem,'old DOI presented in current document')
  for name in [v for k,v in doc['blocks'] if k=='table']:
   t=doc['tables'][name]
   assert len(t['headers'])==len(t['widths']) and all(len(r)==len(t['headers']) for r in t['rows']),name
 assert docs['article']['abstract']==revision.abstract(numbers)
 assert docs['supplement']['abstract']==revision.supplement_abstract()
 cover=(R/'paper/cover_letter.md').read_text()
 assert protected['ai_disclosure'] in cover
 refs=json.loads((R/'literature/verified_references.json').read_text())
 bib=(R/'paper/references.bib').read_text()
 for key in refs:assert '{'+key+',' in bib,key
 # Inspect the Git allowlist, not acquired data/virtual environments.
 paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=R).decode().split('\0')
 findings=[];count=0
 patterns=[r'github_pat_[A-Za-z0-9_]{10,}',r'gh[pousr]_[A-Za-z0-9]{20,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'AKIA[A-Z0-9]{16}']
 for name in sorted(set(paths)-{''}):
  f=R/name
  assert not f.is_symlink(),('Symlink in export',name)
  assert not any(p in Path(name).parts for p in ['source_cache','private','.venv','.venv-revision','runtime','cache']),name
  if not f.is_file() or f.suffix in ['.pdf','.png','.jpg','.zip','.npy']:continue
  text=f.read_text(errors='replace');count+=1
  for pattern in patterns:
   if re.search(pattern,text):findings.append({'file':name,'kind':'credential-pattern'})
  # A redaction regex in its implementation is not a disclosed local path.
  if re.search(r'/Users/[A-Za-z0-9_.-]+/',text):findings.append({'file':name,'kind':'personal-absolute-path'})
 assert not findings,findings
 report={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,
  'scope':'Current complete scientific model, current result manifests, original freeze, unchanged style, protected declarations and intended public tree; PDF visual/remote publication checks are separate.',
  'original_freeze_files_checked':len(main_freeze['frozen_files']),
  'historical_protected_files_checked':len(historical_checked),'unavailable_source_text_files':unavailable,
  'bibliography_records':len(refs),'manuscript_abstract_generated_from_current_results':True,
  'protected_AI_and_funding_exact':True,'official_style_unchanged':True,'all_display_tables_rectangular':True,
  'public_text_files_scanned':count,'credential_or_personal_path_findings':findings,
  'complete_ranking_count':revision.validation['ranking_rows'],'six_budget_scoring_points':revision.validation['scoring_points'],
  'limits':['No independent human semantic review','No cross-platform full-inference replication','No IRRJ submission performed']}
 out=R/'revisions/v3/qa/release_content_validation.json';out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
