"""Exact programme/term lookups and explicitly hypothetical section-bundle planning."""
import argparse,copy,itertools,json
from pathlib import Path
import project_runtime
from programme_policy import *
from markov_planner import solve
DATA=ROOT/'data/programme-v6'
_evidence=ROOT/'data/active_timetable_evidence.json'
if _evidence.exists():DATA=ROOT/json.loads(_evidence.read_text())['courses_dir']
def lookup(major,term,code):
    major=programme(major)
    if not allowed(major,code):return {'document_allowed':False,'course_code':code,'sections':[],'registration_verified':False}
    records=json.loads((DATA/'courses.json').read_text(encoding='utf-8'))
    return next((c for c in records if c['programme']==major and c['term_code']==term and c['course_code']==code),
        {'document_allowed':True,'course_code':code,'term_code':term,'sections':[],'missing_snapshot':True,'registration_verified':False})
def plan(profile,assume_component_linkage=False,model_proposal=None):
    from ge_pathways import recommend,course_scores
    from cm_background_policy import waives_prerequisites
    pathway=recommend(profile)
    major=programme(profile['programme']);term=profile['term'];done=set(profile['completed_courses']);options=[];rejected=[]
    records=json.loads((DATA/'courses.json').read_text(encoding='utf-8'))
    for c in records:
        if c['programme']!=major or c['term_code']!=term or c['course_code'] in done:continue
        from timetable_evidence import verified
        if not verified(c):
            rejected.append({'course':c['course_code'],'reason':'missing_or_changed_source_timetable_PDF'});continue
        if not allowed(major,c['course_code']):continue
        if not waives_prerequisites(profile,c['course_code']) and not any(set(a)<=done for a in c['completion_alternatives']):continue
        if set(c['exclusive_courses'])&done:continue
        from section_eligibility import preferred
        sections=preferred(c['sections'],profile)
        lectures=[s for s in sections if s['credits']>0];tutorials=[s for s in sections if s['credits']==0]
        if not assume_component_linkage:
            rejected.append({'course':c['course_code'],'reason':'official_component_linkage_and_teaching_weeks_unverified'});continue
        for lecture in lectures:
            for tutorial in tutorials or [None]:
                group=[lecture]+([tutorial] if tutorial else []);meetings=[]
                for s in group:
                    for m in s['meetings']:
                        minute=lambda t:int(t[:2])*60+int(t[3:])
                        meetings.append({'day':['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].index(m['day'])+1,
                         'start_minute':minute(m['start_time']),'end_minute':minute(m['end_time']),
                         'weeks':list(range(1,15)),'date_range':[m['start_date'],m['end_date']]})
                from scheduler import conflict
                if any(conflict([a],[b]) for i,a in enumerate(meetings) for b in meetings[i+1:]):continue
                options.append({'option_id':c['course_code']+':'+':'.join(s['crn'] for s in group),'course_code':c['course_code'],
                    'credits':lecture['credits'],'term':term,'rules_reviewed':True,
                    'prerequisites_all':[],'prerequisites_any_groups':[],'corequisites':[],'exclusive_courses':c['exclusive_courses'],
                    'timetable_verified':True,'meetings':meetings,'scores':course_scores(profile,c),
                    'source':c['source_pdf'],'source_sha256':c['source_sha256'],'component_linkage_assumed':True,'teaching_weeks_assumed':True})
    # GE is a separate dated capture, explicitly enabled for degree-chain runs.
    if profile.get('include_GE_snapshot',False) and assume_component_linkage:
        from ge_snapshot_options import options as ge_options
        options.extend(ge_options(profile))
    problem={'programme':major,'selected_stream':pathway['selected_stream'],'stream_reward_multiplier':pathway['stream_reward_multiplier'],
      **{k:profile[k] for k in ['finance_background','GE_history','transcript','course_results','failed_courses','in_progress_courses','withdrawn_courses','ef_no_finance_penalty','ef3320_year4_bonus'] if k in profile},
      'track_ge_graduation':profile.get('include_GE_snapshot',False),
      'cm_ef_cs_prerequisite_waiver':profile.get('cm_ef_cs_prerequisite_waiver',True),
      'prerequisite_bridge_bonus':pathway['prerequisite_bridge_bonus'],
      'weights':profile.get('weights',{'background_mismatch':1.,'difficulty':1.,'workload':1.}),
      'student_year':profile['year'],'term':term,
      'required_courses':profile.get('required_courses',[]),'completed_courses':sorted(done),'credit_min':profile.get('credit_min',0),
      'credit_max':profile.get('credit_max',18),'course_min':profile.get('semester_min_courses',0),'course_max':6,
      'options':options,'data_mode':'hypothetical_component_bundles_over_saved_PDF_meetings'}
    from planning_policy import apply_profile_policy
    apply_profile_policy(problem,{'major':'Computing Mathematics' if major=='CM' else 'Computer Science',
        'year':profile['year'],'completed_courses':sorted(done),'selected_stream':profile.get('selected_stream')})
    if model_proposal is None:result=solve(problem)
    else:
        from markov_planner import plan_from_proposal
        result=plan_from_proposal(problem,model_proposal)
    result.update(programme=major,term=term,official_registration_verified=False,pathway=pathway,
        decision_scope='single_semester_only; full-degree acceptance requires the eight-term terminal audit',
        lambda_weights=problem['weights'],score_label='editable_synthetic_rubric_not_empirical_workload',
        hypothetical_component_linkage=assume_component_linkage,excluded_for_unverified_bundles=rejected,
        note='When enabled, one credit-bearing section plus one zero-credit section is an experimental assumption; confirm component types/linkage and teaching weeks before registration.')
    if result['status'] in ('optimal','feasible'):result['selected_source_options']=[o for o in options if o['option_id'] in result['selected_options']]
    from stream_path import plan_stream
    result['stream_completion_path']=plan_stream(profile)
    return result
