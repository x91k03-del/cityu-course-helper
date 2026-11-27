"""Profit objective and exact increasing course-count penalty, shared by both planners."""
import json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
POLICY=json.loads((ROOT/'data/profit_objective_policy.json').read_text(encoding='utf-8'))

def number(value,name,nonnegative=True):
    if type(value) not in (int,float) or not math.isfinite(value) or nonnegative and value<0:
        raise ValueError('Invalid '+name)
    return float(value)

def settings(problem):
    mode=problem.get('objective_mode',POLICY['objective_mode'])
    if mode not in ['profit','legacy_cost']:raise ValueError('Unknown objective_mode')
    threshold=problem.get('overload_reference_courses',POLICY['overload_reference_courses'])
    if type(threshold) is not int or threshold<0:raise ValueError('Invalid overload_reference_courses')
    overload_mode=problem.get('overload_mode',POLICY.get('overload_mode','course_count'))
    if overload_mode not in ['course_count','year4_credits']:raise ValueError('Invalid overload_mode')
    year=problem.get('student_year')
    if mode=='profit' and overload_mode=='year4_credits' and (type(year) is not int or year not in range(1,5)):
        raise ValueError('student_year is required for the year-4 credit overload policy')
    areas=problem.get('completed_GE_area_counts',{})
    if not isinstance(areas,dict) or any(str(k) not in ['1','2','3'] or type(v) is not int or v<0 for k,v in areas.items()):
        raise ValueError('Invalid completed_GE_area_counts')
    multiplier=number(problem.get('covered_GE_area_multiplier',.1),'covered_GE_area_multiplier')
    if multiplier>=1:raise ValueError('Covered GE area multiplier must be below 1')
    return {'objective_mode':mode,'overload_mode':overload_mode,'student_year':year,
            'completed_courses':list(problem.get('completed_courses',[])),
            'base_course_profit':number(problem.get('base_course_profit',POLICY['base_course_profit']),'base_course_profit'),
            'overload_reference_courses':threshold,
            'overload_threshold_credits':number(problem.get('overload_threshold_credits',POLICY.get('overload_threshold_credits',12)),'overload_threshold_credits'),
            'overload_penalty_weight':number(problem.get('overload_penalty_weight',POLICY['overload_penalty_weight']),'overload_penalty_weight'),
            'completed_GE_area_counts':areas,
            'covered_GE_area_multiplier':multiplier,
            'year4_overload_weight':number(problem.get('year4_overload_weight',POLICY.get('year4_overload_weight',.25)),'year4_overload_weight')}

def overload_penalty(count,config,credits=None):
    if type(count) is not int or count<0:raise ValueError('Invalid distinct course count')
    if config.get('overload_mode')=='year4_credits':
        if config['student_year']!=4:return 0.
        credits=number(credits,'selected credits')
        return config['year4_overload_weight']*max(0,credits-config['overload_threshold_credits'])**2
    return config['overload_penalty_weight']*max(0,count-config['overload_reference_courses'])**2

def option_profit(option,config):
    value=number(option.get('profit',config['base_course_profit']),'option profit')
    area=option.get('ge_area')
    if area is not None:
        if type(area) is not int or area not in [1,2,3]:raise ValueError('Invalid GE distributional area')
        counts=config.get('completed_GE_area_counts',{})
        count=counts.get(str(area),counts.get(area,0))
        if type(count) is not int or count<0:raise ValueError('Invalid completed GE area count')
        if count:value*=config['covered_GE_area_multiplier']
    return value

def option_preparation(option,config):
    from preparation import benefits
    return benefits(config.get('completed_courses',[])).get(option['course_code'],0.)

def components(chosen,priorities,progress_weight,weights,config):
    profits=sum(option_profit(o,config) for o in chosen)
    bonus=progress_weight*sum(priorities.get(o['course_code'],0.) for o in chosen)
    risk=sum(sum(w*o['scores'][k] for k,w in weights.items()) for o in chosen)
    credits=sum(o['credits'] for o in chosen)
    overload=overload_penalty(len(chosen),config,credits)
    preparation=sum(option_preparation(o,config) for o in chosen)
    net=profits+bonus+preparation-risk-overload
    return {'course_profit':profits,'maths_priority_bonus':bonus,'gross_profit':profits+bonus,
            'student_cost_penalty':risk,'overload_penalty':overload,'total_profit_penalty':risk+overload,
            'preparation_benefit':preparation,'net_profit':net,'schedule_loss':-net,'course_count':len(chosen),'selected_credits':credits}
