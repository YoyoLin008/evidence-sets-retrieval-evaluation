"""Render the submission cover letter from author-confirmed declarations."""
from pathlib import Path
import html,json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from matplotlib.font_manager import findfont,FontProperties
from pypdf import PdfReader
import pypdfium2
ROOT=Path(__file__).resolve().parents[1]
def main():
    for name,weight in [("Cover","normal"),("CoverBold","bold")]:
        pdfmetrics.registerFont(TTFont(name,findfont(FontProperties(family="DejaVu Serif",weight=weight))))
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverBody",fontName="Cover",fontSize=9.5,leading=12.4,spaceAfter=9))
    styles.add(ParagraphStyle(name="CoverTitle",fontName="CoverBold",fontSize=14,leading=17,spaceAfter=16))
    paragraphs=(ROOT/"paper/cover_letter.md").read_text().strip().split("\n\n")
    story=[]
    for i,p in enumerate(paragraphs):
        text=html.escape(p.lstrip("# ") if i==0 else p).replace("  \n","<br/>").replace("\n"," ")
        story.append(Paragraph(text,styles["CoverTitle" if i==0 else "CoverBody"]))
    path=ROOT/"paper/cover_letter.pdf"
    doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=61,leftMargin=61,topMargin=48,bottomMargin=45,
                         title="IRRJ cover letter",author="Yunya Lin")
    def foot(canvas,docu):
        canvas.setFont("Cover",7)
        canvas.drawCentredString(297.64,23,f"Yunya Lin · {docu.page}")
    doc.build(story,onFirstPage=foot,onLaterPages=foot)
    pdf=PdfReader(path);texts=[p.extract_text() for p in pdf.pages]
    assert len(texts)==1 and "Pending author confirmations" not in texts[0]
    assert "■" not in texts[0] and "\uFFFD" not in texts[0]
    (ROOT/"paper/qa").mkdir(exist_ok=True)
    rendered=pypdfium2.PdfDocument(str(path))
    rendered[0].render(scale=1.5).to_pil().save(ROOT/"paper/qa/cover_letter.png")
    print(json.dumps({"cover_letter_pages":len(texts),"text_checked":True,"visual_review":"pending"}))
if __name__=="__main__":main()
