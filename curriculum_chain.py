"""Complete a source-backed partial chain with explicitly untimetabled curriculum courses.

An approved curriculum-only mode, never a registration timetable. Existing saved
section selections are preserved; pending courses get no invented day, time or CRN.
Markov insertion states retain the whole remaining path and terminal audit.
"""
import argparse,copy,hashlib,json,math
from functools import lru_cache
from pathlib import Path
import project_runtime
from degree_chain import simulate,terminal_audit,goal
from four_year_markov import catalog
from programme_policy import allowed,policy,progress,chain_reward
from cm_background_policy import finance_background,ef_mismatch_penalty,waives_prerequisites
from profit_objective import settings,components,option_profit,option_year_bonus,option_ge_progress,overload_penalty
from planning_policy import cm_priority_weights
from preparation import graph
from course_relations import graph as rule_graph
from timetable_grounded_training import records
ROOT=Path(__file__).resolve().parent

def plan(profile,timetable_run=None,width=48):
    if profile.get('degree_mode')!='curriculum_with_pending':raise ValueError('Explicit curriculum_with_pending mode is required')
    profile=copy.deepcopy(profile)
    exact=profile.get('curriculum_search_mode')=='exact'
    reward_parameters=profile.get('reward_parameters',{})
    if reward_parameters or 'reward_course_relations' in profile:
        from llm_reward_contract import validate
        validate({'reward_parameters':reward_parameters,'course_relations':profile.get('reward_course_relations',[])})
    strict={**profile,'degree_mode':'saved_timetable_only'}
    baseline=copy.deepcopy(timetable_run) if timetable_run is not None else simulate(strict)
    if not baseline['input_profile']['completed_courses']==profile['completed_courses']:raise ValueError('Baseline transcript mismatch')
    cat={c['id']:c for c in catalog()}
    area_map=json.loads((ROOT/'data/four-year/GE_areas.json').read_text())
    normative=next((ROOT/'GE_SEMA/MA').glob('*2025*.pdf'))
    curriculum=ROOT/'GE_SEMA/MA/CMcourses.pdf'
    source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (normative,curriculum)}
    pending_evidence_path=ROOT/'data/curriculum-pending-evidence.json'
    pending_evidence=json.loads(pending_evidence_path.read_text())
    current_courses=pending_evidence['courses']
    source_hashes[str(pending_evidence_path)]=hashlib.sha256(pending_evidence_path.read_bytes()).hexdigest()
    historical=copy.deepcopy(profile.get('historical_transcript',[]));history_done={r['id'] for r in historical}
    start=profile.get('start_semester',1)
    if start!=3:raise ValueError('This completion mode currently supports the explicit completed Year-1 profiles')
    saved={s['term']:{o['course_code']:o for o in s['selected_timetable_evidence']} for s in baseline['diagnostic_semesters']}
    seed={t:list(saved[t]) for t in range(start,9)}
    removed=[]
    # Excess GE is optional; free its slots before adding required degree work.
    for t in reversed(range(start,9)):
        for code in list(seed[t]):
            if code not in area_map:continue
            remaining=history_done|{c for term,codes in seed.items() for c in codes if not(term==t and c==code)}
            ge=[c for c in remaining if c in area_map]
            if len(ge)>=4 and all(any(area_map[c]['area']==a for c in ge) for a in (1,2,3)):
                seed[t].remove(code);removed.append({'course_code':code,'term':t,'reason':'GE requirement already fulfilled; reserve credits for missing degree work'})
    pending=set()
    def credits(c):return cat[c]['credits'] if c in cat else saved[next(t for t in saved if c in saved[t])][c]['credits']
    def load(codes):return sum(credits(c) for c in codes)
    def fits(codes,code):return load(codes)+credits(code)<=18 and sum(credits(c)>0 for c in codes)+(credits(code)>0)<=6
    already=history_done|{c for codes in seed.values() for c in codes}
    mandatory=[c['id'] for c in cat.values() if c['required'] and c['id'] not in already]
    for code in sorted(mandatory,key=lambda c:(cat[c]['kind']!='capstone',c)):
        if code=='MA4530:A':choices=[7]
        elif code=='MA4530:B':choices=[8]
        elif not credits(code):choices=[start if code=='CSCI1001' else start+1]
        else:choices=range(start,9)
        choices=[t for t in choices if fits(seed[t],code)]
        if not choices:raise ValueError('No remaining curriculum slot for '+code)
        # Catch up missing required work at the earliest slot. Keeping later
        # semester capacity is important for B-only advanced electives.
        t=min(choices)
        seed[t].append(code);pending.add(code)
    official_rules=rule_graph()['verified_rules'];prep_graph=graph()
    if 'reward_course_relations' in profile:
        prep_graph={'edges':profile['reward_course_relations'],'max_preparation_benefit':.35}
    academic={(c['course_code'],c['term_code']):c for c in records() if c['programme']=='CM'}
    weights={'background_mismatch':1.,'difficulty':1.,'workload':1.,**profile.get('weights',{})}
    stream=profile.get('desired_stream','Enriched Mathematics');stream_rule=policy()['streams']['CM'][stream]
    multiplier=profile.get('stream_reward_multiplier',3. if profile.get('desired_stream') else 1.)
    def course_allowed(code):return allowed('CM',code) or code=='GE1601' # mandatory GE in supplied normative path
    def formal(code,done):
        canonical=code.split(':')[0]
        if not course_allowed(code):return False
        r=official_rules.get(canonical,{})
        if set(r.get('exclusive_courses',[]))&done or set(r.get('uncertain_exclusions',[]))&done:return False
        if not waives_prerequisites(profile,canonical):
            pending_rule=current_courses.get(canonical)
            if pending_rule and not any(set(a)<=done for a in pending_rule['completion_alternatives']):return False
            alternatives=r.get('completion_alternatives')
            if alternatives is not None and not any(set(a)<=done for a in alternatives):return False
            source_record=next((v for (c,t),v in academic.items() if c==canonical),None)
            if source_record is not None:
                if not any(set(a)<=done for a in source_record['completion_alternatives']):return False
            elif alternatives is None and not set(cat.get(code,{}).get('prerequisites',[]))<=done:return False
        return True
    @lru_cache(maxsize=100000)
    def term_value(t,codes,done_tuple):
        done=set(done_tuple);year=(t+1)//2;areas={str(a):sum(c in area_map and area_map[c]['area']==a for c in done) for a in (1,2,3)}
        conf=settings({**reward_parameters,**profile,'programme':'CM','student_year':year,'completed_courses':list(done),'track_ge_graduation':True,'completed_GE_area_counts':areas})
        prep={}
        for edge in prep_graph['edges']:
            if edge['source'] in done and edge['target'] not in done and edge['source']!=edge['target']:
                prep[edge['target']]=min(prep_graph.get('max_preparation_benefit',.35),max(prep.get(edge['target'],0),edge['benefit']))
        # The numeric critic uses the frozen LLM packet, rather than consulting
        # a different active relationship graph during final accounting.
        conf['preparation_bonus_by_course']=prep
        options=[]
        for code in codes:
            if not credits(code):continue
            o=copy.copy(saved[t].get(code,{}));canonical=code.split(':')[0]
            record=academic.get((canonical,'202609' if t%2 else '202702'))
            if record and code in saved[t]:
                from ge_pathways import course_scores
                scores=course_scores({**profile,'year':year,'completed_courses':list(done)},record)
            elif code in area_map:scores={'background_mismatch':.3,'difficulty':.35,'workload':.4}
            elif code=='GE1601':scores={'background_mismatch':.1,'difficulty':.1,'workload':.2}
            else:
                level=int(canonical[2]) if canonical.startswith('MA') else 3
                mismatch=finance_background({**profile,'completed_courses':list(done)})['background_mismatch'] if canonical in ('MA4529','MA4537') else .18 if 'MA1301' in done else .45
                scores={'background_mismatch':mismatch,'difficulty':min(.9,.22+.1*level),'workload':.8 if canonical=='MA4530' else .65}
            o.update(course_code=code,credits=credits(code),scores=scores)
            if code in area_map:o['ge_area']=area_map[code]['area']
            options.append(o)
        priorities=cm_priority_weights(year,done);pw=3.
        base=sum(option_profit(o,conf)+option_year_bonus(o,conf)+option_ge_progress(o,conf)+prep.get(o['course_code'],0) for o in options)
        risk=sum(sum(weights[k]*o['scores'][k] for k in weights)+ef_mismatch_penalty({**conf,'weights':weights},o['course_code']) for o in options)
        chain=multiplier*chain_reward('CM',done,stream,codes)
        bridge=multiplier if stream=='Financial Mathematics' and not {'MA2506','MA2510'}&done and 'MA2510' in codes else 0.
        overload=overload_penalty(len(options),conf,sum(o['credits'] for o in options))
        total=base+pw*sum(priorities.get(c,0) for c in codes)+chain+bridge-risk-overload
        return total,options,conf,priorities,chain,bridge
    def evaluate(state,details=False):
        done=set(history_done);transcript=copy.deepcopy(historical);total=0.;steps=[]
        for t,codes in zip(range(start,9),state):
            if len(set(codes))!=len(codes) or set(codes)&done or load(codes)>18 or sum(credits(c)>0 for c in codes)>6:return None
            if sum(c in area_map for c in codes)>1 or any(not formal(c,done) for c in codes):return None
            score,opts,conf,priorities,chain,bridge=term_value(t,tuple(sorted(codes)),tuple(sorted(done)))
            total+=.98**(t-start)*score
            for code in codes:transcript.append({'id':code,'credits':credits(code),'grade':'B','term':t,'year':(t+1)//2,'semester':'A' if t%2 else 'B'})
            if details:
                parts=components(opts,priorities,3.,weights,conf);parts['stream_chain_bonus']=chain;parts['prerequisite_bridge_bonus']=bridge
                parts['net_profit']+=chain+bridge;parts['schedule_loss']=-parts['net_profit']
                if not math.isclose(parts['net_profit'],score,abs_tol=1e-7):raise RuntimeError('Curriculum reward accounting mismatch')
                rows=[]
                for code in codes:
                    if code in saved[t]:
                        row=copy.deepcopy(saved[t][code]);row['evidence_status']='saved_timetable_hypothetical_bundle'
                    else:
                        row={'course_code':code,'credits':credits(code),'option_id':None,'crn':None,'meetings':None,
                            'evidence_status':'pending_timetable','course_offering_verified':False,
                            'current_prerequisite_rule_known':code.split(':')[0] in official_rules or code.split(':')[0] in current_courses,
                            'curriculum_source':str(normative if cat[code]['required'] else curriculum)}
                        if code.split(':')[0] in current_courses:
                            row.update(catalogue_rule_source=current_courses[code.split(':')[0]]['source'],
                                future_offering_repeated_as_assumption=True)
                        if code in ('CSCI1001','CSCI1002'):row['additional_confirmation']='Overdue zero-credit completion; catch-up arrangements require confirmation'
                        if code.startswith('MA4530:'):row['allocation_note']='Three plus three is an advisory allocation of one six-credit year-long project'
                    rows.append(row)
                steps.append({'term':t,'year':(t+1)//2,'semester':'A' if t%2 else 'B','selected_courses':list(codes),
                    'credits':load(codes),'earned_credits_after':sum(r['credits'] for r in transcript),'reward':parts,'course_evidence':rows})
            done.update(codes)
        return total,transcript,steps
    initial=tuple(tuple(sorted(seed[t])) for t in range(start,9))
    initial_eval=evaluate(initial)
    if initial_eval is None:raise ValueError('Mandatory curriculum placement is inconsistent with known prerequisites')
    candidates=[c['id'] for c in cat.values() if c['kind']=='math_elective' and c['credits']==3 and c['id'] in current_courses and course_allowed(c['id']) and c['id'] not in history_done|{x for codes in initial for x in codes}]
    if 'evaluate_completion_proposal' in profile:
        # Shared numeric critic for a blind external comparator. This branch
        # exits before search; it neither repairs nor optimizes the proposal.
        proposal=profile['evaluate_completion_proposal'];errors=[]
        if not isinstance(proposal,dict) or set(proposal)!=set(candidates):
            return {'status':'invalid_proposal','proposal_valid':False,'optimizer_called':False,'violations':['Missing or unknown elective assignments']}
        check=[list(x) for x in initial]
        for code,t in proposal.items():
            if type(t) is not int or t not in range(start,9):errors.append('Invalid term: '+code);continue
            if not cat[code]['earliest']<=t<=cat[code]['latest'] or ('A' if t%2 else 'B') not in current_courses[code]['semesters']:
                errors.append('Wrong offering term: '+code)
            check[t-start].append(code)
        if errors:return {'status':'invalid_proposal','proposal_valid':False,'optimizer_called':False,'violations':errors}
        e=evaluate(tuple(tuple(sorted(x)) for x in check),True)
        if e is None:return {'status':'invalid_proposal','proposal_valid':False,'optimizer_called':False,'violations':['A credit, course-count, prerequisite, exclusion, duplicate or GE constraint failed']}
        value,transcript,steps=e;a=terminal_audit(profile,transcript)
        return {'status':'valid_proposal' if a['all_encoded_requirements_met'] else 'invalid_proposal',
            'proposal_valid':a['all_encoded_requirements_met'],'optimizer_called':False,
            'violations':[k for k,v in a['checks'].items() if not v],'discounted_academic_reward':value,
            'audit':a,'semesters':steps,'transcript':transcript,'proposal_repaired':False}
    beam=[(initial_eval[0],initial)];expanded=[];winner=None
    max_extra=math.ceil(max(0,goal(profile)-sum(r['credits'] for r in initial_eval[1]))/3)+2
    for depth in range(max_extra+1):
        feasible=[]
        for value,state in beam:
            e=evaluate(state);a=terminal_audit(profile,e[1])
            if a['all_encoded_requirements_met']:feasible.append((value,state))
        if feasible:
            winner=max(feasible,key=lambda n:n[0]);break
        next_states={};count=0
        for value,state in beam:
            all_codes=history_done|{c for codes in state for c in codes}
            for code in candidates:
                if code in all_codes:continue
                for t in range(max(start,cat[code]['earliest']),min(8,cat[code]['latest'])+1):
                    if ('A' if t%2 else 'B') not in current_courses[code]['semesters']:continue
                    if not fits(state[t-start],code):continue
                    new=list(state);new[t-start]=tuple(sorted((*new[t-start],code)));new=tuple(new)
                    if new in next_states:continue
                    e=evaluate(new);count+=1
                    if e is not None:next_states[new]=e[0]
        expanded.append(count)
        ordered=sorted(((v,s) for s,v in next_states.items()),key=lambda n:n[0],reverse=True)
        if exact and len(ordered)>profile.get('exact_state_limit',100000):raise RuntimeError('Exact search resource limit reached; no maximum is claimed')
        beam=ordered if exact else ordered[:width]
        print('CURRICULUM additions',depth+1,'evaluated',count,'kept',len(beam),flush=True)
        if not beam:break
    if winner is None:return {'status':'curriculum_search_exhausted','curriculum_credit_plan_complete':False,'registration_timetable_complete':False,'search_expansions':expanded}
    total,transcript,steps=evaluate(winner[1],True);audit=terminal_audit(profile,transcript)
    if not audit['all_encoded_requirements_met']:raise RuntimeError('Refuse incomplete curriculum recommendation')
    pending_rows=[{'term':s['term'],**o} for s in steps for o in s['course_evidence'] if o['evidence_status']=='pending_timetable']
    certificate={'optimality_proven':False,'scope':'Existing source-backed course/section allocations and mandatory catch-up placements are fixed; optimize missing electives over the declared current catalogue pool.'}
    if exact and depth==len(candidates):
        # A second enumeration order independently checks all Cartesian term
        # assignments. It does not use the DP's pruning or retained states.
        import itertools
        domains=[[t for t in range(max(start,cat[c]['earliest']),min(8,cat[c]['latest'])+1)
            if ('A' if t%2 else 'B') in current_courses[c]['semesters']] for c in candidates]
        checked=0;feasible_count=0;maximum=-math.inf
        for terms in itertools.product(*domains):
            check=[list(x) for x in initial]
            for code,t in zip(candidates,terms):check[t-start].append(code)
            checked+=1;e=evaluate(tuple(tuple(sorted(x)) for x in check))
            if e is not None and terminal_audit(profile,e[1])['all_encoded_requirements_met']:
                feasible_count+=1;maximum=max(maximum,e[0])
        if not math.isclose(maximum,total,abs_tol=1e-7):raise RuntimeError('Independent enumeration disagrees with dynamic programming')
        certificate.update(optimality_proven=True,assignments_checked=checked,feasible_assignments=feasible_count,
            objective_upper_bound=maximum,optimality_gap=0.,verification='Independent full Cartesian enumeration agrees with DP maximum')
    return {'status':'curriculum_complete_timetables_pending','curriculum_credit_plan_complete':True,
        'registration_timetable_complete':False,'official_graduation_verified':False,
        'recommendation_scope':'122-credit curriculum path; pending courses are not registerable timetable selections',
        'input_profile':profile,'historical_transcript':historical,'semesters':steps,'transcript':transcript,'audit':audit,
        'discounted_academic_reward':total,'terminal_shortfall_penalty':0.,'pending_courses':pending_rows,
        'removed_optional_GE':removed,'curriculum_source_sha256':source_hashes,
        'method':('Exact dynamic programming over remaining course-to-term assignments; no LLM path generation' if exact else 'Bounded Markov insertion search over remaining full-path allocations; hard terminal credit and graduation checks; no MILP'),
        'global_optimality_claimed':False,'completion_optimality_certificate':certificate,
        'reward_parameter_source':profile.get('LLM_role','configured_policy'),'effective_reward_parameters':reward_parameters,
        'search_expansions':expanded,'beam_width':None if exact else width,
        'baseline_evidence_only_credits':baseline['audit']['earned_credits'],
        'limitations':['Future actual offerings, pending course prerequisites and registration eligibility require confirmation.',
            'Saved meetings retain the existing component/week assumptions; pending courses have no invented meetings.',
            'The Year-1 transcript remains assumed history; no new passes were added to it.',
            'Zero-credit overdue requirements are planned catch-up tasks, not claimed completed passes.']}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--profile',required=True);a.add_argument('--output',required=True);a.add_argument('--width',type=int,default=48);args=a.parse_args()
    p=json.loads(Path(args.profile).read_text());r=plan(p,width=args.width);out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2));print(r['status'],r.get('audit',{}).get('earned_credits'))
