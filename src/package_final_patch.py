"""Package accepted v1.1.1 artifacts without overwriting historical releases.

Stage intended public files first. Run after the correction/build commit and
patch build_provenance.json exist. The ZIP is smaller than the complete tag.
"""
from pathlib import Path
import hashlib,json,subprocess,zipfile
from revision_v3_package import ASSETS,sha
R=Path(__file__).resolve().parents[1]
V='v1.1.1'
PATCH='revisions/patch_v1.1.1'

def main():
 qa=json.loads((R/PATCH/'qa/document_checks.json').read_text())
 assert len(qa)==4 and all(x['visual_inspection']=='passed' for x in qa)
 for x in qa:assert sha(R/x['file'])==x['sha256'],('Changed after QA',x['file'])
 assert json.loads((R/PATCH/'dependency_preflight.json').read_text())['passed']
 assert json.loads((R/PATCH/'scientific_integrity.json').read_text())['all_protected_scientific_files_match']
 out=R/'release_artifacts'/V;out.mkdir(exist_ok=True)
 entries=ASSETS+['paper/manuscript.tex','paper/supplement.tex','paper/references.bib','paper/irrj2e.sty','paper/cover_letter.md',
 'docs/revision_v1.1_reproduction.md','revisions/v3/encoder/README.md','src/encoder_dependency_preflight.py']
 entries += [PATCH+'/'+name for name in ['patch_memo.md','validation_report.md','submission_checklist.md','installation.json','dependency_preflight.json','baseline.json','scientific_integrity.json','qa/document_checks.json','qa/text_comparison.json','build_provenance.json']]
 zpath=out/('submission-'+V+'.zip')
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for rel in sorted(entries):
   info=zipfile.ZipInfo('submission-'+V+'/'+rel,date_time=(2026,10,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,(R/rel).read_bytes())
 with zipfile.ZipFile(zpath) as z:
  assert len(z.namelist())==len(entries) and z.testzip() is None
  for rel in entries:assert z.read('submission-'+V+'/'+rel)==(R/rel).read_bytes(),rel
 checks={'version':V,'zip':zpath.relative_to(R).as_posix(),'zip_bytes':zpath.stat().st_size,'zip_sha256':sha(zpath),
 'internal_file_count':len(entries),'all_internal_files_match_standalone':True,
 'entries':{rel:{'sha256':sha(R/rel),'bytes':(R/rel).stat().st_size} for rel in sorted(entries)},
 'manifest_layers':'ZIP contains no self checksum; this record and asset manifest are outside it. PACKAGE_MANIFEST excludes itself.'}
 (R/PATCH/'package_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
 assets=ASSETS+[zpath.relative_to(R).as_posix(),PATCH+'/patch_memo.md',PATCH+'/validation_report.md']
 manifest={'version':V,'source_provenance':PATCH+'/build_provenance.json','scope':'Frozen patch PDF/ZIP/report assets; no self checksum.',
 'files':{rel:{'sha256':sha(R/rel),'bytes':(R/rel).stat().st_size} for rel in assets}}
 (out/'asset_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (out/'SHA256SUMS').write_text(''.join(v['sha256']+'  '+Path(k).name+'\n' for k,v in manifest['files'].items()))
 files=set(subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'))-{''}
 files.update([zpath.relative_to(R).as_posix(),'release_artifacts/'+V+'/asset_manifest.json','release_artifacts/'+V+'/SHA256SUMS',PATCH+'/package_checks.json'])
 files.discard('PACKAGE_MANIFEST.json')
 for rel in files:
  assert (R/rel).is_file() and not (R/rel).is_symlink(),rel
  assert not any(x.startswith('.venv') or x in ['.git','source_cache','runtime','cache','private','rendered'] for x in Path(rel).parts),rel
 package={'version':V,'scope':'Public content excluding this manifest itself; validate before reproduction modifies files.',
 'files':{rel:{'sha256':sha(R/rel),'bytes':(R/rel).stat().st_size} for rel in sorted(files)}}
 (R/'PACKAGE_MANIFEST.json').write_text(json.dumps(package,indent=2)+'\n')
 print(json.dumps({'zip':str(zpath.relative_to(R)),'internal_files':len(entries),'internal_bytes_verified':True,'public_manifest_files':len(files),'release_assets':len(assets)+2},indent=2))
if __name__=='__main__':main()
