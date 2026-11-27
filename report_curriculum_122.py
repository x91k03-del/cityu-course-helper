"""Report the hard-122 curriculum repair and its remaining evidence limits."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
import project_runtime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'reports/curriculum-122-fix';OUT=ROOT/'output/pdf/curriculum-122-fix'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    runs={n:json.loads((DATA/f'{n}_rollout.json').read_text()) for n in ('F','N','M')}
    old={n:json.loads((ROOT/'reports/ef-late-ge-examples'/f'{n}_rollout.json').read_text()) for n in runs}
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Title2',fontName='Helvetica-Bold',fontSize=20,leading=24,spaceAfter=12,textColor=colors.HexColor('#173d50')))
    styles.add(ParagraphStyle(name='Body2',fontSize=9.2,leading=12.6,spaceAfter=9))
    styles.add(ParagraphStyle(name='Cell2',fontSize=8.1,leading=10.8))
    styles.add(ParagraphStyle(name='Small2',fontSize=8,leading=10.5,spaceAfter=7))
    def p(t,style='Body2'):return Paragraph(t,styles[style])
    def table(rows,widths):
        t=Table([[p(escape(str(c)),'Cell2') for c in row] for row in rows],colWidths=widths,repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#deedf2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f8')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        return t
    story=[p('Repaired CM paths: 122 credits','Title2'),
        p('<b>Why the old schedule stopped early.</b> The timetable-only pool and assumed Year-1 passes contained at most 100 usable unique credits in these examples. '
          'The planner exhausted those subjects and displayed a penalised, incomplete diagnostic path. The no-finance example consequently had 12 credits in Year 3A and zero in Year 4B. '
          'That path was never a completed degree recommendation. Its diagnostic labelling and recommendation output have now been tightened.'),
        p('<b>What changed.</b> With the user\'s approval, the degree planner can now include CM-document courses whose class details are missing, marking them <b>pending timetable</b>. '
          'A Markov insertion search allocates missing requirements and electives across the whole remaining path. It returns a curriculum recommendation only when the terminal audit passes '
          '<b>at least 122 unique credits, four GE passes covering Areas 1-3, the core, elective mathematics, project, free-elective and selected-stream requirements</b>.'),
        p('The planner retains the saved class selections, reserves project work in both final-year terms, and catches up missing compulsory requirements. '
          'It checks the published prerequisites and A/B pattern for the new advanced mathematics courses. A semester may still have fewer than five courses. '
          'The 18-credit / six-course maximum and overload penalties remain: 0.25 times excess credits squared above 15 in Years 1-3 and above 12 in Year 4.'),
        p('<b>Results: projected credits after passing all planned courses.</b> Each example keeps the identical assumed 15+15 Year-1 history.'),
        table([['Term','F: finance prepared','N: no finance at entry','M: enriched mathematics']]+
          [[label]+[15]*3 for label in ['Year 1A (history)','Year 1B (history)']]+
          [[f"Year {runs['F']['semesters'][i]['year']}{runs['F']['semesters'][i]['semester']}"]+[runs[n]['semesters'][i]['credits'] for n in runs] for i in range(6)]+
          [['Planned total']+[runs[n]['audit']['earned_credits'] for n in runs]], [105,130,138,138]),Spacer(1,10),
        p('<b>All three pass the encoded curriculum audit:</b> 122 total credits; four distributional GE courses spanning all three areas; '
          '30 elective mathematics credits; 45 core credits; six project credits; at least 20 free-elective credits; and the requested stream. '
          'Only one stream receives the stream reward. No course earns credit twice.'),
        p('<b>Credit repair:</b> 100 - 3 (one surplus GE) + 1 (GE1601) + 6 (year-long MA4530) + 18 (six additional maths electives) = <b>122</b>. '
          'The two missing zero-credit soft-skills requirements are planned catch-up tasks, not invented historical passes.'),
        p('<b>Evidence boundary.</b> The 122-credit curriculum is complete; the registration timetable is pending. '
          'Twenty-five future credits have no saved class details. They have null meetings and CRNs and are never treated as free time. '
          'Future offerings, clashes involving those courses, eligibility, and late soft-skills completion require confirmation. '
          'The A/B pattern repeats as a simulation assumption. This update changes the planner and model prompt; neural weights were not retrained. '
          '101 checks passed, plus an end-to-end rerun of the new degree-planning entrypoint.','Small2'),PageBreak(),
        p('Worked example: no finance at entry','Title2')]
    n=runs['N'];old_n=old['N'];rows=[['Term','Courses (* = pending timetable)','Credits','Cumulative']]
    running=0
    for term in (1,2):
        history=[r for r in n['historical_transcript'] if r['term']==term];running+=sum(r['credits'] for r in history)
        rows.append([f"Y1 {'A' if term==1 else 'B'}",', '.join(r['id'] for r in history)+' (assumed passes)',15,running])
    for s in n['semesters']:
        text=', '.join(o['course_code']+('*' if o['evidence_status']=='pending_timetable' else '')+(' (0 cr.)' if not o['credits'] else '') for o in s['course_evidence'])
        rows.append([f"Y{s['year']} {s['semester']}",text,s['credits'],s['earned_credits_after']])
    story+=[table(rows,[43,355,48,65]),Spacer(1,10),
        p('<b>The empty final semester is repaired.</b> Year 3A changes from 12 to 15 credits by adding MA4528. '
          'Year 4B changes from zero to 18 credits, with MA4529, the second project allocation, MA4537, MA4546, MA4550 and MA4551. '
          'Year 3B remains 13 credits and Year 4A remains 12; those lighter terms are allowed because the whole curriculum now reaches 122.'),
        p('<b>Why this student has a heavier Year 4B.</b> The fixed saved path finishes MA2510 in Year 3B, then MA3518 and MA3521 in Year 4A. '
          'Those passes unlock the new advanced courses. They cannot be used as prior passes within the same semester. '
          'The Year 4B overload penalty is 0.25 x (18 - 12)<super>2</super> = 9 reward units; it remains in the objective.'),
        table([['Completed earlier','Later course(s) in this example'],
          ['MA3511 in Year 2B','MA4528 in Year 3A'],
          ['MA2510 in Year 3B','MA4537 and MA4546 in Year 4B'],
          ['MA3521 in Year 4A','MA4529 in Year 4B'],
          ['MA2503 and MA3518','MA4550 in Year 4B'],
          ['MA2503 and MA3526','MA4551 in Year 4B']],[205,306]),Spacer(1,9),
        p('<b>Pending advanced-course sources:</b> '+', '.join(f'<link href="https://www.cityu.edu.hk/catalogue/ug/current/course/{code}.htm" color="#245c79">{code}</link>' for code in ['MA4528','MA4529','MA4537','MA4546','MA4550','MA4551','MA4530'])+'. '
          'Rules were checked against indexed official catalogue text on 24 November 2026; direct page retrieval returned an access restriction. '
          'Courses explicitly not offered in the current catalogue year were excluded from this completion pool. '
          'Course membership and credit amounts also follow the supplied CM course-list and 2025 normative-path documents.','Small2'),
        p('MA4530:A and MA4530:B denote one six-credit year-long project allocated three credits per term for planning. '
          'Neither is an invented separate registerable course. Starred CSCI1001/CSCI1002 require confirmation of catch-up arrangements. '
          'Saved non-starred weekly meetings retain their original component-linkage and teaching-week assumptions. '
          'Earlier reports and original profiles were preserved.','Small2')]
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#60717a'));canvas.drawString(42,21,'CM curriculum repair | 24 November 2026 | pending timetable evidence remains explicit');canvas.drawRightString(553,21,str(doc.page))
    path=OUT/'CM_122_Credit_Path_Fix.pdf'
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=32,bottomMargin=35).build(story,onFirstPage=footer,onLaterPages=footer)
    print(path)

if __name__=='__main__':main()
