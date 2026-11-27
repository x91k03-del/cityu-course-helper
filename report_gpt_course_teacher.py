"""Save transparent relation explanations and controlled reward ablations."""
import copy,hashlib,json
from pathlib import Path
import project_runtime
from preparation import benefits,graph
from profit_objective import components,settings
from markov_planner import solve
from test_scheduler import option
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'reports/gpt-course-relations'

def run():
    cases=[]
    for done,target in [(['MA2508'],'MA3512'),(['MA2510'],'MA3518'),(['MA2503'],'CS4487'),
      (['MA2503','MA2510','MA3515'],'CS4487'),(['GE1202'],'EF3320'),(['MA3515'],'EF3320'),(['MA2509'],'GE2134')]:
        cases.append({'passed_courses':done,'target':target,'reward_bonus':benefits(done).get(target,0),
          'reason':[e['reason'] for e in graph()['edges'] if e['source'] in done and e['target']==target]})
    fixed=[option('DEMO'+str(i),day=i+1,cost=.1) for i in range(4)]
    a=option('CS4487',day=5,cost=.1);b=option('DEMO_ALT',day=5,cost=.1);b['profit']=3.1
    p={'student_year':2,'term':'DEMO','required_courses':[o['course_code'] for o in fixed],'completed_courses':['CS3481'],
      'credit_min':15,'credit_max':15,'course_min':5,'course_max':5,'options':fixed+[a,b]}
    synthetic={'label':'Synthetic mechanism illustration, not a CityU timetable','before':solve(p),
        'after_pass_MA2503':solve({**p,'completed_courses':['CS3481','MA2503']})}
    # Freeze only the preparation graph while keeping all source options and
    # other reward terms fixed. The previous source records remain unchanged.
    import preparation
    old=preparation.graph;legacy=json.loads((ROOT/'data/preparation-v5.json').read_text())
    real=[]
    from timetable_grounded_training import problem_for
    for case in json.loads((ROOT/'reports/year3-path-comparison06/cases.json').read_text())[:3]:
        problem=problem_for(case['profile'])
        try:preparation.graph=lambda:legacy;before=solve(problem)
        finally:preparation.graph=old
        after=solve(problem)
        real.append({'id':case['id'],'before':before,'after':after,
            'net_reward_change':after.get('objective',0)-before.get('objective',0),
            'selection_changed':set(before.get('selected_options',[]))!=set(after.get('selected_options',[]))})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'reward_examples.json').write_text(json.dumps({'examples':cases,'synthetic_flip':synthetic,'source_grounded_profiles':real},indent=2)+'\n')
    lines=['# GPT teacher: course preparation rewards','',
      'Teacher: GPT assistant in this conversation, using saved course aims, prior syllabus evidence and official catalogue descriptions. No separate GPT-6.1-sol call is claimed.','',
      'These are deductive preparation hypotheses, not measured statistical correlations or verified workload savings. Values are editable utility assumptions.','',
      'Reward update: net profit = existing net profit + strongest direct preparation benefit for each target. Existing preparation is replaced, not added a second time. '
      'Cap 0.35 per target; passed sources only; no stacking, recursive or same-semester transfer; completed targets earn no new benefit. Timetable, membership and prerequisites remain binding.','',
      '| Passed course(s) | Target | Added preparation reward | GPT explanation |','|---|---|---:|---|']
    for c in cases:lines.append(f"| {', '.join(c['passed_courses'])} | {c['target']} | {c['reward_bonus']:.2f} | {' '.join(c['reason'])} |")
    lines+=['','The synthetic five-course comparison keeps CS3481 passed in both profiles, so ML eligibility is already satisfied. '
      'Adding passed MA2503 increases the ML option by 0.25. Its fifth-slot reward rises from 2.70 to 2.95 and overtakes a competing 2.80 option. '
      'This fixture demonstrates the reward mechanism; DEMO courses are not registerable recommendations.','',
      '## Actual saved-timetable profile ablation','',
      '| Profile | Reward change | Selected courses changed? |','|---|---:|---|']
    for c in real:lines.append(f"| {c['id']} | {c['net_reward_change']:.2f} | {c['selection_changed']} |")
    lines+=['','A positive reward change need not change an already preferred timetable. Existing semester constraints and stream bonuses can dominate a small preparation benefit. '
      'The previously infeasible entering Year-1 source pool remains infeasible; inferred preparation cannot create offered courses.','',
      'Official content references: [Machine Learning](https://www.cityu.edu.hk/catalogue/ug/current/course/CS4487.htm), '
      '[Applied Statistics, historical 2024/25](https://www.cityu.edu.hk/catalogue/ug/202425/course/MA3518.htm). '
      'The interpretation and numeric weights come from GPT reasoning; the university did not publish these reward values.']
    release=ROOT/'reports/gpt-course-relations-max/release.json'
    if release.exists():
        final=json.loads(release.read_text());initial=json.loads((OUT/'before_evaluation.json').read_text())
        lines+=['','## Qwen distillation and verification','',
          f"Initial supervised training: 149 training / 20 validation examples, two epochs. Held-out source-conditioned policy checks: {initial['passed']}/{initial['total']} before, {final['after']['passed']}/{final['after']['total']} after.",'',
          'A fresh three-source P-grade probe initially produced an invalid sum of 0.75. Validation rejected it and used 0.25. '
          'An 82-example corrective pass (one epoch) taught max-versus-sum across passed-course combinations. The corrected probe now returns 0.25; '
          'it was seen in corrective training and is not an independent test. The unchanged held-out set remains 20/20.','',
          'Active relation checkpoint: `'+final['adapter']+'`. General and timetable checkpoints are preserved. '
          'All model reward outputs still require exact validation. The production reward uses the checked teacher graph, so a neural arithmetic error cannot inflate its value.','',
          '86 focused software checks passed. The tests cover bonus caps, non-stacking, failed/IP/W inputs, no recursive/self reward, '
          'source restrictions, prerequisite separation and reward accounting. Learned utilities are policy hypotheses; these checks do not establish improved student grades or calibrated workload savings.']
        paths=['data/gpt-course-relations/reward_graph.json','data/gpt-course-relations/train.jsonl','data/gpt-course-relations/test.jsonl',
          'data/gpt-course-relations-max/train.jsonl','preparation.py','profit_objective.py','markov_planner.py',
          final['adapter']+'/adapter_model.safetensors']
        (OUT/'manifest.json').write_text(json.dumps({'teacher':graph()['teacher'],'sha256':{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in paths}},indent=2)+'\n')
    (OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print([(r['id'],round(r['net_reward_change'],3),r['selection_changed']) for r in real])

if __name__=='__main__':run()
