"""Paired Qwen/GPT retest with updated reward inputs and exact snapshot options."""
import argparse,copy,hashlib,json
from pathlib import Path
import project_runtime
from timetable_grounded_training import problem_for
from markov_planner import Rules,solve,validate_proposal
from profit_objective import components,settings
from programme_policy import policy
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'reports/timetable-retest07'
SYSTEM='''Return JSON only. Plan a Year-3 Semester-A workload for the supplied synthetic end-of-Year-2 transcript using ONLY the supplied exact Semester-A snapshot options. This is a controlled captured-term scenario, not evidence of actual future-year offerings. Select 5-6 distinct courses, at most 18 credits, one option per course, required courses and credit limits, no meeting overlap, at most one distributional GE. Individual eligibility has already been checked, including the user CM EF/CS prerequisite waiver; all remaining constraints still bind. Maximise sum(additive_net) plus stream_multiplier times the gain in stream potential, minus .25*max(0,total credits-15)^2. The updated GPT-teacher preparation bonus is ALREADY included in additive_net: do not add it twice. Stream potential is 2*fulfilled distinct slots +6 once complete; AI core/elective slots cannot reuse one course. If no legal five-course combination exists, return infeasible and empty IDs. Use only supplied IDs. Return exactly case_id,status(feasible/infeasible),selected_option_ids,future_path. Future_path is one sentence at most 35 words: explain the academic next step using only stream members or supplied missing-study notes, conditional on passing current selections and compatible future timetables. Do not invent future offerings, passes or stream credit.'''

def save(name,value):OUT.mkdir(parents=True,exist_ok=True);(OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def build():
    if (OUT/'cases.json').exists():raise RuntimeError('Frozen comparison already exists.')
    old=json.loads((ROOT/'reports/year3-path-comparison06/cases.json').read_text());specs=[(c['id'],c['profile'],c['description']) for c in old]
    base=copy.deepcopy(old[0]['profile'])
    for code,label in [('MA2510','CM_finance_no_statistics'),('MA2503','CM_finance_no_linear_algebra')]:
        p=copy.deepcopy(base);p['completed_courses'].remove(code);p['profile_id']=label
        specs.append((label,p,'Matched finance profile without '+code+' passed.'))
    cases=[]
    for ident,p,desc in specs:
        problem=problem_for(p);problem['options']=Rules(problem).eligible;cfg=settings(problem)
        options=[]
        for o in problem['options']:
            parts=components([o],problem.get('course_priority_weights',{}),problem.get('graduation_priority_weight',0),problem['weights'],cfg)
            options.append({'id':o['option_id'],'course':o['course_code'],'credits':o['credits'],
              'additive_net':round(parts['net_profit']+parts['overload_penalty']+problem.get('prerequisite_bridge_bonus',{}).get(o['course_code'],0),6),
              'included_preparation_bonus':parts['preparation_benefit'],
              'meetings':[{'day':m['day'],'start':m['start_minute'],'end':m['end_minute'],'weeks':m['weeks']} for m in o['meetings']]})
        stream=problem['selected_stream'];rules=policy()['streams'][p['programme']][stream]
        notes=[]
        for code in ['MA3526','MA2510','MA2503','CS3342']:
            if code not in p['completed_courses'] and code.startswith('MA' if p['programme']=='CM' else 'CS'):notes.append(code+' is not passed; do not infer a pass from year of study.')
        query={'case_id':ident,'input_year':2,'workload_planning_year':3,'semester':'A','exact_snapshot_term':'202609',
          'future_year_offerings_verified':False,'programme':p['programme'],'completed_courses':p['completed_courses'],
          'profile_difference':desc,'selected_stream':stream,'stream_definition':rules,'stream_multiplier':problem['stream_reward_multiplier'],
          'course_min':problem['course_min'],'course_max':problem['course_max'],'credit_min':problem['credit_min'],'credit_max':problem['credit_max'],
          'required_courses':problem['required_courses'],'missing_study_notes':notes,'options':options}
        cases.append({'id':ident,'profile':p,'query':query,'problem':problem,'reference':solve(problem)})
    save('cases.json',cases)
    (OUT/'gpt_request.txt').write_text(SYSTEM+'\nReturn a JSON array with all eight answers. You may read only this packet, then write your answers. No code, solver, browsing or other model outputs.\n'+json.dumps([c['query'] for c in cases],separators=(',',':')),encoding='utf-8')
    save('protocol.json',{'profiles':8,'familiar_prior_profiles':6,'new_matched_variations':2,
      'comparison':'Deployed Qwen timetable checkpoint versus requested GPT-6.1 Sol, identical updated reward inputs.',
      'blind_to_other_outputs_and_reference':True,'independent_unseen_document_benchmark':False,
      'term':'202609','actual_future_offerings_verified':False,'instruction':SYSTEM,
      'active_preparation_graph':json.loads((ROOT/'data/active_preparation_graph.json').read_text()),
      'Qwen_adapter':json.loads((ROOT/'data/active_grounded_adapter.json').read_text())['adapter'],
      'cases_sha256':hashlib.sha256((OUT/'cases.json').read_bytes()).hexdigest()})
    print([(c['id'],len(c['query']['options']),c['reference']['status']) for c in cases])

def qwen():
    import torch
    from inference import load,generate
    torch.set_num_threads(8)
    adapter=json.loads((OUT/'protocol.json').read_text())['Qwen_adapter'];tok,model=load(adapter);rows=[]
    for c in json.loads((OUT/'cases.json').read_text()):
        raw=generate(tok,model,[{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(c['query'],separators=(',',':'))}],max_tokens=500)
        rows.append({'case_id':c['id'],'raw':raw});save('qwen_raw.json',rows);print(c['id'],raw,flush=True)

def assess():
    cases=json.loads((OUT/'cases.json').read_text());models={}
    for model in ['qwen','gpt']:
        models[model]={r['case_id']:json.loads(r['raw']) if 'raw' in r else r for r in json.loads((OUT/(model+'_raw.json')).read_text())}
    results=[]
    for c in cases:
        row={'case_id':c['id'],'profile':c['profile'],'reference':c['reference']}
        for name,records in models.items():
            raw=records[c['id']];ids=raw.get('selected_option_ids',[])
            if raw.get('status')=='infeasible':accepted=not ids and c['reference']['status']=='infeasible';validation={'accepted':accepted,'violations':[] if accepted else ['unsupported_infeasibility_claim']}
            else:validation=validate_proposal(c['problem'],raw);accepted=validation['accepted']
            opts={o['option_id']:o for o in c['problem']['options']};chosen=[opts[x] for x in ids if x in opts]
            net=None
            if accepted and chosen:
                from programme_policy import chain_reward
                p=c['problem'];parts=components(chosen,p.get('course_priority_weights',{}),p.get('graduation_priority_weight',0),p['weights'],settings(p))
                net=parts['net_profit']+sum(p.get('prerequisite_bridge_bonus',{}).get(o['course_code'],0) for o in chosen)+p['stream_reward_multiplier']*chain_reward(p['programme'],p['completed_courses'],p['selected_stream'],[o['course_code'] for o in chosen])
            row[name]={'raw_answer':raw,'accepted':accepted,'validation':validation,'course_codes':[o['course_code'] for o in chosen],
                'course_count':len(chosen),'net_reward':net,'reward_regret':None if net is None else c['reference']['objective']-net}
        results.append(row)
    save('comparison.json',results)
    save('summary.json',{m:{'accepted':sum(r[m]['accepted'] for r in results),'total':len(results),
       'feasible_schedules':sum(r[m]['accepted'] and r[m]['course_count']>0 for r in results)} for m in ['qwen','gpt']})
    print([(r['case_id'],r['qwen']['course_codes'],r['gpt']['course_codes'],r['qwen']['accepted'],r['gpt']['accepted']) for r in results])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','qwen','assess']);a=p.parse_args();globals()[a.command]()
