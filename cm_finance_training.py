"""Build, fine-tune/evaluate, and guard the CM finance-background task."""
import argparse
import copy
import contextlib
import gc
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import project_runtime
from cm_background_policy import target, FINANCE_INTRO, FINANCE_ADVANCED
from programme_policy import exact, policy, allowed
from programme_training_v6 import SYSTEM as PRIOR_SYSTEM

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/cm-finance-background'
REPORT=ROOT/'reports/cm-finance-background'
ADAPTER='adapters/cm-finance-background'
PARENT='adapters/cm-cs-programme-v6'
SYSTEM=PRIOR_SYSTEM+''' For task CM_finance_background, apply the user-authorised advisory planning rule: for CM only, document-allowed EF and CS course prerequisites are assumed waived unless cm_ef_cs_prerequisite_waiver=false. Missing those prerequisite passes adds zero extra penalty. This does not grant a pass, a waiver approval, a stream slot, or registration. Preserve source prerequisite facts, programme membership, exclusions, section restrictions and timetable constraints. Prioritise actual finance preparation (passed finance GE, EF, specified finance MA/CB/FB courses, or explicitly declared study), not a missing formal prerequisite. Failed/in-progress/withdrawn courses do not count as finance study. Explicit stream choices override inferred interest. Return only the requested output fields.'''

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def active_adapter():
    manifest=ROOT/'data/active_programme_adapter.json'
    return json.loads(manifest.read_text(encoding='utf-8'))['adapter'] if manifest.exists() else PARENT

def messages(profile,code):
    from course_relations import check_rules
    # The background assessor needs study evidence, not unrelated scheduling
    # preferences. Materialise the default exactly as in its training inputs.
    relevant={'programme','completed_courses','cm_ef_cs_prerequisite_waiver','finance_background',
              'GE_history','transcript','course_results','failed_courses','in_progress_courses','withdrawn_courses'}
    profile={k:v for k,v in profile.items() if k in relevant}
    profile.setdefault('cm_ef_cs_prerequisite_waiver',True)
    major=profile['programme']
    query={'task':'CM_finance_background','profile':profile,'course_code':code,
      'document_allowed':allowed(major,code),'source_rules':check_rules(code,profile.get('completed_courses',[])),
      'finance_preparation_rubric':{'introductory_courses':sorted(FINANCE_INTRO),'advanced_courses':sorted(FINANCE_ADVANCED),
       'other_advanced':'Any passed EF course','mismatch':{'none':.45,'introductory':.15,'advanced':.05},
       'priority_multiplier':{'none':1.,'introductory':3.,'advanced':3.},
       'declared_study':'finance_background=true or finance_background.studied=true is introductory unless passed evidence is advanced'},
      'output_fields':list(target(profile,code))}
    return [{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(query)}]

def build():
    if (DATA/'train.jsonl').exists():raise RuntimeError('Dataset already exists; retain the frozen split instead of overwriting.')
    rng=random.Random(20261121)
    backgrounds=[[],['GE2260'],['GE1202'],['EF3320'],['MA3521'],['GE1105'],['GE2340'],['CB3410'],['GE2260','MA3521']]
    rows=[]
    for major in ['CM','CS']:
      for code in ['EF3320','EF4821','CS4486','CS4487','MA3521','CS2115']:
       for index,done in enumerate(backgrounds):
        for mode in [True,False]:
         p={'programme':major,'completed_courses':sorted(set(done+(['MA1301'] if index%2 else []))),
            'cm_ef_cs_prerequisite_waiver':mode}
         if index==5:p['finance_background']={'studied':True,'topics':['time value of money','bonds']}
         if index==6:p['finance_background']=False
         if index==1 and code in ['CS4486','CS4487']:p['GE_history']=[{'course_code':'GE2260','grade':'F'}]
         expected=target(p,code)
         rows.append({'id':f'finance:{major}:{code}:{index}:{mode}','task':'CM_finance_background',
                      'profile':p,'course_code':code,'messages':messages(p,code)+[{'role':'assistant','content':json.dumps(expected)}]})
    rng.shuffle(rows)
    splits={'test':rows[:20],'validation':rows[20:44],'train':rows[44:]}
    # Keep extraction, exact stream counting and membership in the training mix.
    replay=[json.loads(x) for x in (ROOT/'data/programme-v6/train.jsonl').read_text(encoding='utf-8').splitlines()]
    eligible=[r for r in replay if r['task'] in ['stream','membership','course_rules','section']]
    rng.shuffle(eligible)
    for name,items in [('train',eligible[:64]),('validation',eligible[64:72])]:
        splits[name]+=[{**r,'id':'replay:'+r['id']} for r in items]
    # Explicit complete-CM stream replay fixes counting, not merely the new waiver.
    from programme_policy import context,stream_result
    for name,done in [('Enriched Mathematics',['MA3523','MA4542','MA4545','MA4546']),
                      ('Financial Mathematics',['MA3521','MA4529','MA4537','EF3320'])]:
        for i in range(4):
            query={'task':'stream',**context('CM',done,name),
              'background_courses_not_stream_slots':['MA1301','MA2508','GE2260'],
              'note':'Background study is not a stream slot; a complete stream earns no additional alternative reward.',
              'example':i}
            splits['train'].append({'id':f'complete:{name}:{i}','task':'stream','messages':[
              {'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(query)},
              {'role':'assistant','content':json.dumps(stream_result('CM',done,name))}]})
    DATA.mkdir(parents=True,exist_ok=True)
    for name,items in splits.items():
        (DATA/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in items),encoding='utf-8')
    cases=list(splits['test'])
    # Previously used queries are explicitly regression diagnostics, not new holdouts.
    old=json.loads((ROOT/'reports/programme-v6/evaluation_cases.json').read_text(encoding='utf-8'))
    regressions=[r for r in old if r['task'] in ['stream','membership']]
    save(REPORT/'evaluation_cases.json',cases+[{**r,'id':'regression:'+r['id']} for r in regressions])
    save(REPORT/'protocol.json',{'seed':20261121,'splits':{k:len(v) for k,v in splits.items()},
      'new_heldout_queries':20,'historical_regression_queries':len(regressions),
      'source_adapter':PARENT,'before_after_same_quantised_base':True,
      'scope':'Synthetic user-policy distillation with profile/candidate combinations split before training. Familiar facts/rubric, not independent real-student or university-waiver validation.',
      'waiver_authority':'User instruction; CM advisory planning only. Registration approval remains unverified.',
      'finance_background_scores':{'none':.45,'introductory':.15,'advanced':.05},
      'policy':'No additional missing-prerequisite penalty for document-allowed CM EF/CS courses; preserve all other source constraints.'})
    print(json.dumps({k:len(v) for k,v in splits.items()}))

def evaluate(label):
    import torch
    from inference import load,generate
    sys.setrecursionlimit(5000)
    torch.set_num_threads(8)
    os.environ['CITYU_QUANTIZE_4BIT']='1'
    adapter=PARENT if label=='before' else ADAPTER
    cases=json.loads((REPORT/'evaluation_cases.json').read_text(encoding='utf-8'))
    tok,model=load(adapter);results=[]
    for i in range(0,len(cases),2):
        group=cases[i:i+2]
        # Single unpadded requests avoid this Windows Torch build's nested-vmap
        # mask failure. Both checkpoints use the identical decoding protocol.
        raw=[generate(tok,model,r['messages'][:-1],max_tokens=420) for r in group]
        for r,response in zip(group,raw):
            expected=json.loads(r['messages'][-1]['content'])
            try:value=json.loads(response)
            except ValueError:value=None
            results.append({'id':r['id'],'task':r['task'],'messages':r['messages'][:-1],
              'expected':expected,'raw_model_response':response,'passed':exact(expected,value)})
        save(REPORT/(label+'_predictions.json'),results)
        print(label,len(results),sum(r['passed'] for r in results),flush=True)
    summary={}
    for name,part in [('new_heldout',[r for r in results if not r['id'].startswith('regression:')]),
                      ('historical_regression',[r for r in results if r['id'].startswith('regression:')])]:
        summary[name]={'passed':sum(r['passed'] for r in part),'total':len(part)}
    save(REPORT/(label+'_evaluation.json'),summary)
    if label=='after':
        diagnostic=[]
        folder=DATA/'examples'
        for name in ['no_finance','finance_GE','self_reported_finance','advanced_finance','failed_finance_GE','strict_prerequisites']:
            profile=json.loads((folder/(name+'.json')).read_text(encoding='utf-8'))
            expected=target(profile,'EF3320')
            response=generate(tok,model,messages(profile,'EF3320'),max_tokens=420)
            try:value=json.loads(response)
            except ValueError:value=None
            diagnostic.append({'id':name,'input_profile':profile,'expected':expected,'raw_model_response':response,'passed':exact(expected,value)})
            save(REPORT/'profile_default_diagnostics.json',{'scope':'Six user-facing/default-input diagnostics over familiar policy facts; not an independent holdout.',
                 'results':diagnostic,'passed':sum(r['passed'] for r in diagnostic),'total':len(diagnostic)})
            print('default_input_diagnostic',name,diagnostic[-1]['passed'],flush=True)
    del model;gc.collect();torch.cuda.empty_cache()

def infer(profile,code):
    if not code:raise ValueError('Specify --course, for example --course EF3320')
    from inference import load,generate
    expected=target(profile,code)
    with contextlib.redirect_stdout(sys.stderr):
        tok,model=load(active_adapter());raw=generate(tok,model,messages(profile,code),max_tokens=420)
    try:parsed=json.loads(raw)
    except ValueError:parsed=None
    accepted=exact(expected,parsed)
    return {'input_profile':profile,'course_code':code,'raw_model_response':raw,'model_output_accepted':accepted,
            'verified_policy_output':expected,'policy_fallback_used':not accepted,'registration_verified':False}

def release():
    after=json.loads((REPORT/'after_evaluation.json').read_text(encoding='utf-8'))
    before=json.loads((REPORT/'before_evaluation.json').read_text(encoding='utf-8'))
    diagnostic=json.loads((REPORT/'profile_default_diagnostics.json').read_text(encoding='utf-8'))
    training=json.loads((REPORT/'training.json').read_text(encoding='utf-8'))
    good=after['new_heldout']['passed']>=18 and after['historical_regression']['passed']>=before['historical_regression']['passed'] and diagnostic['passed']==6
    value={'adapter':ADAPTER,'source_adapter':PARENT,'training_performed':training['status']=='complete',
      'training_method':training['training_method'],'selected_epoch':training['selected_epoch'],
      'sha256':hashlib.sha256((ROOT/ADAPTER/'adapter_model.safetensors').read_bytes()).hexdigest(),
      'evaluation':{'before':before,'after':after},'accepted_for_activation':good,
      'default_profile_diagnostics':{'passed':diagnostic['passed'],'total':diagnostic['total'],'independent_holdout':False},
      'model_role':'CM finance-background and advisory EF_CS prerequisite-waiver policy with source-task replay',
      'raw_outputs_require_validation':True,'official_registration_or_graduation_verified':False,
      'policy':'data/cm-finance-background/policy.json',
      'waiver_authority':'User-provided planning assumption, not university approval evidence'}
    save(REPORT/'release.json',value)
    if good:
        old=json.loads((ROOT/'data/active_programme_adapter.json').read_text(encoding='utf-8'))
        save(REPORT/'previous_active_adapter.json',old)
        save(ROOT/'data/active_programme_adapter.json',value)
    print(json.dumps(value,indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['build','before','after','release']);args=a.parse_args()
    if args.command in ['before','after']:evaluate(args.command)
    else:globals()[args.command]()
