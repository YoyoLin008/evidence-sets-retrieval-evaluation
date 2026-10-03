"""Build a deterministic submission ZIP and layered manifests after document QA.

Run after staging intended public files. The ZIP contains submission artifacts and
their provenance; the Git tag separately archives the complete reproducibility
tree. No generated file hashes itself.
"""
from pathlib import Path
import hashlib,json,subprocess,zipfile
R=Path(__file__).resolve().parents[1]
VERSION='v1.1.0'
ASSETS=['paper/manuscript_official_style.pdf','paper/supplement_official_style.pdf',
        'paper/cover_letter.pdf','paper/manuscript_reading_copy.pdf']
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    qa=json.loads((R/'revisions/v3/qa/document_checks.json').read_text())
    assert len(qa)==4 and all(x['visual_inspection']=='passed' for x in qa),'Visual inspection of all four current PDFs is required'
    for x in qa:assert sha(R/x['file'])==x['sha256'],('Document changed after QA',x['file'])
    out=R/'release_artifacts';out.mkdir(exist_ok=True)
    entries=ASSETS+['paper/manuscript.tex','paper/supplement.tex','paper/references.bib','paper/irrj2e.sty',
                    'paper/cover_letter.md','revisions/v3/revision_memo.md','revisions/v3/qa/validation_report.md',
                    'revisions/v3/submission_checklist.md','revisions/v3/author_actions.md','docs/revision_v1.1_reproduction.md',
                    'revisions/v3/qa/document_checks.json','revisions/v3/build_provenance.json']
    zpath=out/('submission-'+VERSION+'.zip')
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel in sorted(entries):
            info=zipfile.ZipInfo('submission-'+VERSION+'/'+rel,date_time=(2026,10,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,(R/rel).read_bytes())
    asset_files=ASSETS+[zpath.relative_to(R).as_posix(),'revisions/v3/revision_memo.md','revisions/v3/qa/validation_report.md']
    manifest={'version':VERSION,'source_provenance':'revisions/v3/build_provenance.json','scope':'Final PDF/ZIP/report release assets; source-tag commit is recorded after commit without embedding a self hash.',
              'files':{rel:{'sha256':sha(R/rel),'bytes':(R/rel).stat().st_size} for rel in asset_files}}
    (out/'asset_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(v['sha256']+'  '+Path(k).name+'\n' for k,v in manifest['files'].items()))
    # Use the explicit Git index allowlist, plus the freshly generated release assets.
    files=set(subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'))-{''}
    files.update([zpath.relative_to(R).as_posix(),'release_artifacts/asset_manifest.json','release_artifacts/SHA256SUMS'])
    files.discard('PACKAGE_MANIFEST.json')
    for rel in files:
        assert (R/rel).is_file() and not (R/rel).is_symlink(),('Missing or forbidden symlink',rel)
        assert not any(x in Path(rel).parts for x in ['.git','.venv','.venv-revision','source_cache','runtime','cache','private']),rel
    package={'version':VERSION,'scope':'Public tag content excluding this manifest itself; verify before modifying any file during reproduction.',
             'files':{rel:{'sha256':sha(R/rel),'bytes':(R/rel).stat().st_size} for rel in sorted(files)}}
    (R/'PACKAGE_MANIFEST.json').write_text(json.dumps(package,indent=2)+'\n')
    print(json.dumps({'submission_zip':str(zpath.relative_to(R)),'package_files':len(files),'asset_count':len(asset_files)},indent=2))
if __name__=='__main__':main()
