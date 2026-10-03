
"""Render a conventional official-style TeX source and a checked PDF reading copy."""
from pathlib import Path
import json,re,html,textwrap
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def latex(s):
    s=str(s)
    if "https://" in s or "http://" in s:
        parts=re.split(r"(https?://[^\s<>]+)",s)
        return "".join((r"\url{"+p.rstrip(".,;")+"}"+p[len(p.rstrip(".,;")):]) if p.startswith(("https://","http://")) else latex(p) for p in parts)
    s=str(s).replace("−","-").replace("→"," to ").replace("≥",">=").replace("≤","<=")
    escapes={"\\":r"\textbackslash{}","&":r"\&","%":r"\%","$":r"\$","#":r"\#","_":r"\_","{":r"\{","}":r"\}","~":r"\textasciitilde{}","^":r"\textasciicircum{}"}
    unicode_map={"–":"--","—":"---","‘":"`","’":"'","“":"``","”":"''","ü":r'\"{u}',"é":r"\'{e}","à":r"\`{a}","α":r"$\alpha$"}
    result="".join(escapes.get(c,unicode_map.get(c,c)) for c in s)
    result=result.replace(r"E\_1,...,E\_m",r"$E_1,\ldots,E_m$")
    result=re.sub(r"\bd([CA])\b",lambda m:"$d_{"+m[1]+"}$",result)
    result=re.sub(r"\bE([1-9])\b",lambda m:"$E_{"+m[1]+"}$",result)
    return result

def prose_html(s):
    s=html.escape(s).replace("E_1,...,E_m","E<sub>1</sub>,...,E<sub>m</sub>")
    s=re.sub(r"\bd([CA])\b",lambda m:"d<sub>"+m[1]+"</sub>",s)
    return re.sub(r"\bE([1-9])\b",lambda m:"E<sub>"+m[1]+"</sub>",s)
def citations(text,refs,tex=False):
    def sub(m):
        keys=m[1].split(";")
        assert all(k in refs for k in keys)
        if tex:return r"\citep{"+",".join(keys)+"}"
        return "("+ "; ".join(refs[k]["label"]+", "+str(refs[k].get("year_label",refs[k]["year"])) for k in keys)+")"
    if tex:
        pieces=re.split(r"(\[\[.*?\]\])",text)
        return "".join(sub(re.match(r"\[\[(.*?)\]\]",p)) if p.startswith("[[") else latex(p) for p in pieces)
    return re.sub(r"\[\[(.*?)\]\]",sub,text)
def refs_text(v):
    return ", ".join(v["authors"])+f". ({v.get('year_label',v['year'])}). "+v["title"]+(" " if v["title"].endswith(("?","!",".")) else ". ")+v["venue"]+((", "+v["volume"]) if v.get("volume") else "")+((", pp. "+v["pages"]) if v.get("pages") else "")+"."
def pgf_figure(name):
    curves=pd.read_csv(ROOT/"tables/curve_estimates.csv");p=pd.read_csv(ROOT/"tables/primary.csv");topo=pd.read_csv(ROOT/"tables/topology.csv")
    raw=[json.loads(s) for s in (ROOT/"outputs/main_v1/rankings.jsonl").read_text().splitlines()]
    pieces=[]
    colors={"hit":"brown","complete":"blue","union_complete":"violet"}
    for d in ["qasper","scifact"]:
        opts=[r"width=.99\linewidth",r"height=5.1cm",r"tick label style={font=\scriptsize}",r"label style={font=\small}",r"title style={font=\small}",f"title={('QASPER' if d=='qasper' else 'SciFact')}",r"grid=major",r"grid style={gray!15}",r"legend style={font=\scriptsize,draw=none}",r"legend pos=south east"]
        commands=[]
        if name=="figure1_completion_curves":
            opts += ["xmin=1","xmax=20","ymin=0","ymax=100","xtick={1,5,10,20}","xlabel={Retrieved units}","ylabel={Items (percent)}"]
            for m,style,mark,lab in [("hit","dotted","triangle*","H"),("complete","solid","*","C"),("union_complete","dashed","square*","A")]:
                t=curves.query("dataset==@d and method=='bm25' and metric==@m").sort_values("k")
                coords=" ".join(f"({r.k},{100*r['mean']:.8f})" for _,r in t.iterrows())
                commands += [r"\addplot["+colors[m]+f",thick,{style},mark={mark}"+"] coordinates {"+coords+"};",r"\addlegendentry{"+lab+"}"]
        elif name=="figure2_paired_gaps":
            opts += ["xmin=0","xmax=40","ymin=-.5","ymax=2.5","ytick={0,1,2}","yticklabels={BM25,TF-IDF,MiniLM}","xlabel={Difference (points)}"]
            for m,offset,color,mark,lab in [("hit_without_complete",-.12,"brown","triangle*","H-C"),("complete_without_union",.12,"blue","*","C-A")]:
                coords=[]
                for j,method in enumerate(["bm25","tfidf","dense"]):
                    t=p.query("dataset==@d and method==@method and metric==@m").iloc[0]
                    coords.append(f"({100*t['mean']:.8f},{j+offset}) += ({100*(t.hi-t['mean']):.8f},0) -= ({100*(t['mean']-t.lo):.8f},0)")
                commands += [r"\addplot+[only marks,"+color+",mark="+mark+r",error bars/.cd,x dir=both,x explicit] coordinates {"+" ".join(coords)+"};",r"\addlegendentry{"+lab+"}"]
        elif name=="figure4_annotation_structure":
            opts += ["xmin=-.6","xmax=1.6","ymin=0","ymax=100","xtick={0,1}","xticklabels={One,Multiple}","xlabel={Minimal observed sets}","ylabel={C-A (points)}"]
            coords=[]
            for j,level in enumerate(["1","2+"]):
                t=topo.query("dataset==@d and method=='bm25' and stratum=='n_minimal_sets' and metric=='complete_without_union' and level==@level").iloc[0]
                coords.append(f"({j},{100*t['mean']:.8f}) += (0,{100*(t.hi-t['mean']):.8f}) -= (0,{100*(t['mean']-t.lo):.8f})")
            commands += [r"\addplot+[ybar,bar width=15pt,blue,fill=blue!40,error bars/.cd,y dir=both,y explicit] coordinates {"+" ".join(coords)+"};"]
        else:
            opts += ["xmin=0","ymin=0","ymax=100","xlabel={Extra units (log1p scale)}","ylabel={Cumulative percent}","xtick={0,.693147,1.791759,2.397895,3.044522,3.931826,4.615121}","xticklabels={0,1,5,10,20,50,100}"]
            for method,color,style in [("bm25","blue","solid"),("tfidf","brown","dashed"),("dense","violet","dotted")]:
                vals=np.sort([r["costs"]["depth_penalty"] for r in raw if r["dataset"]==d and r["method"]==method])
                uniq,cnt=np.unique(vals,return_counts=True);cumul=100*np.cumsum(cnt)/len(vals)
                coords=" ".join(f"({np.log1p(x):.8f},{y:.8f})" for x,y in zip(uniq,cumul))
                commands += [r"\addplot[const plot,thick,"+color+","+style+"] coordinates {"+coords+"};",r"\addlegendentry{"+("MiniLM" if method=="dense" else method.upper())+"}"]
        pieces.append(r"\begin{minipage}{.48\textwidth}\centering\begin{tikzpicture}\begin{axis}["+",".join(opts)+"]\n"+"\n".join(commands)+r"\end{axis}\end{tikzpicture}\end{minipage}")
    return r"\hbox to\textwidth{"+r"\hfill".join(pieces)+"}"
def render_tex(doc, output_path=None):
    # Load the separate, unmodified official IRRJ style.
    s=r"""\documentclass[twoside,a4paper,11pt]{article}
\usepackage[preprint]{irrj2e}
\usepackage[T1]{fontenc}
\usepackage{amsmath,booktabs,pgfplots,array,longtable,xurl}
\emergencystretch=1em
\setcounter{topnumber}{4}\setcounter{totalnumber}{5}
\renewcommand{\topfraction}{.95}\renewcommand{\textfraction}{.05}\renewcommand{\floatpagefraction}{.8}
\pgfplotsset{compat=1.18}
\ShortHeadings{Evidence Sets and Retrieval Evaluation}{Lin}
\firstpageno{1}
\begin{document}
"""
    s+=r"\title{"+latex(doc["title"])+"}\n"+r"\author{\name "+latex(doc["author"])+r" \\ \addr "+latex(doc["affiliation"])+"}\n"+r"\maketitle"+"\n"
    s+=r"\begin{abstract}"+latex(doc["abstract"])+r"\end{abstract}"+"\n"+r"\begin{keywords}"+latex(doc["keywords"])+r"\end{keywords}"+"\n"
    for kind,value in doc["blocks"]:
        if kind in ["section","subsection"]:s+="\n\\"+kind+"{"+latex(value)+"}\n"
        elif kind=="appendix":s+=r"\appendix\setcounter{figure}{0}\renewcommand{\thefigure}{A\arabic{figure}}"+"\n"+r"\section{"+latex(value)+"}\n"
        elif kind=="p":s+=citations(value,doc["references"],True)+"\n\n"
        elif kind=="eq":s+="\\[\n"+value+"\n\\]\n"
        elif kind=="table":
            t=doc["tables"][value];widths=t["widths"]
            # Native layout is 432pt; compensate for tabular padding.
            cols="".join(r">{\raggedright\arraybackslash}p{"+f"{max(25,w-12):.1f}"+"pt}" for w in widths)
            s+=r"\begin{table}[!htbp]\centering\small\caption{"+latex(t["caption"])+"}\n"+r"\begin{tabular}{"+cols+"}\n"+r"\toprule"+"\n"
            s+=" & ".join(r"\textbf{"+latex(x)+"}" for x in t["headers"])+r" \\"+"\n"+r"\midrule"+"\n"
            s+="\n".join(" & ".join("{"+latex(x)+"}" for x in row)+r" \\" for row in t["rows"])+"\n"+r"\bottomrule\end{tabular}\end{table}"+"\n"
        elif kind=="figure":
            # Native self-contained plots show exact means; intervals remain in adjacent tables.
            caption=doc["captions"][value]
            if value=="figure1_completion_curves":caption=caption.replace("Shaded bands are 95% cluster-bootstrap intervals. ","Point estimates are shown; interval data and shaded-band exports accompany the paper. ")
            if value=="figure4_annotation_structure":caption=caption.replace("; labels give item counts",". Stratum counts are given in the text")
            if value=="figure3_extra_depth":caption=caption.replace("linear near zero and logarithmic outside that region","transformed by log(1+extra units)")
            s+=r"\begin{figure}[!htbp]\centering"+"\n"+pgf_figure(value)+"\n"+r"\caption{"+latex(caption)+"}\n"+r"\end{figure}"+"\n"
    s+=r"\clearpage\begin{thebibliography}{99}"+"\n"
    for key,v in sorted(doc["references"].items(),key=lambda kv:(("Qwen" if kv[0]=="qwen" else kv[1]["authors"][0].split()[-1]),str(kv[1].get("year_label",kv[1]["year"])),kv[1]["title"])):
        label=latex(v["label"]).replace(" et al.",r" et~al.")
        s+=r"\bibitem["+label+"("+str(v.get("year_label",v["year"]))+")]{"+key+"}\n"+latex(refs_text(v))+" "+r"\url{"+v["url"]+"}.\n\n"
    s+=r"\end{thebibliography}\end{document}"+"\n"
    (output_path or ROOT/"paper/manuscript.tex").write_text(s)
def render_pdf(doc):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import matplotlib,matplotlib.pyplot as plt
    from matplotlib.font_manager import findfont
    for name,family,weight in [("Research","DejaVu Serif","normal"),("ResearchBold","DejaVu Serif","bold"),("ResearchSans","DejaVu Sans","normal")]:
        pdfmetrics.registerFont(TTFont(name,findfont(matplotlib.font_manager.FontProperties(family=family,weight=weight))))
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyResearch",fontName="Research",fontSize=10.2,leading=14.0,spaceAfter=7,alignment=TA_JUSTIFY,allowWidows=0,allowOrphans=0))
    styles.add(ParagraphStyle(name="AbstractResearch",parent=styles["BodyResearch"],fontSize=9.4,leading=12.7,leftIndent=15,rightIndent=15))
    styles.add(ParagraphStyle(name="TitleResearch",fontName="ResearchBold",fontSize=17,leading=21,spaceAfter=17,alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="SectionResearch",fontName="ResearchBold",fontSize=12,leading=15,spaceBefore=15,spaceAfter=7,keepWithNext=True))
    styles.add(ParagraphStyle(name="SubResearch",fontName="ResearchBold",fontSize=10.5,leading=14,spaceBefore=10,spaceAfter=5,keepWithNext=True))
    styles.add(ParagraphStyle(name="CaptionResearch",fontName="Research",fontSize=8.6,leading=11.3,spaceBefore=6,spaceAfter=10))
    styles.add(ParagraphStyle(name="CellResearch",fontName="ResearchSans",fontSize=8.1,leading=10.3))
    styles.add(ParagraphStyle(name="RefResearch",fontName="Research",fontSize=8.7,leading=11.7,spaceAfter=7))
    story=[Paragraph(html.escape(doc["title"]),styles["TitleResearch"]),Paragraph(doc["author"]+"<br/>"+doc["affiliation"],styles["AbstractResearch"]),Spacer(1,13),
           Paragraph("<b>Abstract</b>",styles["SubResearch"]),Paragraph(html.escape(doc["abstract"]),styles["AbstractResearch"]),
           Paragraph("<b>Keywords:</b> "+html.escape(doc["keywords"]),styles["CaptionResearch"])]
    section=0;sub=0;tn=0;fn=0;appendix=False;eqn=0
    tmp=ROOT/"paper/qa";tmp.mkdir(exist_ok=True)
    for kind,value in doc["blocks"]:
        if kind=="section":
            section+=1;sub=0;story.append(Paragraph(f"{section}. "+html.escape(value),styles["SectionResearch"]))
        elif kind=="subsection":
            sub+=1;story.append(Paragraph(f"{section}.{sub} "+html.escape(value),styles["SubResearch"]))
        elif kind=="appendix":
            appendix=True;fn=0;story.extend([Spacer(1,12),Paragraph("Appendix A. "+html.escape(value),styles["SectionResearch"])])
        elif kind=="p":story.append(Paragraph(prose_html(citations(value,doc["references"])),styles["BodyResearch"]))
        elif kind=="eq":
            eqn+=1;path=tmp/f"equation_{eqn}.png"
            fig=plt.figure(figsize=(10,.7));fig.text(.5,.5,"$"+value.replace(r"\ne",r"\neq")+"$",ha="center",va="center",fontsize=15)
            fig.savefig(path,dpi=200,bbox_inches="tight",pad_inches=.08);plt.close(fig)
            from PIL import Image as PILImage
            iw,ih=PILImage.open(path).size;story.extend([Spacer(1,4),Image(str(path),width=432,height=432*ih/iw),Spacer(1,8)])
        elif kind=="table":
            tn+=1;t=doc["tables"][value]
            values=[[Paragraph(prose_html(str(x)),styles["CellResearch"]) for x in row] for row in [t["headers"]]+t["rows"]]
            # Scale table widths to six-inch manuscript column.
            widths=np.array(t["widths"])*432/sum(t["widths"])
            table=Table(values,colWidths=widths.tolist(),repeatRows=1,hAlign="CENTER")
            table.setStyle(TableStyle([("LINEABOVE",(0,0),(-1,0),.7,colors.black),("LINEBELOW",(0,0),(-1,0),.5,colors.black),
                ("LINEBELOW",(0,-1),(-1,-1),.7,colors.black),("VALIGN",(0,0),(-1,-1),"TOP"),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
            story.extend([Spacer(1,7),KeepTogether([Paragraph(f"Table {tn}. "+prose_html(t["caption"]),styles["CaptionResearch"]),table]),Spacer(1,9)])
        elif kind=="figure":
            fn+=1;path=ROOT/"figures"/(value+".png")
            revised=ROOT/"revisions/v2/figures"/(value+".png")
            if revised.exists():path=revised
            from PIL import Image as PILImage
            iw,ih=PILImage.open(path).size
            story.append(KeepTogether([Image(str(path),width=450,height=450*ih/iw),Paragraph("Figure "+("A" if appendix else "")+str(fn)+". "+html.escape(doc["captions"][value]),styles["CaptionResearch"])]))
    story.extend([PageBreak(),Paragraph("References",styles["SectionResearch"])])
    for key,v in sorted(doc["references"].items(),key=lambda kv:(("Qwen" if kv[0]=="qwen" else kv[1]["authors"][0].split()[-1]),str(kv[1].get("year_label",kv[1]["year"])),kv[1]["title"])):
        link=v.get("doi") or ("arXiv" if "arxiv.org" in v["url"] else "Source")
        story.append(Paragraph(html.escape(refs_text(v))+f' <link href="{html.escape(v["url"],quote=True)}" color="#21618C">'+html.escape(link)+"</link>.",styles["RefResearch"]))
    def footer(canvas,docu):
        canvas.saveState();canvas.setFont("ResearchSans",7)
        canvas.drawCentredString(297.64,24,f"Reading copy · official IRRJ LaTeX source accompanies this document · {docu.page}")
        canvas.setFont("ResearchSans",8);canvas.drawCentredString(297.64,811,"Evidence Sets and Retrieval Evaluation")
        canvas.restoreState()
    document=SimpleDocTemplate(str(ROOT/"paper/manuscript_reading_copy.pdf"),pagesize=(595.28,841.89),rightMargin=81.64,leftMargin=81.64,
            topMargin=52,bottomMargin=47,title=doc["title"],author=doc["author"])
    document.build(story,onFirstPage=footer,onLaterPages=footer)
    # Whole-document prose companion for easy inspection/search.
    md=["# "+doc["title"],doc["author"]+" — "+doc["affiliation"],"## Abstract",doc["abstract"]]
    for kind,value in doc["blocks"]:
        if kind in ["section","appendix"]:md.append("## "+value)
        elif kind=="subsection":md.append("### "+value)
        elif kind=="p":md.append(citations(value,doc["references"]))
        elif kind=="eq":md.append("$$\n"+value+"\n$$")
        elif kind=="table":
            t=doc["tables"][value];md += ["*"+t["caption"]+"*", "\n".join(["| "+" | ".join(t["headers"])+" |","| "+" | ".join(["---"]*len(t["headers"]))+" |"]+["| "+" | ".join(row)+" |" for row in t["rows"]])]
        elif kind=="figure":md+=["![Figure](../"+("revisions/v2/figures/" if (ROOT/"revisions/v2/figures"/(value+".png")).exists() else "figures/")+value+".png)",doc["captions"][value]]
    md+=["## References"]+[refs_text(v)+" ["+(v.get("doi") or "Source")+"]("+v["url"]+")" for v in doc["references"].values()]
    (ROOT/"paper/manuscript.md").write_text("\n\n".join(md)+"\n")
def main():
    doc=json.loads((ROOT/"paper/article.json").read_text())
    render_tex(doc);render_pdf(doc)
    print("Wrote conventional IRRJ LaTeX, PDF reading copy, and Markdown companion.")
if __name__=="__main__":main()
