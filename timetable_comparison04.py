"""Additional paired profiles, preserving all previous comparison artifacts."""
import argparse,copy,hashlib,json,time
from pathlib import Path
import project_runtime
import timetable_benchmark as previous
from scheduler import solve
from profit_objective import components,settings
from programme_policy import policy,stream_result
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'reports/timetable-comparison04'
def save(name,v):OUT.mkdir(parents=True,exist_ok=True);(OUT/name).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def build():
 if (OUT/'cases.json').exists():raise RuntimeError('Frozen cases already exist')
 cases=json.loads((ROOT/'reports/timetable-benchmark/cases.json').read_text(encoding='utf-8'))
 specs=[('CM_early_analysis','CM_Y2_FINANCE_GE','early_analysis'),
        ('CM_calculus_not_passed','CM_Y2_FINANCE_GE','calculus'),
        ('CM_final_year','CM_Y2_FINANCE_GE','final_year'),
        ('CM_enriched_despite_finance_GE','CM_Y2_FINANCE_GE','enriched'),
        ('CS_data_science','CS_Y2_AI_GE','data_science'),
        ('CS_missing_programming','CS_Y2_AI_GE','programming'),
        ('CS_workload_priority','CS_Y2_AI_GE','workload'),
        ('CS_final_year','CS_Y2_AI_GE','final_year')]
 descriptions={
  'early_analysis':'Year 2 CM, finance GE passed and Analysis (MA3526) already passed.',
  'calculus':'Year 2 CM, finance GE passed; multivariable calculus MA2508 not passed.',
  'final_year':'Year 4 student with the same listed passes; no additional passes inferred from year.',
  'enriched':'Year 2 CM, finance GE passed but explicitly prefers Enriched Mathematics.',
  'data_science':'Year 2 CS, AI GE passed but explicitly prefers Data Science.',
  'programming':'Year 2 CS, AI GE passed; CS2310 not passed.',
  'workload':'Year 2 CS with AI interest; workload penalty increased to 20.'}
 import programme_v6
 original=programme_v6.solve
 for ident,filename,variant in specs:
  p=json.loads((ROOT/f'data/ge-pathway-lambda/{filename}.json').read_text(encoding='utf-8'));p['term']='202702'
  if variant=='early_analysis':p['completed_courses'].append('MA3526')
  if variant=='calculus':p['completed_courses'].remove('MA2508')
  if variant=='final_year':p['year']=4
  if variant=='enriched':p['desired_stream']='Enriched Mathematics'
  if variant=='data_science':p['desired_stream']='Data Science'
  if variant=='programming':p['completed_courses'].remove('CS2310')
  if variant=='workload':p['weights']={'background_mismatch':1,'difficulty':1,'workload':20}
  p['completed_courses']=sorted(set(p['completed_courses']))
  box=[];programme_v6.solve=lambda value:(box.append(copy.deepcopy(value)) or original(value))
  programme_v6.plan(p,True);problem=box[0];eligible=[]
  for o in problem['options']:
   if original({**problem,'options':[o],'required_courses':[o['course_code']],'course_min':1,'credit_min':0})['status']=='optimal':eligible.append(o)
  problem['options']=eligible;ref=original(problem);cfg=settings(problem);options=[]
  for o in eligible:
   a=components([o],problem.get('course_priority_weights',{}),problem.get('graduation_priority_weight',0),problem['weights'],cfg)
   net=a['net_profit']+a['overload_penalty']+problem.get('prerequisite_bridge_bonus',{}).get(o['course_code'],0)
   options.append({'id':o['option_id'],'course':o['course_code'],'credits':o['credits'],'additive_net':round(net,6),
    'GE':o['course_code'].startswith('GE') and o['course_code'] not in ['GE1401','GE1501','GE1601','GE2401'],
    'meetings':[{'day':m['day'],'start':m['start_minute'],'end':m['end_minute'],'weeks':m['weeks']} for m in o['meetings']]})
  stream=problem.get('selected_stream') or stream_result(problem['programme'],problem['completed_courses'])['selected_stream']
  query={'case_id':ident,'programme':problem['programme'],'term':p['term'],'year':p['year'],
   'completed_courses':problem['completed_courses'],'course_min':problem['course_min'],'course_max':problem['course_max'],
   'credit_min':problem['credit_min'],'credit_max':problem['credit_max'],'required_courses':problem['required_courses'],
   'selected_stream':stream,'stream_multiplier':problem['stream_reward_multiplier'],
   'stream_definition':policy()['streams'][problem['programme']][stream],'options':options}
  cases.append({'id':ident,'description':descriptions[variant],'profile':p,'problem':problem,'query':query,'reference':ref})
 programme_v6.solve=original;save('cases.json',cases)
 save('qwen_raw.json',json.loads((ROOT/'reports/timetable-benchmark/qwen_raw.json').read_text(encoding='utf-8')))
 save('gpt_raw.json',json.loads((ROOT/'reports/timetable-benchmark/gpt_raw.json').read_text(encoding='utf-8')))
 batch=previous.INSTRUCTION+'\nReturn a JSON array of eight results, each adding case_id. Read only this evidence; no solver, code execution or external sources.\n'+json.dumps([c['query'] for c in cases[6:]],separators=(',',':'))
 (OUT/'gpt_request.txt').write_text(batch,encoding='utf-8')
 save('protocol.json',{'total_profiles':14,'new_profiles':8,'prior_results_reused_unchanged':6,
  'selection_for_report':'Show only examples whose actual model outputs differ; retain all cases and raw outputs in evidence.',
  'same_per_profile_input':True,'GPT_model':'gpt-6.1-sol, model-specific agent, eight-case batch',
  'Qwen':'current fine-tuned adapter, greedy/non-thinking, separate per-case prompts',
  'limitations':'Fictional profiles and shared source-conditioned options; assumed component linkage/weeks. Not a representative performance estimate.',
  'cases_sha256':hashlib.sha256((OUT/'cases.json').read_bytes()).hexdigest()})
 print([(c['id'],len(c['query']['options'])) for c in cases[6:]])
def qwen():
 import torch
 from inference import load,generate
 from cm_finance_training import active_adapter
 torch.set_num_threads(8);tok,model=load(active_adapter());results=json.loads((OUT/'qwen_raw.json').read_text(encoding='utf-8'))
 for c in json.loads((OUT/'cases.json').read_text(encoding='utf-8'))[6:]:
  start=time.perf_counter();raw=generate(tok,model,[{'role':'system','content':previous.INSTRUCTION},{'role':'user','content':json.dumps(c['query'],separators=(',',':'))}],max_tokens=450)
  results.append({'case_id':c['id'],'raw':raw,'seconds':time.perf_counter()-start});save('qwen_raw.json',results);print(c['id'],raw,flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('command',choices=['build','qwen']);v=a.parse_args();globals()[v.command]()
