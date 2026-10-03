"""Check and render every final PDF; visual status must be set only after actual inspection."""
from pathlib import Path
import json,hashlib,re
from pypdf import PdfReader
import pypdfium2
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'revisions/v3/qa/rendered'
def main():
 O.mkdir(parents=True,exist_ok=True)
 reports=[]
 for stem in ['manuscript_official_style','supplement_official_style','manuscript_reading_copy','cover_letter']:
  path=R/'paper'/(stem+'.pdf')
  if stem=='cover_letter' and not path.exists():continue
  reader=PdfReader(path);texts=[p.extract_text() for p in reader.pages]
  assert all(len(t)>70 for t in texts);assert not any('■' in t or '\ufffd' in t for t in texts)
  text=re.sub(r'\s+',' ',re.sub(r'(?<=\w)-\n(?=\w)','','\n'.join(texts)));(O/(stem+'.txt')).write_text(text)
  for token in ['producing agent','same-agent','agent self-review','autonomous execution','revision-v2','approval pending']:
   assert token not in text.lower(),(stem,token)
  assert 'project selection' not in text.lower()
  if 'manuscript' in stem:
   for x in ['875','209','17.8','27.8','8.2']:assert x in texts[0],(stem,x)
   for x in ['Alt','Li','Minimal Evidence Group','User-Centric Evidence Ranking']:assert x in text,(stem,x)
  pdf=pypdfium2.PdfDocument(str(path));pages=[]
  for i in range(len(pdf)):
   im=pdf[i].render(scale=1.5).to_pil().convert('RGB');p=O/f'{stem}_{i+1:02d}.png';im.save(p);pages.append(p)
  for start in range(0,len(pages),2):
   canvas=Image.new('RGB',(1660,1220),'#d7d7d7');d=ImageDraw.Draw(canvas)
   for j,p in enumerate(pages[start:start+2]):
    im=Image.open(p);im.thumbnail((815,1170));x=j*830+(830-im.width)//2;canvas.paste(im,(x,30));d.text((j*830+12,8),f'{stem} page {start+j+1}',fill='black')
   canvas.save(O/f'{stem}_sheet_{start//2+1:02d}.png')
  reports.append({'file':str(path.relative_to(R)),'pages':len(reader.pages),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'text_checks':'passed','all_pages_rendered':True,'visual_inspection':'pending'})
 (O.parent/'document_checks.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports,indent=2))
if __name__=='__main__':main()
