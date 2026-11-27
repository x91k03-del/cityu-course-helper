"""Write a source-linked MA timetable report and reproducible example checks."""
import json
from ma_timetable import ROOT,DATA,REPORT,read,write,lookup,check

def examples():
    results=[]
    def case(ident,question,command,actual,expected):
        results.append({'id':ident,'question':question,'command':command,'expected':expected,
                        'actual':actual,'passed':actual==expected,'method':'deterministic_local_source_and_rule_check'})
    case('missing_conjunct','Is MA1503 alone sufficient for the MA2508 preparation expression?',
         '.\\ma_timetable.cmd check --course MA2508 --completed MA1503',
         check('MA2508',['MA1503'])['requirement_expression_satisfied'],False)
    case('both_conjuncts','Does the MA1503 + MA1508 branch satisfy MA2508?',
         '.\\ma_timetable.cmd check --course MA2508 --completed MA1503,MA1508',
         check('MA2508',['MA1503','MA1508'])['requirement_expression_satisfied'],True)
    case('single_or_branch','Does MA1201 satisfy a MA2508 preparation branch?',
         '.\\ma_timetable.cmd check --course MA2508 --completed MA1201',
         check('MA2508',['MA1201'])['requirement_expression_satisfied'],True)
    case('outer_conjunct','Is MA3526 alone sufficient for MA4542?',
         '.\\ma_timetable.cmd check --course MA4542 --completed MA3526',
         check('MA4542',['MA3526'])['requirement_expression_satisfied'],False)
    case('nested_or','Do MA2508 and MA3524 satisfy the MA4542 preparation expression?',
         '.\\ma_timetable.cmd check --course MA4542 --completed MA2508,MA3524',
         check('MA4542',['MA2508','MA3524'])['requirement_expression_satisfied'],True)
    case('exclusive','Does completed MA1502 conflict with MA2508?',
         '.\\ma_timetable.cmd check --course MA2508 --completed MA1201,MA1502',
         check('MA2508',['MA1201','MA1502'])['exclusive_course_conflicts'],['MA1502'])
    case('cohort','Does cohort 2025 pass the MA1502 CB1 cohort condition?',
         '.\\ma_timetable.cmd check --course MA1502 --section CB1 --no-completed-courses --programme BSCSIU4 --cohort 2025',
         check('MA1502',[],section='CB1',programme='BSCSIU4',cohort='2025')['section_checks'][0]['encoded_conditions_satisfied'],False)
    case('unknown_completion','Does being a CM student establish MA2508 prerequisite completion?',
         '.\\ma_timetable.cmd check --course MA2508',
         check('MA2508')['requirement_expression_satisfied'],None)
    case('nil_without_history','Is a Nil preparation expression satisfied even when course history is unknown?',
         '.\\ma_timetable.cmd check --course MA1502',
         check('MA1502')['requirement_expression_satisfied'],True)
    case('no_cm_section','Is an explicitly CM-listed section absent from this saved MA2510 page?',
         '.\\ma_timetable.cmd lookup --course MA2510',
         lookup('MA2510')['no_cm_section_in_saved_source'],True)
    case('multiple_options','Are all CM alternatives for MA1300 retained?',
         '.\\ma_timetable.cmd lookup --course MA1300',
         [s['section'] for s in lookup('MA1300')['sections']],['C01','T01','T02'])
    write(REPORT/'test_examples.json',results)
    return results

def main():
    records=read(DATA/'courses.json');manifest=read(REPORT/'import.json');dataset=read(REPORT/'dataset.json')
    ex=examples();training=read(REPORT/'training.json') if (REPORT/'training.json').exists() else None
    evaluation=read(REPORT/'evaluation.json') if (REPORT/'evaluation.json').exists() else None
    lines=['# CM MA timetable and requirement report','',
        'The 17 supplied AIMS course PDFs were imported locally for Semester A 2026/27 (term 202609). '
        'The source pages were captured on 15 November 2026. This snapshot does not establish current registration availability.','',
        f"The import selected **{manifest['selected_sections']} sections / {manifest['selected_meetings']} meetings across {manifest['courses_with_cm_sections']} courses** and excluded {manifest['excluded_sections']} section records. "
        'Every selected section explicitly includes the exact major token CM. Shared lists containing CM are retained, alongside their programme/cohort conditions. '
        'No other-major-only, not-for-CM, minor-only or unspecified section clocks are included in the new MA training targets.','',
        '## Captured CM schedules','',
        'Each row is a section/component record. Multiple tutorial options are alternatives; valid lecture/tutorial bundles have not been verified. '
        'Date ranges do not establish teaching weeks or holiday exceptions.','',
        '| Course | CRN / section | Meetings | Date range(s) | Additional restrictions |',
        '| --- | --- | --- | --- | --- |']
    for c in records:
        for s in c['sections']:
            meetings='; '.join(f"{m['day']} {m['start_time']}-{m['end_time']} {m['building']} {m['room']}" for m in s['meetings'])
            dates='; '.join(dict.fromkeys(m['start_date']+' to '+m['end_date'] for m in s['meetings']))
            rs='; '.join(r['mode']+' for '+r['field']+': '+', '.join(r['values']) for r in s['restrictions'] if r['field']!='major') or 'Major CM listed; other individual eligibility not verified'
            lines.append(f"| {c['course_code']} | {s['crn']} / {s['section']} | {meetings} | {dates} | {rs} |")
    lines+=['','No explicitly CM-listed timetable is present in these six saved pages: '+', '.join(manifest['courses_without_cm_sections'])+'. '
            'Their rules remain queryable. This does not establish a permanent ban or the absence of another authorized offering.','',
            '## Prerequisites/precursors and exclusive courses','',
            'The source uses a combined **Pre-requisites/precursors** heading. It does not distinguish strict prerequisites from precursors. '
            'The helper preserves the wording and Boolean logic without claiming that distinction is verified. '
            'An exclusive course is a separate registration condition; passing a preparation expression does not override it.','',
            '| Course | Source requirement wording | Exclusive courses | CM sections |',
            '| --- | --- | --- | --- |']
    for c in records:
        source=ROOT/'GE_SEMA/MA'/(c['course_code']+'.pdf')
        lines.append(f"| [{c['course_code']}]({source.as_posix()}) | {c['requirement_text']} | {', '.join(c['exclusive_courses']) or 'Nil'} | {', '.join(s['section'] for s in c['sections']) or 'None captured'} |")
    lines+=['','MA2508/MA2510 require **MA1201 OR MA1301 OR (MA1503 AND MA1508)**. '
            'MA4542 requires **MA2508 AND (MA3526 OR MA3524)**. The local rule evaluator does not flatten these into a single OR list. '
            'Missing completion data remain unknown, and a BSCM major or year never supplies a passed-course history. '
            'A Nil preparation expression is satisfied without completed courses, but exclusive-course conflicts still remain unknown without a completion history.','',
            '## Training','',
            f"Dataset sizes: {dataset['examples']['train']} training, {dataset['examples']['validation']} validation and {dataset['examples']['test']} test examples. "
            'The new MA facts are mixed with 160 prior GE/BSCM examples. The previous datasets and adapters remain intact. '
            'All captured facts are intentionally taught; the evaluation tests learned-fact paraphrases and evidence extraction, not unseen-fact generalization.','']
    if training and training['status']=='complete':
        lines += [f"Completed {training['args']['epochs']} continued-training epochs on Qwen3-8B with rank-8 LoRA, initialized from `adapters/bscm-timetable`. "
                  f"The selected checkpoint is epoch {training['selected_epoch']}, saved separately as `adapters/bscm-ma-timetable`. "
                  f"Training took {training['seconds']/60:.1f} minutes; peak GPU allocation was {training['peak_gpu_allocated_gb']:.2f} GiB.",'',
                  '| Epoch | Training loss | Validation loss |','| --- | --- | --- |']
        for h in training['history']:lines.append(f"| {h['epoch']} | {h['train_loss']:.4f} | {h['validation_loss']:.4f} |")
    else:lines+=['Training is still running or has not completed. See `reports/ma-timetable/training.json`.']
    lines+=['','## Raw model evaluation','',
            'Prior = the existing GE/BSCM timetable adapter. New = the MA-continued adapter. '
            'A pass requires exact decoded JSON equality, without fixing answers or substituting the lookup. '
            'Recall prompts omit source context; grounded prompts supply it. Reworded evaluation prompts do not prove that source facts were unseen.','']
    if evaluation:
        lines+=['| Task | Prior | New |','| --- | --- | --- |']
        for task in evaluation['prior']:
            a=evaluation['prior'][task];b=evaluation['ma_tuned'][task]
            lines.append(f"| {task} | {a['passed']}/{a['total']} | {b['passed']}/{b['total']} |")
        failures=[r for r in read(REPORT/'predictions.json') if r['model']=='ma_tuned' and not r['passed']]
        lines+=['',f"The new raw model failed {len(failures)} exact-output checks. "
                'Exact source lookup and deterministic rule evaluation are the deployed path for schedule/requirement questions. '
                'Unchecked model memory is diagnostic, not an authority for registration planning. '
                'Full responses and fixed test IDs are saved in `predictions.json` and `evaluation_plan.json`.']
        recall_failures=[r for r in failures if r['task'] in ['rules_recall','schedule_recall']]
        if recall_failures:
            lines[4:4]=['**Model-memory limitation:** the fine-tuned adapter still gives incorrect ungrounded course facts. '
                        'The default helper answers schedule and requirement questions from exact saved records. '
                        'Fine-tuning completion is not proof of factual memorization.','']
            example=next((r for r in recall_failures if r['id']=='MA2508:rules3'),None)
            if example:
                try:
                    actual=json.loads(example['raw_response']).get('requirement_text')
                    lines+=['',f"For example, its ungrounded MA2508 requirement answer was `{actual}`, while the source requires "
                            f"`{example['expected']['requirement_text']}`. The source lookup retains the complete expression."]
                except (ValueError,AttributeError):pass
        reused=sum(r.get('reused_prior_result',False) for r in read(REPORT/'predictions.json'))
        if reused:
            lines+=['',f"{reused} prior-adapter results were reused after matching the unchanged prompt fingerprints, expected targets and adapter weights hash. "
                    'The added Nil/unknown-history case and all final-adapter checks were generated fresh.']
    else:lines+=['Before/after model evaluation is pending.']
    verification=read(REPORT/'validation.json') if (REPORT/'validation.json').exists() else None
    if verification:
        lines+=['',f"Automated parser/rule regression checks: **{verification['automated_parser_and_rule_tests']} passed**, recorded in `reports/ma-timetable/validation.json`. "
                'These check imported evidence and software behavior; they are separate from generated model answers.']
    lines+=['','## Reproducible example checks','',
            f"The local source/rule examples passed **{sum(x['passed'] for x in ex)}/{len(ex)}**. "
            'These are software/source checks, not raw-model accuracy. Commands and expected/actual results are in `reports/ma-timetable/test_examples.json`.','',
            '| Example | Expected result | Result |','| --- | --- | --- |']
    for x in ex:lines.append(f"| {x['question']} | `{json.dumps(x['expected'])}` | {'PASS' if x['passed'] else 'FAIL'} |")
    lines+=['','## Source traceability and limits','',
            'Every normalized course has its source PDF path and SHA-256 hash. Section and meeting records preserve physical PDF page numbers. '
            'CM-only filtering can be rebuilt from the original files. Source URLs embedded in those PDFs were read as term evidence; no CityU requests were made.','',
            'Programme/cohort restrictions are retained; identity and completed-course evidence are not inferred. '
            'Current seats, permission overrides, component linkage, holidays, teaching weeks and complete university eligibility remain unverified. '
            'Historical FULL/availability values are source metadata and are not taught as current seat availability. '
            'The importer does not auto-register courses or pass unverified section bundles into the optimizer.','',
            'Usage: [MA_CM_UPDATE.md](MA_CM_UPDATE.md). Parsed data: `data/ma-timetable/courses.json` and `sections.json`. '
            'Provenance: `reports/ma-timetable/import.json`. Raw training and model outputs remain separate from exact lookup results.']
    (ROOT/'MA_CM_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Wrote MA_CM_REPORT.md and reports/ma-timetable/test_examples.json')

if __name__=='__main__':main()
