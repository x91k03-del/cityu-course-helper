"""Explicit course-load constraints and advisory CM graduation-progress weights."""
import json
from pathlib import Path
POLICY=json.loads((Path(__file__).resolve().parent/'data/cm_year_priority_policy.json').read_text(encoding='utf-8'))
COMMON_MATH_CORE=POLICY['common_maths_core']
YEAR_FOCUS={int(k):v for k,v in POLICY['year_focus'].items()}

def cm_priority_weights(year,completed):
    if type(year) is not int or year not in range(1,5):raise ValueError('CM student year must be 1 to 4')
    done=set(completed)
    # Common core list: supplied handbook physical page 10. Year focus is an editable
    # planning policy derived from course levels, not an official completion deadline.
    return {code:float(POLICY['year_focus_weight']) if code in YEAR_FOCUS[year] else float(POLICY['base_core_weight'])
            for code in COMMON_MATH_CORE if code not in done}

def apply_profile_policy(problem,profile):
    from programme_policy import programme
    problem['programme']=programme(profile['major'])
    if profile.get('selected_stream'):problem['selected_stream']=profile['selected_stream']
    problem.setdefault('student_year',profile['year'])
    problem.setdefault('course_min',0);problem.setdefault('course_max',POLICY['maximum_courses'])
    area_file=Path(__file__).resolve().parent/'data/four-year/GE_areas.json'
    if area_file.exists():
        areas=json.loads(area_file.read_text(encoding='utf-8'));done=set(profile['completed_courses'])
        problem.setdefault('completed_GE_area_counts',{str(a):sum(code in done and entry['area']==a for code,entry in areas.items()) for a in [1,2,3]})
        for option in problem.get('options',[]):
            if option['course_code'] in areas:option.setdefault('ge_area',areas[option['course_code']]['area'])
    if profile.get('major') in ['Computing Mathematics','BSCM','computing math']:
        problem.setdefault('course_priority_weights',cm_priority_weights(profile['year'],profile['completed_courses']))
        problem.setdefault('graduation_priority_weight',float(POLICY['graduation_priority_weight']))
        problem.setdefault('priority_policy_note','Advisory year-focused weights for unfinished common CM maths core; not an official graduation audit.')
    if problem['programme']=='CS':
        focus={1:['CS1302A','CS2115','CS2310','CS2402','MA1503','MA1508'],
               2:['CS2312','CS3201','CS3334','CS3103','CS3342','CS3402','MA2185','JC2066'],
               3:['CS4335'],4:['CS4514']}
        problem.setdefault('course_priority_weights',{c:3. for c in focus[profile['year']] if c not in profile['completed_courses']})
        problem.setdefault('graduation_priority_weight',3.)
        problem.setdefault('priority_policy_note','Year focus derived from supplied 2025 CS suggested schedule; 2026/27 major-page differences need cohort confirmation.')
    return problem
