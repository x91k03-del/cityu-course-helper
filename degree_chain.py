"""Flexible semester loads with hard terminal graduation acceptance."""
import copy,json
from pathlib import Path
from four_year_markov import catalog
from programme_policy import policy,progress
from timetable_data import records,compatible_sections,problem_for
from markov_planner import solve,plan_from_proposal
ROOT=Path(__file__).resolve().parent

def optimise_full_chain(profile,certificate):
    import math
    from terminal_markov import search
    penalty_weight=profile.get('terminal_credit_shortfall_penalty',1_000_000.)
    if type(penalty_weight) not in (int,float) or not math.isfinite(penalty_weight) or penalty_weight<=0:raise ValueError('Invalid terminal credit shortfall penalty')
    initial=copy.deepcopy(profile.get('historical_transcript',[]))
    start=profile.get('start_semester',1);horizon=9-start
    explore_late_ef=False
    def actions(state,local_term):
        term=local_term+start-1
        p={**profile,'year':(term+1)//2,'term':'202609' if term%2 else '202702','course_min':0,'completed_courses':[r['id'] for r in state]}
        problem=problem_for(p);options={o['option_id']:o for o in problem['options']}
        if explore_late_ef and p['year']<4:
            problem={**problem,'options':[o for o in problem['options'] if o['course_code']!='EF3320']}
        limit=profile.get('chain_branch_width',12);state_limit=profile.get('chain_state_limit',100000)
        result=solve(problem,state_limit=state_limit,candidate_limit=limit)
        candidates=result.get('candidate_schedules',[])
        # A locally profitable EF3320 can be better later. Preserve an explicit
        # deferral action rather than pruning every such path from the beam.
        if p['year']<4 and problem.get('ef3320_year4_bonus',4.)>0 and any(o['course_code']=='EF3320' for o in problem['options']):
            deferred={**problem,'options':[o for o in problem['options'] if o['course_code']!='EF3320']}
            candidates+=solve(deferred,state_limit=state_limit,candidate_limit=limit).get('candidate_schedules',[])
        seen=set()
        for c in candidates:
            key=tuple(sorted(c['selected_options']))
            if key in seen:continue
            seen.add(key)
            yield {'selected':[options[x] for x in c['selected_options']],'reward':c['net_reward'],'problem_term':p['term']}
    def transition(state,action,local_term):
        term=local_term+start-1
        return state+[{'id':o['course_code'],'credits':o['credits'],'grade':'B','term':term,'year':(term+1)//2,'semester':'A' if term%2 else 'B'} for o in action['selected']],action['reward']
    def terminal(state):return terminal_audit(profile,state)['all_encoded_requirements_met']
    def shortfall(state):return max(0,goal(profile)-sum(r['credits'] for r in state))
    def heuristic(state):return 0.
    def stage_heuristic(state,local_term):
        term=local_term+start-1
        # Guide by capacity still available, rather than forcing early credits.
        # This keeps room for a more profitable later offering of the same course.
        reachable_target=min(goal(profile),certificate['unique_source_credit_upper_bound'])
        capacity=-1000.*max(0,reachable_target-sum(r['credits'] for r in state)-18*(8-term))
        # Retain delayed-reward states: a narrow beam otherwise discards every
        # EF deferral because its immediate return is smaller. This is search
        # guidance only, never added to the reported earned reward.
        future_timing=0.
        if term<8 and 'EF3320' in certificate.get('available_course_codes',[]) and not any(r['id']=='EF3320' for r in state):
            future_timing=.98**(horizon-1)*profile.get('ef3320_year4_bonus',4.)
        return capacity+future_timing
    key=lambda s:tuple(sorted((r['id'],r['credits']) for r in s))
    args=(initial,horizon,actions,transition,terminal,key,heuristic)
    if not certificate['proof_of_insufficient_coverage']:
        result=search(*args,width=profile.get('chain_beam_width',16),stage_heuristic=stage_heuristic)
        if result['status']=='complete':result['degree_feasible_search']=True;return result
    # Keep the best found candidate visible when the hard problem is infeasible.
    # Its penalty never turns it into a graduating plan.
    result=search(initial,horizon,actions,transition,lambda s:True,key,heuristic,width=profile.get('chain_beam_width',16),
        terminal_reward=lambda state:-penalty_weight*shortfall(state),stage_heuristic=stage_heuristic)
    alternative=search(initial,horizon,actions,transition,lambda s:True,key,
        lambda state:-1000.*shortfall(state),width=profile.get('chain_credit_beam_width',8),
        terminal_reward=lambda state:-penalty_weight*shortfall(state))
    trials=[r for r in (result,alternative) if r['status']=='complete']
    if profile.get('ef3320_year4_bonus',4.)>0 and 'EF3320' in certificate.get('available_course_codes',[]):
        # Diversify the search with a late-EF candidate. This is not a hard
        # student constraint: retain it only if its actual penalised return wins.
        explore_late_ef=True
        late=search(initial,horizon,actions,transition,lambda s:True,key,heuristic,
            width=profile.get('chain_beam_width',16),stage_heuristic=stage_heuristic,
            terminal_reward=lambda state:-penalty_weight*shortfall(state))
        explore_late_ef=False
        if late['status']=='complete':trials.append(late)
    if trials:result=max(trials,key=lambda r:r['best']['return'])
    result.update(degree_feasible_search=False,credit_shortfall_penalty_per_credit=penalty_weight,
        globally_optimal=False,search_strategies='Capacity-aware, credit-progress and late-EF candidate beams; retain the highest actual penalised return.',
        candidate_scope='Best found valid path with terminal shortfall penalty; no proof of a global optimum.')
    return result

def goal(profile):
    # Both the supplied CM normative path and saved CS major page say 122.
    return max(122,profile.get('minimum_degree_credits',121))

def terminal_audit(profile,transcript):
    cat={c['id']:c for c in catalog()};passed={r['id'] for r in transcript};credits=sum(r['credits'] for r in transcript)
    required={c['id'] for c in cat.values() if c['required'] and c['kind']!='capstone'}
    math=sum(r['credits'] for r in transcript if cat.get(r['id'],{}).get('kind')=='math_elective')
    free=sum(r['credits'] for r in transcript if cat.get(r['id'],{}).get('kind')=='free_elective')+max(0,math-12)
    area_map=json.loads((ROOT/'data/four-year/GE_areas.json').read_text())
    ge=[r for r in transcript if r['id'] in area_map or cat.get(r['id'],{}).get('kind')=='distribution_GE']
    areas={str(a):sum(area_map.get(r['id'],{}).get('area',cat.get(r['id'],{}).get('area'))==a for r in ge) for a in [1,2,3]}
    project=sum(r['credits'] for r in transcript if r['id'] in ['MA4530','MA4530:A','MA4530:B'])
    core=sum(r['credits'] for r in transcript if cat.get(r['id'],{}).get('kind')=='core')
    stream=profile.get('desired_stream','Enriched Mathematics');rule=policy()['streams']['CM'][stream]
    checks={'credit_minimum':credits>=goal(profile),'total_at_least_121':credits>=121,'total_at_least_122':credits>=122,
      'credit_maximum':credits<=144,'no_duplicate_credit':len(passed)==len(transcript),'all_mandatory_complete':required<=passed,
      'GE_at_least_four':len(ge)>=4,'GE_all_areas':all(areas.values()),'math_elective_at_least_20':math>=20,
      'core_45_credits':core==45,'capstone_six_credits':project==6,'major_elective_at_least_18':min(12,math)+project>=18,
      'free_elective_at_least_20':free>=20,'selected_stream_complete':progress(rule,passed)>=rule['slots'],
      'GE_at_most_one_per_semester':all(sum(r['term']==t for r in ge)<=1 for t in range(1,9))}
    return {'earned_credits':credits,'minimum_degree_credits':goal(profile),'checks':checks,
      'all_encoded_requirements_met':all(checks.values()),'missing_mandatory':sorted(required-passed),
      'GE_area_counts':areas,'distribution_GE_count':len(ge),'elective_math_credits':math,'official_graduation_verified':False}

def coverage(profile):
    available={}
    for c in records():
        if c['programme']!=profile['programme'] or not c['document_allowed']:continue
        ss=compatible_sections(profile,c)
        if any(s['credits']>0 for s in ss):available[c['course_code']]=max(available.get(c['course_code'],0),max(s['credits'] for s in ss))
    required={c.get('course_code_display',c['id']) for c in catalog() if c['required']}
    historical={r['id']:r['credits'] for r in profile.get('historical_transcript',[])}
    absent=sorted(required-set(available)-set(historical));upper=sum({**available,**historical}.values())
    ge_upper=0
    if profile.get('include_GE_snapshot',False):
        from ge_snapshot_options import options
        ge={o['course_code']:o['credits'] for o in options({**profile,'term':'202609','completed_courses':list(historical)})}
        a_terms=sum(t%2 for t in range(profile.get('start_semester',1),9))
        ge_upper=min(sum(ge.values()),3*a_terms);upper+=ge_upper
    return {'mandatory_without_compatible_timetable':absent,'unique_source_credit_upper_bound':upper,
        'available_course_codes':sorted(available),
        'additional_GE_credit_upper_bound':ge_upper,
        'credit_target':goal(profile),'proof_of_insufficient_coverage':bool(absent) or upper<goal(profile),
        'note':'This is a source-coverage certificate, not a claim that the university does not offer the missing subjects.'}

def simulate(profile,model_provider=None):
    if model_provider is not None:
        raise ValueError('Use objective parameters with the external optimiser; model-generated schedules are not supported.')
    if profile.get('degree_mode')=='curriculum_with_pending':
        from curriculum_chain import plan
        return plan(profile,width=profile.get('curriculum_beam_width',48))
    history=profile.get('historical_transcript',[]);start=profile.get('start_semester',1)
    if profile['programme']!='CM':raise ValueError('CM simulation only')
    if history:
        if start!=3 or profile.get('year')!=2:raise ValueError('Completed Year-1 history must start at Year 2 Semester A')
        if len({r['id'] for r in history})!=len(history) or {r['id'] for r in history}!=set(profile.get('completed_courses',[])):raise ValueError('Historical passes must match unique completed course IDs')
        if any(r['term'] not in (1,2) or r.get('grade') not in ('A','B','C','D','P') or r['credits']<0 for r in history):raise ValueError('Invalid fictional Year-1 history')
    elif profile.get('year',1)!=1 or profile.get('completed_courses',[]) or start!=1:raise ValueError('Use an entering Year-1 CM profile or explicit completed Year-1 history.')
    profile=copy.deepcopy(profile);profile.setdefault('programme_code','BSCSIU4')
    certificate=coverage(profile);global_plan=optimise_full_chain(profile,certificate);transcript=copy.deepcopy(history);done=[r['id'] for r in history];steps=[]
    for term in range(start,9):
        snapshot='202609' if term%2 else '202702';year=(term+1)//2
        p={**profile,'year':year,'term':snapshot,'course_min':0,'completed_courses':done.copy()}
        problem=problem_for(p)
        if global_plan['status']=='complete':
            chosen=global_plan['best']['actions'][term-start]['selected']
            result={'status':'feasible','selected_options':[o['option_id'] for o in chosen],'course_codes':[o['course_code'] for o in chosen],
                'course_count':len(chosen),'planner':('Whole-chain Markov beam search with hard terminal graduation checks'
                    if global_plan.get('degree_feasible_search') else 'Diagnostic incomplete path; not a degree recommendation')}
        else:result=solve(problem)
        options={o['option_id']:o for o in problem['options']}
        selected=[options[x] for x in result.get('selected_options',[])]
        for o in selected:
            done.append(o['course_code']);transcript.append({'id':o['course_code'],'credits':o['credits'],'grade':'B','term':term,'year':year,'semester':'A' if term%2 else 'B'})
        steps.append({'term':term,'year':year,'semester':'A' if term%2 else 'B','snapshot_term':snapshot,
            'snapshot_repeated_by_user_authorisation':True,'completed_before':problem['completed_courses'],
            'selected_courses':[o['course_code'] for o in selected],'credits':sum(o['credits'] for o in selected),
            'course_count':len(selected),'result':result,'selected_timetable_evidence':selected})
    audit=terminal_audit(profile,transcript);accepted=audit['all_encoded_requirements_met'] and not certificate['proof_of_insufficient_coverage']
    shortfall=max(0,goal(profile)-audit['earned_credits']);weight=profile.get('terminal_credit_shortfall_penalty',1_000_000.)
    academic_reward=sum(.98**i*a['reward'] for i,a in enumerate(global_plan.get('best',{}).get('actions',[]))) if global_plan['status']=='complete' else None
    return {'status':'complete' if accepted else 'best_available_infeasible_candidate','whole_chain_accepted':accepted,
      'path_valid':all(s['result']['status'] in ('optimal','feasible') for s in steps),'credit_shortfall':shortfall,'terminal_shortfall_penalty':weight*shortfall,
      'discounted_academic_reward':academic_reward,'penalised_objective':None if academic_reward is None else academic_reward-weight*shortfall,
      'optimality_claim':'Best found path; global optimality is not required or claimed.',
      'minimum_degree_credits':goal(profile),'semester_minimum_courses':0,'input_profile':profile,
      'historical_input_assumed_not_timetable_verified':bool(history),
      'offering_mode':'User-authorised repeating A/B snapshot simulation; future actual offerings unverified.',
      'coverage_certificate':certificate,'global_search':{k:v for k,v in global_plan.items() if k!='best'},'audit':audit,'diagnostic_semesters':steps,'transcript':transcript,
      'recommended_semesters':steps if accepted else [],
      'diagnostic_only':not accepted,'explanation':'A partial semester can be legal. The four-year plan is accepted only if the terminal credit and all encoded graduation constraints pass. Missing source coverage prevents a complete plan; rewards cannot override it.'}

def plan_degree(profile):
    """Public full-path entrypoint, distinct from the strict timetable simulation."""
    path=ROOT/'data/active_degree_planning_policy.json'
    defaults=json.loads(path.read_text()) if path.exists() else {'degree_mode':'saved_timetable_only'}
    request={**defaults,**profile}
    if request.get('degree_mode')=='curriculum_with_pending' and request.get('reward_contract_path') and 'reward_parameters' not in request:
        from llm_reward_contract import apply
        packet=json.loads((ROOT/request['reward_contract_path']).read_text(encoding='utf-8'))
        request=apply(request,packet)
    return simulate(request)

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--profile',required=True);a.add_argument('--output',required=True)
    a.add_argument('--mode',choices=['saved_timetable_only','curriculum_with_pending']);args=a.parse_args()
    p=json.loads(Path(args.profile).read_text(encoding='utf-8'))
    if args.mode:p['degree_mode']=args.mode
    r=plan_degree(p);out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(r['status'],r.get('audit',{}).get('earned_credits'))
