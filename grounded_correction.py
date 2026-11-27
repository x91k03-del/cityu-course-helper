"""A preserved second trial correcting EF input types/scaling and over-refusal."""
import argparse,copy,hashlib,json,random,shutil
from pathlib import Path
import project_runtime
import timetable_grounded_training as task
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/timetable-grounded-correction';REPORT=ROOT/'reports/timetable-grounded-correction'
ADAPTER='adapters/timetable-grounded-correction'

def build():
    if (DATA/'train.jsonl').exists():raise RuntimeError('Correction dataset already frozen.')
    DATA.mkdir(parents=True);REPORT.mkdir(parents=True,exist_ok=True)
    rows=[]
    def add(label,weight,code,mode):
        p={'programme':'CM','programme_code':'BSCSIU4','cohort':2025,'year':2,'term':'202702' if code=='EF3320' else '202609',
          'completed_courses':[],'weights':{'background_mismatch':weight,'difficulty':1.,'workload':1.}}
        if mode=='none':p['finance_background']=False
        elif mode=='declared':p['finance_background']=True
        elif mode=='declared_object':p['finance_background']={'studied':True}
        elif mode=='failed':p.update(completed_courses=['GE1202'],GE_history=[{'course_code':'GE1202','grade':'F'}])
        elif mode=='passed':p['completed_courses']=['GE1202']
        elif mode=='advanced':p['completed_courses']=['EF3320']
        return {'id':f'{label}:{code}:{weight}:{mode}','task':'timetable_EF_policy',
            'messages':task.messages(p,code)+[{'role':'assistant','content':json.dumps(task.assessment(p,code))}]}
    # Keep the frozen test weights .5 and 2 out of both train and validation.
    for weight in [0.,.25,.75,1.,1.25,1.5,3.,4.]:
      for code in ['EF3320','EF4821']:
       for mode in ['none','declared','declared_object','failed','passed','advanced']:rows.append(add('corrective',weight,code,mode))
    val=[add('validation',w,c,m) for w in [.125,1.1] for c in ['EF3320','EF4821'] for m in ['none','declared','failed','advanced']]
    previous=[json.loads(x) for x in (task.DATA/'train.jsonl').read_text().splitlines()]
    rng=random.Random(2026112402);factual=[r for r in previous if r['task']=='timetable_EF_policy'];rng.shuffle(factual)
    rows+=[{**r,'id':'source-replay:'+r['id']} for r in factual[:48]]
    sched=[r for r in previous if r['task']=='grounded_timetable']
    for r in sched:
        positive=json.loads(r['messages'][-1]['content'])['status']=='feasible'
        for n in range(10 if positive else 1):rows.append({**r,'id':f'reweighted:{n}:'+r['id']})
    replay=[r for r in previous if r['id'].startswith('replay:')];rows+=[{**r,'id':'retention:'+r['id']} for r in replay[:32]]
    for name,items in [('train',rows),('validation',val)]:
        (DATA/(name+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in items),encoding='utf-8')
    for filename in ['evaluation_cases.json','after_evaluation.json','after_predictions.json']:
        dest=filename.replace('after_','before_')
        shutil.copyfile(task.REPORT/filename,REPORT/dest)
    task.save(REPORT/'protocol.json',{'source_adapter':task.ADAPTER,'splits':{'train':len(rows),'validation':len(val)},
        'scope':'Corrective supervised trial; output-label types and unseen penalty weights. Feasible timetable examples reweighted tenfold; familiar diagnostics remain familiar.',
        'test_weights_excluded_from_train_and_validation':[.5,2.],
        'before_evaluation':'Reused exact saved first-trial predictions on unchanged frozen prompts; no prompt or criterion changes.',
        'first_trial_report':'reports/timetable-grounded','previous_rollout_corrections':45})
    task.save(REPORT/'dataset_hashes.json',{name:hashlib.sha256((DATA/(name+'.jsonl')).read_bytes()).hexdigest() for name in ['train','validation']})
    print('CORRECTION_DATA',len(rows),len(val),flush=True)

def activate_domain():
    release=json.loads((REPORT/'release.json').read_text());scores=release['evaluation']['after']
    good=scores['heldout_policy']['passed']>=18 and scores['familiar_schedule_diagnostics']['passed']>=8
    if not good:raise RuntimeError('Timetable-domain release criteria not met.')
    general=json.loads((ROOT/'data/active_programme_adapter.json').read_text())
    value={'adapter':ADAPTER,'report_dir':str(REPORT.relative_to(ROOT)).replace('\\','/'),'accepted_for_activation':True,
        'scope':'Timetable availability, offered option selection, minimum load and EF background penalty only.',
        'general_stream_model_replaced':False,'general_adapter_retained':general['adapter'],
        'reason':'Timetable-domain checks passed; retain the prior general checkpoint after a historical stream-answer regression.',
        'sha256':release['sha256'],'evaluation':scores,'raw_outputs_require_validation':True}
    task.save(REPORT/'domain_release.json',value)
    task.save(ROOT/'data/active_grounded_adapter.json',value)
    print(json.dumps(value,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','after','release','activate-domain']);a=p.parse_args()
    if a.command=='build':build()
    elif a.command=='activate-domain':activate_domain()
    else:
        task.REPORT=REPORT;task.ADAPTER=ADAPTER
        if a.command=='after':task.evaluate('after')
        else:task.release()
