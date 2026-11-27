"""MILP over complete section bundles. Missing hard-constraint evidence fails closed."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from profit_objective import settings,option_profit,option_preparation,overload_penalty,components


def conflict(a, b):
    return any(x['day'] == y['day'] and set(x['weeks']) & set(y['weeks']) and
               x['start_minute'] < y['end_minute'] and y['start_minute'] < x['end_minute']
               for x in a for y in b)


def solve(problem):
    opts = problem['options']
    n = len(opts)
    required = set(problem['required_courses'])
    completed = set(problem['completed_courses'])
    config=settings(problem)
    programme_name=problem.get('programme',problem.get('major'))
    stream_info=None
    if programme_name:
        from programme_policy import allowed,stream_result
        stream_info=stream_result(programme_name,completed,problem.get('selected_stream'))
    lo, hi = problem['credit_min'], problem['credit_max']
    if not 0 <= lo <= hi:
        raise ValueError('Invalid credit limits')
    course_min,course_max=problem.get('course_min',0 if config.get('student_year')==4 else 5),problem.get('course_max',6)
    if type(course_min) is not int or type(course_max) is not int or not 0<=course_min<=course_max:
        raise ValueError('Invalid distinct-course count limits')
    priorities=problem.get('course_priority_weights',{})
    if not isinstance(priorities,dict) or any(not isinstance(c,str) or (not allowed(programme_name,c) if programme_name else not c.startswith('MA')) or type(v) not in (int,float) or not math.isfinite(v) or v<0 for c,v in priorities.items()):
        raise ValueError('Invalid maths graduation-priority weights')
    progress_weight=problem.get('graduation_priority_weight',3.0 if priorities else 0.0)
    if type(progress_weight) not in (int,float) or not math.isfinite(progress_weight) or progress_weight<0:
        raise ValueError('Invalid graduation-priority objective weight')
    priorities={c:v for c,v in priorities.items() if c not in completed}
    if not n:
        return {'status':'infeasible','reason':'no_verified_course_options','course_min':course_min,'eligible_course_count':0}
    weights = problem.get('weights', {'background_mismatch': 1., 'difficulty': 1., 'workload': 1.})
    if not weights or any(k not in ['background_mismatch', 'difficulty', 'workload'] or not math.isfinite(v) or v < 0 for k, v in weights.items()):
        raise ValueError('Invalid objective weights')
    stream_multiplier=problem.get('stream_reward_multiplier',1.)
    if type(stream_multiplier) not in (int,float) or not math.isfinite(stream_multiplier) or not 0<=stream_multiplier<=10:raise ValueError('Invalid stream_reward_multiplier')
    bridges={c:v for c,v in problem.get('prerequisite_bridge_bonus',{}).items() if c not in completed}
    if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=10 or programme_name and not allowed(programme_name,c) for c,v in bridges.items()):raise ValueError('Invalid prerequisite bridge bonus')
    ids = [o['option_id'] for o in opts]
    if len(set(ids)) != n:
        raise ValueError('Duplicate option IDs')
    ub = np.ones(n)
    rows, lower, upper = [], [], []
    rejected = {}
    from cm_background_policy import waives_prerequisites

    def constraint(row, low=-np.inf, high=np.inf):
        rows.append(row)
        lower.append(low)
        upper.append(high)

    courses = sorted({o['course_code'] for o in opts})
    for i, o in enumerate(opts):
        for k in ['background_mismatch', 'difficulty', 'workload']:
            v = o['scores'][k]
            if type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1:
                raise ValueError('Invalid score for ' + o['option_id'])
        if not isinstance(o['credits'], (int, float)) or not math.isfinite(o['credits']) or o['credits'] < 0:
            raise ValueError('Invalid credits')
        reason = None
        from course_relations import check_rules
        known_rule=check_rules(o['course_code'],completed)
        waived=waives_prerequisites(problem,o['course_code'])
        if programme_name and not allowed(programme_name,o['course_code']):
            reason='not_in_programme_document_or_verified_GE'
        elif known_rule['exclusive_conflicts']:
            reason='source_verified_exclusive_conflict'
        elif known_rule['source_conflict_courses_needing_confirmation']:
            reason='conflicting_source_rules_need_confirmation'
        elif not waived and known_rule['known_prerequisites_satisfied'] is False:
            reason='source_verified_prerequisites_not_met'
        elif o['credits']==0:
            reason = 'non_credit_component_not_a_course_bundle'
        elif o['course_code'] in completed:
            reason = 'already_completed'
        elif o.get('term') != problem['term']:
            reason = 'wrong_or_unknown_term'
        elif o.get('rules_reviewed') is not True or not all(k in o for k in ['prerequisites_all', 'prerequisites_any_groups', 'corequisites', 'exclusive_courses']):
            reason = 'missing_reviewed_rules'
        elif not waived and (not set(o['prerequisites_all']) <= completed or any(not set(group) & completed for group in o['prerequisites_any_groups'])):
            reason = 'prerequisites_not_met'
        elif set(o['exclusive_courses']) & completed:
            reason = 'exclusive_course_completed'
        elif o.get('timetable_verified') is not True or not o.get('meetings'):
            reason = 'missing_verified_timetable'
        else:
            for m in o['meetings']:
                if (m.get('day') not in range(1, 8) or not m.get('weeks') or
                    any(type(w) is not int or w < 1 for w in m['weeks']) or
                    not 0 <= m.get('start_minute', -1) < m.get('end_minute', -1) <= 1440):
                    raise ValueError('Invalid meeting')
        if reason:
            ub[i] = 0
            rejected[o['option_id']] = reason
    for code in courses:
        row = [int(o['course_code'] == code) for o in opts]
        constraint(row, low=1 if code in required else 0, high=1)
    absent = required - set(courses)
    if absent:
        return {'status': 'infeasible', 'reason': 'required_courses_missing', 'courses': sorted(absent)}
    constraint([o['credits'] for o in opts], lo, hi)
    # At most one complete option per course is already enforced above. Therefore
    # this counts distinct credit-bearing courses, not lecture/tutorial CRNs.
    constraint([1]*n,course_min,course_max)
    # Compulsory language/development GE codes are outside distributional GE.
    language={'GE1401','GE1501','GE1601','GE2401'}
    constraint([int(o.get('ge_area') in [1,2,3] or o['course_code'].startswith('GE') and o['course_code'] not in language) for o in opts],high=1)
    eligible_codes={o['course_code'] for i,o in enumerate(opts) if ub[i]>0}
    if len(eligible_codes)<course_min:
        return {'status':'infeasible','reason':'insufficient_eligible_courses','course_min':course_min,
                'eligible_course_count':len(eligible_codes),'eligible_courses':sorted(eligible_codes),
                'rejected_options':rejected,'message':'Supply more verified eligible course options; the minimum was not relaxed.'}
    for i, a in enumerate(opts):
        for j in range(i+1, n):
            b = opts[j]
            if (conflict(a.get('meetings', []), b.get('meetings', [])) or
                b['course_code'] in a.get('exclusive_courses', []) or a['course_code'] in b.get('exclusive_courses', [])):
                row = [0]*n
                row[i] = row[j] = 1
                constraint(row, high=1)
        for code in a.get('corequisites', []):
            if code not in completed:
                row = [int(k == i) - int(o['course_code'] == code) for k, o in enumerate(opts)]
                constraint(row, high=0)
    for week, cap in problem.get('weekly_workload_caps', {}).items():
        if type(cap) not in (float, int) or not math.isfinite(cap) or cap < 0:
            raise ValueError('Invalid weekly cap')
        if any(str(week) not in o.get('workload_by_week', {}) for o in opts):
            raise ValueError('Missing reliable assessment-week workload data')
        values = [o['workload_by_week'][str(week)] for o in opts]
        if any(type(v) not in (float, int) or not math.isfinite(v) or v < 0 for v in values):
            raise ValueError('Invalid weekly workload')
        constraint(values, high=cap)
    base_costs=np.array([sum(w*o['scores'][k] for k,w in weights.items()) for o in opts])
    costs=base_costs-np.array([progress_weight*priorities.get(o['course_code'],0.) for o in opts])
    if config['objective_mode']=='profit':
        costs=costs-np.array([option_profit(o,config)+option_preparation(o,config)+bridges.get(o['course_code'],0) for o in opts])
        # Exact linearization of the quadratic count penalty: one binary z_k
        # selects the total number of courses, so penalty is exactly f(k).
        credit_overload=config.get('overload_mode')=='year4_credits' and config['student_year']==4
        if credit_overload:
            if any(not float(o['credits']).is_integer() for o in opts):raise ValueError('Year-4 overload MILP currently requires integer credit units')
            counts=list(range(math.ceil(lo),min(math.floor(hi),sum(int(o['credits']) for i,o in enumerate(opts) if ub[i]>0))+1))
            load=[o['credits'] for o in opts]
            penalties=[overload_penalty(0,config,k) for k in counts]
        else:
            counts=list(range(course_min,min(course_max,len(eligible_codes))+1))
            load=[1]*n
            penalties=[overload_penalty(k,config) for k in counts]
        extra=len(counts)
        rows=[list(row)+[0]*extra for row in rows]
        constraint([0]*n+[1]*extra,1,1)
        constraint(load+[-k for k in counts],0,0)
        costs=np.concatenate([costs,penalties])
        ub=np.concatenate([ub,np.ones(extra)])
    if stream_info and config['objective_mode']=='profit':
        import itertools
        from programme_policy import chain_reward
        members=sorted(set(stream_info['course_chain_bonus']) & eligible_codes)
        patterns=list(itertools.product([0,1],repeat=len(members)));old=len(costs);extra=len(patterns)
        rows=[list(row)+[0]*extra for row in rows]
        constraint([0]*old+[1]*extra,1,1)
        for k,code in enumerate(members):
            constraint([int(o['course_code']==code) for o in opts]+[0]*(old-n)+[-pattern[k] for pattern in patterns],0,0)
        costs=np.concatenate([costs,[-stream_multiplier*chain_reward(programme_name,completed,stream_info['selected_stream'],[c for c,b in zip(members,pattern) if b]) for pattern in patterns]])
        ub=np.concatenate([ub,np.ones(extra)])
    res = milp(costs, integrality=np.ones(len(costs)), bounds=Bounds(np.zeros(len(costs)), ub),
               constraints=LinearConstraint(np.array(rows), lower, upper), options={'time_limit': 30.})
    if not res.success:
        return {'status': 'infeasible' if res.status == 2 else 'solver_failed', 'message': res.message,
                'reason':'hard_constraints_infeasible','course_min':course_min,'course_max':course_max,'rejected_options': rejected}
    chosen = [o for o, x in zip(opts, res.x[:n]) if x > .5]
    # Recheck the numerical solution against the encoded matrix before returning it.
    binary = np.rint(res.x)
    totals = np.array(rows) @ binary
    if np.any(totals < np.array(lower)-1e-6) or np.any(totals > np.array(upper)+1e-6) or np.any(binary > ub):
        raise RuntimeError('Solver output violates encoded constraints')
    profit=components(chosen,priorities,progress_weight,weights,config) if config['objective_mode']=='profit' else None
    if profit is not None:
        bridge_gain=sum(bridges.get(o['course_code'],0) for o in chosen)
        profit.update(prerequisite_bridge_bonus=bridge_gain)
        profit['net_profit']+=bridge_gain;profit['schedule_loss']=-profit['net_profit']
    if profit is not None and stream_info:
        gain=stream_multiplier*chain_reward(programme_name,completed,stream_info['selected_stream'],[o['course_code'] for o in chosen])
        profit.update(stream_chain_bonus=gain,selected_stream=stream_info['selected_stream'],stream_reward_multiplier=stream_multiplier)
        profit['net_profit']+=gain;profit['schedule_loss']=-profit['net_profit']
    if profit is not None and not math.isclose(profit['schedule_loss'],float(res.fun),rel_tol=1e-7,abs_tol=1e-6):
        raise RuntimeError('Profit accounting differs from optimized loss')
    return {'status': 'optimal', 'selected_options': [o['option_id'] for o in chosen],
            'course_codes': [o['course_code'] for o in chosen], 'credits': sum(o['credits'] for o in chosen),
            'objective': profit['net_profit'] if profit is not None else float(res.fun+progress_weight*sum(priorities.values())),
            'objective_sense':'maximize' if profit is not None else 'minimize',
            'objective_model':'net_course_profit_after_cost_and_overload_penalties' if profit is not None else 'student_cost_plus_weighted_unselected_maths_core',
            **({'profit_breakdown':profit,'objective_settings':config} if profit is not None else {}),
            'course_count':len(chosen),'course_min':course_min,'course_max':course_max,
            'student_cost':sum(sum(w*o['scores'][k] for k,w in weights.items()) for o in chosen),
            'graduation_priority_weight':progress_weight,
            'selected_priority_courses':[o['course_code'] for o in chosen if priorities.get(o['course_code'],0)>0],
            'unselected_priority_courses':sorted(set(priorities)-{o['course_code'] for o in chosen}),
            'priority_policy_note':problem.get('priority_policy_note'), 'rejected_options': rejected,
            'data_mode': problem.get('data_mode', 'unspecified'),
            'weekly_balance_verified': bool(problem.get('weekly_workload_caps')),
            'prerequisite_waivers_assumed':[o['course_code'] for o in chosen if waives_prerequisites(problem,o['course_code'])],
            'limitations': ['Only the supplied reviewed rules and meetings are enforced.',
                            'Scores may be synthetic estimates. Seats and registration are not guaranteed.']}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('problem')
    a = ap.parse_args()
    print(json.dumps(solve(json.loads(Path(a.problem).read_text(encoding='utf-8'))), indent=2))
