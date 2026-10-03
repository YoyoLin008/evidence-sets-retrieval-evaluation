"""Export revised display tables separately; never overwrite frozen v1 tables."""
from pathlib import Path
import json
from render_manuscript import latex
ROOT=Path(__file__).resolve().parents[1]
def main():
    doc=json.loads((ROOT/'paper/article.json').read_text())
    out=ROOT/'revisions/final/tables/display';out.mkdir(parents=True,exist_ok=True)
    names=[value for kind,value in doc['blocks'] if kind=='table']
    for number,name in enumerate(names,1):
        t=doc['tables'][name]
        md=[f"# Table {number}. {t['caption']}",'','| '+' | '.join(t['headers'])+' |','| '+' | '.join(['---']*len(t['headers']))+' |']
        md+=['| '+' | '.join(map(str,row))+' |' for row in t['rows']]
        (out/f'table{number}_{name}.md').write_text('\n'.join(md)+'\n')
        widths=[max(25,w-12) for w in t['widths']]
        cols=''.join(r'>{\raggedright\arraybackslash}p{'+str(w)+'pt}' for w in widths)
        s=r'\begin{table}[htbp]\centering\small\caption{'+latex(t['caption'])+'}\n'
        s+=r'\begin{tabular}{'+cols+'}\n'+r'\toprule'+'\n'
        row=lambda xs:' & '.join('{'+latex(str(x))+'}' for x in xs)+r' \\'
        s+=row(t['headers'])+'\n'+r'\midrule'+'\n'
        s+='\n'.join(row(xs) for xs in t['rows'])+'\n'+r'\bottomrule\end{tabular}\end{table}'+'\n'
        (out/f'table{number}_{name}.tex').write_text(s)
    print(f'Exported {len(names)} revised tables under revisions/final/tables/display; frozen tables untouched.')
if __name__=='__main__':main()
