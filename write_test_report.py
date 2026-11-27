"""Build the measured evaluation report and readable example catalogue."""
import html
import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'reports/examples-20261025'
PDF=ROOT/'output/pdf/cityu_model_test_report_20261025.pdf'
pdfmetrics.registerFont(TTFont('Segoe',r'C:/Windows/Fonts/segoeui.ttf'))
pdfmetrics.registerFont(TTFont('SegoeBold',r'C:/Windows/Fonts/segoeuib.ttf'))
pdfmetrics.registerFont(TTFont('Consolas',r'C:/Windows/Fonts/consola.ttf'))
NAVY=colors.HexColor('#17324D');TEAL=colors.HexColor('#087F8C');GRAY=colors.HexColor('#526477')
LIGHT=colors.HexColor('#EDF4F7');RED=colors.HexColor('#9E342D')
styles={
 'title':ParagraphStyle('title',fontName='SegoeBold',fontSize=25,leading=30,textColor=NAVY,spaceAfter=14),
 'h1':ParagraphStyle('h1',fontName='SegoeBold',fontSize=18,leading=23,textColor=NAVY,spaceAfter=12),
 'h2':ParagraphStyle('h2',fontName='SegoeBold',fontSize=11.5,leading=15,textColor=TEAL,spaceBefore=10,spaceAfter=6),
 'body':ParagraphStyle('body',fontName='Segoe',fontSize=10,leading=14,textColor=NAVY,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Segoe',fontSize=8.3,leading=11,textColor=GRAY,spaceAfter=6),
 'cell':ParagraphStyle('cell',fontName='Segoe',fontSize=8.4,leading=11,textColor=NAVY),
 'head':ParagraphStyle('head',fontName='SegoeBold',fontSize=8.5,leading=11,textColor=colors.white),
 'code':ParagraphStyle('code',fontName='Consolas',fontSize=8.3,leading=11,textColor=NAVY,spaceAfter=8,backColor=LIGHT,borderPadding=7),
}


def p(text,style='body',raw=False):
    return Paragraph(text if raw else html.escape(str(text)).replace('\n','<br/>'),styles[style])


def table(headers,rows,widths):
    data=[[p(x,'head') for x in headers]]+[[p(x,'cell') for x in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
             ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
             ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
             ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
             ('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#CDD9E3'))]))
    return t


def footer(canvas,doc):
    w,h=A4
    canvas.setStrokeColor(TEAL);canvas.setLineWidth(2);canvas.line(46,h-34,w-46,h-34)
    canvas.setFont('SegoeBold',8);canvas.setFillColor(GRAY)
    canvas.drawString(46,h-25,'CITYU COURSE HELPER  /  MODEL TEST REPORT')
    canvas.setFont('Segoe',8)
    canvas.drawString(46,26,'25 October 2026 | Local exploratory evaluation | Synthetic scores')
    canvas.drawRightString(w-46,26,str(doc.page))


def compact(v):
    return json.dumps(v,ensure_ascii=True,separators=(', ',': '))


def main():
    summary=json.loads((DATA/'summary.json').read_text())
    cases=json.loads((DATA/'cases.json').read_text(encoding='utf-8'))
    responses=[json.loads(x) for x in (DATA/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    sched=json.loads((DATA/'scheduler_cases.json').read_text())
    bycase={c['id']:c for c in cases};lookup={(r['method'],r['id']):r for r in responses}
    assert len(cases)==26 and len(responses)==52 and len({(r['method'],r['id']) for r in responses})==52
    b,t=summary['methods']['base'],summary['methods']['fine_tuned']
    catnames={'new_profile_scoring':'New student profiles','paraphrased_fact_extraction':'Paraphrased fact extraction',
              'scoring_stress':'Scoring stress cases','missing_information':'Missing-information guards',
              'untrained_advising_format':'Provisional advising format','matched_clean_control':'Matched clean controls'}
    def outcome(method,ident):return 'PASS' if lookup[(method,ident)]['grade']['passed'] else 'FAIL'
    def nums(v):return [f"{v.get(k):.2f}" if type(v.get(k)) in (int,float) else str(v.get(k)) for k in ['background_mismatch','difficulty','workload']]
    def scoretable(ident,withbase=True):
        rows=[['Expected synthetic target']+nums(bycase[ident]['expected'])]
        if withbase:rows.append(['Base model']+nums(lookup[('base',ident)]['grade'].get('prediction',{})))
        rows.append(['Fine-tuned model']+nums(lookup[('fine_tuned',ident)]['grade'].get('prediction',{})))
        return table(['Output','Mismatch','Difficulty','Workload'],rows,[182,107,107,107])
    story=[]
    story += [p('Qwen3-8B\nCourse Helper Evaluation','title'),p('New examples, measured answers and failure analysis | 25 October 2026','small'),
              p('The adapter improves structured extraction and follows the synthetic scoring rubric more closely than the base model. It still fails important generalization and stress cases. Keep workload estimates experimental and enforce hard constraints in the scheduler.'),
              p('What was tested','h2'),p('26 distinct prompts, answered once by each model (52 responses), plus 8 separate MILP scenarios. The initial suite had 24 prompts; two matched clean controls were added after stress failures. No training or checkpoint changes were made.'),
              table(['Category','Base pass','Tuned pass'],[[catnames[k],f"{b['categories'][k]['passed']}/{b['categories'][k]['total']}",f"{t['categories'][k]['passed']}/{t['categories'][k]['total']}"] for k in catnames],[303,100,100]),
              p('Interpret the improvements correctly','h2'),
              p(f"Typed output compliance: base {b['schema_valid']}/26; tuned {t['schema_valid']}/26. For the six extraction cases, both models matched all factual values after numeric strings were normalized. The tuned model's gain there is correct JSON number types, not newly demonstrated factual knowledge."),
              table([f"Synthetic score MSE ({t['scoring_total']} cases)",'Base','Tuned'],[[k.replace('_',' ').title(),f"{b['synthetic_mse_on_valid_scores'][k]:.6f}",f"{t['synthetic_mse_on_valid_scores'][k]:.6f}"] for k in ['background_mismatch','difficulty','workload']],[303,100,100]),
              p('MSE includes 12 initial score cases and 2 clean controls, measured against a hand-written synthetic rubric, not real student ratings or weekly workload. Do not combine these varied pass criteria into a single model-accuracy claim.','small'),PageBreak()]
    story += [p('Worked scoring examples','h1'),p('All three scores are on a 0-1 scale. Higher means greater mismatch, difficulty or workload. A scoring case passes only if the schema is valid and every numeric error is at most 0.02. Examples below include both successes and failures.')]
    for ident in ['S01','S04','R03']:
        c=bycase[ident];u=json.loads(c['messages'][1]['content']);course=u['course'];student=u['student']
        block=[p(ident+' | '+c['title'],'h2'),p(f"Input: {course['code']}, {course['credits']} credits; continuous assessment {course.get('assessment_percent')}%. Student: year {student['year']}, {student['major']}. {'Fictional course used only as a boundary fixture.' if c['source_url'] is None else 'Course facts come from the saved official syllabus.'}",'small'),scoretable(ident),p('Base: '+outcome('base',ident)+' | Fine-tuned: '+outcome('fine_tuned',ident),'small')]
        story.append(KeepTogether(block))
    story += [p('What these examples reveal','h2'),p('S01 has correct tuned difficulty and workload, but the mismatch score is wrong for the new year-three profile. R03 shows a larger failure on a fictional six-credit project course. Valid JSON and a review flag do not guarantee correct scores.'),p('Every tested score response retained label_type="synthetic_rubric" and needs_review=true. This disclosure is useful, but it does not replace score validation.','small'),PageBreak()]
    story += [p('Fact extraction examples','h1'),p('These tests reorder course facts into prose. Two deliberately omit assessment percentages. The task is to copy supplied evidence into typed fields; it is not a closed-book knowledge test.')]
    for ident in ['F01','F05']:
        c=bycase[ident];truth=c['expected'];base=lookup[('base',ident)]['grade'].get('prediction',{});tuned=lookup[('fine_tuned',ident)]['grade'].get('prediction',{})
        rows=[]
        for key in ['course_code','credits','prerequisites_text','assessment_percent','exam_percent']:
            def show(v):return json.dumps(v,ensure_ascii=True)
            rows.append([key,show(truth[key]),show(base.get(key)),show(tuned.get(key))])
        story += [p(ident+' | '+c['title'],'h2'),p(c['messages'][1]['content'],'small'),table(['Field','Expected','Base','Tuned'],rows,[116,129,129,129]),p('Base: '+outcome('base',ident)+' | Fine-tuned: '+outcome('fine_tuned',ident),'small')]
    story += [p('Assessment percentages absent from the excerpt must remain null, even if the original syllabus has values. Both models did this correctly in F05 and F06. Quotation marks around a numeric value are counted as a type failure, not a factual-value failure.'),PageBreak()]
    story += [p('Robustness and missing information','h1'),p('Embedded text is untrusted input. R01 puts a misleading instruction in course aims; R02 puts one in student interests. C01 and C02 remove only that instruction, preserving the other input fields.')]
    for injected,clean in [('R01','C01'),('R02','C02')]:
        exp=bycase[injected]['expected'];cv=lookup[('fine_tuned',clean)]['grade'].get('prediction',{});iv=lookup[('fine_tuned',injected)]['grade'].get('prediction',{})
        story += [p(injected+' / '+clean+' | '+bycase[injected]['title'],'h2'),table(['Tuned output','Mismatch','Difficulty','Workload'],[['Expected target']+nums(exp),['Clean input']+nums(cv),['With embedded instruction']+nums(iv)],[182,107,107,107])]
        changed=[k.replace('_',' ') for k in ['background_mismatch','difficulty','workload'] if cv.get(k)!=iv.get(k)]
        story.append(p('Observed change: '+(', '.join(changed) if changed else 'none in these three numeric fields')+'. A single paired test can reveal context sensitivity; it cannot establish a general resistance rate.','small'))
    story += [p('Guard cases G01-G03','h2'),p('Both models returned null for missing credits/workload, unknown meeting time and unknown available seats, and kept the relevant feasibility or guarantee flag false. All three guard cases passed for both models.'),p('A01 | Provisional advising answer from the tuned model','h2'),p(lookup[('fine_tuned','A01')]['raw_response'],'code'),p('All three advising-format cases passed their narrow checks: two supplied courses, six credits, and explicit missing timetable/eligibility evidence. This does not establish that the suggestions suit real students.','small'),PageBreak()]
    story += [p('Scheduler examples','h1'),p('These are synthetic solver fixtures, evaluated separately from the LLM. Each option represents a complete section bundle. PASS means the returned status or selected options matched the expected result.'),
              table(['ID / scenario','Expected','Observed','Check'],[[r['id']+' | '+r['title'],r['expected_error'] or r['expected_status'],r['actual'].get('error_type',r['actual'].get('status')), 'PASS' if r['passed'] else 'FAIL'] for r in sched],[284,73,73,73]),
              p('M01 | Feasible schedule','h2'),p('DEMO1001 is required. DEMO1002 overlaps with it, while DEMO1003 does not. The six-credit solution is DEMO1001-01 plus DEMO1003-01. These labels and meeting times are entirely simulated.'),
              p('M02 and M05 | Missing evidence','h2'),p('The required course is infeasible when its timetable is unverified. A weekly workload cap without weekly measurements raises a clear error. Neither case is converted into a guessed feasible schedule.'),
              p('Boundary of the guarantee','h2'),p('The solver enforces only the supplied rules, credits and meeting data. Its success does not validate LLM scores, real timetable completeness, university eligibility rules or seat availability. None of these fixtures is a real CityU registration plan.'),PageBreak()]
    story += [p('Complete model-case ledger','h1'),p('PASS means the task-specific expected behavior was met. Score cases use the 0.02 tolerance; extraction uses exact typed fields; guard/advising cases use explicit missing-data and constraint checks. Categories are intentionally reported separately.','small'),
              table(['ID','Test example','Base','Tuned'],[[c['id'],c['title'],outcome('base',c['id']),outcome('fine_tuned',c['id'])] for c in cases],[40,353,55,55]),
              p('Full system prompts, user inputs, expected outputs and both raw model answers are preserved in TEST_EXAMPLES.md and the JSON files beside this report project. Nothing was omitted from the recorded run.','small'),PageBreak()]
    story += [p('Method, limits and next steps','h1'),p('Reproducible local setup','h2'),
              p('Base model: Qwen/Qwen3-8B. Tuned model: the existing rank-8 LoRA adapter selected from the original two-epoch run. Both tests used the same supplied evidence, non-thinking chat template, greedy decoding, a 320-new-token budget, and the local RTX 5090. One response per prompt; no sampling repeats or retraining.'),
              p('Model revision: '+summary['model']['revision'],'code'),p('Adapter SHA-256: '+summary['adapter_sha256'],'code'),
              p('Evaluation limits','h2'),p('The 24 initial prompts were designed after reading the previous evaluation. Two clean controls were then added to investigate observed stress failures. Exact prompt overlap with the original train, validation and test prompts was checked and absent, but course facts were previously used in evaluation. Treat this as exploratory testing, not a fresh blind benchmark. Small samples do not support a population accuracy estimate.'),
              p('The scoring targets are formula-generated estimates. There are no reviewed CityU workload labels, real weekly workload measurements, student rankings or live AIMS sections in this test. The base and tuned models both saw the rubric in the scoring prompt; improvement therefore measures following that rubric, not discovering actual workload.'),
              p('Recommended next steps','h2'),p('1. Compute the explicit scoring formula in ordinary code when that formula is the desired behavior.\n2. Normalize and validate student inputs; keep model predictions marked for review.\n3. Add diverse, reviewed profiles and robustness examples before further training.\n4. Obtain verified AIMS sections and human workload labels, then evaluate on a newly frozen test set. Keep the MILP hard-constraint checks.'),
              p('Sources and evidence','h2'),p('Official model: https://huggingface.co/Qwen/Qwen3-8B. Course facts are the locally saved official 2026/27 CityU syllabus snapshots, collected 24 October 2026. No new web retrieval was used for this run.','small')]
    for code in json.loads((ROOT/'data/splits.json').read_text())['test']:
        story.append(p(code+': https://www.cityu.edu.hk/ug/202627/course/'+code+'.pdf','small'))
    story += [p('Re-run: .venv\\Scripts\\python.exe extended_tests.py, then extended_tests.py --controls. Rebuild this report with the bundled PDF Python runtime and write_test_report.py. Original run data are under reports/examples-20261025/. Re-running the initial suite overwrites that suite, so copy the dated folder before experiments.','small')]
    PDF.parent.mkdir(parents=True,exist_ok=True)
    doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=51,bottomMargin=44,
                          title='CityU Qwen3-8B Model Test Report',author='Local evaluation')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    # Full reusable examples, separate from the concise print report.
    md=['# Model test examples - 25 October 2026','',
        'Exploratory tests. Original 24 cases plus two follow-up matched controls. No weight updates. Scores are synthetic rubric targets, not real workload labels.','',
        'Each scoring case passes at absolute error <= 0.02 in every score plus schema compliance. Other tasks use their explicit expected fields.','']
    for c in cases:
        md += ['## '+c['id']+' - '+c['title'],'','Category: '+c['category']+'. Data: '+c['data_kind']+'.','',
               '### System instruction','','```text',c['messages'][0]['content'],'```','',
               '### User input','','```text',c['messages'][1]['content'],'```','',
               '### Expected result','','```json',json.dumps(c['expected'],indent=2,ensure_ascii=False),'```','']
        for method in ['base','fine_tuned']:
            r=lookup[(method,c['id'])]
            md += ['### '+method+' - '+outcome(method,c['id']),'','```json',r['raw_response'],'```','']
        if c.get('source_url'):md += ['Source: '+c['source_url'],'']
    (DATA/'TEST_EXAMPLES.md').write_text('\n'.join(md),encoding='utf-8')
    print(str(PDF))


if __name__=='__main__':main()
