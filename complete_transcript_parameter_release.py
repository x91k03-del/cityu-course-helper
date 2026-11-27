"""Publish a validated parameter-only pipeline and its fictional PDF evidence."""
import copy,hashlib,json,shutil,zipfile
from pathlib import Path
from xml.sax.saxutils import escape
import project_runtime
import transcript_parameter_pipeline as p

ROOT=p.ROOT;OUT=p.OUT

def main():
    comparisons=json.loads((OUT/'after_comparison.json').read_text())
    predictions=json.loads((OUT/'after_predictions.json').read_text(encoding='utf-8'))
    training=json.loads((OUT/'training/training.json').read_text())
    final_adapter=p.ADAPTER
    english_training=None;english_controls=None
    if (OUT/'english-correction/training.json').exists():
        english_training=json.loads((OUT/'english-correction/training.json').read_text())
        english_controls=json.loads((OUT/'english-correction/control_evaluation.json').read_text())
        assert english_training['status']=='complete' and english_controls['passed']==english_controls['total']==4
        final_adapter='adapters/objective-parameters'
    protocol=json.loads((OUT/'training/protocol.json').read_text())
    holdout=json.loads((OUT/'training/heldout_evaluation.json').read_text())
    cases=json.loads((OUT/'cases.json').read_text())
    assert training['status']=='complete' and holdout['passed']==holdout['total']==8
    assert len(comparisons)==3 and all(r['parameters_identical'] and r['optimizer_paths_identical'] for r in comparisons)
    assert all(r['accepted'] for r in predictions) and len(predictions)==6
    for r in predictions:p.validate_parameters(json.loads(r['raw']),next(c['expected_parameters'] for c in cases if c['id']==r['id']))
    runs={}
    for c in cases:
        for mode in ['transcript','prompted']:
            r=json.loads((OUT/f'after_{c["id"]}_{mode}_optimizer.json').read_text(encoding='utf-8'))
            assert r['audit']['all_encoded_requirements_met'] and r['audit']['earned_credits']==122
            assert r['completion_optimality_certificate']['optimality_proven'] and r['completion_optimality_certificate']['optimality_gap']==0
        runs[c['id']]=json.loads((OUT/f'after_{c["id"]}_transcript_optimizer.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT/p.PARENT/'adapter_model.safetensors').read_bytes()).hexdigest()==protocol['parent_sha256']
    manifest={'adapter':final_adapter,'accepted_for_activation':True,'role':'objective_parameters_only',
      'LLM_output_keys':sorted(p.PARAMETER_KEYS),'student_facts_reader':'deterministic PDF/text parser outside the LLM',
      'path_solver':'external exact dynamic programming; independent finite enumeration certificate',
      'LLM_generates_timetable':False,'transcript_prompt_consistency':'3/3 cases: parameter and optimizer-path equality',
      'heldout_parameter_exports':holdout,'training_performed':True,'selected_epoch':(english_training or training)['selected_epoch'],
      'sha256':hashlib.sha256((ROOT/final_adapter/'adapter_model.safetensors').read_bytes()).hexdigest(),
      'no_custom_system_prompt_for_transcript_input':True,'fallback_used':False,
      'scope':'Known reviewed reward policy, synthetic records, fixed CM completion contexts; pending timetable details are not invented.'}
    if english_controls:manifest.update(ordinary_english_exports=english_controls,
        english_correction={'train_examples':english_training['train_examples'],'epochs':len(english_training['history']),'selected_epoch':english_training['selected_epoch']})
    p.save(OUT/'release.json',manifest);p.save(ROOT/'data/active_objective_parameter_adapter.json',manifest)
    old_path=ROOT/'data/active_natural_language_adapter.json'
    old=json.loads(old_path.read_text())
    if not (OUT/'legacy_profile_manifest_before.json').exists():p.save(OUT/'legacy_profile_manifest_before.json',old)
    old.update(default_enabled=False,superseded_by='data/active_objective_parameter_adapter.json')
    p.save(old_path,old)
    destination=ROOT/'output/pdf/transcript-parameter-pipeline';destination.mkdir(parents=True,exist_ok=True)
    from pypdf import PdfReader,PdfWriter
    writer=PdfWriter()
    for c in cases:
        for page in PdfReader(ROOT/c['pdf']).pages:writer.add_page(page)
    with (destination/'Fictional_Transcripts.pdf').open('wb') as stream:writer.write(stream)
    summary=['TRANSCRIPT INPUT / PARAMETER-ONLY QWEN / EXTERNAL OPTIMIZER\n',
      'Three clearly fictional PDF transcripts reproduce the sample layout. The original student identity and record were not used in training.\n',
      'Before training: 0/3 transcript inputs and 0/3 prompted inputs passed the strict objective-parameter contract; rejected answers never reached the solver.\n',
      'Corrective training: 84 train, 8 validation, 8 separate record/weight export tests; three rank-8 QLoRA epochs. The six original failure prompts are familiar corrective retests.\n',
      'After training: 3/3 paired examples have identical validated objective parameters and identical externally optimized paths. Separate parameter exports: 8/8. No repair or fallback.\n',
      '\nRole boundary\n',
      'PDF/text parsing is external. Qwen returns only reward_parameters, course_relations, penalty_weights and stream_reward_multiplier.\n',
      'The program rejects profile fields, selected courses, timetables, paths, altered hard requirements, unknown relations and invalid weights.\n',
      'The external exact DP chooses the remaining course placements. Independent enumeration checks all 64 allowed elective assignments. MILP and language-model planning are not called.\n',
      '\nResults\n']
    for c in comparisons:
        r=runs[c['id']];summary.append(f"{c['id']}: {r['audit']['earned_credits']:g} credits; reward {c['objective']:.6f}; GE {r['audit']['distribution_GE_count']} across Areas 1-3; mathematics electives {r['audit']['elective_math_credits']:g} credits; optimality gap 0.\n")
        for s in r['semesters']:summary.append(f"  Year {s['year']} {s['semester']}: "+', '.join(s['selected_courses'])+f" ({s['credits']:g} credits)\n")
    summary += ['\nLimits and input handling\n',
      'The maximum is within each supplied fixed source-backed completion context, not over every possible curriculum reallocation. Contexts differ between students; compare input formats within each case.\n',
      'Saved Semester A/B evidence is repeated for simulation as authorised. 25 future credits have pending class details. These are curriculum plans, not confirmed registration timetables or official graduation certification.\n',
      'Zero-credit P requirements count as passed and add zero credits. In-progress rows are not past passes. A star is retained; it alone never determines degree-credit eligibility. The fictional language row explicitly says Non-degree. Actual unclear credit treatment requires confirmation.\n',
      'The eight scalar policy settings and 26 reviewed relations are familiar and fixed. Student state drives contextual rewards in external code; the model does not independently invent a different policy for each transcript.\n',
      'The separate tests use new synthetic records and user weight combinations, with familiar formatting and policy. This is not unseen-policy or real-student outcome validation.\n',
      '\nHow to use\nRun .\\run_transcript_optimizer.cmd F (or N or M). The old natural-input launcher now uses this parameter-only interface.\n',
      'For other PDFs/TXT files or ordinary student messages, the interface exports parameters and external facts. It does not fabricate a full-degree context when the supplied evidence is insufficient.\n',
      '\nFiles\nall_inputs.txt: exact transcript-mode user messages.\nafter_predictions.json: raw model parameter responses and paired solver results.\nafter_*_optimizer.json: external solver outputs, credit audits and maximum certificates.\ntraining/heldout_predictions.json: separate raw export tests.\n']
    if english_controls:summary += [f"\nOrdinary-English compatibility: {english_controls['passed']}/{english_controls['total']} new messages export parameters only. An additional {english_training['train_examples']}-row correction round retained all PDF examples; the observed English compatibility failure was explicitly taught.\n"]
    (OUT/'RESULTS.txt').write_text(''.join(summary),encoding='utf-8')
    (OUT/'raw_model_outputs.txt').write_text('\n\n'.join('CASE '+r['id']+' MODE '+r['mode']+'\n'+r['raw'] for r in predictions),encoding='utf-8')
    (OUT/'paired_inputs.txt').write_text('\n\n'.join(
      'CASE '+c['id']+' MODE '+mode+'\n'+json.dumps(p.model_messages(c['text'],c['preferences'],mode),ensure_ascii=False,indent=2)
      for c in cases for mode in ['transcript','prompted']),encoding='utf-8')
    # A readable validation report with source-format examples and actual solver output.
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Title2',fontName='Helvetica-Bold',fontSize=19,leading=23,spaceAfter=12,textColor=colors.HexColor('#193b50')))
    styles.add(ParagraphStyle(name='Body2',fontName='Helvetica',fontSize=9.5,leading=13,spaceAfter=9))
    styles.add(ParagraphStyle(name='Cell2',fontName='Helvetica',fontSize=8.5,leading=11))
    def para(text,style='Body2'):return Paragraph(text,styles[style])
    def table(rows,widths):
        t=Table([[para(escape(str(v)),'Cell2') for v in row] for row in rows],colWidths=widths,repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4eef2')),('VALIGN',(0,0),(-1,-1),'TOP'),
          ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#193b50'))]))
        return t
    story=[para('Transcript-to-optimiser validation','Title2'),
      para('We generated three fictional transcript PDFs using the sample\'s semester-table structure. The model receives extracted transcript text and ordinary user preferences. It supplies objective parameters only.'),
      table([['Component','Responsibility'],['PDF/text reader','Extracts course codes, grades, credits and semester facts outside the model'],
       ['Fine-tuned Qwen','8 scalar settings, 26 relation coefficients, 3 penalty weights and a stream multiplier'],
       ['Parameter validator','Rejects schedule/profile fields and changes to reviewed or hard requirements'],
       ['External exact DP','Selects the course-to-term assignments and returns the path and maximum certificate']],[118,393]),Spacer(1,12),
      para('<b>Correction and comparison.</b> Both input modes initially failed the strict contract. After 84-example training'+(' and a 120-example English compatibility correction' if english_controls else '')+', all three transcript/prompted pairs agree in their parameters and external plans. Original failures were taught and are corrective retests. Eight separate record/weight exports pass.'+(' Four new ordinary-English parameter exports also pass.' if english_controls else '')),
      table([['Profile','Parameter / path equality','Credits','Reward'],*[[r['id'],'Yes / Yes',122,f"{r['objective']:.6f}"] for r in comparisons]],[60,245,62,144]),Spacer(1,12),
      para('<b>What maximum means.</b> Exact DP optimises the supplied finite completion problem while existing source-backed allocations and mandatory placements remain fixed. An independent enumeration checks all 64 elective-placement combinations and confirms a zero gap. The programme does not claim a global optimum over every possible curriculum reallocation.'),
      para('<b>Scope.</b> The reviewed policy and formatting families are familiar. Eight scalar settings and 26 relations remain shared; student state changes the computed course rewards. Fixed contexts differ across profiles. These tests measure input-format consistency and tool handoff, not causal learning benefits.'),
      para('<b>Timetable limits.</b> Each plan passes the encoded 122-credit, GE, mathematics-elective and selected-stream audit. The authorised repeated A/B snapshots are a simulation assumption. Twenty-five future credits retain pending class details; no times or CRNs are invented.')]
    for c in cases:
        r=runs[c['id']];history=c['source_profile']['historical_transcript'];ge=[x['id'] for x in history if x['id'] in ['GE2260','GE1105','GE1113','GE1305','GE2134']]
        story += [PageBreak(),para('Profile '+c['id']+': optimiser output','Title2'),
          para('<b>Input.</b> Fictional Year-2 Computing Mathematics student; 15 credits in Year 1A and 15 in Year 1B. Distributional GE history: '+', '.join(ge)+'. Desired stream: '+escape(c['preferences']['desired_stream'])+'.'),
          para('The zero-credit P row is a completed requirement. The language row has an explicit fictional Non-degree remark. MA2503 is in progress and is not a prior pass. Source facts are parsed outside Qwen.'),
          table([['Term','Courses selected by external DP','Credits'],*[[f"Y{s['year']}{s['semester']}",', '.join(s['selected_courses']),s['credits']] for s in r['semesters']]],[48,410,53]),Spacer(1,12),
          para(f"<b>Audit:</b> {r['audit']['earned_credits']:g} total credits; {r['audit']['distribution_GE_count']} distributional GEs spanning Areas 1-3; {r['audit']['elective_math_credits']:g} mathematics-elective credits; encoded core, project, free-elective and chosen-stream checks pass."),
          para(f"<b>Objective:</b> {r['discounted_academic_reward']:.6f}. Exact maximum in the supplied completion context, independently checked over {r['completion_optimality_certificate']['assignments_checked']} assignments. Both model input formats produce this same path."),
          para('MA4530 A/B are allocations of one six-credit year-long project. Pending class details and catch-up requirements remain subject to confirmation. No official registration or degree-award claim is made.')]
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawString(42,22,'Fictional tests - Qwen parameters, external dynamic programming');canvas.drawRightString(553,22,str(doc.page))
    report=destination/'Transcript_Parameter_Test_Report.pdf'
    SimpleDocTemplate(str(report),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=35,bottomMargin=36).build(story,onFirstPage=footer,onLaterPages=footer)
    archive=OUT/'Transcript_Parameter_Test_Package.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for file in [destination/'Fictional_Transcripts.pdf',report,OUT/'RESULTS.txt',OUT/'all_inputs.txt',OUT/'paired_inputs.txt',OUT/'raw_model_outputs.txt',OUT/'after_comparison.json',OUT/'release.json',OUT/'software_checks.log']:
            z.write(file,file.name)
        for file in (OUT/'fixtures').glob('*.pdf'):z.write(file,'individual_transcripts/'+file.name)
        for file in OUT.glob('after_*_optimizer.json'):z.write(file,'optimizer_outputs/'+file.name)
        for name in ['training/heldout_predictions.json','training/heldout_evaluation.json','training/training.json',
                     'english-correction/training.json','english-correction/control_evaluation.json',
                     'english-correction/control_predictions.json','english_input_demo/model_messages.json',
                     'english_input_demo/raw_model_output.txt','english_input_demo/model_parameters.json',
                     'english_input_demo/validation.json']:
            file=OUT/name
            if file.exists():z.write(file,'audit/'+name)
    print(json.dumps({'activated':True,'pairs':len(comparisons),'heldout':holdout,'output_pdf_directory':str(destination),'package':str(archive)},indent=2))

if __name__=='__main__':main()
