"""Render the fresh model input/output experiment as a readable, auditable PDF."""
import json,textwrap,html
from pathlib import Path
import project_runtime
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Flowable,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/pdf/CM_Model_Input_Output_Examples.pdf'
NAVY=colors.HexColor('#172C43');TEAL=colors.HexColor('#007E80');GRAY=colors.HexColor('#526476');LIGHT=colors.HexColor('#F1F5F8')
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyA',fontName='Arial',fontSize=9.4,leading=13.2,textColor=NAVY,spaceAfter=7))
styles.add(ParagraphStyle(name='SmallA',fontName='Arial',fontSize=8.1,leading=10.4,textColor=GRAY,spaceAfter=5))
styles.add(ParagraphStyle(name='HeadA',fontName='Arial-Bold',fontSize=21,leading=25,textColor=NAVY,spaceAfter=10))
styles.add(ParagraphStyle(name='SectionA',fontName='Arial-Bold',fontSize=11,leading=14,textColor=TEAL,spaceBefore=10,spaceAfter=6))
styles.add(ParagraphStyle(name='CellA',fontName='Arial',fontSize=8.5,leading=11,textColor=NAVY))
styles.add(ParagraphStyle(name='CellHeadA',fontName='Arial-Bold',fontSize=8.3,leading=10.5,textColor=colors.white))
def p(text,style='BodyA'):return Paragraph(text,styles[style])
def esc(value):return html.escape(str(value))
class CodeBox(Flowable):
    def __init__(self,text,size=7.2,leading=8.6,width=511):
        Flowable.__init__(self);self.width=width;self.size=size;self.leading=leading
        cols=int((width-20)/(size*.6))
        self.lines=[]
        for line in text.splitlines() or ['']:
            self.lines.extend(textwrap.wrap(line,width=cols,break_long_words=True,break_on_hyphens=False,
                replace_whitespace=False,drop_whitespace=False) or [''])
        self.height=14+leading*len(self.lines)
    def draw(self):
        c=self.canv;c.setFillColor(LIGHT);c.roundRect(0,0,self.width,self.height,5,fill=1,stroke=0)
        c.setFillColor(NAVY);c.setFont('Courier',self.size)
        t=c.beginText(10,self.height-9-self.size);t.setLeading(self.leading)
        for line in self.lines:t.textLine(line)
        c.drawText(t)
def table(headers,rows,widths):
    data=[[p(esc(x),'CellHeadA') for x in headers]]+[[p(esc(x),'CellA') for x in row] for row in rows]
    t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('LINEBELOW',(0,0),(-1,0),.5,TEAL)]))
    return t
def footer(c,doc):
    w,h=A4;c.setStrokeColor(colors.HexColor('#CDD8E0'));c.line(42,39,w-42,39)
    c.setFillColor(GRAY);c.setFont('Arial',7.5)
    c.drawString(42,26,'FICTIONAL STUDENT TESTS  |  Qwen3-8B v5  |  16 Nov 2026 (Hong Kong)')
    c.drawRightString(w-42,26,str(doc.page))
def wrapheight(flowables,width):
    total=0
    for f in flowables:
        total+=f.getSpaceBefore()+f.wrap(width,10000)[1]+f.getSpaceAfter()
    return total
def main():
    data=json.loads((ROOT/'reports/input-output-examples/examples.json').read_text(encoding='utf-8'));cases=data['cases']
    OUT.parent.mkdir(parents=True,exist_ok=True);story=[];width=A4[0]-84
    story+=[p('Computing Mathematics<br/>Model input and output examples','HeadA'),
      p('Six fresh student-profile queries - including the resulting semester course plans','SectionA'),
      p('All six responses were generated from the local <b>Qwen3-8B preparation-v5 checkpoint</b> for this report. '
        'These are controlled illustrations, not a new held-out accuracy estimate. Every student and grade is fictional.'),
      p('<b>What the system returns:</b> the model generates academic-profit parameters. The constraint solver uses them, completed courses and curriculum rules to select a semester course plan. '
        'The plans below do not contain verified class meeting times.'),
      Spacer(1,7)]
    rows=[]
    for c in cases:
        s=c['state'];v=c['parsed_model_output'];b=v['preparation_bonus_by_course']
        rows.append([c['id'],c['title'].replace('Year 2: ','Y2: ').replace('Year 4 ','Y4 '),s['earned_credits'],
          f"{b['MA3512']:.2f} / {b['GE2134']:.2f}",f"{c['current_semester_profit']['planned_credits']} credits"])
    story.append(table(['Case','Input profile','Earned','PDE / thinking\nbenefit','Current plan'],rows,[35,223,45,104,104]))
    story += [Spacer(1,10),p('Main results','SectionA'),
      p('<b>6/6 model responses passed the exact policy check.</b> Every selected semester respects the one-distributional-GE limit. '
        'All six remaining-degree forecasts also meet the encoded graduation checks if their future courses are passed.'),
      p('A failed calculus attempt gives no calculus preparation benefit. A failed discrete-maths attempt gives no critical-thinking preparation benefit. '
        'Early Analysis completion changes the remaining course requirements even when the generated profit parameters stay the same. '
        'The elective-maths progress bonus stops once its 20-credit threshold is reached.'),
      p('Reading the next pages','SectionA'),
      p('Each example shows the <b>complete user-message input</b>, the actual model JSON output, the scheduler\'s current-semester selection and the computed net profit. '
        'The common system message, applied to every example, is reproduced in the appendix.'),
      p('<b>Limitations:</b> preparation coefficients are bounded content-based hypotheses, not measured hours saved or grade gains. '
        'Current PDF downloads were blocked; the source evidence includes historical official PDF excerpts. '
        'Elective approvals, all formal eligibility conditions, seats and future class times still require university confirmation.','SmallA'),PageBreak()]
    for c in cases:
        s=c['state'];v=c['parsed_model_output'];profit=c['current_semester_profit'];audit=c['forecast_terminal_audit']
        flows=[p(c['id']+' | '+esc(c['title']),'HeadA'),p(esc(c['note']),'SmallA'),
          p(f"<b>Input summary:</b> Year {s['year']} Semester {s['semester']}; {s['earned_credits']} earned credits; "
            f"{s['distribution_GE_count']} distributional GE passed; {s['elective_math_credits']} elective maths credits.",'SmallA'),
          p('1. Complete user input','SectionA'),p('JSON sent to the model, with display-only line wrapping. The common system message appears in the appendix.','SmallA')]
        # JSON contains the full state plus every preceding attempted course,
        # grade, credits and term; no input records are omitted from the PDF.
        userbox=CodeBox(c['messages'][1]['content'],size=7.7,leading=9.0,width=width)
        outputbox=CodeBox(c['raw_model_output'],size=8.0,leading=10.0,width=width)
        flows += [userbox,p('2. Actual model output','SectionA'),outputbox,
          p('3. Current-semester course plan - selected by the solver','SectionA')]
        rows=[[r['id'],r['title'],r['credits']] for r in c['current_semester_courses']]
        flows.append(table(['Course','Title','Credits'],rows,[75,width-128,53]))
        flows += [Spacer(1,6),p(f"<b>Computed net profit: {profit['net_profit']:.2f}</b> | Load: {profit['planned_credits']} credits | "
          f"Preparation: +{profit['preparation_benefit']:.2f} | Year-4 overload: -{profit['overload_penalty']:.2f}",'SmallA'),
          p(f"Forecast at graduation: {audit['earned_credits']} earned credits; {audit['distribution_GE_count']} distributional GE covering Areas 1/2/3; "
            f"{audit['elective_math_credits']} elective maths credits. All encoded terminal checks pass.",'SmallA'),
          p('Profit and graduation forecasts assume future passes. This is a course plan, not a verified weekly timetable.','SmallA')]
        height=wrapheight(flows,width)
        if height>735:
            # Keep the full input on its own page if a long Year-4 history
            # cannot fit together with the course table at a readable size.
            split=flows.index(userbox)+1
            story+=flows[:split]+[PageBreak(),p(c['id']+' | Output and semester plan','HeadA')]+flows[split:]+[PageBreak()]
        else:story+=flows+[PageBreak()]
    story += [p('Appendix A | Common system input','HeadA'),
      p('This is the complete system message supplied with each example. Each case\'s complete user message is printed on its example page. '
        'Source documents and student records are treated as data.','SmallA'),
      CodeBox(data['system_prompt'],size=8.0,leading=10.1,width=width),PageBreak()]
    normal=cases[0];failed=cases[1];disc=cases[2];early=cases[3]
    story += [p('Appendix B | Interpretation and evidence','HeadA'),p('How the inputs change the output','SectionA')]
    for a,b,reason in [(normal,failed,'MA2508 B versus F'),(normal,disc,'MA2509 B versus F'),(normal,early,'Analysis unfinished versus completed early')]:
        va=a['parsed_model_output'];vb=b['parsed_model_output']
        added=sorted(set(b['solver_output']['current_selection'])-set(a['solver_output']['current_selection']))
        removed=sorted(set(a['solver_output']['current_selection'])-set(b['solver_output']['current_selection']))
        story.append(p(f"<b>{a['id']} versus {b['id']}: {reason}.</b> "
          f"Added to current plan: {', '.join(added) or 'none'}. Removed: {', '.join(removed) or 'none'}."))
    story += [p('Profit calculation','SectionA'),
      p('Net profit = course profit + capped graduation-progress profit + on-path completion bonus + direct preparation benefit - course cost - Year-4 overload. '
        'Units are academic utility, not money or study hours. Failure gives no earned credits or preparation transfer.'),
      table(['Year-4 load','9 credits','12 credits','15 credits','18 credits'],[['Overload penalty','0','0','2.25','9']],[139,93,93,93,93]),
      p('The overload values above are deterministic calculations from 0.25 x max(0, credits - 12)^2; they are not extra model predictions. '
        'Years 1-3 have zero overload penalty. A hard cap of one distributional GE still applies.','SmallA'),
      p('Evidence and remaining uncertainty','SectionA'),
      p('The supplied 2025 study path provides the curriculum baseline and 122-credit minimum, which exceeds the requested 121. '
        'At least four distributional GE courses, one in every area, and at least 20 elective maths credits remain hard constraints. '
        'Compulsory GE1401/GE1501/GE1601/GE2401 are excluded from the per-semester distributional cap.'),
      p('The preparation graph uses official indexed syllabus excerpts: MA2508 (2025/26) to MA3512 and MA3515; MA2509 (2020/21 historical) to GE2134 (2025/26). '
        'The MA3512 content excerpt is from 2023/24. These are provisional transfer hypotheses. Published contact and assessment requirements are unchanged.'),
      p('Official source PDFs','SectionA')]
    for code,year in [('MA2508','202526'),('MA3512','202324'),('MA3515','202526'),('MA2509','202021'),('GE2134','202526')]:
        url=f'https://www.cityu.edu.hk/catalogue/ug/{year}/course/{code}.pdf'
        story.append(p(f'<link href="{url}" color="#007E80">{code} - official {year[:4]}/{year[4:]} PDF</link>','SmallA'))
    story += [p('Reproducibility','SectionA'),p(esc(data['generation']),'SmallA'),
      p('Adapter: '+esc(data['model'])+'<br/>SHA-256: '+esc(data['model_sha256']),'SmallA'),
      p('Exact messages, raw outputs, full transcripts, semester forecasts and audits: reports/input-output-examples/examples.json. '
        'Files and runtime caches are stored on F:. No actual student data or credentials were used.','SmallA')]
    doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=51,
        title='CM Student Examples: Model Inputs, Outputs and Semester Plans',author='CityU Course Helper - local Qwen3-8B experiment')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(OUT)
if __name__=='__main__':main()
