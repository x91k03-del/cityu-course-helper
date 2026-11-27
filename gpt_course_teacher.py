"""GPT-authored course preparation policy and supervised Qwen distillation."""
import argparse,copy,hashlib,json,random,sys
from pathlib import Path
import project_runtime
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data/gpt-course-relations';REPORT=ROOT/'reports/gpt-course-relations'
ADAPTER='adapters/gpt-course-relations'
SYSTEM='''Return JSON only. Use the supplied GPT-teacher direct preparation relationships as advisory utility, not statistical correlations or prerequisites. Only passed courses count. F, IP and W do not count. Use the maximum applicable direct edge, capped at 0.35, not the sum. No recursive, same-semester or self-course bonus. A completed target receives zero new-course benefit. Return target, preparation_bonus, strongest_sources (all tied strongest direct passed sources, sorted). Timetable, programme, prerequisite and stream rules are enforced separately and are never overridden by preparation.'''

def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def create_graph():
    original=json.loads((ROOT/'data/preparation-v5.json').read_text());g=copy.deepcopy(original)
    g.update(teacher='GPT assistant in the current Codex conversation; no separate GPT-6.1-sol API call claimed',
      interpretation='GPT content-based preparation hypotheses; not empirical causal effects or measured workload reductions. Strongest direct prior pass only; no sum or recursion.',
      created_date_Hong_Kong='2026-11-24',source_access='Saved course aims, prior source-indexed syllabus evidence and official catalogue evidence listed per edge. Historical sources retain their scope.')
    additions=[
      ('MA2510','MA3518',.30,'Probability, estimation and testing foundations support applied statistical analysis.','statistics'),
      ('MA2503','MA3525',.25,'Matrix/vector manipulation supports numerical linear-system methods; numerical error analysis remains new.','linear_algebra'),
      ('MA3511','MA3512',.30,'Differential-equation solution methods support learning PDE models; extra spatial variables introduce new theory.','differential_equations'),
      ('MA3525','MA3514',.25,'Approximation and numerical error concepts support computational differential equations.','numerical_methods'),
      ('MA3526','MA4542',.25,'Proofs, limits and convergence support advanced real-analysis reasoning.','analysis'),
      ('MA2510','MA3521',.25,'Probability, expectations and uncertainty prepare for mathematical treatment of finance.','probability'),
      ('MA3521','MA4529',.30,'Introductory mathematical finance prepares for later financial modelling; new methods remain to be learned.','financial_mathematics'),
      ('MA2510','MA4546',.25,'Distributions and conditional expectations support random-process reasoning.','probability'),
      ('MA2503','EF3320',.20,'Covariance matrices and quadratic forms offer mathematical preparation for portfolio risk.','portfolio_mathematics'),
      ('MA3515','EF3320',.25,'Constrained optimisation helps interpret portfolio weights and risk-return tradeoffs.','portfolio_optimisation'),
      ('GE1202','EF3320',.10,'Introductory financial planning provides investment vocabulary, not advanced valuation skills.','finance_vocabulary'),
      ('GE2260','EF3320',.10,'Introductory finance study provides limited risk-return vocabulary, not quantitative competence.','finance_vocabulary'),
      ('CS1302','CS2360',.20,'Python programming concepts transfer to learning Java control flow and program structure; language details differ.','programming'),
      ('CS1302A','CS2360',.20,'Prior Python programming provides transferable procedural concepts for Java.','programming'),
      ('CS2360','CS2468',.25,'Java implementation practice helps implement and test data structures.','data_structures'),
      ('CS2468','CS4335',.25,'Data-structure operations and representation costs support algorithm design.','algorithms'),
      ('CS3334','CS4335',.30,'Heaps, trees, hashing and algorithm-analysis practice support advanced algorithm design.','algorithms'),
      ('MA2509','CS3334',.20,'Counting, relations and graph reasoning support analysis of discrete data structures.','discrete_structures'),
      ('MA2503','CS4487',.25,'Vectors and matrices provide representations for data and model parameters.','machine_learning'),
      ('MA2510','CS4487',.25,'Probability and statistical reasoning support uncertainty and model evaluation.','machine_learning'),
      ('MA3515','CS4487',.25,'Optimisation concepts help interpret model fitting and loss minimisation.','machine_learning'),
      ('MA3518','CS4487',.20,'Applied data analysis and inference provide limited preparation for empirical model assessment.','machine_learning'),
      ('GE2340','CS4487',.10,'AI vocabulary and motivation offer limited orientation, not programming or mathematical competence.','AI_orientation')]
    deep=json.loads((ROOT/'data/deep_course_relations.json').read_text())
    for source,target,benefit,reason,topic in additions:
        refs=[deep.get('content_sources',{}).get(target,'Saved curriculum title plus GPT disciplinary deduction')]
        if target=='CS4487':refs=['https://www.cityu.edu.hk/catalogue/ug/current/course/CS4487.htm','https://www.cityu.edu.hk/catalogue/ug/202526/course/CS4487.pdf']
        if target=='MA3518':refs=['https://www.cityu.edu.hk/catalogue/ug/202425/course/MA3518.htm']
        if source.startswith('CS') or target in ('CS2360','CS2468','CS3334'):refs+=['data/courses.jsonl: saved course aims for CS1302/CS1302A/CS2360/CS2468/CS3334']
        g['edges'].append({'source':source,'target':target,'benefit':benefit,'reason':reason,'topic':topic,
            'confidence':'GPT_content_deduction_not_empirically_calibrated','evidence':refs,'formal_prerequisite':False})
    save(DATA/'reward_graph.json',g)
    save(ROOT/'data/active_preparation_graph.json',{'path':'data/gpt-course-relations/reward_graph.json',
        'teacher':g['teacher'],'aggregation':'strongest_direct_passed_edge','cap':.35})
    return g

def target(rows,code,g):
    from preparation import PASS
    done={r['course_code'] for r in rows if r['grade'] in PASS}
    edges=[e for e in g['edges'] if e['target']==code and e['source'] in done and code not in done and e['source']!=code]
    value=min(.35,max([0.]+[e['benefit'] for e in edges]))
    return {'target':code,'preparation_bonus':value,'strongest_sources':sorted({e['source'] for e in edges if e['benefit']==value})}

def messages(rows,code,g):
    return [{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps({'transcript':rows,'target':code,
        'direct_teacher_edges':[e for e in g['edges'] if e['target']==code]})}]

def build():
    if (DATA/'train.jsonl').exists():raise RuntimeError('Frozen teacher dataset exists.')
    g=create_graph();rows=[];rng=random.Random(20261124)
    for code in sorted({e['target'] for e in g['edges']}):
        sources=sorted({e['source'] for e in g['edges'] if e['target']==code})
        histories=[[]]
        histories += [[{'course_code':s,'grade':grade}] for s in sources for grade in ['B','F','IP','W']]
        histories += [[{'course_code':s,'grade':'B'} for s in sources], [{'course_code':code,'grade':'B'}], [{'course_code':'GE1305','grade':'B'}]]
        unique={json.dumps(x,sort_keys=True):x for x in histories}
        for n,h in enumerate(unique.values()):rows.append({'id':f'relation:{code}:{n}','task':'GPT_preparation_reward',
          'messages':messages(h,code,g)+[{'role':'assistant','content':json.dumps(target(h,code,g))}]})
    rng.shuffle(rows);splits={'test':rows[:20],'validation':rows[20:40],'train':rows[40:]}
    replay=[json.loads(x) for x in (ROOT/'data/timetable-grounded-correction/train.jsonl').read_text().splitlines()]
    rng.shuffle(replay);splits['train'] += [{**r,'id':'replay:'+r['id']} for r in replay[:32]]
    for name,items in splits.items():(DATA/(name+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in items),encoding='utf-8')
    save(REPORT/'evaluation_cases.json',splits['test'])
    parent=json.loads((ROOT/'data/active_grounded_adapter.json').read_text())['adapter']
    save(REPORT/'protocol.json',{'teacher':g['teacher'],'parent_adapter':parent,'splits':{k:len(v) for k,v in splits.items()},
        'edges':len(g['edges']),'scope':'GPT-authored utility distillation, shared course facts; not empirical correlation learning.',
        'graph_sha256':hashlib.sha256((DATA/'reward_graph.json').read_bytes()).hexdigest()})
    print(parent,{k:len(v) for k,v in splits.items()},flush=True)

def evaluate(label):
    import torch
    from inference import load,generate
    torch.set_num_threads(8);sys.setrecursionlimit(5000)
    parent=json.loads((REPORT/'protocol.json').read_text())['parent_adapter'];tok,model=load(parent if label=='before' else ADAPTER)
    out=[]
    from programme_policy import exact
    for r in json.loads((REPORT/'evaluation_cases.json').read_text()):
        raw=generate(tok,model,r['messages'][:-1],max_tokens=180)
        try:parsed=json.loads(raw)
        except ValueError:parsed=None
        expected=json.loads(r['messages'][-1]['content']);passed=exact(expected,parsed)
        out.append({'id':r['id'],'expected':expected,'raw':raw,'passed':passed});save(REPORT/(label+'_predictions.json'),out)
        print(label,len(out),passed,flush=True)
    save(REPORT/(label+'_evaluation.json'),{'passed':sum(r['passed'] for r in out),'total':len(out)})

def release():
    training=json.loads((REPORT/'training.json').read_text());before=json.loads((REPORT/'before_evaluation.json').read_text());after=json.loads((REPORT/'after_evaluation.json').read_text())
    accepted=training['status']=='complete' and after['passed']>=18 and after['passed']>=before['passed']
    value={'adapter':ADAPTER,'accepted_for_activation':accepted,'role':'GPT-teacher direct preparation relation reward task only',
        'sha256':hashlib.sha256((ROOT/ADAPTER/'adapter_model.safetensors').read_bytes()).hexdigest(),
        'before':before,'after':after,'training_performed':True,'selected_epoch':training['selected_epoch'],
        'teacher':json.loads((REPORT/'protocol.json').read_text())['teacher'],'raw_outputs_require_validation':True,
        'general_and_timetable_checkpoints_replaced':False}
    save(REPORT/'release.json',value)
    if accepted:save(ROOT/'data/active_relation_adapter.json',value)
    print(json.dumps(value,indent=2),flush=True)

def infer(profile,code):
    import torch
    from inference import load,generate
    from preparation import profile_passes
    from programme_policy import exact
    g=json.loads((DATA/'reward_graph.json').read_text());rows=[{'course_code':c,'grade':'P'} for c in profile_passes(profile)]
    active=json.loads((ROOT/'data/active_relation_adapter.json').read_text());torch.set_num_threads(8)
    tok,model=load(active['adapter']);raw=generate(tok,model,messages(rows,code,g),max_tokens=180)
    try:value=json.loads(raw)
    except ValueError:value=None
    expected=target(rows,code,g);accepted=exact(expected,value)
    return {'raw_model_response':raw,'model_output_accepted':accepted,'verified_reward':expected,
        'policy_fallback_used':not accepted,'registration_verified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','before','after','release','infer']);p.add_argument('--profile');p.add_argument('--course');a=p.parse_args()
    if a.command=='build':build()
    elif a.command=='release':release()
    elif a.command=='infer':print(json.dumps(infer(json.loads(Path(a.profile).read_text()),a.course),indent=2))
    else:evaluate(a.command)
