"""User-authorised CM advisory waiver and content-based finance preparation.

Source prerequisite facts are retained; the waiver is a planning assumption,
not evidence of an approved university registration exception.
"""
from programme_policy import programme, allowed

FINANCE_INTRO = {'GE1202', 'GE2260'}
FINANCE_ADVANCED = {'CB3410', 'FB3410', 'MA3521', 'MA4529', 'MA4537'}
NONPASS = {'F', 'IP', 'W', 'FAIL', 'FAILED', 'IN PROGRESS', 'WITHDRAWN'}

def ef_mismatch_penalty(profile,code):
    """Extra utility cost for EF without finance study, never a prerequisite fee."""
    import math
    weight=profile.get('weights',{}).get('background_mismatch',1.)
    amount=profile.get('ef_no_finance_penalty',1.5)
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in (weight,amount)):
        raise ValueError('Invalid EF background penalty')
    return weight*amount if code.startswith('EF') and finance_background(profile)['level']=='none' else 0.

def waiver_enabled(profile):
    value = profile.get('cm_ef_cs_prerequisite_waiver', True)
    if type(value) is not bool:
        raise ValueError('cm_ef_cs_prerequisite_waiver must be a boolean')
    return value

def waives_prerequisites(profile, code):
    major = profile.get('programme', profile.get('major'))
    if major is None:
        return False
    major = programme(major)
    return major == 'CM' and waiver_enabled(profile) and code.startswith(('EF', 'CS')) and allowed(major, code)

def finance_background(profile):
    done = set(profile.get('completed_courses', []))
    for key in ['failed_courses', 'in_progress_courses', 'withdrawn_courses']:
        done -= set(profile.get(key, []))
    # A listed failure/IP/W is not finance preparation. A later actual pass counts.
    observations = {}
    for key in ['GE_history', 'transcript', 'course_results']:
        for item in profile.get(key, []):
            code = item.get('course_code', item.get('id'))
            grade = str(item.get('grade', '')).strip().upper()
            if code and grade:
                observations.setdefault(code, []).append(grade)
    for code, grades in observations.items():
        if all(g in NONPASS for g in grades):
            done.discard(code)
    courses = sorted(c for c in done if c in FINANCE_INTRO | FINANCE_ADVANCED or c.startswith('EF'))
    declared = profile.get('finance_background', False)
    if type(declared) is bool:
        studied = declared
    elif isinstance(declared, dict) and type(declared.get('studied', False)) is bool:
        studied = declared.get('studied', False)
    else:
        raise ValueError('finance_background must be a boolean or an object with boolean studied')
    advanced = any(c in FINANCE_ADVANCED or c.startswith('EF') for c in courses)
    level = 'advanced' if advanced else 'introductory' if courses or studied else 'none'
    return {'level': level, 'evidence_courses': courses, 'self_reported_study': studied,
            'background_mismatch': {'none': .45, 'introductory': .15, 'advanced': .05}[level],
            'priority_multiplier': 1. if level == 'none' else 3.,
            'label': 'configurable_content_background_rubric_not_measured_learning'}

def target(profile, code):
    """Exact teacher/guard for the new source-conditioned model task."""
    from course_relations import check_rules
    major = programme(profile['programme'])
    rule = check_rules(code, profile.get('completed_courses', []))
    waived = waives_prerequisites(profile, code)
    status = ('waived_for_CM_planning' if waived else
              'satisfied' if rule['known_prerequisites_satisfied'] is True else
              'not_satisfied' if rule['known_prerequisites_satisfied'] is False else 'unknown')
    bg = finance_background(profile)
    return {'programme': major, 'course_code': code, 'document_allowed': allowed(major, code),
            'prerequisite_waiver_assumed': waived, 'prerequisite_handling': status,
            'additional_missing_prerequisite_penalty': 0.,
            'finance_background_level': bg['level'], 'finance_evidence_courses': bg['evidence_courses'],
            'finance_background_mismatch': bg['background_mismatch'],
            'finance_priority_multiplier': bg['priority_multiplier'], 'registration_verified': False}
