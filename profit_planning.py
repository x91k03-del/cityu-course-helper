"""Profit-based planning branch using the copied Qwen adapter and exact source checks."""
import argparse,copy,hashlib,itertools,json,math
from pathlib import Path
import cm_planning_update as previous
from cm_planning_update import ROOT,public_profile,input_for,priorities
from ma_timetable import read,write
from test_cm_profiles import source_options,option_id,compatible
from profit_objective import POLICY,settings,components

ADAPTER='adapters/bscm-profit-v3'
REPORT=ROOT/'reports/profit-v3'
SCORE_WEIGHTS={'background_mismatch':1.,'difficulty':1.,'workload':1.}
SYSTEM=previous.SYSTEM.replace(
    'Minimize: number of selected courses + 3 times the sum of the supplied priority weights of UNSELECTED unfinished maths core courses.',
    'Maximize net academic profit: sum of base_course_profit plus 3 times the selected unfinished maths core weights, minus one unit of cost per selected course, minus overload_penalty_weight * max(0, course_count - overload_reference_courses)^2. Use supplied profit_settings. The unit course cost is a synthetic experiment constant, not measured workload.')

def scored_options(profile):
    options,blocked=source_options(profile)
    return [{**o,'scores':{k:1/3 for k in SCORE_WEIGHTS}} for o in options],blocked

def reference(profile,overrides=None):
    config=settings({'overload_mode':'course_count',**(overrides or {})})
    if config['objective_mode']!='profit':raise ValueError('This branch requires objective_mode profit')
    pool,blocked=scored_options(profile);best=None;weights=priorities(profile)
    for count in [5,6]:
        for group in itertools.combinations(pool,count):
            if not 15<=sum(o['credits'] for o in group)<=18:continue
            if not all(compatible(a,b) for a,b in itertools.combinations(group,2)):continue
            result=components(group,weights,3.,SCORE_WEIGHTS,config)
            key=(-result['net_profit'],sorted(option_id(o) for o in group))
            if best is None or key<best[0]:best=(key,group,result)
    plan={'profile_id':profile['profile_id'],'status':'infeasible' if best is None else 'candidate','minimum_courses':5,
          'completed_courses':previous.completed(profile),'selected_options':[],
          'needs_confirmation':True,'feasibility_verified':False}
    if best is not None:
        plan['selected_options']=[{k:o[k] for k in ['course_code','class_section','tutorial_section','meetings']} for o in sorted(best[1],key=option_id)]
    return {'plan':plan,'course_count':len(plan['selected_options']),
            'credits':0 if best is None else sum(o['credits'] for o in best[1]),
            'profit_breakdown':None if best is None else best[2],'objective_settings':config,
            'blocked_courses':blocked,'data_mode':'experimental_MA_snapshot_with_unverified_component_linkage_and_teaching_weeks',
            'profit_units':'academic utility; per-course cost 1 is synthetic, not measured workload',
            'selection_method':'exhaustive_source_option_enumeration_maximizing_net_profit'}

def grade(profile,value,overrides=None):
    # Reuse every factual and hard-constraint check; replace ONLY the old objective check.
    validation=previous.grade_plan(profile,value)
    errors=[e for e in validation['errors'] if e!='weighted_graduation_objective_not_optimal']
    expected=reference(profile,overrides)
    if not errors and isinstance(value,dict) and value.get('status')=='candidate':
        pool,_=scored_options(profile);by_id={option_id(o):o for o in pool}
        chosen=[by_id[option_id(o)] for o in value['selected_options']]
        actual=components(chosen,priorities(profile),3.,SCORE_WEIGHTS,expected['objective_settings'])
        if not math.isclose(actual['net_profit'],expected['profit_breakdown']['net_profit'],rel_tol=1e-8,abs_tol=1e-7):
            errors.append('net_profit_not_optimal')
    return {'passed':not errors,'errors':errors,'expected_status':expected['plan']['status']}

def demo():
    from scheduler import solve
    opts=[]
    for i in range(8):
        opts.append({'option_id':f'DEMO{1000+i}-SIM','course_code':f'DEMO{1000+i}','credits':3,
            'term':'SIMULATED_PROFIT_TEST','rules_reviewed':True,'timetable_verified':True,
            'prerequisites_all':[],'prerequisites_any_groups':[],'corequisites':[],'exclusive_courses':[],
            'meetings':[{'day':1+i//5,'weeks':list(range(1,14)),'start_minute':480+75*(i%5),'end_minute':540+75*(i%5)}],
            'scores':{k:.1 for k in SCORE_WEIGHTS}})
    base={'data_mode':'synthetic_policy_test_not_actual_CityU_times_or_eligibility','term':'SIMULATED_PROFIT_TEST',
          'overload_mode':'course_count',
          'required_courses':[],'completed_courses':[],'options':opts,'course_min':5,'course_max':8,'credit_min':15,'credit_max':24}
    results={}
    for label,overrides in [('no_overload_penalty',{'overload_penalty_weight':0}),
                            ('default_overload_penalty',{}),('high_course_profit',{'base_course_profit':8})]:
        results[label]=solve({**base,**overrides})
    write(REPORT/'demo_comparison.json',results)
    return results

def snapshot():
    source=ROOT/'adapters/bscm-planning-v2';dest=ROOT/ADAPTER
    manifest=[]
    for path in sorted(source.iterdir()):
        if not path.is_file():continue
        target=dest/path.name
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise ValueError('Checkpoint copy differs: '+path.name)
        manifest.append({'file':path.name,'bytes':path.stat().st_size,'sha256':digest})
    weights=hashlib.sha256((dest/'adapter_model.safetensors').read_bytes()).hexdigest()
    record={'adapter':ADAPTER,'copied_from':'adapters/bscm-planning-v2','adapter_sha256':weights,
        'source_and_copy_identical':True,'files':manifest,'base_model':'models/Qwen3-8B (shared, unchanged)',
        'training_performed':False,'optimizer_state_available':False,
        'checkpoint_scope':'Saved LoRA adapter and tokenizer; original run did not save optimizer state.',
        'objective_policy':POLICY,'year_priority_policy':read(ROOT/'data/cm_year_priority_policy.json'),
        'schedule_loss':'student_cost_penalty + overload_penalty - course_profit - maths_priority_bonus',
        'neural_training_loss':'Unchanged assistant-token cross entropy. Discrete schedule profit is not a differentiable replacement.',
        'final_selection_authority':'constraint_solver_or_exact_source_enumerator',
        'raw_model_planning_reliability':'Copy inherits existing planning-v2 limitations; no new inference accuracy claim.'}
    write(REPORT/'checkpoint_copy.json',record);write(dest/'planning_objective.json',record)
    write(ROOT/'data/active_planning_adapter.json',{'adapter':ADAPTER,'adapter_sha256':weights,
        'copied_from':record['copied_from'],'checkpoint_manifest':'reports/profit-v3/checkpoint_copy.json',
        'profit_policy_file':'data/profit_objective_policy.json','year_policy_file':'data/cm_year_priority_policy.json',
        'objective_sense':'maximize_net_profit','schedule_loss':'negative_net_profit','training_performed':False,
        'minimum_courses':5,'final_selection_authority':'constraint_solver_not_raw_model_planning'})
    return record

def report():
    record=read(REPORT/'checkpoint_copy.json');results=read(REPORT/'demo_comparison.json')
    lines=['# Profit and overload planning branch','',
        'The current planning-v2 LoRA checkpoint and tokenizer were copied to `adapters/bscm-profit-v3`. Every original checkpoint file was checked byte-for-byte by SHA-256. '
        'The 8B base model is shared. The copy is an inference/continued-LoRA checkpoint; optimizer state was not saved in the original run. '
        '**No new fine-tuning was performed. The copied weights are identical to the source.**','',
        '## Profit and loss','',
        '`gross_profit = sum(selected course profits) + graduation_priority_weight * sum(selected unfinished maths core weights)`','',
        '`profit_penalty = sum(selected mismatch/difficulty/workload costs) + overload_weight * max(0, distinct_course_count - reference_load)^2`','',
        '`net_profit = gross_profit - profit_penalty`','',
        '**Maximize net_profit.** The equivalent minimization loss used by the solver is `schedule_loss = profit_penalty - gross_profit = -net_profit`. '
        'This is the planning/optimization loss. The Qwen assistant-token training loss remains cross-entropy; attaching a constant/discrete schedule penalty to token loss would not train the desired policy.','',
        'Profit is a configurable academic utility, not money or a measured student outcome. Default per-course profit is 3 points; an option can override it with its `profit` field. '
        'Existing year-weighted maths core benefits remain included. Existing mismatch, difficulty and workload estimates are deductions from profit.','',
        '## Increasing overload penalty','',
        'The default reference load is five courses and overload weight is 3. The penalty is based on distinct courses, not tutorial/lecture CRNs.','',
        '| Courses | Overload penalty | Extra penalty for this course |','| --- | --- | --- |',
        '| 5 | 0 | 0 |','| 6 | 3 | 3 |','| 7 | 12 | 9 |','| 8 | 27 | 15 |','',
        'Five remains the default hard minimum and six the default maximum. The overload penalty is an increasing soft deduction, so a sufficiently valuable sixth course can still be selected. '
        'Prerequisites, required courses, exclusions, credit bounds and verified timetable evidence remain hard constraints. A profit cannot buy permission to violate them.','',
        'The quadratic penalty is implemented exactly with binary course-count selectors. The solver remains a MILP; no approximation or floating-point penalty is substituted for a hard eligibility constraint.','',
        '## Controlled comparison','',
        'This synthetic comparison deliberately permits up to eight courses to expose the overload curve. All eight courses have non-conflicting simulated meetings, equal three-credit values and cost 0.3 each. '
        'It is not a real CityU timetable or real eligibility assessment.','',
        '| Scenario | Courses selected | Gross profit | Course-cost penalty | Overload penalty | Net profit |','| --- | --- | --- | --- | --- | --- |']
    for label,r in results.items():
        p=r['profit_breakdown'];lines.append(f"| {label} | {r['course_count']} | {p['gross_profit']:.2f} | {p['student_cost_penalty']:.2f} | {p['overload_penalty']:.2f} | {p['net_profit']:.2f} |")
    validation=REPORT/'validation.json'
    if validation.exists():lines += ['',f"Validation: {read(validation)['tests']} automated tests passed, including exhaustive enumeration against the MILP, course-count/penalty accounting, per-course profit overrides and hard-constraint regressions."]
    lines += ['','## Use','',
      'Edit `data/profit_objective_policy.json` to change the default profit, reference load or overload coefficient. Per-problem fields override these values. '
      'An option may specify a non-negative finite `profit`. `objective_mode: legacy_cost` reproduces the prior cost objective for historical comparisons. '
      'Year priorities remain in `data/cm_year_priority_policy.json`.','',
      '```powershell','cd F:\\CODEX\\cityu-course-helper','.\\profit_planning.cmd demo',
      '.\\profit_planning.cmd plan --profile data/cm-planning-v2/example_student.json',
      '.\\profit_planning.cmd predict --profile data/cm-planning-v2/example_student.json',
      '```','',
      '`plan` enumerates source-supported hypothetical MA bundles and returns the best net-profit plan with a full penalty breakdown. '
      'Its unit per-course cost is synthetic. `predict` uses the copied adapter with the new policy in context and displays independent validation; the copy retains the prior model’s unreliable unconstrained planning behavior. '
      'Saved MA source teaching weeks and official component linkage remain unverified, so these MA-only plans remain experimental. '
      '`scheduler.py` is the production solver for reviewed complete options and verified meetings.','',
      'Model-copy hashes and complete settings: `reports/profit-v3/checkpoint_copy.json`. Controlled optimizer outputs: `demo_comparison.json`. '
      'The original checkpoint remains in `adapters/bscm-planning-v2`.']
    (ROOT/'PROFIT_OBJECTIVE_UPDATE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Wrote PROFIT_OBJECTIVE_UPDATE.md')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['snapshot','demo','plan','predict','report'])
    ap.add_argument('--profile',type=Path);ap.add_argument('--base-course-profit',type=float)
    ap.add_argument('--overload-penalty-weight',type=float);ap.add_argument('--overload-reference-courses',type=int)
    a=ap.parse_args();overrides={k:getattr(a,k) for k in ['base_course_profit','overload_penalty_weight','overload_reference_courses'] if getattr(a,k) is not None}
    if a.command=='snapshot':print(json.dumps(snapshot(),indent=2));return
    if a.command=='demo':print(json.dumps(demo(),indent=2));return
    if a.command=='report':report();return
    if not a.profile:ap.error('--profile is required')
    profile=read(a.profile);result=reference(profile,overrides)
    if a.command=='plan':print(json.dumps(result,indent=2));return
    from inference import load,generate
    tok,model=load(ADAPTER);evidence=input_for(profile);evidence['profit_settings']=settings({'overload_mode':'course_count',**overrides})
    raw=generate(tok,model,[{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps({'task':'PLAN',**evidence})}],max_tokens=1500)
    try:validation=grade(profile,json.loads(raw),overrides)
    except (ValueError,TypeError,KeyError):validation={'passed':False,'errors':['invalid_model_json_or_schema']}
    print(json.dumps({'raw_model_response':raw,'validation':validation,'source_reference':result},indent=2))

if __name__=='__main__':main()
