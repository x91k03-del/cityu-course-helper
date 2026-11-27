"""Balanced direct-edge teaching; new, profile-disjoint final evaluation."""
import argparse,copy,hashlib,json,random,shutil
from pathlib import Path
import project_runtime
import natural_language_training as n
from preparation import graph
from programme_policy import policy

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/natural-language-students-corrected'
REPORT=ROOT/'reports/natural-language-students-corrected'
ADAPTER='adapters/natural-language-students-corrected'
PARENT='adapters/natural-language-students'

def build():
    if (DATA/'train.jsonl').exists():raise RuntimeError('Correction dataset frozen')
    DATA.mkdir(parents=True);REPORT.mkdir(parents=True,exist_ok=True)
    rng=random.Random(20261128);g=graph()
    train=[json.loads(line) for line in (n.DATA/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    development=[json.loads(line) for line in (n.DATA/'test.jsonl').read_text(encoding='utf-8').splitlines()]
    train += [{**r,'id':'development-correction:'+r['id']} for r in development]
    def profile(history,target,request='preparation'):
        major=rng.choice(['CM','CS'])
        return {'programme':major,'year':rng.choice([1,2,3,4]),'semester':rng.choice(['A','B',None]),
          'cohort':rng.choice([2024,2025,None]),'transcript':history,'target':target,'request':request,
          'desired_stream':rng.choice([None,*policy()['streams'][major]]),
          'weights':{'background_mismatch':1.,'difficulty':1.,'workload':1.}}
    balanced=[]
    for i,e in enumerate(g['edges']):
        for grade in ['P','F','B+']:
            p=profile([{'course_code':e['source'],'grade':grade}],e['target'])
            for style in [4,5]:balanced.append(n.row(f'direct:{i}:{grade}:{style}',p,n.render(p,style)))
    for i,target in enumerate(sorted({e['target'] for e in g['edges']})):
        sources=sorted({e['source'] for e in g['edges'] if e['target']==target})
        for mode,history in [('no_history',[]),('all_sources',[{'course_code':c,'grade':'P'} for c in sources]),
                             ('target_already_passed',[{'course_code':c,'grade':'B'} for c in sources+[target]])]:
            p=profile(history,target)
            for style in [4,5]:balanced.append(n.row(f'balanced:{i}:{mode}:{style}',p,n.render(p,style)))
    train += balanced
    for i in range(32):
        target=rng.choice(sorted({e['target'] for e in g['edges']}))
        p=profile([{'course_code':'MA2510','grade':rng.choice(['P','F','IP','W','UNKNOWN'])}],None,rng.choice(['profile','plan']))
        if i%4==0:p['weights']={k:rng.choice([0.,.5,1.,2.]) for k in p['weights']}
        train.append(n.row('context:'+str(i),p,n.render(p,i%6)))
    seen={r['profile_key'] for r in train if 'profile_key' in r}
    # Keep all earlier validation profiles outside the final evaluation as well.
    seen.update(json.loads(s)['profile_key'] for s in (n.DATA/'validation.jsonl').read_text(encoding='utf-8').splitlines())
    def independent(split,count):
        result=[];i=0
        while i<count:
            edge=rng.choice(g['edges']);target=edge['target']
            sources=sorted({e['source'] for e in g['edges'] if e['target']==target})
            codes=sorted(set(rng.sample(sources,rng.randint(0,len(sources)))+rng.sample(['CS1302','CS1302A','CS2310','GE1305','MA1300','GE1105'],rng.randint(0,2))))
            history=[{'course_code':c,'grade':rng.choice(['P','A-','B+','F','IP','W'])} for c in codes]
            p=profile(history,target)
            if i%5==0:p.update(request=rng.choice(['profile','plan']),target=None)
            if i%4==0:p['weights']={k:rng.choice([0.,.5,1.,2.]) for k in p['weights']}
            key=json.dumps(p,sort_keys=True)
            if key in seen:continue
            seen.add(key)
            for j in range(2):
                style=(2*i+j)%6
                result.append(n.row(f'{split}:{i}:{j}',p,n.render(p,style)))
            i+=1
        return result
    splits={'train':train,'validation':independent('validation',16),'test':independent('final_test',24)}
    for split,rows in splits.items():
        rng.shuffle(rows)
        (DATA/(split+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    for name in ['diagnostic_cases.json','fresh_manual_cases.json','fresh_manual_inputs.txt','parent_manifest.json']:
        shutil.copyfile(n.REPORT/name,REPORT/name)
    n.save(REPORT/'before_evaluation.json',{'scope':'Initial candidate evaluated on a development set; final test profiles are new and were frozen before correction training.'})
    n.save(REPORT/'protocol.json',{'parent_adapter':PARENT,'new_adapter':ADAPTER,
      'splits':{k:len(v) for k,v in splits.items()},'balanced_additional_rows':len(balanced),
      'previous_test_promoted_to_training_development':48,'final_test_random_profiles':24,
      'final_test_messages':48,'final_test_profile_keys_disjoint':True,
      'final_test_templates_shared_with_training':True,'new_test_used_for_training':False,
      'familiar_failures_used_for_training':12,'manual_wordings_unseen_but_some_profiles_familiar':True,
      'natural_language_messages_have_no_system_prompt':True,'teacher_graph_provided_at_inference':False,
      'scope':'Synthetic extraction and configured reward policy; familiar courses/relations, new final test profiles. No real-student outcome claim.',
      'parent_sha256':hashlib.sha256((ROOT/PARENT/'adapter_model.safetensors').read_bytes()).hexdigest()})
    all_inputs=splits['test']+json.loads((REPORT/'diagnostic_cases.json').read_text())+json.loads((REPORT/'fresh_manual_cases.json').read_text())
    (REPORT/'all_natural_test_inputs.txt').write_text('\n\n'.join(r['id']+'\n'+r['messages'][0]['content'] for r in all_inputs),encoding='utf-8')
    print(json.dumps({k:len(v) for k,v in splits.items()}),flush=True)

def configure():
    n.DATA=DATA;n.REPORT=REPORT;n.ADAPTER=ADAPTER;n.PARENT=PARENT

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','after','release']);args=ap.parse_args()
    if args.command=='build':build()
    else:
        configure()
        n.evaluate('after') if args.command=='after' else n.release()
