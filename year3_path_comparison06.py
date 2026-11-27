"""Year-2 completed profiles -> hypothetical Year-3 Semester-A plan and later path."""
import argparse,copy,hashlib,json
from pathlib import Path
import project_runtime
from scheduler import solve
from profit_objective import components,settings
from programme_policy import policy,stream_result
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'reports/year3-path-comparison06'
SYSTEM='''Plan Year 3 Semester A for a fictional student currently in Year 2. The completed_courses input is the projected end-of-Year-2 passing transcript. Source options are saved Semester A 2026 snapshots used only as a proxy; actual Year-3 offerings are unverified. Use only supplied option IDs, at most one per course, no already-passed course, required courses, credit/count bounds, no meeting overlap. Candidates already passed individual programme/prerequisite checks, including the user-assumed CM EF/CS waiver. Maximise additive_net plus selected-stream potential gain*multiplier minus .25*max(0,credits-15)^2. Stream potential=2*distinct slots+6 once complete; AI core/elective slots cannot reuse a course. Return JSON with case_id,status(feasible/infeasible),selected_option_ids,and future_path (one short English sentence, maximum 35 words). If fewer legal courses than course_min or no legal combination, return infeasible and empty IDs. Explain how the given passed/missing course or explicit stream changes the later academic path. Later course suggestions must come from the supplied stream definition or missing prerequisite list, and be conditional on passing current selections. Do not invent future availability, passes, stream credit or graduation. No markdown or extra evidence.'''
def save(name,v):OUT.mkdir(parents=True,exist_ok=True);(OUT/name).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def build():
 if (OUT/'cases.json').exists():raise RuntimeError('Frozen data already exists.')
 cm=['MA1300','MA1301','CS1302','MA2503','MA2508','MA2509','CS2360','MA2507','MA2510','MA3511','MA3526','CS2468','GE1401','GE1501','GE2401']
 cs=['CS1302A','CS2115','CS2310','CS2312','CS2402','CS3201','CS3334','CS3342','CS3103','MA1503','MA1508','MA2185','GE1401','GE1501','GE1601']
 specs=[('CM_finance_analysis','CM',cm+['GE2260'],'Financial Mathematics','Finance GE and Analysis passed.'),
 ('CM_finance_no_analysis','CM',[c for c in cm if c!='MA3526']+['GE2260'],'Financial Mathematics','Same CM profile, but Analysis is not passed.'),
 ('CM_enriched','CM',cm+['GE2260'],'Enriched Mathematics','Same passed CM courses and finance GE; explicitly prefers Enriched Mathematics.'),
 ('CS_AI','CS',cs+['GE2340'],'Artificial Intelligence','AI GE and CS3342 passed; prefers AI.'),
 ('CS_AI_no_CS3342','CS',[c for c in cs if c!='CS3342']+['GE2340'],'Artificial Intelligence','Same CS profile, but CS3342 is not passed.'),
 ('CS_data_science','CS',cs+['GE2340'],'Data Science','Same passed CS courses and AI GE; explicitly prefers Data Science.')]
 import programme_v6
 original=programme_v6.solve;cases=[]
 for ident,major,done,stream,description in specs:
  p={'profile_id':ident,'programme':major,'programme_code':'BSCSIU4' if major=='CM' else 'BSCCCU4','cohort':2025,
   'current_year':2,'year':3,'term':'202609','completed_courses':sorted(done),'desired_stream':stream,'stream_reward_multiplier':3.}
  box=[];programme_v6.solve=lambda problem:(box.append(copy.deepcopy(problem)) or original(problem))
  programme_v6.plan(p,True);problem=box[0];eligible=[]
  for o in problem['options']:
   if original({**problem,'options':[o],'required_courses':[o['course_code']],'course_min':1,'credit_min':0})['status']=='optimal':eligible.append(o)
  problem['options']=eligible;cfg=settings(problem);options=[]
  for o in eligible:
   a=components([o],problem.get('course_priority_weights',{}),problem.get('graduation_priority_weight',0),problem['weights'],cfg)
   net=a['net_profit']+a['overload_penalty']+problem.get('prerequisite_bridge_bonus',{}).get(o['course_code'],0)
   options.append({'id':o['option_id'],'course':o['course_code'],'credits':o['credits'],'additive_net':round(net,6),
    'meetings':[{'day':m['day'],'start':m['start_minute'],'end':m['end_minute'],'weeks':m['weeks']} for m in o['meetings']]})
  query={'case_id':ident,'current_year':2,'planning_year':3,'planning_semester':'A','planning_term':'202709 (unverified)',
   'proxy_source_term':'202609','programme':major,'profile_difference':description,'completed_courses':p['completed_courses'],
   'selected_stream':stream,'stream_multiplier':3,'stream_definition':policy()['streams'][major][stream],
   'course_min':problem['course_min'],'course_max':problem['course_max'],'credit_min':problem['credit_min'],'credit_max':problem['credit_max'],
   'required_courses':problem['required_courses'],'options':options,
   'missing_prerequisite_notes':['CS3342 is missing; normally needed before CS3383'] if ident=='CS_AI_no_CS3342' else
    ['MA3526 is missing; upper-level analysis-dependent routes need that pass first'] if ident=='CM_finance_no_analysis' else []}
  cases.append({'id':ident,'profile':p,'description':description,'problem':problem,'query':query,'reference':original(problem)})
 programme_v6.solve=original;save('cases.json',cases)
 save('protocol.json',{'current_year':2,'planning_year':3,'planning_semester':'A','future_term':'202709','proxy_term':'202609',
  'fictional_end_of_Year2_transcripts':True,'profiles':6,'paired_factors':['MA3526 pass','explicit CM stream','CS3342 pass','explicit CS stream'],
  'blind_definition':'Neither model receives other-model outputs or the solver reference.',
  'same_per_profile_payload':True,'future_availability_verified':False,'Qwen':'greedy/non-thinking; separate cases',
  'GPT':'requested gpt-6.1-sol model-specific agent; six-case batch','instruction':SYSTEM,
  'cases_sha256':hashlib.sha256((OUT/'cases.json').read_bytes()).hexdigest()})
 (OUT/'gpt_request.txt').write_text(SYSTEM+'\nReturn a JSON array of all six responses. No tools beyond reading this packet; no code/solver/external evidence.\n'+json.dumps([c['query'] for c in cases],separators=(',',':')),encoding='utf-8')
 print([(c['id'],len(c['query']['options']),c['reference']['status']) for c in cases])
def qwen():
 import torch
 from inference import load,generate
 from cm_finance_training import active_adapter
 torch.set_num_threads(8);tok,model=load(active_adapter());results=[]
 for c in json.loads((OUT/'cases.json').read_text(encoding='utf-8')):
  response=generate(tok,model,[{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(c['query'],separators=(',',':'))}],max_tokens=500)
  results.append({'case_id':c['id'],'raw':response});save('qwen_raw.json',results);print(c['id'],response,flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('command',choices=['build','qwen']);v=a.parse_args();globals()[v.command]()
