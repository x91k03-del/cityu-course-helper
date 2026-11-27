"""User-only natural language profile/reward distillation and frozen evaluation."""
import argparse,copy,hashlib,json,random,re,shutil
from pathlib import Path
import project_runtime
from preparation import graph,PASS
from gpt_course_teacher import target as preparation_target
from programme_policy import exact,policy

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/natural-language-students'
REPORT=ROOT/'reports/natural-language-students'
ADAPTER='adapters/natural-language-students'
PARENT='adapters/gpt-course-relations-max'
FIELDS={'programme','year','semester','cohort','transcript','completed_courses','desired_stream','weights','target','preparation_bonus','strongest_sources','request','missing_fields'}
PROFILE_FIELDS=FIELDS-{'preparation_bonus','strongest_sources','missing_fields'}

def explicit_grades(text):
    """Guard explicit grade statements independently of the neural extraction."""
    upper=text.upper();found={}
    grade=r'(A\+|A-|A|B\+|B-|B|C\+|C-|C|D|P|F|IP|W)(?![A-Z+\-])'
    for code in set(re.findall(r'\b[A-Z]{2,6}\d{4}[A-Z]?\b',upper)):
        match=re.search(r'\b'+code+r'\s*(?::|\(|WITH\s+(?:GRADE\s+)?|GRADE\s+(?:OF\s+)?)\s*'+grade,upper)
        if match:found[code]=match.group(1);continue
        for pattern,value in [(r'(?:FAILED|FAIL)\s+'+code,'F'),
                              (r'(?:WITHDREW FROM|WITHDRAWN FROM)\s+'+code,'W'),
                              (code+r'\s+(?:IS\s+)?(?:STILL\s+)?IN PROGRESS','IP'),
                              (code+r'\s*[:(]\s*GRADE\s+(?:NOT PROVIDED|UNKNOWN)','UNKNOWN')]:
            if re.search(pattern,upper):found[code]=value;break
    return found

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def canonical(p):
    transcript=sorted(copy.deepcopy(p['transcript']),key=lambda r:r['course_code'])
    completed=sorted({r['course_code'] for r in transcript if r['grade'] in PASS})
    target=p.get('target')
    relation=preparation_target(transcript,target,graph()) if target else None
    missing=['grade:'+r['course_code'] for r in transcript if r['grade']=='UNKNOWN']
    if p['request']=='plan':
        missing += [k for k in ['programme','year','semester','cohort'] if p.get(k) is None]
    return {'programme':p.get('programme'),'year':p.get('year'),'semester':p.get('semester'),
      'cohort':p.get('cohort'),'transcript':transcript,'completed_courses':completed,
      'desired_stream':p.get('desired_stream'),'weights':p.get('weights',{'background_mismatch':1.,'difficulty':1.,'workload':1.}),
      'target':target,'preparation_bonus':relation['preparation_bonus'] if relation else None,
      'strongest_sources':relation['strongest_sources'] if relation else [],'request':p['request'],'missing_fields':missing}

def validate(value,text):
    if not isinstance(value,dict) or set(value)!=FIELDS:raise ValueError('Invalid natural-language output schema')
    codes=set(re.findall(r'\b[A-Z]{2,6}\d{4}[A-Z]?\b',text.upper()))
    if value['programme'] not in ['CM','CS',None]:raise ValueError('Unknown programme')
    if value['year'] is not None and (type(value['year']) is not int or value['year'] not in range(1,5)):raise ValueError('Invalid study year')
    if value['semester'] not in ['A','B',None]:raise ValueError('Invalid semester')
    if value['cohort'] is not None and (type(value['cohort']) is not int or not 2000<=value['cohort']<=2100):raise ValueError('Invalid cohort')
    if value['cohort'] is not None and str(value['cohort']) not in text:raise ValueError('Unmentioned entry cohort')
    if value['semester'] is not None and not re.search(r'\bSEM(?:ESTER)?\s*'+value['semester']+r'\b',text,re.I):raise ValueError('Unmentioned semester')
    if value['programme']=='CM' and not re.search(r'\bCM\b|COMPUTING MATH(?:EMATICS)?',text,re.I):raise ValueError('Unmentioned programme')
    if value['programme']=='CS' and not re.search(r'\bCS\b|COMPUTER SCIENCE',text,re.I):raise ValueError('Unmentioned programme')
    if value['year'] is not None:
        year=value['year'];ordinal=['','FIRST','SECOND','THIRD','FOURTH'][year]
        if not re.search(r'\bYEAR\s*(?:IS\s*)?'+str(year)+r'\b|\b'+str(year)+r'(?:ST|ND|RD|TH)[ -]*YEAR\b|\b'+ordinal+r'[ -]*YEAR\b',text,re.I):raise ValueError('Unmentioned study year')
    if value['request'] not in ['profile','preparation','plan']:raise ValueError('Invalid request')
    if not isinstance(value['transcript'],list):raise ValueError('Invalid transcript')
    seen=set()
    for row in value['transcript']:
        if not isinstance(row,dict) or set(row)!={'course_code','grade'} or row['course_code'] not in codes:raise ValueError('Unmentioned course in transcript')
        if row['course_code'] in seen or row['grade'] not in PASS|{'F','IP','W','UNKNOWN'}:raise ValueError('Duplicate course or invalid grade')
        seen.add(row['course_code'])
    grade_evidence=explicit_grades(text)
    observed={r['course_code']:r['grade'] for r in value['transcript']}
    if any(observed.get(c)!=grade for c,grade in grade_evidence.items()):raise ValueError('Transcript contradicts an explicit input grade')
    if value['target'] is not None and value['target'] not in codes:raise ValueError('Unmentioned target')
    if value['desired_stream'] is not None:
        if value['programme'] is None or value['desired_stream'] not in policy()['streams'][value['programme']]:raise ValueError('Stream outside programme')
        if value['desired_stream'].lower() not in text.lower():raise ValueError('Unmentioned desired stream')
    if not isinstance(value['weights'],dict) or set(value['weights'])!={'background_mismatch','difficulty','workload'}:raise ValueError('Invalid weights')
    import math
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in value['weights'].values()):raise ValueError('Invalid weight value')
    expected=canonical(value)
    if not exact(expected,value):raise ValueError('Profile, pass grades or preparation reward contradict reviewed policy')
    return value

def validate_profile(value,text):
    """Validate neural interpretation; external code derives rewards/context needs."""
    if not isinstance(value,dict) or set(value)!=FIELDS:raise ValueError('Invalid natural-language output schema')
    calculated=canonical(value)
    if not exact({k:value[k] for k in PROFILE_FIELDS},{k:calculated[k] for k in PROFILE_FIELDS}):raise ValueError('Interpreted completed courses contradict transcript grades')
    return validate(calculated,text)

def render(p,style):
    names={'CM':'Computing Mathematics','CS':'Computer Science',None:None}
    if p.get('programme') and p.get('year'):
        intro=[f"I am a Year {p['year']} {names[p['programme']]} student at CityUHK.",
          f"I'm studying {names[p['programme']]} in year {p['year']} at City University of Hong Kong.",
          f"My programme is {p['programme']} and I'm in Year {p['year']}.",
          f"At CityUHK, I study {names[p['programme']]}; my current year is {p['year']}.",
          f"I'm a {names[p['programme']]} student, currently in year {p['year']}.",
          f"I'm in my {['','first','second','third','fourth'][p['year']]} year of {names[p['programme']]} at CityUHK."][style%6]
    else:intro="Here is my course history."
    context=[]
    if p.get('semester'):context.append(f"I am planning semester {p['semester']}.")
    if p.get('cohort'):context.append(f"I entered in {p['cohort']}.")
    parts=[]
    for r in p['transcript']:
        c=r['course_code'];g=r['grade']
        if style%3==0:parts.append(f"{c}: {g}" if g!='UNKNOWN' else f"{c}: grade not provided")
        elif style%3==1:
            parts.append({'F':f"I failed {c}",'IP':f"{c} is still in progress",'W':f"I withdrew from {c}",'P':f"I passed {c} with P",'UNKNOWN':f"I studied {c}, but I have not given a grade"}.get(g,f"I passed {c} with {g}"))
        else:parts.append(f"{c} ({g})" if g!='UNKNOWN' else f"{c} (grade unknown)")
    history=('My transcript is '+', '.join(parts)+'.') if style%3==0 else '; '.join(parts)+'.'
    if not parts:history="I have not completed any courses yet."
    if p.get('desired_stream'):context.append(f"I want the {p['desired_stream']} stream.")
    w=p.get('weights',{})
    if w and any(v!=1 for v in w.values()):
        context.append(f"Use background mismatch weight {w['background_mismatch']}, difficulty weight {w['difficulty']}, and workload weight {w['workload']}.")
    if p['request']=='preparation':
        question=[f"How does my completed study prepare me for {p['target']}?",f"What preparation do I have for {p['target']}?",f"Would my previous courses help with {p['target']}?",f"I am considering {p['target']}. How relevant is my background?",f"Could you assess my background for taking {p['target']}?",f"With this record, how ready am I for {p['target']}?"][style%6]
    elif p['request']=='plan':question=["What should I consider next semester?","Help me plan my next semester.","Can you help plan the next part of my degree?"][style%3]
    else:question=''
    return ' '.join([intro,history,*context,question]).strip()

def row(ident,p,text):
    answer=canonical(p)
    return {'id':ident,'task':'natural_student_profile','profile_key':json.dumps(p,sort_keys=True),
      'messages':[{'role':'user','content':text},{'role':'assistant','content':json.dumps(answer,separators=(',',':'))}]}

def build():
    if (DATA/'train.jsonl').exists():raise RuntimeError('Dataset already frozen')
    DATA.mkdir(parents=True);REPORT.mkdir(parents=True,exist_ok=True)
    save(REPORT/'parent_manifest.json',json.loads((ROOT/'data/active_relation_adapter.json').read_text()))
    rng=random.Random(20261127);g=graph();targets=sorted({e['target'] for e in g['edges']});profiles=[];seen=set()
    pool=['MA1300','MA1301','CS1302','CS1302A','CS2310','CS3334','GE1305','GE1105']
    while len(profiles)<200:
        target=rng.choice(targets);sources=[e['source'] for e in g['edges'] if e['target']==target]
        candidates=list(dict.fromkeys(sources+pool+[target]));codes=rng.sample(candidates,rng.randint(0,min(5,len(candidates))))
        programme=rng.choice(['CM','CS']);request=rng.choices(['preparation','profile','plan'],[.65,.15,.20])[0]
        p={'programme':programme,'year':rng.choice([1,2,3,4]),'semester':rng.choice(['A','B',None]),
           'cohort':rng.choice([2024,2025,2026,None]),
           'transcript':[{'course_code':c,'grade':rng.choice(['A-','B+','B','C','P','F','IP','W'])} for c in codes],
           'target':target if request=='preparation' else None,'request':request,
           'desired_stream':rng.choice([None,*policy()['streams'][programme]]),
           'weights':{'background_mismatch':1.,'difficulty':1.,'workload':1.}}
        if rng.random()<.25:p['weights']={k:rng.choice([0.,.5,1.,2.]) for k in p['weights']}
        key=json.dumps(p,sort_keys=True)
        if key in seen:continue
        seen.add(key);profiles.append(p)
    rng.shuffle(profiles);groups={'train':profiles[:160],'validation':profiles[160:176],'test':profiles[176:]}
    splits={}
    for split,items in groups.items():
        styles=[0,1,2,3] if split=='train' else [4,5]
        splits[split]=[row(f'{split}:{i}:{j}',p,render(p,styles[(2*i+j)%len(styles)])) for i,p in enumerate(items) for j in range(2)]
    # Explicit correction of observed failures. These are diagnostics, not holdout data.
    old=json.loads((ROOT/'reports/additional-qwen-examples-20261127/results.json').read_text())
    old={r['id']:r for r in old}
    diagnostics=[]
    for c in json.loads((ROOT/'reports/qwen-natural-language-20261127/cases.json').read_text()):
        p=copy.deepcopy(old[c['group']]['profile_context'])
        p['transcript']=json.loads(old[c['group']]['messages'][1]['content'])['transcript']
        p.update(semester=None,cohort=None,desired_stream=None,weights={'background_mismatch':1.,'difficulty':1.,'workload':1.})
        p['request']={'natural_language_question':'preparation','transcript_only_no_question':'profile','ordinary_planning_question':'plan'}[c['mode']]
        p['target']=old[c['group']]['expected']['target'] if p['request']=='preparation' else None
        r=row('correct:'+c['id'],p,c['input_text']);splits['train'].append(r);diagnostics.append(r)
    # Add repeated-P, fail/IP/W, missing-grade and empty-profile teaching probes.
    for i in range(24):
        p={'programme':'CM' if i%2 else 'CS','year':2,'semester':None,'cohort':None,'desired_stream':None,
           'transcript':[{'course_code':'MA2510','grade':['P','F','IP','W','UNKNOWN'][i%5]}],
           'target':'CS4487','request':'preparation'}
        splits['train'].append(row('grade:'+str(i),p,render(p,i%4)))
    # Replay parent tasks and the reward-export contract to protect existing clients.
    replay=[json.loads(line) for line in (ROOT/'data/gpt-course-relations-max/train.jsonl').read_text(encoding='utf-8').splitlines()]
    rng.shuffle(replay);splits['train'] += [{**r,'id':'replay:'+r['id']} for r in replay[:32]]
    from llm_reward_contract import teacher_packet,messages
    for i in range(8):
        packet=teacher_packet();splits['train'].append({'id':'packet:'+str(i),'task':'reward_export',
          'messages':messages(packet)+[{'role':'assistant','content':json.dumps(packet,separators=(',',':'))}]})
    for split,rows in splits.items():
        rng.shuffle(rows)
        (DATA/(split+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    keys={split:{r['profile_key'] for r in rows if 'profile_key' in r} for split,rows in splits.items()}
    assert not(keys['train']&keys['validation'] or keys['train']&keys['test'] or keys['validation']&keys['test'])
    save(REPORT/'diagnostic_cases.json',diagnostics)
    save(REPORT/'protocol.json',{'parent_adapter':PARENT,'new_adapter':ADAPTER,
         'splits':{k:len(v) for k,v in splits.items()},'unique_random_profiles':{k:len(v) for k,v in groups.items()},
         'natural_input_system_message':False,'natural_input_teacher_graph_provided':False,
         'validation_and_test_styles':[4,5],'train_styles':[0,1,2,3],
         'test_used_for_training':False,'diagnostic_cases_used_for_training':12,
         'scope':'Synthetic supervised natural-language extraction and configured preparation rewards. Documents/course relations shared; heldout random profiles and phrase templates differ.',
         'parent_sha256':hashlib.sha256((ROOT/PARENT/'adapter_model.safetensors').read_bytes()).hexdigest()})
    print(json.dumps({k:len(v) for k,v in splits.items()}),flush=True)

def evaluate(label):
    import torch
    from inference import load,generate_batch
    torch.set_num_threads(8)
    adapter=PARENT if label=='before' else ADAPTER
    tok,model=load(adapter);results=[]
    groups={'heldout':[json.loads(s) for s in (DATA/'test.jsonl').read_text(encoding='utf-8').splitlines()],
            'familiar_failures':json.loads((REPORT/'diagnostic_cases.json').read_text()),
            'legacy_relations':json.loads((ROOT/'reports/gpt-course-relations-max/evaluation_cases.json').read_text())}
    if label=='after' and (REPORT/'fresh_manual_cases.json').exists():
        groups['fresh_manual']=json.loads((REPORT/'fresh_manual_cases.json').read_text())
    for group,rows in groups.items():
        for i in range(0,len(rows),4):
            batch=rows[i:i+4];raws=generate_batch(tok,model,[r['messages'][:-1] for r in batch],max_tokens=470 if group!='legacy_relations' else 180)
            for r,raw in zip(batch,raws):
                expected=json.loads(r['messages'][-1]['content'])
                try:parsed=json.loads(raw)
                except ValueError:parsed=None
                checked=False;error=None
                if group!='legacy_relations' and parsed is not None:
                    try:validate(parsed,r['messages'][0]['content']);checked=True
                    except (ValueError,TypeError,KeyError) as e:error=str(e)
                results.append({'id':r['id'],'group':group,'input':r['messages'][:-1],
                      'expected':expected,'raw':raw,'parsed':parsed,'passed':exact(expected,parsed),
                      'validated':checked,'validation_error':error,'fallback_used':False})
            save(REPORT/(label+'_predictions.json'),results)
            print(label,group,min(i+4,len(rows)),sum(r['passed'] for r in results if r['group']==group),flush=True)
    summary={group:{'passed':sum(r['passed'] for r in results if r['group']==group),'total':len(rows)} for group,rows in groups.items()}
    save(REPORT/(label+'_evaluation.json'),summary)
    print(json.dumps(summary),flush=True)

def release():
    training=json.loads((REPORT/'training.json').read_text());before=json.loads((REPORT/'before_evaluation.json').read_text());after=json.loads((REPORT/'after_evaluation.json').read_text())
    predictions=json.loads((REPORT/'after_predictions.json').read_text(encoding='utf-8'))
    profile_scores={}
    for group in ['heldout','familiar_failures','fresh_manual']:
        rows=[r for r in predictions if r['group']==group]
        correct=sum(isinstance(r['parsed'],dict) and exact({k:r['expected'][k] for k in PROFILE_FIELDS},{k:r['parsed'].get(k) for k in PROFILE_FIELDS}) for r in rows)
        profile_scores[group]={'passed':correct,'total':len(rows)}
    passed=training['status']=='complete' and profile_scores['heldout']['passed']>=.95*profile_scores['heldout']['total'] and profile_scores['familiar_failures']['passed']==12 and after['legacy_relations']['passed']>=18
    manifest={'adapter':ADAPTER,'parent_adapter':PARENT,'accepted_for_activation':passed,
      'role':'User-only natural-language transcript/profile extraction; external code computes contextual rewards and selects paths',
      'before':before,'after':after,'training_performed':True,'requires_system_prompt':False,
      'selected_epoch':training['selected_epoch'],'sha256':hashlib.sha256((ROOT/ADAPTER/'adapter_model.safetensors').read_bytes()).hexdigest(),
      'legacy_active_relation_adapter_unchanged':True,'validation_required':True,
      'activation_basis':'Exact natural-language profile extraction; raw numeric reward proposals are not deployed',
      'profile_extraction':profile_scores,'contextual_reward_source':'external reviewed course-relation calculator'}
    save(REPORT/'release.json',manifest)
    if passed:save(ROOT/'data/active_natural_language_adapter.json',manifest)
    print(json.dumps(manifest,indent=2),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','before','after','release']);args=ap.parse_args()
    if args.command=='build':build()
    elif args.command=='release':release()
    else:evaluate(args.command)
