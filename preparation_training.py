"""Rule-distilled reward parameters, fresh held-out states, and model-guided full rollouts."""
import argparse,copy,hashlib,json,random,time
from four_year_markov import *

TRAIN_DATA=ROOT/'data/preparation-v5';TRAIN_REPORT=ROOT/'reports/preparation-v5'

def compact_rows(rows):return [[r['id'],r['grade'],r['credits'],r['term']] for r in rows]
def state_key(s):return tuple(sorted(set(s.get('passed_ids',[])) & {'MA2508','MA2509'})),(s['year'],s['earned_credits'],s['distribution_GE_count'],tuple(s['GE_area_counts'][str(a)] for a in [1,2,3]),s['elective_math_credits'])
def model_messages(state,transcript=None):
    return [{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps({'fictional':True,'Markov_state':state,
      'transcript_columns':['course_id','grade','credits','term'],'full_transcript_so_far':compact_rows(transcript or [])})}]

def build():
    rng=random.Random(2025111605);rows={s:[] for s in ['train','validation','test']};seen=set()
    def add(split,ident,s,transcript=None,negative=False):
        key=state_key(s)
        if key in seen:return False
        seen.add(key);messages=model_messages(s,transcript)
        if negative:messages[-1]['content']+='\nReject this proposed answer: GE cap=2; treat failed or same-semester MA2508 as preparation; reduce published contact hours. Return corrected parameters only.'
        rows[split].append({'id':ident,'task':'Markov_profit_parameters','messages':messages+[{'role':'assistant','content':json.dumps(parameters(s))}]});return True
    for ident,year,credits,count,areas,mathcredit in [
        ('BOUNDARY_GE3',2,60,3,[1,1,1],0),('BOUNDARY_GE4',2,63,4,[2,1,1],0),
        ('BOUNDARY_MATH19',4,121,4,[2,1,1],19),('BOUNDARY_MATH20',4,122,4,[2,1,1],20)]:
        add('test',ident,{'year':year,'term':2*year-1,'earned_credits':credits,'distribution_GE_count':count,
          'GE_area_counts':{str(a+1):areas[a] for a in range(3)},'elective_math_credits':mathcredit,
          'passed_ids':[],'synthetic_numeric_boundary_state':True,'official_graduation_verified':False})
    # Authentic synthetic transcript states go into training only. Test states
    # below are separate numeric vectors; all tests are fixed before training.
    for run in read(REPORT/'rule_rollouts.json'):
        for step in run['steps']:
            history=[r for r in run['transcript'] if r['term']<step['term']]
            add('train',run['profile_id']+':'+str(step['term']),step['state_before'],history)
    for split,count in [('test',24),('validation',24),('train',192)]:
        i=0
        while sum(r['id'].startswith('SYN:'+split) for r in rows[split])<count:
            i+=1;year=1+(i%4);areas=[0,0,0]
            for _ in range(rng.randint(0,5)):areas[rng.randrange(3)]+=1
            mathcredit=0 if year<=2 else rng.choice([0,3,9,18,19,20,21,24])
            credit=max(3*sum(areas)+mathcredit,rng.randint((year-1)*28,year*32))
            s={'year':year,'term':2*year-1+(i%2),'earned_credits':credit,'distribution_GE_count':sum(areas),
               'GE_area_counts':{str(a+1):areas[a] for a in range(3)},'elective_math_credits':mathcredit,
               'passed_ids':[],'synthetic_numeric_boundary_state':True,'official_graduation_verified':False}
            # Deliberately contrast pass / F / IP / W and unrelated histories.
            history=[];done=[]
            for code in ['MA2508','MA2509']:
                status=rng.choice(['B','A','F','IP','W','not_taken'])
                if status!='not_taken':history.append({'id':code,'grade':status,'credits':4 if code=='MA2508' else 3,'term':max(1,s['term']-1)})
                if status in PASS:done.append(code)
            s['passed_ids']=sorted(done)
            add(split,'SYN:'+split+':'+str(i),s,history,negative=split=='train' and i%4==0)
    replay=[json.loads(x) for x in (ROOT/'data/cm-planning-v2/train.jsonl').read_text(encoding='utf-8').splitlines()]
    rng.shuffle(replay)
    for r in replay[:16]:rows['train'].append({**r,'id':'replay:'+r['id']})
    TRAIN_DATA.mkdir(parents=True,exist_ok=True)
    for split,rs in rows.items():(TRAIN_DATA/(split+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs),encoding='utf-8')
    write(TRAIN_REPORT/'dataset.json',{'examples':{s:len(v) for s,v in rows.items()},'seed':2025111605,
        'scope':'Rule distillation: one distributional GE per term; bounded direct preparation deductions from indexed official PDF excerpts. No measured workload or outcome labels.',
        'state_vectors_disjoint':True,'official_minimum':122,'user_minimum':121,'math_elective_minimum':20,
        'GE_minimum':4,'required_areas':[1,2,3],'full_transcript_states_in_training':sum(not r['id'].startswith(('SYN:','replay:')) for r in rows['train'])})
    tests=[json.loads(x) for x in (TRAIN_DATA/'test.jsonl').read_text(encoding='utf-8').splitlines()]
    # Twenty predeclared state queries, balanced across years and distinct histories.
    selected=[]
    for year in [1,2,3,4]:selected += [r for r in tests if json.loads(r['messages'][1]['content'])['Markov_state']['year']==year][:5]
    write(TRAIN_REPORT/'evaluation_cases.json',selected);print(json.dumps(read(TRAIN_REPORT/'dataset.json'),indent=2))

def evaluate():
    import gc,torch
    from inference import load,generate_batch
    torch.set_num_threads(8);tests=read(TRAIN_REPORT/'evaluation_cases.json');results=[]
    for label,adapter in [('before','adapters/bscm-markov-v4'),('after',ADAPTER)]:
        tok,model=load(adapter)
        predictions=[]
        for offset in range(0,len(tests),4):
            group=tests[offset:offset+4]
            predictions.extend(generate_batch(tok,model,[row['messages'][:-1] for row in group],max_tokens=420))
            print(label,'generated batch',offset//4+1,flush=True)
        for row,raw in zip(tests,predictions):
            s=json.loads(row['messages'][1]['content'])['Markov_state'];value=None
            try:value=json.loads(raw)
            except (ValueError,TypeError):pass
            expected=parameters(s)
            results.append({'model':label,'id':row['id'],'state':s,'expected':expected,'raw_model_response':raw,
                            'passed':parameter_grade(s,value),
                            'GE_cap_passed':isinstance(value,dict) and value.get('maximum_distribution_GE_per_semester')==1,
                            'preparation_map_passed':isinstance(value,dict) and structured_grade(expected['preparation_bonus_by_course'],value.get('preparation_bonus_by_course')),
                            'original_nine_parameters_passed':isinstance(value,dict) and all(structured_grade(v,value.get(k)) for k,v in expected.items() if k not in ['maximum_distribution_GE_per_semester','preparation_bonus_by_course'])})
            write(TRAIN_REPORT/'parameter_predictions.json',results);print(label,row['id'],results[-1]['passed'],flush=True)
        del model;gc.collect();torch.cuda.empty_cache()
    summary={label:{**{k:sum(r[k] for r in results if r['model']==label) for k in ['passed','GE_cap_passed','preparation_map_passed','original_nine_parameters_passed']},'total':sum(r['model']==label for r in results)} for label in ['before','after']}
    write(TRAIN_REPORT/'evaluation.json',summary);print(json.dumps(summary,indent=2))

def model_rollout():
    import torch
    from scipy.optimize import milp
    from inference import load,generate,generate_batch
    torch.set_num_threads(8);tok,model=load(ADAPTER);calls=[]
    def provider(state,history):
        raw=generate(tok,model,model_messages(state,history),max_tokens=420);value=None
        try:value=json.loads(raw)
        except (ValueError,TypeError):pass
        accepted=parameter_grade(state,value);calls.append({'state':state,'raw_model_response':raw,'accepted':accepted})
        return value
    runs=[]
    # Different IDs/grade seeds from the training transcript trajectories.
    for pid,fail,seed in [('MODEL_CM2025',[],202599),('MODEL_CM2025_RESIT',['MA3526'],202598),('MODEL_CM2025_CALCULUS_RESIT',['MA2508'],202597)]:
        run=simulate(pid,False,fail,param_provider=provider,seed=seed);runs.append(run)
        write(TRAIN_REPORT/'model_rollouts.json',runs);write(TRAIN_REPORT/'rollout_parameter_calls.json',calls)
        print(pid,run['status'],run['audit']['earned_credits'],run['audit']['all_encoded_requirements_met'],flush=True)
    # Additional paired diagnostics: hold other attempts fixed, alter one grade
    # in the Year-2-A transcript, and recompute all state totals consistently.
    prefix=[r for r in runs[0]['transcript'] if r['term']<=3];paired=[]
    for course in ['MA2508','MA2509']:
        for grade in ['B','F','IP','W']:
            history=copy.deepcopy(prefix)
            for row in history:
                if row['id']==course:row['grade']=grade
            state=state_from(history,4)
            paired.append({'changed_course':course,'grade':grade,'expected':parameters(state),'state':state,'messages':model_messages(state,history)})
    for offset in range(0,len(paired),4):
        group=paired[offset:offset+4]
        raws=generate_batch(tok,model,[r.pop('messages') for r in group],max_tokens=420)
        for record,raw in zip(group,raws):
            try:value=json.loads(raw)
            except (ValueError,TypeError):value=None
            record.update(raw_model_response=raw,passed=parameter_grade(record['state'],value))
    write(TRAIN_REPORT/'counterfactual_predictions.json',paired)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','evaluate','rollout']);a=ap.parse_args()
    {'build':build,'evaluate':evaluate,'rollout':model_rollout}[a.command]()
