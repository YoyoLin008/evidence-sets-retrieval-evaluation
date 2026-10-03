"""Publication figures: source tables plus frozen rank-level cost distributions."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.labelsize":10,"axes.titlesize":11,
 "axes.spines.top":False,"axes.spines.right":False,"axes.edgecolor":"#444444","text.color":"#222222",
 "axes.labelcolor":"#222222","xtick.color":"#333333","ytick.color":"#333333","savefig.facecolor":"white",
 "pdf.fonttype":42,"ps.fonttype":42})
COLORS={"hit":"#B15A00","complete":"#21618C","union_complete":"#725A86"}
LABELS={"hit":"Any annotated hit (H)","complete":"One full annotated set (C)","union_complete":"All annotated units (A)"}
def save(fig,name):
    fig.savefig(ROOT/"figures"/(name+".pdf"),bbox_inches="tight")
    fig.savefig(ROOT/"figures"/(name+".png"),dpi=220,bbox_inches="tight")
    plt.close(fig)
def main():
    curves=pd.read_csv(ROOT/"tables/curve_estimates.csv");p=pd.read_csv(ROOT/"tables/primary.csv")
    fig,axs=plt.subplots(1,2,figsize=(10,3.7),sharey=True)
    for ax,d,n in zip(axs,["qasper","scifact"],[875,209]):
        for metric,marker,style in zip(COLORS,["^","o","s"],[":","-","--"]):
            t=curves.query("dataset==@d and method=='bm25' and metric==@metric").sort_values("k")
            ax.plot(t.k,t["mean"],marker=marker,linestyle=style,color=COLORS[metric],label=LABELS[metric],linewidth=1.7)
            ax.fill_between(t.k,t.lo,t.hi,color=COLORS[metric],alpha=.08)
        ax.set(title=f"{('QASPER' if d=='qasper' else 'SciFact')} · n = {n}",xlabel="Retrieved units (k)",xticks=[1,3,5,10,20],ylim=(-.015,1.025))
        ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(axis="y",alpha=.18)
    axs[0].set_ylabel("Fraction of eligible items")
    handles,labels=axs[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",bbox_to_anchor=(.5,-.09),ncol=3,frameon=False,fontsize=9)
    fig.tight_layout();save(fig,"figure1_completion_curves")
    fig,axs=plt.subplots(1,2,figsize=(10,3.6),sharex=True,sharey=True)
    for ax,d,k in zip(axs,["qasper","scifact"],[5,3]):
        for offset,metric,color,marker,label in [(-.13,"hit_without_complete","#B15A00","^","H − C: hit without a full set"),(.13,"complete_without_union","#21618C","o","C − A: full set without union")]:
            t=p.query("dataset==@d and metric==@metric").set_index("method").loc[["bm25","tfidf","dense"]]
            y=np.arange(3)+offset
            ax.errorbar(t["mean"]*100,y,xerr=np.vstack([(t["mean"]-t.lo)*100,(t.hi-t["mean"])*100]),
                        fmt=marker,color=color,capsize=3,label=label)
        ax.set(title=f"{('QASPER' if d=='qasper' else 'SciFact')} · k = {k}",yticks=np.arange(3),yticklabels=["BM25","TF–IDF","MiniLM"],xlabel="Difference (percentage points)",xlim=(-1,40))
        ax.grid(axis="x",alpha=.18);ax.set_ylim(2.5,-.5)
    handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,loc="lower center",bbox_to_anchor=(.5,-.07),ncol=2,frameon=False,fontsize=9)
    fig.tight_layout();save(fig,"figure2_paired_gaps")
    raw=[json.loads(x) for x in (ROOT/"outputs/main_v1/rankings.jsonl").read_text().splitlines()]
    fig,axs=plt.subplots(1,2,figsize=(10,3.6),sharey=True)
    for ax,d in zip(axs,["qasper","scifact"]):
        for method,color,style in [("bm25","#21618C","-"),("tfidf","#B15A00","--"),("dense","#725A86",":")]:
            vals=np.sort([r["costs"]["depth_penalty"] for r in raw if r["dataset"]==d and r["method"]==method])
            ax.step(vals,np.arange(1,len(vals)+1)/len(vals),where="post",label=method.upper() if method!="dense" else "MiniLM",color=color,linestyle=style)
        ax.set(title=('QASPER' if d=='qasper' else 'SciFact'),xlabel="Extra ranked units: union minus one set",ylim=(0,1.01),xscale="symlog")
        ax.set_xlim(left=0)
        ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(axis="y",alpha=.18)
    axs[0].set_ylabel("Cumulative fraction of items");axs[1].legend(frameon=False,loc="lower right")
    fig.tight_layout();save(fig,"figure3_extra_depth")
    t=pd.read_csv(ROOT/"tables/topology.csv")
    fig,axs=plt.subplots(1,2,figsize=(10,3.6),sharey=True)
    for ax,d in zip(axs,["qasper","scifact"]):
        data=t.query("dataset==@d and method=='bm25' and stratum=='n_minimal_sets' and metric=='complete_without_union'")
        for j,label in enumerate(["1","2+"]):
            row=data[data.level.astype(str)==label].iloc[0]
            ax.bar(j,row["mean"]*100,width=.5,color="#21618C" if j else "#BBCBD7")
            ax.errorbar(j,row["mean"]*100,yerr=[[100*(row["mean"]-row.lo)],[100*(row.hi-row["mean"])]],color="#222222",capsize=4)
            ax.text(j,row.hi*100+3,f"n = {int(row.n)}",ha="center",fontsize=9)
        ax.set(title=('QASPER' if d=='qasper' else 'SciFact'),xticks=[0,1],xticklabels=["One minimal set","Multiple minimal sets"],ylim=(0,105))
        ax.grid(axis="y",alpha=.18)
    axs[0].set_ylabel("C − A (percentage points)");fig.tight_layout();save(fig,"figure4_annotation_structure")
    print("Exported four figures as vector PDF and PNG.")
if __name__=="__main__":main()
