"""Fine-tune the corrected EF section and flexible-load terminal-degree policy."""
import argparse,copy,hashlib,json,random,sys
from pathlib import Path
import project_runtime
import timetable_grounded_training as old
from programme_policy import exact
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data/degree-chain-policy';REPORT=ROOT/'reports/degree-chain-policy';ADAPTER='adapters/degree-chain-policy'
SYSTEM=old.SYSTEM+''' For task degree_policy return semester_min_courses=0, graduation_min_credits=122, satisfies_user_121, meets_source_122, and chain_accepted. Accept the whole chain only at semester 8 with at least 122 credits and other_graduation_requirements_met=true. 121 alone is insufficient for these supplied degree documents. A semester with 1,2,3 or 4 courses may be legal. Repeating A/B snapshots is authorised only as a simulation assumption, never actual future-year verification. Section EF3320 CA1 CRN11425 is Semester B 202702, Friday16:00-18:50, not for College CB; non-CB CM students are not blocked merely because it lacks an ONLY FOR CM label. EF3320:10000 and Semester-A placement remain unsupported.'''
SYSTEM+=''' Search for the best reward path found; no proof of global optimality is required. The hard full-chain credit requirement stays 122. An infeasible candidate may be displayed separately with a terminal penalty of 1000000 per missing credit, but must never be labelled a graduating chain. This changes planner ranking, not the supervised-loss definition.'''
SYSTEM+=''' If and only if the input explicitly requests degree_mode=curriculum_with_pending, a document-listed course without saved meetings may be included in the curriculum path with evidence_status=pending_timetable and null meetings/CRN. Its offering and eligibility are unverified. The curriculum must still satisfy at least 122 unique credits and every encoded graduation requirement; a pending curriculum path is not a complete registration timetable. Never add passed courses to the supplied historical transcript. Without this mode, missing timetable evidence remains a hard exclusion and incomplete paths are diagnostic only.'''
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def target(s):
    c=s['earned_credits'];return {'semester_min_courses':0,'graduation_min_credits':122,
      'satisfies_user_121':c>=121,'meets_source_122':c>=122,
      'chain_accepted':s['semester']==8 and c>=122 and s['other_graduation_requirements_met']}
def degree_messages(s):return [{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps({'task':'degree_policy',**s})}]
def semester_messages(problem):
    ms=old.schedule_messages(problem);ms[0]={'role':'system','content':SYSTEM};return ms
def build():
    if (DATA/'train.jsonl').exists():raise RuntimeError('Dataset frozen')
    rows=[];rng=random.Random(2026112409)
    for c in [0,72,114,120,121,122,123,144]:
      for sem in [1,4,7,8]:
       for complete in [False,True]:
        s={'semester':sem,'earned_credits':c,'other_graduation_requirements_met':complete}
        rows.append({'id':f'degree:{c}:{sem}:{complete}','task':'degree_policy','messages':degree_messages(s)+[{'role':'assistant','content':json.dumps(target(s))}]})
    # Boundary variants use different totals, separate from terminal tests.
    rng.shuffle(rows);split={'test':rows[:16],'validation':rows[16:28],'train':rows[28:]}
    from timetable_grounded_training import problem_for,schedule_target
    profiles=[c['profile'] for c in json.loads((ROOT/'reports/timetable-retest07/cases.json').read_text())]
    for major in ['CM','CS']:
      for term in ['202609','202702']:
        profiles.append({'programme':major,'programme_code':'BSCSIU4' if major=='CM' else 'BSCCCU4','cohort':2025,'year':1,'term':term,'completed_courses':[]})
    for i,p in enumerate(profiles):
      for term in ['202609','202702']:
        p={**p,'term':term,'course_min':0};problem=problem_for(p)
        split['train'].append({'id':f'load:{i}:{term}','task':'flexible_timetable','messages':semester_messages(problem)+[{'role':'assistant','content':json.dumps(schedule_target(problem))}]})
    for code in ['EF3320','EF4821']:
      for term in ['202609','202702']:
       for bg in [[],['GE1202'],['EF3320']]:
        p={'programme':'CM','programme_code':'BSCSIU4','cohort':2025,'year':2,'term':term,'completed_courses':bg}
        ms=old.messages(p,code);ms[0]={'role':'system','content':SYSTEM}
        split['train'].append({'id':f'EF:{code}:{term}:{bg}','task':'EF_section','messages':ms+[{'role':'assistant','content':json.dumps(old.assessment(p,code))}]})
    replay=[json.loads(x) for x in (ROOT/'data/gpt-course-relations/train.jsonl').read_text().splitlines() if json.loads(x)['task']=='GPT_preparation_reward']
    rng.shuffle(replay);split['train'] += [{**r,'id':'replay:'+r['id']} for r in replay[:24]]
    for name,items in split.items():(DATA/(name+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in items),encoding='utf-8')
    tests=copy.deepcopy(split['test'])
    for code,term in [('EF3320','202702'),('EF3320','202609')]:
      p={'programme':'CM','programme_code':'BSCSIU4','cohort':2025,'year':2,'term':term,'completed_courses':['MA2510'],'finance_background':True}
      ms=old.messages(p,code);ms[0]={'role':'system','content':SYSTEM}
      tests.append({'id':'EF-diagnostic:'+term,'task':'EF_section','messages':ms+[{'role':'assistant','content':json.dumps(old.assessment(p,code))}]})
    # New profile variants, not the three old report selections.
    for major in ['CM','CS']:
      p={'programme':major,'programme_code':'BSCSIU4' if major=='CM' else 'BSCCCU4','cohort':2025,'year':2,'term':'202609','completed_courses':['MA1300'] if major=='CM' else ['CS1302A']}
      problem=problem_for(p);tests.append({'id':'load-diagnostic:'+major,'task':'flexible_timetable','problem':problem,
        'messages':semester_messages(problem)+[{'role':'assistant','content':json.dumps(schedule_target(problem))}]})
    save(REPORT/'evaluation_cases.json',tests)
    parent=json.loads((ROOT/'data/active_grounded_adapter.json').read_text())['adapter']
    save(REPORT/'protocol.json',{'parent_adapter':parent,'splits':{k:len(v) for k,v in split.items()},
       'policy':'No fixed five-course minimum; full eight-term chain must satisfy source minimum 122 and all other graduation rules.',
       'user_authorised_repeating_AB':True,'scope':'Synthetic rule distillation and source-evidence diagnostics, not real-student generalisation.'})
    print(parent,{k:len(v) for k,v in split.items()},flush=True)
def evaluate(label):
    import torch
    from inference import load,generate
    from markov_planner import validate_proposal
    torch.set_num_threads(8);sys.setrecursionlimit(5000)
    parent=json.loads((REPORT/'protocol.json').read_text())['parent_adapter'];tok,model=load(parent if label=='before' else ADAPTER);results=[]
    for r in json.loads((REPORT/'evaluation_cases.json').read_text()):
        raw=generate(tok,model,r['messages'][:-1],max_tokens=260)
        try:value=json.loads(raw)
        except ValueError:value=None
        expected=json.loads(r['messages'][-1]['content']);passed=exact(expected,value)
        if r['task']=='flexible_timetable' and isinstance(value,dict):passed=value.get('status')=='feasible' and validate_proposal(r['problem'],value)['accepted']
        results.append({'id':r['id'],'task':r['task'],'raw':raw,'expected':expected,'passed':passed});save(REPORT/(label+'_predictions.json'),results)
        print(label,len(results),passed,flush=True)
    save(REPORT/(label+'_evaluation.json'),{'passed':sum(r['passed'] for r in results),'total':len(results)})
def release():
    before=json.loads((REPORT/'before_evaluation.json').read_text());after=json.loads((REPORT/'after_evaluation.json').read_text())
    accepted=after['passed']>=18 and after['passed']>=before['passed']
    value={'adapter':ADAPTER,'report_dir':'reports/degree-chain-policy','accepted_for_activation':accepted,'before':before,'after':after,
      'sha256':hashlib.sha256((ROOT/ADAPTER/'adapter_model.safetensors').read_bytes()).hexdigest(),
      'scope':'Flexible semester timetable and hard terminal degree-credit policy; general/relations checkpoints preserved.'}
    save(REPORT/'release.json',value)
    if accepted:
        save(REPORT/'previous_grounded_adapter.json',json.loads((ROOT/'data/active_grounded_adapter.json').read_text()))
        save(ROOT/'data/active_grounded_adapter.json',value)
    print(json.dumps(value,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','before','after','release']);a=p.parse_args()
    if a.command in ['before','after']:evaluate(a.command)
    else:globals()[a.command]()
