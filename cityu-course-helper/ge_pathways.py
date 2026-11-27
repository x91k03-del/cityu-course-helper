"""Advisory GE interest links; never prerequisite, stream or minor credit."""
import math
from programme_policy import programme,policy
def recommend(profile):
    from cm_background_policy import finance_background
    finance=finance_background(profile)
    major=programme(profile.get('programme',profile.get('major')));done=set(profile['completed_courses'])
    desired=profile.get('desired_stream')
    selected=desired or profile.get('selected_stream');multiplier=3. if desired else 1.;evidence=[]
    if selected:
        names=policy()['streams'][major]
        aliases={'ai':'Artificial Intelligence','finance':'Financial Mathematics','enriched':'Enriched Mathematics'}
        selected=aliases.get(selected.strip().lower(),selected.strip())
        selected=next((n for n in names if n.casefold()==selected.casefold()),selected)
    if selected is None:
        if major=='CM' and finance['level']!='none':selected='Financial Mathematics';multiplier=3.;evidence=finance['evidence_courses']
        elif major=='CS' and 'GE2340' in done:selected='Artificial Intelligence';multiplier=3.;evidence=['GE2340']
    elif (major,selected)==('CM','Financial Mathematics') and finance['level']!='none':
        multiplier=3.;evidence=finance['evidence_courses']
    elif (major,selected)==('CS','Artificial Intelligence') and 'GE2340' in done:
        multiplier=3.;evidence=['GE2340']
    multiplier=profile.get('stream_reward_multiplier',multiplier)
    if type(multiplier) not in (int,float) or not math.isfinite(multiplier) or not 0<=multiplier<=10:raise ValueError('Stream multiplier must be finite and between 0 and 10')
    if selected is not None and selected not in policy()['streams'][major]:raise ValueError('Stream not available to programme')
    minor=None
    if 'GE2340' in done:
        minor={'name':'Artificial Intelligence','GE_is_minor_credit':False,'declaration_verified':False,
          'source':'https://www.cityu.edu.hk/catalogue/ug/current/Minor/MNR-AINT.htm'}
        if major=='CS':minor.update(status='not_allowed_for_CS_major',reason='Official AI minor excludes Computer Science; use the AI major stream instead.')
        else:minor.update(status='interest_only_blocked_by_current_course_allowlist',reason='AI minor courses are outside the user-specified CM allowlist. CGPA >=3.0, a listed programming pass and departmental approval are also required; no exception is assumed.')
    bridges={}
    if selected=='Financial Mathematics' and not {'MA2506','MA2510'}&done:bridges['MA2510']=float(multiplier)
    if selected=='Artificial Intelligence' and not {'CS3342','CS3383'}&done:bridges['CS3342']=float(multiplier)
    from course_relations import finance_audit
    return {'selected_stream':selected,'selection_source':'user_desired_stream' if desired else 'legacy_selection_or_GE_inference',
      'stream_reward_multiplier':float(multiplier),'evidence_GE_passes':evidence,'prerequisite_bridge_bonus':bridges,
      'finance_background':finance,
      'finance_route_audit':finance_audit(major,done,profile) if selected=='Financial Mathematics' else None,
      'interpretation':'User-requested interest preference, not proven ability, prerequisite substitution or earned stream/minor credit. Explicit stream choice overrides automatic GE inference.',
      'minor':minor}
def course_scores(profile,course):
    """Transparent editable test rubric; not measured course workload."""
    code=course['course_code'];overrides=profile.get('course_scores',{})
    if code in overrides:return dict(overrides[code])
    prereqs=course.get('completion_alternatives',[[]]);depth=min([len(x) for x in prereqs] or [0])
    from cm_background_policy import waives_prerequisites,finance_background
    if waives_prerequisites(profile,code):depth=0
    level=int(code[-4]) if code[-4:].isdigit() else 2
    math=code.startswith('MA');done=set(profile['completed_courses'])
    mismatch=.18 if math and 'MA1301' in done or code.startswith('CS') and {'CS1302','CS1302A','CS2310'}&done else .45
    if code.startswith('EF') or code in {'MA3521','MA4529','MA4537'}:
        mismatch=finance_background(profile)['background_mismatch']
    difficulty=min(.9,.22+.1*level+.08*depth)
    hours=max([sum((int(m['end_time'][:2])*60+int(m['end_time'][3:])-int(m['start_time'][:2])*60-int(m['start_time'][3:]))/60 for m in s['meetings']) for s in course['sections'] if s['credits']>0] or [0])
    workload=min(.9,.2+.07*hours+.04*level)
    return {'background_mismatch':round(mismatch,3),'difficulty':round(difficulty,3),'workload':round(workload,3)}
