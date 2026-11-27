"""Report the completed fine-tune and strict source-based rerun, separately."""
import hashlib,json
from pathlib import Path
from xml.sax.saxutils import escape
import project_runtime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from timetable_grounded_training import REPORT,DATA,ADAPTER
ROOT=Path(__file__).resolve().parent

def build():
    global REPORT,ADAPTER
    from grounded_model import selected_run
    chosen=selected_run();REPORT=ROOT/chosen['report_dir'];ADAPTER=chosen['adapter']
    training=json.loads((REPORT/'training.json').read_text());assert training['status']=='complete'
    release=json.loads((REPORT/'release.json').read_text());run=json.loads((REPORT/'rerun_year1.json').read_text())
    semesters=json.loads((REPORT/'rerun_semesters.json').read_text());pairs=json.loads((REPORT/'EF_penalty_examples.json').read_text())
    before=json.loads((ROOT/'reports/timetable-grounded/before_evaluation.json').read_text());after=release['evaluation']['after']
    initial=json.loads((ROOT/'reports/timetable-grounded/training.json').read_text())
    out=ROOT/'output/pdf/timetable-grounded';out.mkdir(parents=True,exist_ok=True)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Title2',fontName='Helvetica-Bold',fontSize=21,leading=25,textColor=colors.HexColor('#15394b'),spaceAfter=12))
    styles.add(ParagraphStyle(name='Body2',fontSize=9.5,leading=13.2,spaceAfter=9))
    styles.add(ParagraphStyle(name='Sub2',fontName='Helvetica-Bold',fontSize=12,leading=15,spaceBefore=10,spaceAfter=8,textColor=colors.HexColor('#15394b')))
    styles.add(ParagraphStyle(name='Cell2',fontSize=8.5,leading=11))
    styles.add(ParagraphStyle(name='Note2',fontSize=8.1,leading=11,spaceAfter=8,textColor=colors.HexColor('#45535c')))
    def p(t,s='Body2'):return Paragraph(t,styles[s])
    def table(rows,widths):
        t=Table([[p(escape(str(v)),'Cell2') for v in r] for r in rows],colWidths=widths,repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebf0')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f8')]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
            ('TOPPADDING',(0,0),(-1,-1),5.5),('BOTTOMPADDING',(0,0),(-1,-1),5.5)]))
        return t
    story=[p('Learning to respect<br/>the offered timetable','Title2'),p('Fine-tuning and post-training rerun | 24 November 2026','Note2'),
        p('<b>A new Qwen checkpoint has been fine-tuned.</b> Course selections now depend on compatible timetable evidence '
          'in the requested MA/CS folders. The entering Year-1 simulation stops honestly when that source pool cannot support five courses.'),
        p('What the model and planner now learn','Sub2'),
        p('Only compatible programme/major sections in the exact saved semester may be selected. Source PDF hashes are checked. '
          'Curriculum membership does not prove an offering, and no A/B swaps or future-year extrapolation are accepted. '
          'This run applies the MA/CS-only source restriction literally; separate GE folders are outside its pool.'),
        p('An EF course adds <b>1.5 x lambda_background</b> utility cost when the student has no finance-study background. '
          'Passed or declared finance study removes this extra cost; F/IP/W do not count. The ordinary mismatch score still applies. '
          'This cost is separate from formal prerequisites; the user-authorised CM EF/CS prerequisite assumption remains.'),
        p('Training and evaluation','Sub2'),
        p(f"The initial pass used {initial['train_examples']} training and {initial['validation_examples']} validation examples over two epochs, including 45 prior-simulation corrections. "
          f"A corrective pass used {training['train_examples']} training and {training['validation_examples']} validation examples over {training['args']['epochs']} epoch(s), "
          'teaching finance-label types and varied weights, with feasible-plan examples reweighted to counter excessive refusals. '
          'Training uses assistant-only supervised loss with NF4 QLoRA; '
          'the reward penalty is enforced by the planner, rather than being a reinforcement-learning loss.'),
        table([['Evaluation group','Before','After'],
          ['Held-out source/profile policy combinations',f"{before['heldout_policy']['passed']}/{before['heldout_policy']['total']}",f"{after['heldout_policy']['passed']}/{after['heldout_policy']['total']}"],
          ['Corrected timetable diagnostics (familiar examples)',f"{before['familiar_schedule_diagnostics']['passed']}/{before['familiar_schedule_diagnostics']['total']}",f"{after['familiar_schedule_diagnostics']['passed']}/{after['familiar_schedule_diagnostics']['total']}"],
          ['Historical membership/stream regression checks',f"{before['historical_regression']['passed']}/{before['historical_regression']['total']}",f"{after['historical_regression']['passed']}/{after['historical_regression']['total']}"]],[340,85,86]),Spacer(1,7),
        p('The policy combinations share taught source facts. Corrected timetable diagnostics were included in training and are not independent generalisation tests. '
          'A timetable pass requires valid supplied options or verified infeasibility. Planner repairs never count as raw-model successes.','Note2'),
        p('The new checkpoint is active for the timetable domain. The prior general checkpoint remains in use because one older finance-stream answer regressed.','Note2'),
        p('EF background examples decoded after training','Sub2')]
    rows=[['Course','Student background','Extra EF penalty','Raw model correct?']]
    for r in pairs:
        rows.append([r['course_code'],r['profile_label'].replace('_',' '),r['expected']['EF_mismatch_penalty'],'Yes' if r['model_output_accepted'] else 'No - guarded'])
    story+=[table(rows,[72,198,100,141]),Spacer(1,7),p('Both EF courses remain unavailable for CM in the supplied compatible-section records. '
        'Finance preparation changes the penalty, not section permission. Inputs explicitly supply the default background weight of 1. '
        'These examples demonstrate learned utility values, not an EF registration outcome.','Note2'),PageBreak(),
        p('Rerunning the student profile','Title2'),
        p('Input: synthetic entering Year-1 CM, cohort 2025, no completed courses, desired Enriched Mathematics stream. '
          'Semester A uses the saved 202609 source term.'),
        table([['Check','Post-training outcome'],
          ['Eligible subjects in the saved source pool',', '.join(run['blocked_at']['candidate_course_codes'])],
          ['Normal minimum / available subjects',f"5 / {len(run['blocked_at']['candidate_course_codes'])}"],
          ['Qwen raw answer',run['steps'][0]['result'].get('raw_model_response','')],
          ['Acceptance / planner result',('Verified model refusal' if run['steps'][0]['result'].get('model_output_accepted') else 'Model answer rejected; policy result used')+'; no legal five-course semester'],
          ['Committed courses / added credits','0 / 0'],['Graduation requirement check','Incomplete - insufficient compatible timetable evidence']],[200,311]),Spacer(1,9),
        p('Why the previous 127-credit result changes','Sub2'),
        p('The preceding run demonstrated curriculum-credit feasibility using assumed offering windows. It did not establish '
          'timetable feasibility. Rechecking its A/B allocations against the MA/CS snapshot finds 30 unsupported entries out of 45 '
          '(including zero-credit entries and project parts). For example, MA3523 was placed in A and MA3512 in B without matching '
          'CM timetable evidence. Repeating a source year for this diagnostic does not validate later academic years.'),
        p('Mandatory courses without compatible timetable evidence in either supplied source semester: <b>'+
          escape(', '.join(run['mandatory_courses_without_any_compatible_saved_timetable']))+'</b>. '
          'Some files may be absent; others lack an explicit CM-compatible section or a recognised meeting schedule. '
          'This does not mean the university does not offer those courses.'),
        p('Additional synthetic progression-profile reruns','Sub2')]
    rows=[['Profile','Validated output subjects','Raw model accepted?']]
    for r in semesters:
        result=r['result'];codes=', '.join(result.get('course_codes',[])) or 'Infeasible with the supplied options'
        rows.append([r['id'].removeprefix('diagnostic:corrected:').replace('_',' '),codes,'Yes' if result.get('model_output_accepted') else 'No - planner fallback'])
    story+=[table(rows,[120,297,94]),Spacer(1,8),p('Every returned option is tied to the saved source term, course, section bundle and meetings. '
        'The table reuses the actual post-training diagnostic decodes; it is not a fresh independent benchmark. '
        'Section component linkage and teaching weeks retain the prior explicitly hypothetical assumptions, and registration remains unverified.','Note2'),
        p('The five-course minimum, 18-credit limit, GE cap, prerequisite assumptions and year-specific overload penalties are preserved. '
          'No requirement is weakened to force a complete degree. Completing the four-year validation needs compatible foundation/GE/project timetable coverage '
          'and later-year offerings, or a separately declared assumption about future offerings.','Note2')]
    def footer(c,d):
        c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#546570'));c.drawString(42,23,'CityU Course Helper | Source-grounded fine-tuning');c.drawRightString(A4[0]-42,23,str(d.page))
    target=out/'Timetable_Grounded_Finetuning_Rerun.pdf'
    SimpleDocTemplate(str(target),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=36,bottomMargin=42,
      title='Timetable-grounded Fine-tuning and Rerun').build(story,onFirstPage=footer,onLaterPages=footer)
    paths=['cm_background_policy.py','profit_objective.py','markov_planner.py','programme_v6.py','timetable_evidence.py','grounded_degree.py',
      'timetable_grounded_training.py','data/timetable-grounded/train.jsonl','data/timetable-grounded/validation.jsonl',
      'data/timetable-grounded/snapshot/courses.json','reports/timetable-grounded/rerun_year1.json',ADAPTER+'/adapter_model.safetensors']
    paths.remove('reports/timetable-grounded/rerun_year1.json')
    paths+=[str((REPORT/'rerun_year1.json').relative_to(ROOT)).replace('\\','/'),
      training['args']['data_dir']+'/train.jsonl',training['args']['data_dir']+'/validation.jsonl',
      str((REPORT/'after_predictions.json').relative_to(ROOT)).replace('\\','/')]
    (REPORT/'manifest.json').write_text(json.dumps({'adapter':ADAPTER,'accepted_for_activation':release['accepted_for_activation'],
        'accepted_for_grounded_timetable_domain':chosen.get('accepted_for_activation',False),
        'sha256':{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in paths},'all_run_outputs_on_drive':'F'},indent=2)+'\n')
    lines=['# Timetable-grounded fine-tuning and rerun','',
        f"Actual supervised QLoRA training completed: initial {initial['train_examples']}/{initial['validation_examples']} train/validation, 2 epochs; corrective {training['train_examples']}/{training['validation_examples']}, {training['args']['epochs']} epoch(s). Previous checkpoints and simulations remain preserved.",'',
        'Strict source rule: exact saved terms and CM/CS-compatible sections from the supplied MA/CS folders; source hashes verified. '
        'No opposite-semester/future-year substitution. This run does not import separate GE folders.','',
        'EF surcharge: lambda_background * 1.5 without passed or declared finance study; zero with finance study. '
        'This is additional to ordinary mismatch, never a missing-prerequisite fee.','',
        '## Evaluation','',json.dumps(release['evaluation'],indent=2),'',
        '## Entering Year-1 CM rerun','',
        'Incomplete: the eligible source pool contains only '+', '.join(run['blocked_at']['candidate_course_codes'])+'. '
        'Five courses cannot be selected. No courses or credits were committed and graduation requirements were not fulfilled.','',
        'Raw model response: `'+run['steps'][0]['result'].get('raw_model_response','')+'`','',
        'Missing compatible timetable evidence for mandatory courses: '+', '.join(run['mandatory_courses_without_any_compatible_saved_timetable'])+'.','',
        'This is not proof that the real programme cannot be completed. The snapshot/section scope is incomplete; future offerings and official registration are unverified.','',
        'Run the new checkpoint: `.\\.venv\\Scripts\\python.exe grounded_model.py degree --profile data/markov-repair/year1_CM.json --output reports/timetable-grounded/user_degree.json`','',
        'Inspect EF with `grounded_model.py assess --profile <profile.json> --course EF3320 --output <result.json>`; the profile term must match the intended semester.','',
        'The report, actual raw decodes, guarded reruns, training progress, snapshots and hashes are all retained in this run folder.']
    (REPORT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(target,flush=True)

if __name__=='__main__':build()
