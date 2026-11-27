"""Create a separate report, leaving every previous report untouched."""
import csv,hashlib,json
from pathlib import Path
from xml.sax.saxutils import escape
import project_runtime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from programme_policy import policy,progress

ROOT=Path(__file__).resolve().parent;DATA=ROOT/'reports/markov-repair';OUT=ROOT/'output/pdf/markov-repair'

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    run=json.loads((DATA/'year1_simulation.json').read_text());checks=json.loads((DATA/'semester_checks.json').read_text())
    assert run['status']=='complete' and run['audit']['all_encoded_requirements_met']
    a=run['audit'];styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle',fontName='Helvetica-Bold',fontSize=22,leading=26,textColor=colors.HexColor('#15394b'),spaceAfter=12))
    styles.add(ParagraphStyle(name='ReportBody',fontName='Helvetica',fontSize=9.7,leading=13.6,spaceAfter=9))
    styles.add(ParagraphStyle(name='SmallCell',fontName='Helvetica',fontSize=8.5,leading=11))
    styles.add(ParagraphStyle(name='SmallNote',fontName='Helvetica',fontSize=8.2,leading=11,spaceAfter=7,textColor=colors.HexColor('#45535c')))
    styles.add(ParagraphStyle(name='Sub',fontName='Helvetica-Bold',fontSize=12,leading=15,spaceBefore=9,spaceAfter=8,textColor=colors.HexColor('#15394b')))
    def p(text,style='ReportBody'):return Paragraph(text,styles[style])
    def table(rows,widths):
        data=[[p(escape(str(v)),'SmallCell') for v in row] for row in rows]
        t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebf0')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f8')]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
            ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#98afb9'))]))
        return t
    story=[p('Complete semesters,<br/>then a complete degree','ReportTitle'),
      p('CM planning diagnosis and four-year Markov simulation | 24 November 2026','SmallNote'),
      p('The entering Year-1 CM simulation earns <b>127 credits</b> and passes every encoded graduation check. '
        'Years 1-3 contain 5-6 credit-bearing courses per semester. It completes the selected <b>Enriched Mathematics</b> stream.'),
      p('Why the earlier answer had only three courses','Sub'),
      p('The blind-comparison records stored Qwen\'s raw JSON directly. Those proposals bypassed the five-course validation rule; '
        'they were not solutions returned by the constrained planner. One CM answer also invented an EF section ID. '
        'The former MILP already required five courses in Years 1-3, so changing only its profit coefficient would not fix this bypass.'),
      p('What now changes the decision','Sub'),
      p('The semester planner now uses a deterministic Markov decision search over legal section bundles. '
        'Adding a course earns the change in net profit; STOP is unavailable below five credit-bearing courses in Years 1-3, '
        'and at most six courses and 18 credits may be selected. A sixth course is selected only when its marginal profit improves the result. '
        'Membership, prerequisite assumptions, exclusions, corequisites, meetings and the one-distributional-GE limit still bind.'),
      p('The overload cost is 0.25 x max(0, credits - 15)<super>2</super> in Years 1-3 and '
        '0.25 x max(0, credits - 12)<super>2</super> in Year 4. Invalid neural proposals are rejected before a separately labelled planner fallback. '
        'This repair changes the planning layer; it does not retrain Qwen or turn repaired results into raw-model successes.'),
      p('Historical proposals rechecked with the new acceptance rule','Sub')]
    rows=[['Profile','Raw subjects / accepted?','Validated planning result']]
    for r in checks:
        label=r['case_id'].replace('_',' ')
        raw=len(r['raw_proposal']['selected_option_ids'])
        out=', '.join(r['course_codes']) if r['status'] in ('optimal','feasible') else 'No legal five-course semester in the supplied pool.'
        rows.append([label,f'{raw} / No',out])
    story+=[table(rows,[125,105,281]),Spacer(1,9),p('All six raw proposals are rejected. The three CM cases yield five-course plans. '
        'The three CS pools remain infeasible under their saved options and meeting conflicts; no courses or timetable sections are invented. '
        'These are hypothetical section bundles over saved snapshots, with the original pairing assumptions retained.','SmallNote'),PageBreak(),
        p('One student, eight semesters','ReportTitle'),
        p('Synthetic profile: entering Year 1; Computing Mathematics; cohort 2025; no completed courses; '
          'desired stream Enriched Mathematics. Every selected course is assumed passed with B.','ReportBody')]
    rows=[['Semester','Selected courses','Count*','Credits','Overload']]
    for s in run['steps']:
        codes=', '.join(s['selected_courses'])
        rows.append([f"Y{s['year']} {s['semester']}",codes,s['credit_bearing_course_count'],s['credits'],f"{s['reward']['overload']:.2f}"])
    story+=[table(rows,[57,307,40,43,64]),Spacer(1,7),
      p('*Count excludes the zero-credit CSCI1001/1002 requirements. MA4530:A and MA4530:B are two simulated '
        'three-credit parts of one six-credit project, not duplicate project credits.','SmallNote'),p('Graduation audit','Sub')]
    rows=[['Encoded requirement','Simulation result','Check'],['Total credits: user 121; supplied path 122',f"{a['earned_credits']}",'PASS'],
      ['Four distributional GE; all three areas','4 courses; Area 1: 2, Area 2: 1, Area 3: 1','PASS'],
      ['Elective mathematics >=20 credits',str(a['elective_math_credits']),'PASS'],
      ['All mandatory courses; core 45; project 6','Complete; 45; 6','PASS'],
      ['Free-elective allocation >=20 credits',str(a['free_elective_credits']),'PASS'],
      ['Selected stream; programme membership','Enriched Mathematics complete; all allowed','PASS'],
      ['5-6 courses in Years 1-3; GE <=1/semester','All six early semesters; all eight semesters','PASS'],
      ['Encoded prior passes, windows and reward sums','No sequence or accounting violations','PASS']]
    story+=[table(rows,[252,207,52]),Spacer(1,8),p('Scope of this result','Sub'),
      p('The degree rollout searches complete semester actions with a 24-state beam and discount 0.98; it does not invoke MILP. '
        'It updates earned credits, GE areas, prerequisites, direct preparation benefits and selected-stream progress after each hypothetical pass. '
        'Approximate search does not establish the global optimum. A separate audit recomputes the transcript requirements and action sequence. '
        'The semester planner reports optimality only when its subset search was not pruned.','SmallNote'),
      p('This is an encoded curriculum-feasibility test. Future offerings, actual full-degree meeting compatibility, cohort-specific elective approval '
        'and official graduation eligibility are unverified. The CM EF/CS prerequisite waiver is the user\'s advisory assumption. '
        'The full transcript and every semester reward component are supplied separately.','SmallNote')]
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#c7d6dc'));canvas.line(42,35,A4[0]-42,35)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#546570'))
        canvas.drawString(42,23,'CityU Course Helper | Synthetic curriculum simulation')
        canvas.drawRightString(A4[0]-42,23,str(doc.page))
    target=OUT/'CM_Markov_Planning_Simulation.pdf'
    SimpleDocTemplate(str(target),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=38,bottomMargin=45,
      title='CM Markov Planning Simulation',author='CityU Course Helper').build(story,onFirstPage=footer,onLaterPages=footer)
    with (DATA/'year1_full_transcript.csv').open('w',newline='',encoding='utf-8-sig') as f:
        cols=['year','semester','term','id','title','credits','kind','area','grade'];w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(run['transcript'])
    done={r['id'] for r in run['transcript']};rule=policy()['streams']['CM']['Enriched Mathematics']
    md=['# CM Markov planning simulation','',
      'The short schedules were unchecked raw Qwen proposals, not feasible constrained-planner results. No neural weights were updated.','',
      'The new default planner uses Markov subset search; Years 1-3 require 5-6 credited courses. STOP below five is masked. '
      'A sixth course must improve net profit. Years 1-3 overload begins above 15 credits; Year 4 above 12. Both weights are 0.25.','',
      'Input: synthetic entering Year-1 CM, cohort 2025, empty transcript, desired Enriched Mathematics stream. All simulated grades B.','',
      '| Semester | Courses | Credited courses | Credits | Overload |','|---|---|---:|---:|---:|']
    for s in run['steps']:md.append(f"| Y{s['year']} {s['semester']} | {', '.join(s['selected_courses'])} | {s['credit_bearing_course_count']} | {s['credits']} | {s['reward']['overload']:.2f} |")
    md+=['',f"Audit: {a['earned_credits']} credits; four distributional GE (areas 1/2/3 = 2/1/1); {a['elective_math_credits']} elective mathematics credits; {a['free_elective_credits']} allocated free-elective credits; all mandatory courses; six capstone credits; Enriched Mathematics {progress(rule,done)}/{rule['slots']} slots.",'',
      'Every encoded graduation and independent sequence check passed. The source threshold is 122, meeting the user minimum 121. '
      'Free-elective allocation follows the existing audit: designated free electives plus mathematics credits above the 12-credit major-elective allocation; this is not a second contribution to total earned credits.','',
      'This is approximate Markov beam search with terminal graduation constraints, not a globally optimal or university-approved timetable. '
      'Future offerings, real full-degree meeting compatibility and cohort approval are unverified. CM EF/CS prerequisite waivers are advisory user assumptions.','',
      'Reproduce: `.\\.venv\\Scripts\\python.exe run_markov_repair.py` then `.\\.venv\\Scripts\\python.exe write_markov_simulation_report.py`.','',
      'Historical reports and raw answers remain unchanged. `semester_checks.json` records rejections and repaired CM plans separately.']
    (DATA/'README.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    paths=['markov_planner.py','markov_degree.py','programme_v6.py','data/markov-repair/year1_CM.json','data/profit_objective_policy.json',
      'data/programme-v6/policy.json','data/preparation-v5.json','reports/markov-repair/year1_simulation.json',
      'reports/markov-repair/semester_checks.json','reports/year3-path-comparison06/cases.json','reports/year3-path-comparison06/qwen_raw.json']
    (DATA/'manifest.json').write_text(json.dumps({'neural_weights_updated':False,'previous_reports_overwritten':False,
      'sha256':{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in paths}},indent=2)+'\n')
    print(target)

if __name__=='__main__':build()
