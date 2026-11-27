"""Readable record of the corrected EF section and hard degree-credit gate."""
import json,hashlib
from pathlib import Path
from xml.sax.saxutils import escape
import project_runtime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'reports/degree-chain-policy';OUT=ROOT/'output/pdf/degree-chain-policy'
def main():
    OUT.mkdir(parents=True,exist_ok=True);r=json.loads((DATA/'model_rollout.json').read_text());e=json.loads((DATA/'EF3320_source_check.json').read_text());release=json.loads((DATA/'release.json').read_text())
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='T',fontSize=20,leading=24,fontName='Helvetica-Bold',spaceAfter=12,textColor=colors.HexColor('#15394b')))
    styles.add(ParagraphStyle(name='B',fontSize=9.5,leading=13,spaceAfter=9));styles.add(ParagraphStyle(name='C',fontSize=8.3,leading=11))
    def p(t,k='B'):return Paragraph(t,styles[k])
    def table(rows,widths):
        t=Table([[p(escape(str(c)),'C') for c in row] for row in rows],colWidths=widths,repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebf0')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f8')]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        return t
    story=[p('EF3320 and the four-year credit gate','T'),
      p('<b>EF3320 is on the saved Semester B timetable.</b> Section CA1, CRN 11425, meets Friday 16:00-18:50 and excludes College CB. '
        'The non-CB CM profile is compatible. The old importer wrongly required an explicit ONLY FOR CM label. Its section filter and cross-folder programme assessment have been corrected.'),
      p('The previously rejected answer nevertheless used Semester A and the invented ID EF3320:10000. That particular selection remains invalid. '
        'The real source is the supplied EF3320_SEMB PDF for term 202702. Section C01 remains restricted to CB; ordinary timetable and prerequisite assumptions still apply.'),
      p('<b>Flexible semester load; hard final target.</b> There is no five-course minimum. A legal semester may contain 0-6 courses and at most 18 credits. '
        'The complete eight-term CM chain must reach at least 122 credits (also meeting 121) and satisfy all encoded GE, core, project, elective and stream requirements. '
        'A shortfall cannot be compensated by reward. User-authorised repeating A/B snapshots are a simulation assumption, not verified future offerings.'),
      p(f"<b>Actual retraining:</b> 96 training and 12 validation examples, two QLoRA epochs. Exact policy/diagnostic checks changed from {release['before']['passed']}/20 to {release['after']['passed']}/20. "
        'The two remaining exact failures mislabel declared introductory finance study as advanced; timing availability and zero extra surcharge were correct. Deterministic validation retains the correct background score. Fresh 121/122 boundary probes and the EF3320 no-finance probe passed.'),
      p('<b>Four-year rerun: no accepted graduating chain.</b> The diagnostic below earns '+str(r['audit']['earned_credits'])+' credits. '
        'The currently confirmed compatible timetable pool has a 70-credit upper bound across unique subjects. Repeating a course cannot earn its credits again. '
        'Even a perfect selection cannot reach 122 using this pool, so the global planner rejects a complete chain before treating any diagnostic as a degree plan.')]
    rows=[['Semester','Diagnostic selected courses','Count','Credits']]
    for s in r['diagnostic_semesters']:rows.append([f"Y{s['year']} {s['semester']}",', '.join(s['selected_courses']) or 'None',s['course_count'],s['credits']])
    story+=[table(rows,[57,357,45,52]),Spacer(1,10),p('<b>Missing compatible mandatory-source coverage:</b> '+', '.join(r['coverage_certificate']['mandatory_without_compatible_timetable'])+'. '
        'Further GE/college/project and elective timetable coverage is needed. This is a limitation of the currently confirmed source pool, not proof that the university degree cannot be completed. '
        'The diagnostic assumes passes and is not a registration recommendation.')]
    SimpleDocTemplate(str(OUT/'EF3320_Flexible_Load_Update.pdf'),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=36,bottomMargin=36).build(story)
    lines=['# EF3320 correction and flexible-load degree policy','',
      'EF3320: Semester B 202702, CA1, CRN 11425, Friday 16:00-18:50. Source restriction: not for College CB. The non-CB CM profile is eligible for consideration. '
      'The importer wrongly required ONLY FOR CM. C01 remains CB-only. Old Semester-A EF3320:10000 is still unsupported.','',
      'No five-course hard minimum. Six-course / 18-credit maxima retained. Complete CM chain must earn >=122, satisfying >=121 too, '
      'and pass all other encoded graduation requirements. Repeating A/B is user-authorised simulation only. No repeated credit.','',
      '96/12 train/validation examples, 2 epochs. Exact evaluation: 12/20 before, 18/20 after. Two remaining finance-level labels are guard-corrected, not counted as raw passes.','',
      f"Model diagnostic earned {r['audit']['earned_credits']}; confirmed source-pool credit ceiling {r['coverage_certificate']['unique_source_credit_upper_bound']}; no accepted graduating chain.",'',
      '| Semester | Courses | Credits |','|---|---|---:|']
    for s in r['diagnostic_semesters']:lines.append(f"| Y{s['year']} {s['semester']} | {', '.join(s['selected_courses']) or 'None'} | {s['credits']} |")
    lines+=['','Missing mandatory source coverage: '+', '.join(r['coverage_certificate']['mandatory_without_compatible_timetable'])+'.','',
      'Full-chain search enforces the terminal predicate. The source-coverage certificate proves failure under current confirmed inputs; partial single-semester feasibility never implies degree completion. '
      'Current reports/benchmark results with a five-course minimum remain historical and were not overwritten.']
    (DATA/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=['section_eligibility.py','degree_chain.py','terminal_markov.py','degree_chain_training.py','programme_v6.py','markov_planner.py',
      'data/degree-chain-policy/train.jsonl','data/degree-chain-policy/snapshot_cross/courses.json','adapters/degree-chain-policy/adapter_model.safetensors']
    (DATA/'manifest.json').write_text(json.dumps({'sha256':{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in paths},
      'prior_reports_preserved':True,'whole_chain_accepted':False,'source_credit_upper_bound':70},indent=2))
    print(OUT/'EF3320_Flexible_Load_Update.pdf')
if __name__=='__main__':main()
