from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def main():
 rows=[json.loads(x) for x in (ROOT/'outputs/main_v1/rankings.jsonl').read_text().splitlines()]
 fig,axes=plt.subplots(1,2,figsize=(9,3.25),constrained_layout=True)
 for ax,d in zip(axes,['qasper','scifact']):
  for method,color,style,label in [('bm25','#2166ac','-','BM25'),('tfidf','#a6611a','--','TF-IDF'),('dense','#762a83',':','MiniLM')]:
   v=np.array([r['costs']['depth_penalty'] for r in rows if r['dataset']==d and r['method']==method]);u,n=np.unique(v,return_counts=True)
   ax.step(np.log1p(u),100*np.cumsum(n)/len(v),where='post',color=color,linestyle=style,label=label)
  ticks=[v for v in [0,1,5,10,20,50,100,200] if v<=max(r['costs']['depth_penalty'] for r in rows if r['dataset']==d)]
  ax.set_xticks(np.log1p(ticks),[str(v) for v in ticks]);ax.set_ylim(0,101);ax.set_title(('QASPER' if d=='qasper' else 'SciFact'));ax.set_xlabel('Additional ranked units (log1p scale)');ax.set_ylabel('Cumulative percent');ax.grid(alpha=.2);ax.legend(frameon=False,loc='lower right')
 out=ROOT/'revisions/v2/figures';out.mkdir(exist_ok=True)
 fig.savefig(out/'figure3_extra_depth.png',dpi=250);fig.savefig(out/'figure3_extra_depth.svg');plt.close(fig)
if __name__=='__main__':main()
