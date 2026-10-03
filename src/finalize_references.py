"""Regenerate the current bibliography from verified metadata, preserving historical ledgers."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def main():
 refs=json.loads((R/'literature/verified_references.json').read_text());entries=[]
 for k,v in refs.items():
  typ='article' if k in ['ev2r','bm25','saracevic'] else 'misc' if k in ['conjunctive','relational','qwen','complement2026','rinse2026'] else 'inproceedings'
  fields={'author':('{Qwen Team}' if k=='qwen' else ' and '.join(v['authors'])),'title':'{'+v['title']+'}','year':v['year'],('journal' if typ=='article' else 'booktitle' if typ=='inproceedings' else 'howpublished'):v['venue'],'url':v['url']}
  for f in ['doi','pages','volume']:
   if v.get(f):fields[f]=v[f]
  entries.append('@'+typ+'{'+k+',\n'+',\n'.join('  '+f+' = {'+str(val).replace('–','--')+'}' for f,val in fields.items())+'\n}')
 (R/'paper/references.bib').write_text('\n\n'.join(entries)+'\n');print('Current bibliography:',len(refs),'records')
if __name__=='__main__':main()
