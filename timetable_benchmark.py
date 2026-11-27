"""Frozen-data diagnostic: direct Qwen and requested GPT timetable selection."""
import copy,hashlib,json,time,argparse
from pathlib import Path
import project_runtime
from scheduler import solve
from profit_objective import components,settings
from programme_policy import policy
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'reports/timetable-benchmark'
INSTRUCTION='''Choose a semester timetable using only the supplied options and facts. Return a JSON object with status (feasible or infeasible) and selected_option_ids (list). No markdown. Do not invent or repair options. Respect min/max course count, credits, mandatory courses, one bundle per course, at most one distributional GE, and same-day/week overlap. All supplied options already passed programme/known-prerequisite checks; CM EF/CS planning waivers do not grant real registration approval. Maximise sum of option additive_net plus the single selected stream potential gain times stream_multiplier, minus overload. Stream potential=2*distinct completed slots+6 if complete. Use stream_definition (required plus choose options; for AI one core_choice plus choose distinct options with no reuse), and completed_courses. Overload=.25*max(0,credits-(12 in Year 4 else 15))^2. Feasible is not a claim of proven optimality. If no legal plan meets all hard limits return infeasible with an empty list. Teaching weeks and component pairing are shared explicit assumptions.'''
def save(name,v):OUT.mkdir(parents=True,exist_ok=True);(OUT/name).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def build():
 import programme_v6
 original=programme_v6.solve;cases=[]
 specs=[('CM_B_finance','CM_Y2_FINANCE_GE','202702',None),('CM_B_no_finance','CM_Y2_FINANCE_GE','202702','neutral'),
        ('CS_B_AI','CS_Y2_AI_GE','202702',None),('CS_B_difficulty','CS_Y2_AI_GE','202702','difficulty'),
        ('CM_A_missing_options','CM_Y2_FINANCE_GE','202609',None),('CS_A_missing_options','CS_Y2_AI_GE','202609',None)]
 for ident,filename,term,variant in specs:
  p=json.loads((ROOT/f'data/ge-pathway-lambda/{filename}.json').read_text(encoding='utf-8'));p['term']=term
  if variant=='neutral':p['completed_courses']=[c for c in p['completed_courses'] if c!='GE2260']+['GE1105'];p.pop('GE_history',None)
  if variant=='difficulty':p['weights']={'background_mismatch':1,'difficulty':20,'workload':1}
  box=[];programme_v6.solve=lambda value:(box.append(copy.deepcopy(value)) or original(value))
  programme_v6.plan(p,True);problem=box[0]
  # Supply candidates that pass individual source checks; same set for both models.
  eligible=[]
  for o in problem['options']:
   probe={**problem,'options':[o],'required_courses':[o['course_code']],'course_min':1,'credit_min':0}
   if original(probe)['status']=='optimal':eligible.append(o)
  problem['options']=eligible;reference=original(problem);config=settings(problem)
  options=[]
  for o in eligible:
   additive=components([o],problem.get('course_priority_weights',{}),problem.get('graduation_priority_weight',0),problem['weights'],config)
   net=additive['net_profit']+additive['overload_penalty']+problem.get('prerequisite_bridge_bonus',{}).get(o['course_code'],0)
   options.append({'id':o['option_id'],'course':o['course_code'],'credits':o['credits'],
      'additive_net':round(net,6),'GE':o['course_code'].startswith('GE') and o['course_code'] not in ['GE1401','GE1501','GE1601','GE2401'],
      'meetings':[{'day':m['day'],'start':m['start_minute'],'end':m['end_minute'],'weeks':m['weeks']} for m in o['meetings']]})
  stream=reference.get('profit_breakdown',{}).get('selected_stream') or problem.get('selected_stream')
  if stream is None:
   from programme_policy import stream_result
   stream=stream_result(problem['programme'],problem['completed_courses'])['selected_stream']
  query={'case_id':ident,'programme':problem['programme'],'term':term,'year':problem['student_year'],
    'completed_courses':problem['completed_courses'],'course_min':problem['course_min'],'course_max':problem['course_max'],
    'credit_min':problem['credit_min'],'credit_max':problem['credit_max'],'required_courses':problem['required_courses'],
    'selected_stream':stream,'stream_multiplier':problem['stream_reward_multiplier'],
    'stream_definition':policy()['streams'][problem['programme']][stream],'options':options}
  cases.append({'id':ident,'profile':p,'problem':problem,'query':query,'reference':reference})
 programme_v6.solve=original
 save('cases.json',cases);save('protocol.json',{'date':'2026-11-24','cases':6,'instruction':INSTRUCTION,
  'cases_sha256':hashlib.sha256((OUT/'cases.json').read_bytes()).hexdigest(),
  'scope':'Frozen familiar-source diagnostic. Actual saved meeting times; assumed pairing/weeks. Not registration verification or an independent generalisation benchmark.',
  'treatments':['Current fine-tuned Qwen direct selection','GPT-6.1 Sol direct selection'],
  'reference':'Exact common MILP objective; no solver repair counted as model success',
  'decoding':'Qwen greedy/non-thinking; GPT agent reasoning defaults are not identical. No fair latency/cost claim.'})
 batch=INSTRUCTION+'\nReturn a JSON array of six result objects, each adding case_id. No tools or external sources are permitted; reason only over this frozen evidence.\n'+json.dumps([c['query'] for c in cases],separators=(',',':'))
 (OUT/'gpt_request.txt').write_text(batch,encoding='utf-8');print('reference',[(c['id'],c['reference']['status'],len(c['query']['options'])) for c in cases]);print('GPT request chars',len(batch))
def qwen():
 import torch
 from inference import load,generate
 from cm_finance_training import active_adapter
 torch.set_num_threads(8);tok,model=load(active_adapter());results=[]
 for c in json.loads((OUT/'cases.json').read_text(encoding='utf-8')):
  start=time.perf_counter();raw=generate(tok,model,[{'role':'system','content':INSTRUCTION},{'role':'user','content':json.dumps(c['query'],separators=(',',':'))}],max_tokens=450)
  results.append({'case_id':c['id'],'raw':raw,'seconds':time.perf_counter()-start});save('qwen_raw.json',results);print(c['id'],raw,flush=True)
def grade(response,c):
 ref=c['reference'];p=c['problem']
 if not isinstance(response,dict) or response.get('status') not in ['feasible','infeasible'] or not isinstance(response.get('selected_option_ids'),list):return {'valid':False,'reason':'invalid_schema'}
 ids=response['selected_option_ids']
 if response['status']=='infeasible':return {'valid':ref['status']=='infeasible' and not ids,'infeasible_correct':ref['status']=='infeasible' and not ids,'reason':'infeasibility_claim'}
 index={o['option_id']:o for o in p['options']}
 if any(not isinstance(i,str) or i not in index for i in ids) or len(set(ids))!=len(ids):return {'valid':False,'reason':'invented_or_duplicate_option'}
 chosen=[index[i] for i in ids];codes=[o['course_code'] for o in chosen]
 if len(codes)!=len(set(codes)) or not set(p['required_courses'])<=set(codes):return {'valid':False,'reason':'duplicate_course_or_missing_required'}
 fixed={**p,'options':chosen,'required_courses':codes};r=solve(fixed)
 if r['status']!='optimal':return {'valid':False,'reason':'hard_constraints_failed'}
 return {'valid':True,'infeasible_correct':False,'utility':r['objective'],'regret':ref['objective']-r['objective'],
         'optimal':abs(ref['objective']-r['objective'])<1e-6,'courses':codes,'credits':r['credits'],
         'timetable':[{'course':o['course_code'],'option_id':o['option_id'],'meetings':o['meetings']} for o in chosen]}
def summarise():
 cases=json.loads((OUT/'cases.json').read_text(encoding='utf-8'));allrows=[];summary={}
 for label in ['qwen','gpt']:
  responses=json.loads((OUT/(label+'_raw.json')).read_text(encoding='utf-8'));part=[]
  for c in cases:
   r=next(r for r in responses if r['case_id']==c['id'])
   try:value=json.loads(r['raw']) if 'raw' in r else r
   except ValueError:value=None
   g=grade(value,c);row={'model':label,'case_id':c['id'],'response':value,'grade':g,'reference':c['reference']};allrows.append(row);part.append(row)
  feasible=[r for r in part if r['reference']['status']=='optimal'];inf=[r for r in part if r['reference']['status']=='infeasible']
  summary[label]={'valid_feasible_plans':sum(r['grade']['valid'] for r in feasible),'feasible_cases':len(feasible),
    'optimal_feasible_plans':sum(r['grade'].get('optimal',False) for r in feasible),
    'correct_infeasible':sum(r['grade'].get('infeasible_correct',False) for r in inf),'infeasible_cases':len(inf)}
 save('graded_results.json',allrows);save('summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('command',choices=['build','qwen','summarise']);v=a.parse_args();globals()[v.command]()
