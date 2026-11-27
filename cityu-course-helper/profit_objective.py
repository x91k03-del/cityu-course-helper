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
    from preparation import profile_passes
    mode=problem.get('objective_mode',POLICY['objective_mode'])
    if mode not in ['profit','legacy_cost']:raise ValueError('Unknown objective_mode')
    threshold=problem.get('overload_reference_courses',POLICY['overload_reference_courses'])
    if type(threshold) is not int or threshold<0:raise ValueError('Invalid overload_reference_courses')
    overload_mode=problem.get('overload_mode',POLICY.get('overload_mode','course_count'))
    if overload_mode not in ['course_count','year4_credits','year_specific_credits']:raise ValueError('Invalid overload_mode')
    year=problem.get('student_year')
    if mode=='profit' and overload_mode in ['year4_credits','year_specific_credits'] and (type(year) is not int or year not in range(1,5)):
        raise ValueError('student_year is required for the year-4 credit overload policy')
    areas=problem.get('completed_GE_area_counts',{})
    if not isinstance(areas,dict) or any(str(k) not in ['1','2','3'] or type(v) is not int or v<0 for k,v in areas.items()):
        raise ValueError('Invalid completed_GE_area_counts')
    multiplier=number(problem.get('covered_GE_area_multiplier',.1),'covered_GE_area_multiplier')
    if multiplier>=1:raise ValueError('Covered GE area multiplier must be below 1')
    return {'objective_mode':mode,'overload_mode':overload_mode,'student_year':year,
            'programme':problem.get('programme',problem.get('major')),
            'ef3320_year4_bonus':number(problem.get('ef3320_year4_bonus',4.),'ef3320_year4_bonus'),
            'track_ge_graduation':problem.get('track_ge_graduation',False),
            'new_GE_area_bonus':number(problem.get('new_GE_area_bonus',5.),'new_GE_area_bonus'),
            'GE_count_progress_bonus':number(problem.get('GE_count_progress_bonus',2.),'GE_count_progress_bonus'),
            **{k:problem[k] for k in ['finance_background','GE_history','transcript','course_results','failed_courses','in_progress_courses','withdrawn_courses'] if k in problem},
            'ef_no_finance_penalty':number(problem.get('ef_no_finance_penalty',1.5),'ef_no_finance_penalty'),
            'completed_courses':list(problem.get('completed_courses',[])),
            'preparation_completed_courses':profile_passes(problem),
            'base_course_profit':number(problem.get('base_course_profit',POLICY['base_course_profit']),'base_course_profit'),
            'overload_reference_courses':threshold,
            'overload_threshold_credits':number(problem.get('overload_threshold_credits',POLICY.get('overload_threshold_credits',12)),'overload_threshold_credits'),
            'overload_penalty_weight':number(problem.get('overload_penalty_weight',POLICY['overload_penalty_weight']),'overload_penalty_weight'),
            'completed_GE_area_counts':areas,
            'covered_GE_area_multiplier':multiplier,
            'years_1_to_3_overload_weight':number(problem.get('years_1_to_3_overload_weight',POLICY.get('years_1_to_3_overload_weight',.25)),'years_1_to_3_overload_weight'),
            'years_1_to_3_overload_threshold_credits':number(problem.get('years_1_to_3_overload_threshold_credits',POLICY.get('years_1_to_3_overload_threshold_credits',15)),'years_1_to_3_overload_threshold_credits'),
            'year4_overload_weight':number(problem.get('year4_overload_weight',POLICY.get('year4_overload_weight',.25)),'year4_overload_weight')}

def overload_penalty(count,config,credits=None):
    if type(count) is not int or count<0:raise ValueError('Invalid distinct course count')
    if config.get('overload_mode') in ['year4_credits','year_specific_credits']:
        if config['student_year']!=4:
            if config['overload_mode']=='year4_credits':return 0.
            credits=number(credits,'selected credits')
            return config['years_1_to_3_overload_weight']*max(0,credits-config['years_1_to_3_overload_threshold_credits'])**2
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
    if 'preparation_bonus_by_course' in config:
        return number(config['preparation_bonus_by_course'].get(option['course_code'],0.),'preparation benefit')
    from preparation import benefits
    return benefits(config.get('preparation_completed_courses',config.get('completed_courses',[]))).get(option['course_code'],0.)

def option_year_bonus(option,config):
    """Advisory timing preference; never an eligibility or prerequisite gate."""
    return config.get('ef3320_year4_bonus',4.) if (config.get('programme') in ('CM','BSCM','Computing Mathematics')
        and config.get('student_year')==4 and option['course_code']=='EF3320') else 0.

def option_ge_progress(option,config):
    if not config.get('track_ge_graduation') or option.get('ge_area') not in (1,2,3):return 0.
    counts=config.get('completed_GE_area_counts',{})
    total=sum(counts.values());area=option['ge_area']
    # At most one distribution GE per term, so these marginal quota rewards
    # cannot double-count two same-term courses.
    return (config.get('new_GE_area_bonus',5.) if not counts.get(str(area),counts.get(area,0)) else 0.)+(config.get('GE_count_progress_bonus',2.) if total<4 else 0.)

def components(chosen,priorities,progress_weight,weights,config):
    profits=sum(option_profit(o,config) for o in chosen)
    bonus=progress_weight*sum(priorities.get(o['course_code'],0.) for o in chosen)
    risk=sum(sum(w*o['scores'][k] for k,w in weights.items()) for o in chosen)
    ef_penalty=sum(ef_background_cost(o,config,weights) for o in chosen)
    risk+=ef_penalty
    credits=sum(o['credits'] for o in chosen)
    overload=overload_penalty(len(chosen),config,credits)
    preparation=sum(option_preparation(o,config) for o in chosen)
    timing=sum(option_year_bonus(o,config) for o in chosen)
    ge_progress=sum(option_ge_progress(o,config) for o in chosen)
    net=profits+bonus+preparation+timing+ge_progress-risk-overload
    return {'course_profit':profits,'maths_priority_bonus':bonus,'gross_profit':profits+bonus+timing+ge_progress,
            'EF3320_year4_bonus':timing,'GE_graduation_progress_bonus':ge_progress,
            'ef_finance_mismatch_penalty':ef_penalty,
            'preparation_by_course':{o['course_code']:option_preparation(o,config) for o in chosen},
            'student_cost_penalty':risk,'overload_penalty':overload,'total_profit_penalty':risk+overload,
            'preparation_benefit':preparation,'net_profit':net,'schedule_loss':-net,'course_count':len(chosen),'selected_credits':credits}

def ef_background_cost(option,config,weights):
    from cm_background_policy import ef_mismatch_penalty
    return ef_mismatch_penalty({**config,'weights':weights},option['course_code'])
