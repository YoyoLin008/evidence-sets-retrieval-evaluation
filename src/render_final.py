"""Regenerate final manuscript/supplement and export with an existing TeX installation."""
from pathlib import Path
import json,subprocess,shutil,sys,tempfile
R=Path(__file__).resolve().parents[1]
def main():
 for script in ['finalize_references.py','build_manuscript.py','export_tables.py','render_manuscript.py','render_cover_letter.py']:
  if script=='render_cover_letter.py' and not (R/'paper/cover_letter.md').exists():continue
  subprocess.run([sys.executable,str(R/'src'/script)],cwd=R,check=True)
 from render_manuscript import render_tex
 render_tex(json.loads((R/'paper/supplement.json').read_text()),R/'paper/supplement.tex')
 tex=shutil.which('pdflatex')
 if not tex and Path('/Library/TeX/texbin/pdflatex').exists():tex='/Library/TeX/texbin/pdflatex'
 if not tex:raise SystemExit('Sources saved. Export requires an existing TeX runtime; native compilation is available separately.')
 out=R/'paper/build-final';out.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='irrj_clean_tex_') as tmp:
  build=Path(tmp)
  shutil.copy2(R/'paper/irrj2e.sty',build/'irrj2e.sty')
  for stem in ['manuscript','supplement']:
   shutil.copy2(R/'paper'/(stem+'.tex'),build/(stem+'.tex'))
   for passno in [1,2]:
    p=subprocess.run([tex,'-interaction=nonstopmode','-halt-on-error',stem+'.tex'],cwd=build,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/f'{stem}-pass{passno}.txt').write_text(p.stdout);assert p.returncode==0,p.stdout[-3000:]
   shutil.copy2(build/(stem+'.log'),out/(stem+'.log'))
   shutil.copy2(build/(stem+'.pdf'),R/'paper'/(stem+'_official_style.pdf'))
 print('Exported final official-style main and supplementary PDFs.')
if __name__=='__main__':main()
