"""Finite-horizon, deterministic Markov decision search over section bundles.

State = passed transcript + selected bundle set. Actions add one legal bundle;
STOP is available only at the minimum load. Reward is the change in net profit.
The former MILP remains in scheduler.py as a reference, never called here.
"""
import copy
import itertools
import math
from profit_objective import settings, components, overload_penalty, option_profit,ef_background_cost,option_year_bonus,option_ge_progress
from preparation import benefits
from cm_background_policy import waives_prerequisites
from course_relations import check_rules

LANGUAGE_GE={'GE1401','GE1501','GE1601','GE2401'}

def conflict(a,b):
    return any(x['day']==y['day'] and set(x['weeks'])&set(y['weeks']) and
        x['start_minute']<y['end_minute'] and y['start_minute']<x['end_minute'] for x in a for y in b)

def distribution(o):
    return o.get('ge_area') in (1,2,3) or o['course_code'].startswith('GE') and o['course_code'] not in LANGUAGE_GE

class Rules:
    def __init__(self,problem):
        self.p=problem;self.config=settings(problem);self.done=set(problem['completed_courses'])
        self.major=problem.get('programme',problem.get('major'))
        if self.major:
            from programme_policy import programme
            self.major=programme(self.major)
        self.minimum=problem.get('course_min',0)
        self.maximum=problem.get('course_max',6)
        if type(self.minimum) is not int or type(self.maximum) is not int or not 0<=self.minimum<=self.maximum:
            raise ValueError('Invalid distinct-course limits')
        # Default semester load is flexible; graduation is checked over eight terms.
        if self.config.get('student_year') in (1,2,3,4):self.maximum=min(6,self.maximum)
        if self.minimum>self.maximum:raise ValueError('Maximum is below the normal minimum load')
        self.lo=problem['credit_min'];self.hi=problem['credit_max']
        if not 0<=self.lo<=self.hi:raise ValueError('Invalid credit limits')
        self.required=set(problem['required_courses']);self.options=problem['options']
        ids=[o['option_id'] for o in self.options]
        if len(set(ids))!=len(ids):raise ValueError('Duplicate option IDs')
        self.by_id=dict(zip(ids,self.options));self.rejected={}
        from programme_policy import allowed
        for o in self.options:
            code=o['course_code'];reason=None;known=check_rules(code,self.done)
            waived=waives_prerequisites(problem,code)
            if type(o['credits']) not in (int,float) or not math.isfinite(o['credits']) or o['credits']<0:raise ValueError('Invalid credits')
            for k in ('background_mismatch','difficulty','workload'):
                v=o['scores'][k]
                if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1:raise ValueError('Invalid score')
            if self.major and not allowed(self.major,code):reason='not_in_programme_document_or_verified_GE'
            elif known['exclusive_conflicts']:reason='source_verified_exclusive_conflict'
            elif known['source_conflict_courses_needing_confirmation']:reason='conflicting_source_rules_need_confirmation'
            elif not waived and known['known_prerequisites_satisfied'] is False:reason='source_verified_prerequisites_not_met'
            elif not o['credits']:reason='non_credit_component_not_a_course_bundle'
            elif code in self.done:reason='already_completed'
            elif o.get('term')!=problem['term']:reason='wrong_or_unknown_term'
            elif o.get('rules_reviewed') is not True or not all(k in o for k in ('prerequisites_all','prerequisites_any_groups','corequisites','exclusive_courses')):reason='missing_reviewed_rules'
            elif not waived and (not set(o['prerequisites_all'])<=self.done or any(not set(g)&self.done for g in o['prerequisites_any_groups'])):reason='prerequisites_not_met'
            elif set(o['exclusive_courses'])&self.done:reason='exclusive_course_completed'
            elif o.get('timetable_verified') is not True or not o.get('meetings'):reason='missing_verified_timetable'
            else:
                for m in o['meetings']:
                    if m.get('day') not in range(1,8) or not m.get('weeks') or any(type(w) is not int or w<1 for w in m['weeks']) or not 0<=m.get('start_minute',-1)<m.get('end_minute',-1)<=1440:raise ValueError('Invalid meeting')
            if reason:self.rejected[o['option_id']]=reason
        self.eligible=[o for o in self.options if o['option_id'] not in self.rejected]
        for week,cap in problem.get('weekly_workload_caps',{}).items():
            if type(cap) not in (int,float) or not math.isfinite(cap) or cap<0:raise ValueError('Invalid weekly cap')
            for o in self.options:
                v=o.get('workload_by_week',{}).get(str(week))
                if type(v) not in (int,float) or not math.isfinite(v) or v<0:raise ValueError('Missing reliable assessment-week workload data')

    def violations(self,chosen,terminal=True):
        reasons=[];codes=[o['course_code'] for o in chosen];ids=[o['option_id'] for o in chosen]
        if len(set(ids))!=len(ids) or len(set(codes))!=len(codes):reasons.append('duplicate_course_or_option')
        reasons.extend(sorted({self.rejected[x] for x in ids if x in self.rejected}))
        if len(chosen)>self.maximum or terminal and len(chosen)<self.minimum:reasons.append('course_count_outside_limits')
        credits=sum(o['credits'] for o in chosen)
        if credits>self.hi or terminal and credits<self.lo:reasons.append('credits_outside_limits')
        if sum(distribution(o) for o in chosen)>1:reasons.append('more_than_one_distribution_GE')
        if terminal and not self.required<=set(codes):reasons.append('required_courses_missing')
        if terminal and any(not set(o['corequisites'])<=self.done|set(codes) for o in chosen):reasons.append('corequisites_missing')
        for a,b in itertools.combinations(chosen,2):
            if conflict(a['meetings'],b['meetings']):reasons.append('meeting_clash')
            if a['course_code'] in b['exclusive_courses'] or b['course_code'] in a['exclusive_courses']:reasons.append('exclusive_courses_selected')
        for week,cap in self.p.get('weekly_workload_caps',{}).items():
            if sum(o['workload_by_week'][str(week)] for o in chosen)>cap:reasons.append('weekly_workload_cap_exceeded')
        return sorted(set(reasons))

def validate_proposal(problem,proposal):
    """Acceptance gate for raw neural timetable proposals; never repairs silently."""
    rules=Rules(problem)
    ids=proposal.get('selected_option_ids',proposal.get('selected_options')) if isinstance(proposal,dict) else None
    reasons=[]
    if not isinstance(ids,list) or any(not isinstance(x,str) for x in ids):reasons=['missing_option_id_list'];ids=[]
    unknown=[x for x in ids if x not in rules.by_id]
    if unknown:reasons.append('unknown_option_ids')
    chosen=[rules.by_id[x] for x in ids if x in rules.by_id]
    reasons+=rules.violations(chosen)
    if isinstance(proposal,dict) and 'course_count' in proposal and (type(proposal['course_count']) is not int or proposal['course_count']!=len({o['course_code'] for o in chosen})):
        reasons.append('incorrect_reported_course_count')
    if isinstance(proposal,dict) and proposal.get('status')=='infeasible':reasons.append('infeasible_claim_requires_verification')
    return {'accepted':not reasons,'violations':sorted(set(reasons)),'unknown_option_ids':unknown,
        'course_count':len({o['course_code'] for o in chosen}),'minimum_courses':rules.minimum}

def solve(problem,state_limit=100000,candidate_limit=0):
    """Bellman subset DP, bounded only when a layer exceeds state_limit.

    Exact for unpruned searches; feasible (not optimal) is reported after pruning.
    Failed bounded searches are search_exhausted, not a proof of infeasibility.
    """
    if type(state_limit) is not int or state_limit<1:raise ValueError('state_limit must be a positive integer')
    r=Rules(problem);p=problem;c=r.config
    weights=p.get('weights',{'background_mismatch':1.,'difficulty':1.,'workload':1.})
    if not weights or any(k not in ('background_mismatch','difficulty','workload') or type(v) not in (int,float) or not math.isfinite(v) or v<0 for k,v in weights.items()):raise ValueError('Invalid objective weights')
    priorities={k:v for k,v in p.get('course_priority_weights',{}).items() if k not in r.done}
    from programme_policy import allowed,stream_result,policy,progress
    if any(not isinstance(k,str) or r.major and not allowed(r.major,k) or type(v) not in (int,float) or not math.isfinite(v) or v<0 for k,v in priorities.items()):raise ValueError('Invalid priorities')
    pw=p.get('graduation_priority_weight',3. if priorities else 0.)
    multiplier=p.get('stream_reward_multiplier',1.)
    if type(pw) not in (int,float) or not math.isfinite(pw) or pw<0:raise ValueError('Invalid priority weight')
    if type(multiplier) not in (int,float) or not math.isfinite(multiplier) or not 0<=multiplier<=10:raise ValueError('Invalid stream multiplier')
    bridges={k:v for k,v in p.get('prerequisite_bridge_bonus',{}).items() if k not in r.done}
    if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=10 or r.major and not allowed(r.major,k) for k,v in bridges.items()):raise ValueError('Invalid prerequisite bridge bonus')
    stream=stream_result(r.major,r.done,p.get('selected_stream'))['selected_stream'] if r.major else None
    rule=policy()['streams'][r.major][stream] if r.major else None
    before=progress(rule,r.done) if rule else 0
    def chain_gain(chosen):
        if not rule:return 0.
        after=progress(rule,r.done|{o['course_code'] for o in chosen})
        return multiplier*(2*(after-before)+6*(after>=rule['slots'])-6*(before>=rule['slots']))
    opts=sorted(r.eligible,key=lambda o:o['option_id'])
    if 'reward_course_relations' in p:
        # An explicit objective packet is authoritative; never substitute the
        # global graph for model-supplied, validated relation parameters.
        prep={};prior=set(c.get('preparation_completed_courses',r.done))
        for edge in p['reward_course_relations']:
            if edge['source'] in prior and edge['target'] not in prior and edge['source']!=edge['target']:
                prep[edge['target']]=min(.35,max(prep.get(edge['target'],0.),edge['benefit']))
    else:prep=benefits(c.get('preparation_completed_courses',r.done))
    # The final objective breakdown must use the same packet as the search.
    c['preparation_bonus_by_course']=prep
    def score(chosen):
        cost=sum(sum(w*o['scores'][k] for k,w in weights.items())+ef_background_cost(o,c,weights) for o in chosen)
        priority=pw*sum(priorities.get(o['course_code'],0) for o in chosen)
        if c['objective_mode']!='profit':return -cost+priority
        gain=sum(option_profit(o,c)+option_year_bonus(o,c)+option_ge_progress(o,c)+prep.get(o['course_code'],0)+bridges.get(o['course_code'],0) for o in chosen)
        chain=chain_gain(chosen)
        return gain+priority+chain-cost-overload_penalty(len(chosen),c,sum(o['credits'] for o in chosen))
    # Appending in index order deduplicates states. Marginal rewards telescope,
    # so every path to the same subset has the same return (Bellman state value).
    layer=[()];best=None;best_score=-math.inf;bounded=False;counts=[];candidate_states={}
    for depth in range(r.maximum+1):
        counts.append(len(layer));next_layer=[]
        for state in layer:
            chosen=[opts[i] for i in state]
            if not r.violations(chosen):
                value=score(chosen)
                if candidate_limit:
                    codes=tuple(sorted(o['course_code'] for o in chosen))
                    if codes not in candidate_states or value>candidate_states[codes][0]:candidate_states[codes]=(value,state)
                if value>best_score+1e-10:best_score=value;best=state
            if depth==r.maximum:continue
            for i in range(state[-1]+1 if state else 0,len(opts)):
                new=state+(i,);selection=chosen+[opts[i]]
                if not r.violations(selection,terminal=False):next_layer.append(new)
        if len(next_layer)>state_limit:
            bounded=True
            next_layer=sorted(next_layer,key=lambda s:score([opts[i] for i in s]),reverse=True)[:state_limit]
        layer=next_layer
        if not layer:break
    common={'planner':'Markov decision subset search; no MILP','search_exact':not bounded,'states_by_course_count':counts,
        'course_min':r.minimum,'course_max':r.maximum,'rejected_options':r.rejected,
        'eligible_course_count':len({o['course_code'] for o in opts})}
    if candidate_limit:
        common['candidate_schedules']=[{'selected_options':[opts[i]['option_id'] for i in state],'net_reward':value}
            for value,state in sorted(candidate_states.values(),reverse=True)[:candidate_limit]]
    if best is None:return {**common,'status':'search_exhausted' if bounded else 'infeasible',
        'reason':'hard_constraints_infeasible','message':'No legal semester found. The minimum course load was not relaxed.'}
    chosen=[opts[i] for i in best];assert not r.violations(chosen)
    parts=components(chosen,priorities,pw,weights,c) if c['objective_mode']=='profit' else None
    if parts:
        bridge=sum(bridges.get(o['course_code'],0) for o in chosen)
        chain=chain_gain(chosen)
        parts.update(prerequisite_bridge_bonus=bridge,stream_chain_bonus=chain,selected_stream=stream)
        parts['net_profit']+=bridge+chain;parts['schedule_loss']=-parts['net_profit']
        if not math.isclose(parts['net_profit'],best_score,abs_tol=1e-7):raise RuntimeError('Markov reward accounting mismatch')
    marginal=[];old=score([])
    for i in range(len(chosen)):
        new=score(chosen[:i+1]);marginal.append({'added_option':chosen[i]['option_id'],'reward':new-old});old=new
    return {**common,'status':'feasible' if bounded else 'optimal','selected_options':[o['option_id'] for o in chosen],
        'course_codes':[o['course_code'] for o in chosen],'credits':sum(o['credits'] for o in chosen),'course_count':len(chosen),
        'objective':best_score if parts else -best_score+pw*sum(priorities.values()),'objective_sense':'maximize' if parts else 'minimize',
        'profit_breakdown':parts,'objective_settings':c,'marginal_rewards':marginal,
        'stop_action_available':True,'neural_output_repaired':False,
        'student_cost':sum(sum(w*o['scores'][k] for k,w in weights.items())+ef_background_cost(o,c,weights) for o in chosen),
        'selected_priority_courses':[o['course_code'] for o in chosen if priorities.get(o['course_code'],0)>0],
        'unselected_priority_courses':sorted(set(priorities)-{o['course_code'] for o in chosen}),
        'weekly_balance_verified':bool(p.get('weekly_workload_caps')),
        'prerequisite_waivers_assumed':[o['course_code'] for o in chosen if waives_prerequisites(p,o['course_code'])],
        'limitations':['Only supplied reviewed rules and meetings are enforced.','No neural weights were updated by this planner change.']}

def plan_from_proposal(problem,proposal):
    if isinstance(proposal,dict) and proposal.get('status')=='infeasible' and proposal.get('selected_option_ids')==[] and proposal.get('course_count',0)==0:
        result=solve(problem)
        accepted=result['status']=='infeasible' and result.get('search_exact') is True
        result.update(model_output_accepted=accepted,verified_model_infeasibility=accepted,policy_fallback_used=not accepted,
            neural_output_repaired=not accepted,proposal=copy.deepcopy(proposal),
            proposal_validation={'accepted':accepted,'violations':[] if accepted else ['unsupported_infeasibility_claim']})
        return result
    validation=validate_proposal(problem,proposal)
    if validation['accepted']:
        ids=proposal.get('selected_option_ids',proposal.get('selected_options'))
        by_id={o['option_id']:o for o in problem['options']};chosen=[by_id[x] for x in ids]
        return {'status':'feasible','model_output_accepted':True,'proposal_validation':validation,'proposal':copy.deepcopy(proposal),
            'selected_options':ids,'course_codes':[o['course_code'] for o in chosen],'credits':sum(o['credits'] for o in chosen),
            'course_count':len(chosen),'policy_fallback_used':False,'neural_output_repaired':False,
            'planner':'Validated neural proposal; no optimality claim'}
    result=solve(problem)
    result.update(model_output_accepted=False,proposal_validation=validation,policy_fallback_used=True,neural_output_repaired=True)
    return result
