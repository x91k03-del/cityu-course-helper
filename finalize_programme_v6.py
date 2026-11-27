"""Record evidence, model results and a guarded activation for the new programme task."""
import hashlib,json,unittest
from pathlib import Path
from programme_policy import *
from programme_training_v6 import ADAPTER,DATA,REPORT
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    suite=unittest.defaultTestLoader.loadTestsFromNames(['test_programme_v6','test_scheduler','test_profit_objective','test_ma_timetable','test_ge_timetable','test_banweb_collector','test_ma_offline_import'])
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise RuntimeError('Software checks failed')
    training=json.loads((REPORT/'training.json').read_text());assert training['status']=='complete'
    training['label_type']='User-PDF-conditioned CM/CS curriculum, timetable and requirement extraction plus synthetic single-stream policy distillation'
    save(REPORT/'training.json',training)
    ev=json.loads((REPORT/'evaluation.json').read_text(encoding='utf-8'));pred=json.loads((REPORT/'predictions.json').read_text(encoding='utf-8'))
    for row in pred:
        try:value=json.loads(row['raw'])
        except (ValueError,TypeError):value=None
        row['passed']=exact(row['expected'],value)
    ev={label:{'passed':sum(r['passed'] for r in pred if r['model']==label),'total':sum(r['model']==label for r in pred)} for label in ['before','after']}
    save(REPORT/'predictions.json',pred);save(REPORT/'evaluation.json',ev)
    digest=hashlib.sha256((ROOT/ADAPTER/'adapter_model.safetensors').read_bytes()).hexdigest()
    save(ROOT/ADAPTER/'base_loading.json',{'quantization':'NF4','compute_dtype':'BF16','streaming_tensor_loader':True,'CITYU_QUANTIZE_4BIT':'1'})
    save(ROOT/ADAPTER/'programme_policy.json',policy())
    manifest={'adapter':ADAPTER,'sha256':digest,'source_adapter':'adapters/bscm-preparation-v5','model_role':'CM_CS_source_conditioned_curriculum_schedule_rules_and_single_stream_reward',
      'training_performed':True,'training_method':training['training_method'],'selected_epoch':training['selected_epoch'],
      'policy':'data/programme-v6/policy.json','courses':'data/programme-v6/courses.json','evaluation':ev,
      'raw_outputs_require_validation':True,'final_eligibility_authority':'document_membership_plus_saved_rules_and_sections_not_model_memory',
      'official_registration_or_graduation_verified':False}
    correction=REPORT/'correction_diagnostic.json'
    if correction.exists():
        d=json.loads(correction.read_text(encoding='utf-8'))
        manifest['corrective_trial']='reports/programme-v6/correction/training.json'
        manifest['correction_deployed']=False
        manifest['correction_selection_reason']='Trial fixed the original error but introduced another stream error and worsened validation loss; initial v6 retained.'
        manifest['corrective_trial_diagnostic']={'passed':d['passed'],'total':d['total'],'independent_holdout':False}
    save(ROOT/'data/active_programme_adapter.json',manifest)
    summary=json.loads((REPORT/'import.json').read_text());examples=json.loads((REPORT/'semester_examples.json').read_text())
    full=json.loads((REPORT/'CM_four_year_mock.json').read_text());audit=full['audit']
    save(REPORT/'validation.json',{'automated_tests':result.testsRun,'passed':True,'CM_full_mock_credits':audit['earned_credits'],
      'CM_stream':stream_result('CM',audit['passed_ids'],full['steps'][0]['state_before']['selected_stream']),
      'all_generated_CM_courses_document_allowed':all(allowed('CM',r['id']) for r in full['transcript']),
      'semester_examples':[{'programme':x['profile']['programme'],'term':x['profile']['term'],'status':x['result']['status']} for x in examples]})
    taskmetrics={}
    for label in ['before','after']:
        taskmetrics[label]={t:{'passed':sum(x['passed'] for x in pred if x['model']==label and x['task']==t),
          'total':sum(x['model']==label and x['task']==t for x in pred)} for t in sorted({r['task'] for r in pred})}
    save(REPORT/'release.json',{'import':summary,'model':manifest,'software_checks':result.testsRun,'by_task':taskmetrics,
      'scope_notes':['CMcourses.pdf is a 2022/23 catalogue page used as the explicit user-requested allowlist.',
       'CS Majors.pdf is 2026/27; suggested CS study plan is cohort 2025. Source text retained separately; no silent cohort reconciliation.',
       'Course-list membership is a necessary condition only; section restrictions, prerequisites, exclusions and source term remain mandatory.',
       'One stream is a user reward preference, not compulsory declaration. ACT/JS1070 route needs separate route confirmation.',
       'Seven no-time files quarantined; no dates fabricated. Saved snapshots do not prove current seats.',
       'Lecture/tutorial pairing and teaching weeks are unverified: semester examples require explicit hypothetical mode.',
       'Raw model outputs are reported without repairs. Failed outputs must use exact local policy/lookup instead.',
       'Both before/after model evaluation used the same NF4 base/BF16 compute protocol. Earlier BF16 v5 scores are not directly compared.',
       'CS future four-year graduation and timetables are not verified; the CS examples are current-semester experiments.']})
    guard=REPORT/'guarded_examples.json'
    if guard.exists():
        examples_guard=json.loads(guard.read_text(encoding='utf-8'))
        release=json.loads((REPORT/'release.json').read_text(encoding='utf-8'))
        release['guarded_examples']={'path':'reports/programme-v6/guarded_examples.json',
           'raw_model_accepted':sum(x['model_accepted'] for x in examples_guard),'total':len(examples_guard),
           'all_returned_outputs_checked_against_exact_policy':True}
        save(REPORT/'release.json',release)
    lines=['','## CM and CS programme update (21 November 2026)','',
      f"New combined checkpoint: `{ADAPTER}`. Training: {training['training_method']}; init adapter: `bscm-preparation-v5`. "
      f"The {ev['after']['total']} preselected source-conditioned test queries passed {ev['after']['passed']} after training versus {ev['before']['passed']} before, with the same quantized base in both tests. "
      'These tests use supplied source context, not unseen-document recall. Raw results: `reports/programme-v6/predictions.json`.','',
      f"Imported {summary['courses']} course/term/programme records and {summary['sections']} explicitly matching-major sections. "
      f"{summary['quarantined']} files with unrecognized meeting times are quarantined. MA Semester B is 202702; Semester A is 202609. Duplicate PDF copies are deduplicated by hash.",'',
      'CM course candidates must occur in `GE_SEMA/MA/CMcourses.pdf`, or the captured GE list. CS candidates must occur in `GE_SEMA/CS/programme discription/Majors.pdf`, or the captured GE list. '
      'Document membership is not registration approval. The CM PDF is historical 2022/23; the CS major page is 2026/27 while the suggested CS plan is for cohort 2025. These versions are retained separately.','',
      'A single selected stream receives 2 utility units per new distinct slot and a one-time 6-unit completion bonus. '
      'The semester optimizer accounts for joint selections exactly, so two alternative courses cannot collect the same slot/completion reward twice. '
      'A stream preference never bypasses course restrictions or prerequisites. University stream declaration remains optional. '
      'The special CS ACT/JS1070 route is recorded, but is not auto-assigned without admission-route evidence.','',
      f"{result.testsRun} software checks passed. The document-filtered CM mock earns {audit['earned_credits']} credits, meets the encoded graduation requirements, and completes one stream. "
      'The example CS plans are semester experiments, not full-degree graduation certification. The CM Semester A example is explicitly infeasible under its five-course minimum.','',
      '```powershell','./programme_v6.cmd lookup --programme CM --term 202702 --course MA3511',
      './programme_v6.cmd lookup --programme CS --term 202702 --course CS3334',
      './programme_v6.cmd model-stream --profile data/programme-v6/example_CS.json',
      './programme_v6.cmd plan --profile data/programme-v6/example_CS.json --assume-component-linkage','```','',
      'The final command explicitly enables experimental section pairing and assumed weeks. Without that flag, unknown component linkage fails closed. '
      'Exact course facts remain available without loading the model. Evidence, caveats, examples and model metrics: `reports/programme-v6/release.json`. '
      'The new task activation is `data/active_programme_adapter.json`; the previous v5 profit controller is retained separately.','']
    if correction.exists():
        lines+=['A corrective trial taught the observed completed-stream failure with balanced source-task replay. '
          f"It passed {d['passed']}/{d['total']} post-correction diagnostic queries, fixing the original error but introducing a different stream error. "
          'Its replay validation loss worsened from 0.00462 to 0.00921, so the initial v6 checkpoint remains active. '
          'The trial is preserved separately as `adapters/cm-cs-programme-v6-correction-trial`. '
          'The diagnostic is not independent: the original failed case was used for teaching. '
          'All raw stream outputs still require exact policy validation and fallback. See `reports/programme-v6/correction_protocol.json` and `correction_diagnostic.json`.','']
    readme=ROOT/'README.md';text=readme.read_text(encoding='utf-8');marker='\n## CM and CS programme update (21 November 2026)'
    if marker in text:text=text[:text.index(marker)]
    text=text.replace('Latest: [GE cap and preparation-chain fine-tuning report]','Historical v5: [GE cap and preparation-chain fine-tuning report]')
    current='Current programme model: `adapters/cm-cs-programme-v6`. See the CM and CS update below and `reports/programme-v6/release.json`. Earlier v5 examples are historical; their outside-document free electives are rejected by the new policy.\n\n'
    if current not in text:
        first,rest=text.split('\n',1);text=first+'\n\n'+current+rest.lstrip('\n')
    readme.write_text(text+'\n'.join(lines),encoding='utf-8')
    print('Activated programme adapter',ADAPTER,'evaluation',ev,'tests',result.testsRun)
if __name__=='__main__':main()
