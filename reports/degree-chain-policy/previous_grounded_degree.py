"""Full-degree attempt using exact saved terms, sections and meeting evidence."""
import copy,json
from pathlib import Path
from four_year_markov import catalog,audit
from programme_policy import allowed
from timetable_grounded_training import records,assessment,problem_for,schedule_messages
ROOT=Path(__file__).resolve().parent

def simulate(profile,model_provider=None):
    from degree_chain import simulate as flexible_chain
    return flexible_chain(profile,model_provider)
    if profile['programme']!='CM' or profile.get('year',1)!=1 or profile.get('completed_courses',[]):
        raise ValueError('This degree attempt requires an entering Year-1 CM profile with no completed courses.')
    from markov_planner import solve,plan_from_proposal
    initial=copy.deepcopy(profile);done=list(profile.get('completed_courses',[]));transcript=[];steps=[]
    missing=[]
    for course in catalog():
        if not course['required']:continue
        code=course.get('course_code_display',course['id'])
        if not any(assessment({**profile,'term':term},code)['timetable_available'] for term in ['202609','202702']):missing.append(code)
    for term in range(1,9):
        year=(term+1)//2;semester='A' if term%2 else 'B'
        term_code=str(2026+year-1)+('09' if semester=='A' else '02') if semester=='A' else str(2026+year)+'02'
        p={**profile,'year':year,'term':term_code,'completed_courses':sorted(set(done))}
        problem=problem_for(p)
        if model_provider is not None:
            raw,parsed=model_provider(schedule_messages(problem))
            result=plan_from_proposal(problem,parsed)
            result['raw_model_response']=raw
        else:result=solve(problem)
        provenance={o['option_id']:{'source_pdf':o['source'],'course_code':o['course_code'],'meetings':o['meetings'],
            'snapshot_term':o['term'],'component_linkage_assumed':o.get('component_linkage_assumed',False)} for o in problem['options']}
        step={'term':term,'year':year,'semester':semester,'term_code':term_code,'input_profile':p,
            'candidate_course_codes':sorted({o['course_code'] for o in problem['options']}),'result':result,
            'selected_timetable_evidence':{x:provenance[x] for x in result.get('selected_options',[])}}
        steps.append(step)
        if result['status'] not in ('optimal','feasible','validated_proposal'):
            return {'status':'incomplete_missing_or_incompatible_saved_timetables','input_profile':initial,
                'method':'Markov decision search over saved section bundles; no MILP','steps':steps,'transcript':transcript,
                'blocked_at':{'year':year,'semester':semester,'term_code':term_code,'reason':result.get('reason'),
                    'candidate_course_codes':step['candidate_course_codes'],'minimum_courses':problem['course_min']},
                'mandatory_courses_without_any_compatible_saved_timetable':sorted(set(missing)),
                'audit':{'earned_credits':sum(r['credits'] for r in transcript),'all_encoded_requirements_met':False,
                    'official_graduation_verified':False},
                'interpretation':'Insufficient source evidence is not proof that the actual university programme cannot be completed. No unsupported course was selected.',
                'assumptions':['Exact saved terms only; no Semester A/B or future-year extrapolation.',
                    'Source section bundle pairing/teaching weeks retain the explicitly hypothetical assumptions from prior experiments.',
                    'No initial completed courses or transcript credits are invented.']}
        options={o['option_id']:o for o in problem['options']}
        for opt in result['selected_options']:
            o=options[opt];done.append(o['course_code'])
            transcript.append({'id':o['course_code'],'credits':o['credits'],'grade':'B','term':term,'year':year,'semester':semester})
    # This path needs complete saved source coverage, not curriculum-only windows.
    result=audit(transcript)
    return {'status':'complete' if result['all_encoded_requirements_met'] else 'graduation_incomplete',
        'input_profile':initial,'steps':steps,'transcript':transcript,'audit':result,'future_offerings_extrapolated':False}
