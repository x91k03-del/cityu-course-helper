"""Six fresh model queries with complete fictional inputs and solver outputs."""
import copy,hashlib,json,time
from four_year_markov import *
from preparation_training import model_messages
OUT=ROOT/'reports/input-output-examples'
def main():
    import torch
    from scipy.optimize import milp
    from inference import load,generate_batch
    OUT.mkdir(parents=True,exist_ok=True)
    base=read(ROOT/'reports/preparation-v5/model_rollouts.json')[0]
    prefix=[copy.deepcopy(r) for r in base['transcript'] if r['term']<4]
    # Fresh controlled transcripts: other passing grades are held at B.
    for row in prefix:row['grade']='B'
    failed_calc=copy.deepcopy(prefix);failed_discrete=copy.deepcopy(prefix)
    for row in failed_calc:
        if row['id']=='MA2508':row['grade']='F'
    for row in failed_discrete:
        if row['id']=='MA2509':row['grade']='F'
    early=copy.deepcopy(prefix)
    _,extra=transition(state_from([r for r in prefix if r['term']<2],2),['MA3526'],{'MA3526':'B'})
    early+=extra;early.sort(key=lambda r:(r['term'],r['id']))
    y4a=[copy.deepcopy(r) for r in base['transcript'] if r['term']<7]
    y4b=[copy.deepcopy(r) for r in base['transcript'] if r['term']<8]
    for row in y4a+y4b:row['grade']='B'
    specs=[('E01','Year 2: calculus and discrete mathematics passed',4,prefix,
              'Baseline: both preparation sources passed; Analysis has not yet been completed.'),
           ('E02','Year 2: calculus failed',4,failed_calc,
              'Only MA2508 changes from B to F relative to E01. Earned credits and eligibility are recomputed.'),
           ('E03','Year 2: discrete mathematics failed',4,failed_discrete,
              'Only MA2509 changes from B to F relative to E01. It earns no credit and gives no critical-thinking preparation benefit.'),
           ('E04','Year 2: Analysis completed early',4,early,
              'Adds a passed MA3526 in Year 1 Semester B, a route permitted by the supplied study path. Other attempts match E01.'),
           ('E05','Year 4 A: elective maths quota still short',7,y4a,
              'A transcript-based Year 4 A profile with 18 earned elective maths credits; at least 20 are required.'),
           ('E06','Year 4 B: elective maths quota reached',8,y4b,
              'A transcript-based Year 4 B profile with 24 earned elective maths credits. The progress bonus should stop.')]
    cases=[]
    for ident,title,term,history,note in specs:
        s=state_from(history,term)
        cases.append({'id':ident,'title':title,'note':note,'state':s,'transcript':history,'messages':model_messages(s,history)})
    torch.set_num_threads(8);tok,model=load(ADAPTER)
    for start in range(0,len(cases),3):
        group=cases[start:start+3];tic=time.perf_counter()
        raw=generate_batch(tok,model,[c['messages'] for c in group],max_tokens=420)
        for c,text in zip(group,raw):
            c['raw_model_output']=text
            try:value=json.loads(text)
            except (ValueError,TypeError):value=None
            c['parsed_model_output']=value;c['model_output_accepted']=parameter_grade(c['state'],value)
            if not c['model_output_accepted']:raise RuntimeError('Fresh model response failed policy validation: '+c['id'])
            sol=solve_remaining(c['state'],value)
            c['solver_output']=sol
            if sol['status']!='optimal':raise RuntimeError('Example infeasible: '+c['id']+' '+str(sol))
            after,rows=transition(c['state'],sol['current_selection'])
            c['current_semester_courses']=rows;c['current_semester_profit']=reward(c['state'],sol['current_selection'],value,after)
            c['current_semester_assumption']='All currently selected courses are assumed passed for the displayed realized-profit calculation. Future grades and class meetings are not predicted.'
            continuation=copy.deepcopy(c['transcript']);state=copy.deepcopy(c['state'])
            for t in range(state['term'],9):
                state['term']=t;state['year']=(t+1)//2;state['semester']='A' if t%2 else 'B'
                state,new=transition(state,sol['forecast'][str(t)])
                continuation+=new
            c['forecast_terminal_audit']=audit(continuation)
            if not c['forecast_terminal_audit']['all_encoded_requirements_met']:raise RuntimeError('Forecast audit failed '+c['id'])
            print(c['id'],'accepted',c['state']['earned_credits'],sol['current_selection'],flush=True)
        print('Batch seconds',round(time.perf_counter()-tic,1),flush=True)
        write(OUT/'examples.partial.json',cases)
    result={'model':ADAPTER,'model_sha256':hashlib.sha256((ROOT/ADAPTER/'adapter_model.safetensors').read_bytes()).hexdigest(),
       'report_date_Hong_Kong':'2026-11-16','generation':'Fresh local Qwen3-8B v5 inference; greedy decoding; batch size three; max_new_tokens 420; non-thinking.',
       'scope':'Fictional controlled examples, not independent held-out accuracy estimates. Model outputs parameters; the solver outputs schedules.',
       'system_prompt':SYSTEM,'cases':cases}
    write(OUT/'examples.json',result)
if __name__=='__main__':main()
