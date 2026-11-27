"""Readable examples, with assumed historical inputs separated from evidence."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
import project_runtime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'reports/ef-late-ge-examples'
OUT=ROOT/'output/pdf/ef-late-ge-examples'

def main():
    r=json.loads((DATA/'examples.json').read_text());cases=r['examples'];OUT.mkdir(parents=True,exist_ok=True)
    st=getSampleStyleSheet()
    st.add(ParagraphStyle(name='Title2',fontName='Helvetica-Bold',fontSize=21,leading=25,textColor=colors.HexColor('#173d50'),spaceAfter=12))
    st.add(ParagraphStyle(name='Body2',fontSize=9,leading=12.5,spaceAfter=8))
    st.add(ParagraphStyle(name='Cell2',fontSize=8,leading=10.5))
    st.add(ParagraphStyle(name='Small2',fontSize=8,leading=10.5,spaceAfter=7))
    def p(text,style='Body2'):return Paragraph(text,st[style])
    def table(rows,widths):
        t=Table([[p(escape(str(c)),'Cell2') for c in row] for row in rows],colWidths=widths,repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#deedf2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f8')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        return t
    story=[p('EF3320 and GE: three CM examples','Title2'),
        p('<b>Reward update.</b> CM EF3320 has no missing-prerequisite penalty under the requested planning waiver. '
          'It receives an additional <b>4 reward units in Year 4</b>, interpreted as after Year 3; Years 1-3 receive no timing bonus. '
          'Earlier selection remains allowed. The separate surcharge for no finance study remains 1.5 times the background weight. '
          'Passed GE2260 (Introduction to Finance) or GE1202 removes that surcharge.'),
        p('<b>GE correction.</b> These examples include the saved GE Semester A meetings. A new area earns +5, and a GE pass earns +2 while fewer than four GE passes are complete. '
          'Previously covered areas retain only 10% of base course reward. At most one distributional GE is selected each semester; language GE do not count towards that cap.'),
        p('<b>Inputs: assumed completed Year 1, exactly 15 + 15 credits.</b> Each listed course carries three credits. '
          'These are fictional pass histories, not verified past timetables. In particular, the Semester B GE passes are assumed historical input; no Semester B GE offering is inferred.'),
        table([['Historical term','Common completed courses','Distributional GE'],
          ['Year 1 A','MA1300, CS1302, PHY1201, GE1401','One profile-specific GE (below)'],
          ['Year 1 B','MA1301, CHEM1200, GE1501, GE2401','One profile-specific GE (below)']],[65,295,151]),Spacer(1,9),
        table([['Profile','Y1 A GE / area','Y1 B GE / area','Desired stream'],
          ['F: finance prepared','GE2260 / Area 2','GE1105 / Area 1','Financial Mathematics'],
          ['N: no finance preparation','GE1305 / Area 3','GE1113 / Area 1','Financial Mathematics'],
          ['M: maths / critical thinking','GE2134 / Area 1','GE1305 / Area 3','Enriched Mathematics']],[132,116,116,147]),Spacer(1,10),
        p('<b>Source-only control for a fresh entrant.</b> A separate test starts with no passed courses and imposes exactly 15 credits in both Year 1 terms. '
          'Semester A succeeds. After those passes, the compatible Semester B pool contains only 12 unique credits, so a 15-credit Semester B is infeasible.'),
        table([['Test','Selected source-backed courses','Credits / result'],
          ['Y1 A, exactly 15',', '.join(r['source_only_control']['Y1_A_exact15']['course_codes']),'15; feasible'],
          ['Y1 B, exactly 15','No legal 15-credit selection','Infeasible'],
          ['Y1 B, flexible',', '.join(r['source_only_control']['Y1_B_flexible_after_A']['course_codes']),'12; feasible']],[100,311,100]),Spacer(1,10),
        p('All future schedules below are hypothetical bundles over saved meetings. MA/CS eligibility filters remain active; GE eligibility, section linkage and teaching weeks require confirmation. '
          'The user-authorised A/B snapshot repetition is a simulation assumption. Reward policy and prompts were updated; this run did not change the neural checkpoint.','Small2'),
        PageBreak(),p('Future paths and graduation checks','Title2')]
    rows=[['Term','F: finance prepared','N: no finance at entry','M: enriched maths']]
    for i in range(6):
        terms=[c['result']['diagnostic_semesters'][i] for c in cases]
        rows.append([f"Y{terms[0]['year']} {terms[0]['semester']}"]+[
            (', '.join(s['selected_courses']) or 'No course')+f" ({s['credits']} cr.)" for s in terms])
    story+=[table(rows,[43,156,156,156]),Spacer(1,10)]
    summary=[['Profile','EF3320 selected','GE passes / areas 1,2,3','Total / target']]
    for c in cases:
        s=c['result'];a=s['audit'];ef=next((f"Y{t['year']} {t['semester']}" for t in s['diagnostic_semesters'] if 'EF3320' in t['selected_courses']),'Not selected')
        summary.append([c['id'],ef,f"{a['distribution_GE_count']} passes / "+','.join(str(a['GE_area_counts'][str(x)]) for x in (1,2,3)),f"{a['earned_credits']} / 122"])
    story+=[table(summary,[53,118,205,135]),Spacer(1,9),
        p('<b>Effect of the EF3320 update.</b> With F\'s identical completed transcript, the zero-bonus baseline selects EF3320 in Year 2B; '
          'the updated reward selects Year 4B. The +4 timing increment is verified with all other inputs held constant. The complete paths differ as the planner reallocates courses. '
          'N first studies GE2260 in Year 2A, gaining finance preparation before EF3320 in Year 2B. A later-year bonus is a preference, not a rule that forces every student to delay.'),
        p('<b>GE now passes for every example.</b> All have five distributional GE passes, at least one in each of Areas 1-3, and no semester contains more than one. '
          'The fifth GE is allowed and helps the unmet total-credit target. GE language passes are counted separately.'),
        p('<b>The degree still fails the final audit.</b> Each path reaches 100 credits, including the assumed 30-credit history; the shortfall is 22. '
          'The terminal penalty is therefore 22,000,000 reward units and none is labelled a graduating plan. '
          'The combined saved pool and assumed history have a 100-credit upper bound in these demonstrations. '
          'Missing compatible mandatory coverage includes GE1601, CSCI1001, CSCI1002 and MA4530; elective maths reaches only 12 of the required 20 credits. '
          'A reward change cannot supply missing timetable evidence.'),
        p('<b>Reproducibility.</b> Future search uses the MA/CS PDF pool and six declared GE candidates: GE1105, GE1113, GE1202, GE1305, GE2134, GE2260. '
          'A bounded Markov search compares capacity, credit-progress and late-EF candidates by actual penalised reward; global optimality is not claimed. '
          'Overload remains 0.25 times excess credits squared: above 15 in Years 1-3, above 12 in Year 4. The first-year 15+15 inputs do not incur overload.','Small2'),
        p('Evidence: saved EF3320_SEMB PDF (CA1, CRN 11425, Semester B); GE Semester A browser capture and GE area PDFs. '
          'Full profiles, source hashes, selected sections and audits are retained alongside the examples. Earlier reports were preserved.','Small2')]
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#60717a'))
        canvas.drawString(42,22,'CM planning examples | 24 November 2026 | hypothetical simulation')
        canvas.drawRightString(553,22,str(doc.page))
    path=OUT/'EF3320_GE_15plus15_Examples.pdf'
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=32,bottomMargin=35).build(story,onFirstPage=footer,onLaterPages=footer)
    print(path)

if __name__=='__main__':main()
