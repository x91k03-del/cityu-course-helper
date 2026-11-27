"""Controlled course-to-course effects, mechanism decomposition and a predeclared LLM probe."""
import argparse,copy,csv,json,math
from pathlib import Path
import project_runtime
from programme_policy import *
from ge_pathways import recommend
from preparation import benefits
from profit_objective import settings,option_profit
from stream_path import rules,model_messages
ROOT=Path(__file__).resolve().parent
OUT=ROOT/('reports/dependency-experiment-gpt-teacher' if (ROOT/'data/active_preparation_graph.json').exists() else 'reports/dependency-experiment')
def save(name,v):OUT.mkdir(parents=True,exist_ok=True);(OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def profile(major,done,stream,**extra):return {'programme':major,'year':2,'selected_stream':stream,'completed_courses':done,**extra}
def measure(p,target):
    done=set(p['completed_courses']);route=recommend(p);major=programme(p['programme'])
    selected=route['selected_stream'] or stream_result(major,done)['selected_stream']
    areas=json.loads((ROOT/'data/four-year/GE_areas.json').read_text(encoding='utf-8'))
    area=areas.get(target,{}).get('area');counts={str(a):sum(areas.get(c,{}).get('area')==a for c in done) for a in [1,2,3]}
    config=settings({'student_year':2,'completed_courses':list(done),'completed_GE_area_counts':counts})
    opt={'course_code':target,'ge_area':area} if area else {'course_code':target}
    base=option_profit(opt,config);prep=benefits(done).get(target,0.)
    chain=chain_reward(major,done,selected,[target])*route['stream_reward_multiplier'] if target not in done else 0.
    bridge=route['prerequisite_bridge_bonus'].get(target,0.)
    # Fixed scores, fixed lambdas, no quota/year/load/course-count terms.
    cost=.6;net=base+prep+chain+bridge-cost
    fact=rules().get(target,{})
    if target in ['GE1113','GE2134']:fact={'completion_alternatives':[[]]}
    alts=fact.get('completion_alternatives');pre=None if alts is None else any(set(a)<=done for a in alts)
    conflict=bool(done&set(fact.get('exclusive_courses',[])))
    member=allowed(major,target)
    eligible=None if pre is None else bool(member and pre and not conflict and target not in done)
    return {'target':target,'selected_stream':selected,'stream_multiplier':route['stream_reward_multiplier'],
      'components':{'base_GE_adjusted_profit':base,'preparation_bonus':prep,'stream_chain_bonus':chain,'bridge_bonus':bridge,'fixed_cost_penalty':cost},
      'advertised_marginal_utility':round(net,8),'known_prerequisite_satisfied':pre,'programme_allowed':member,
      'already_passed':target in done,'eligibility_under_known_rules':eligible,
      'usable_marginal_utility':round(net,8) if eligible else None,
      'eligibility_note':'Known prerequisite/membership check only; no source of current seats, component linkage or actual timetable.'}
def build():
    pairs=[]
    def add(ident,mechanism,source,target,before,after,expected,expected_gate=None,note=''):
        a=measure(before,target);b=measure(after,target);delta=round(b['advertised_marginal_utility']-a['advertised_marginal_utility'],8)
        assert abs(delta-expected)<1e-7,(ident,delta,expected)
        if expected_gate is not None:assert (a['known_prerequisite_satisfied'],b['known_prerequisite_satisfied'])==expected_gate
        changes={k:round(b['components'][k]-v,8) for k,v in a['components'].items()}
        pairs.append({'id':ident,'mechanism':mechanism,'source_change':source,'target':target,'before_profile':before,'after_profile':after,
          'before':a,'after':b,'observed_delta':delta,'expected_delta_predeclared':expected,'component_deltas':changes,'passed':True,'note':note})
    def with_course(p,code):return {**p,'completed_courses':p['completed_courses']+[code]}
    p=profile('CM',['MA2503'],'Enriched Mathematics')
    add('D01','direct_preparation','pass MA2508','MA3515',p,with_course(p,'MA2508'),.2,(True,True),'Prerequisite MA2503 is already passed in both profiles.')
    p=profile('CM',[],'Enriched Mathematics')
    add('D02','direct_preparation','pass MA2509','GE2134',p,with_course(p,'MA2509'),.15,(True,True))
    a=profile('CM',['GE1202'],'Enriched Mathematics');b=profile('CM',['GE1105'],'Enriched Mathematics')
    add('D03','same_area_diminishing_profit','replace a passed Area-2 GE with Area-1 GE','GE1113',a,b,-2.7,(True,True),'Matched 3-credit GE substitution isolates target-area coverage, not earned-credit change.')
    p=profile('CM',['MA2510'],'Financial Mathematics')
    add('D04','GE_interest_multiplier','pass GE2260; selected finance stream held fixed','MA3521',p,with_course(p,'GE2260'),4.,(True,True),'Legacy fixed stream lets GE change weight 1 to 3. It does not earn a stream slot.')
    p=profile('CM',['MA2510'],'Enriched Mathematics',desired_stream='Enriched Mathematics')
    add('D05','explicit_choice_negative_control','pass GE2260 with explicit Enriched preference','MA3521',p,with_course(p,'GE2260'),0.,(True,True))
    p=profile('CS',['CS1302A','CS2310','CS2402'],'Data Science')
    add('D06','prerequisite_unlock','pass CS3481','CS4487',p,with_course(p,'CS3481'),0.,(False,True),'Reward coefficients do not change; the option becomes usable. Ineligibility is not represented as zero reward.')
    p=profile('CS',['CS1302A','CS2310','CS2402','CS3402','CS3481'],'Data Science')
    add('D07','completion_threshold','pass CS4480','CS4487',p,with_course(p,'CS4480'),6.,(True,True),'Last required stream slot becomes worth 2+6 rather than 2.')
    p=profile('CM',['MA2510'],'Financial Mathematics')
    add('D08','unrelated_course_negative_control','pass GE1305','MA3521',p,with_course(p,'GE1305'),0.,(True,True))
    p=profile('CM',['MA2509'],'Enriched Mathematics')
    add('D09','repeat_normalization_control','repeat an already-passed MA2509 ID','GE2134',p,with_course(p,'MA2509'),0.,(True,True),'Duplicate passed IDs are not a valid new credit record; this probes normalization only.')
    p=profile('CM',[],'Financial Mathematics')
    add('D10','bridge_weight_amplification','pass GE2260','MA2510',p,with_course(p,'GE2260'),2.,None,'The existing bridge reward rises from 1 to 3; combined-source prerequisite eligibility is intentionally tracked separately.')
    p=profile('CM',['MA2510'],'Financial Mathematics',desired_stream='Financial Mathematics')
    add('D11','explicit_weight_saturation','pass GE2260 when explicit finance weight is already 3','MA3521',p,with_course(p,'GE2260'),0.,(True,True))
    p=profile('CM',['MA2510'],'Financial Mathematics')
    add('D12','GPT_content_preparation','pass MA2503; portfolio mathematics preparation','EF3320',p,with_course(p,'MA2503'),.20,(False,False),'GPT assigns 0.20 direct utility for covariance/quadratic-form preparation. This does not modify the raw published prerequisite check; CM advisory waiver and actual section eligibility remain separate.')
    grades=[]
    for g in ['B','F','IP','W']:
        p=profile('CM',['MA2509'] if g=='B' else [],'Enriched Mathematics');value=measure(p,'GE2134')
        expected=.15 if g=='B' else 0.;assert value['components']['preparation_bonus']==expected
        grades.append({'source':'MA2509','grade':g,'passed_ids':p['completed_courses'],'result':value})
    # Two independent source passes for a 3-of-4 stream produce a last-slot interaction.
    factorial=[];base=profile('CS',['CS1302A','CS2310','CS3342'],'Software Engineering and Project Management')
    for a,b in [(0,0),(1,0),(0,1),(1,1)]:
        p=copy.deepcopy(base);p['completed_courses']+=['CS3346']*a+['CS3356']*b
        factorial.append({'A_CS3346':a,'B_CS3356':b,'profile':p,'target':'CS4348','result':measure(p,'CS4348')})
    values=[x['result']['advertised_marginal_utility'] for x in factorial]
    interaction=round(values[3]-values[1]-values[2]+values[0],8);assert interaction==6.
    # Formal OR prerequisite gate is a different kind of interaction.
    gate=[]
    for a,b in [(0,0),(1,0),(0,1),(1,1)]:
        p=profile('CS',['CS1302A','CS2310','CS2402']+['CS3481']*a+['CS4486']*b,'Data Science')
        gate.append({'A_CS3481':a,'B_CS4486':b,'result':measure(p,'CS4487')})
    assert [x['result']['known_prerequisite_satisfied'] for x in gate]==[False,True,True,True]
    save('paired_results.json',pairs);save('grade_controls.json',grades);save('factorial.json',{'cases':factorial,'reward_interaction':interaction,'gate_cases':gate})
    save('protocol.json',{'seed':20261121,'design':'Predeclared paired computational intervention; not causal evidence of actual learning or workload savings.',
      'target_estimand':'Within-target change in advertised marginal utility, decomposed into base, preparation, stream and prerequisite-bridge components.',
      'frozen':{'year':2,'base_profit':3,'scores':{'background_mismatch':.2,'difficulty':.2,'workload':.2},'lambdas':[1,1,1],'cost':.6},
      'excluded_confounds':['earned-credit progress','GE count quotas','year-priority bonuses','overload','semester competition'],
      'phase2':'Use identical complete candidate sets, timetable facts, lambda values and required courses; compare plan selection and rank separately. A changed reward need not change an optimal schedule.',
      'phase3':'Four predeclared SE factorial model probes, greedy decoding, current v6 weights, exact raw JSON grading. Rule fallback is reported separately, never a model pass.',
      'empirical_followup':'To validate real preparation benefits, collect authorized prior-grade/target-assessment/time-spent data with comparable backgrounds; use held-out cohorts and uncertainty intervals. Do not interpret policy agreement as educational causality.'})
    requests=[]
    from programme_training_v6 import SYSTEM
    for i,c in enumerate(factorial):
        requests.append({'id':'F'+str(i),'messages':model_messages(c['profile'],SYSTEM),'expected':stream_result('CS',c['profile']['completed_courses'],base['selected_stream'])})
    save('model_protocol.json',requests)
    with (OUT/'dependency_effects.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['case','mechanism','source change','target','before utility','after utility','delta','before prerequisite','after prerequisite'])
        for r in pairs:w.writerow([r['id'],r['mechanism'],r['source_change'],r['target'],r['before']['advertised_marginal_utility'],r['after']['advertised_marginal_utility'],r['observed_delta'],r['before']['known_prerequisite_satisfied'],r['after']['known_prerequisite_satisfied']])
    print([(r['id'],r['target'],r['observed_delta']) for r in pairs]);print('Reward interaction',interaction)
def model():
    import torch
    from inference import load,generate_batch
    from programme_training_v6 import ADAPTER
    rows=json.loads((OUT/'model_protocol.json').read_text(encoding='utf-8'));torch.set_num_threads(8);tok,network=load(ADAPTER)
    raw=generate_batch(tok,network,[x['messages'] for x in rows],max_tokens=900);results=[]
    for r,text in zip(rows,raw):
        try:value=json.loads(text)
        except ValueError:value=None
        results.append({**r,'raw_model_response':text,'accepted':exact(r['expected'],value),
          'raw_target_stream_bonus':value.get('course_chain_bonus',{}).get('CS4348') if isinstance(value,dict) else None})
    bonuses=[r['raw_target_stream_bonus'] for r in results];interaction=None
    if all(type(x) in (int,float) for x in bonuses):interaction=bonuses[3]-bonuses[1]-bonuses[2]+bonuses[0]
    save('model_results.json',{'results':results,'passed':sum(r['accepted'] for r in results),'total':4,'raw_model_reward_interaction':interaction,'expected_interaction':6.,'neural_weights_changed':False})
    print('Raw model accepted',sum(r['accepted'] for r in results),'/4','interaction',interaction)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['build','model']);v=a.parse_args();globals()[v.command]()
