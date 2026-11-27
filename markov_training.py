"""Rule-distilled reward parameters, fresh held-out states, and model-guided full rollouts."""
import argparse,copy,hashlib,json,random,time
from four_year_markov import *

TRAIN_DATA=ROOT/'data/markov-v4';TRAIN_REPORT=ROOT/'reports/markov-v4'

def compact_rows(rows):return [[r['id'],r['grade'],r['credits'],r['term']] for r in rows]
def state_key(s):return (s['year'],s['earned_credits'],s['distribution_GE_count'],tuple(s['GE_area_counts'][str(a)] for a in [1,2,3]),s['elective_math_credits'])
def model_messages(state,transcript=None):
    return [{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps({'fictional':True,'Markov_state':state,
      'transcript_columns':['course_id','grade','credits','term'],'full_transcript_so_far':compact_rows(transcript or [])})}]

def build():
    rng=random.Random(2025111604);rows={s:[] for s in ['train','validation','test']};seen=set()
    def add(split,ident,s,transcript=None,negative=False):
        key=state_key(s)
        if key in seen:return False
        seen.add(key);messages=model_messages(s,transcript)
        if negative:messages[-1]['content']+='\nCorrect these invalid proposed parameters: '+json.dumps({**parameters(s),'covered_GE_area_multiplier':1.,'year4_overload_weight':.25})
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
            add(split,'SYN:'+split+':'+str(i),s,negative=split=='train' and i%4==0)
    replay=[json.loads(x) for x in (ROOT/'data/cm-planning-v2/train.jsonl').read_text(encoding='utf-8').splitlines()]
    rng.shuffle(replay)
    for r in replay[:32]:rows['train'].append({**r,'id':'replay:'+r['id']})
    TRAIN_DATA.mkdir(parents=True,exist_ok=True)
    for split,rs in rows.items():(TRAIN_DATA/(split+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs),encoding='utf-8')
    write(TRAIN_REPORT/'dataset.json',{'examples':{s:len(v) for s,v in rows.items()},'seed':2025111604,
        'scope':'User-rule distillation of configured academic utility parameters. Not empirical reward learning or actual student outcomes.',
        'state_vectors_disjoint':True,'official_minimum':122,'user_minimum':121,'math_elective_minimum':20,
        'GE_minimum':4,'required_areas':[1,2,3],'full_transcript_states_in_training':sum(not r['id'].startswith(('SYN:','replay:')) for r in rows['train'])})
    tests=[json.loads(x) for x in (TRAIN_DATA/'test.jsonl').read_text(encoding='utf-8').splitlines()]
    # Twelve predeclared state queries, balanced across all four years.
    selected=[]
    for year in [1,2,3,4]:selected += [r for r in tests if json.loads(r['messages'][1]['content'])['Markov_state']['year']==year][:3]
    write(TRAIN_REPORT/'evaluation_cases.json',selected);print(json.dumps(read(TRAIN_REPORT/'dataset.json'),indent=2))

def evaluate():
    import gc,torch
    from inference import load,generate
    torch.set_num_threads(8);tests=read(TRAIN_REPORT/'evaluation_cases.json');results=[]
    for label,adapter in [('before','adapters/bscm-profit-v3'),('after',ADAPTER)]:
        tok,model=load(adapter)
        for row in tests:
            raw=generate(tok,model,row['messages'][:-1],max_tokens=300)
            s=json.loads(row['messages'][1]['content'])['Markov_state'];value=None
            try:value=json.loads(raw)
            except (ValueError,TypeError):pass
            results.append({'model':label,'id':row['id'],'state':s,'expected':parameters(s),'raw_model_response':raw,
                            'passed':parameter_grade(s,value)})
            write(TRAIN_REPORT/'parameter_predictions.json',results);print(label,row['id'],results[-1]['passed'],flush=True)
        del model;gc.collect();torch.cuda.empty_cache()
    summary={label:{'passed':sum(r['passed'] for r in results if r['model']==label),'total':sum(r['model']==label for r in results)} for label in ['before','after']}
    write(TRAIN_REPORT/'evaluation.json',summary);print(json.dumps(summary,indent=2))

def model_rollout():
    import torch
    from scipy.optimize import milp
    from inference import load,generate
    torch.set_num_threads(8);tok,model=load(ADAPTER);calls=[]
    def provider(state,history):
        raw=generate(tok,model,model_messages(state,history),max_tokens=300);value=None
        try:value=json.loads(raw)
        except (ValueError,TypeError):pass
        accepted=parameter_grade(state,value);calls.append({'state':state,'raw_model_response':raw,'accepted':accepted})
        return value
    runs=[]
    # Different IDs/grade seeds from the training transcript trajectories.
    for pid,fail,seed in [('MODEL_CM2025',[],202599),('MODEL_CM2025_RESIT',['MA3526'],202598)]:
        run=simulate(pid,False,fail,param_provider=provider,seed=seed);runs.append(run)
        write(TRAIN_REPORT/'model_rollouts.json',runs);write(TRAIN_REPORT/'rollout_parameter_calls.json',calls)
        print(pid,run['status'],run['audit']['earned_credits'],run['audit']['all_encoded_requirements_met'],flush=True)

if __name__=='__main__':
    raise SystemExit('Historical v4 data and reports are retained. Use preparation_training.py for the current v5 schema; v4 report files will not be overwritten.')
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','evaluate','rollout']);a=ap.parse_args()
    {'build':build,'evaluate':evaluate,'rollout':model_rollout}[a.command]()
