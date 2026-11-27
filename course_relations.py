"""Typed course relationships and route diagnostics; inferred links never unlock courses."""
import json
from pathlib import Path
from programme_policy import allowed,programme
ROOT=Path(__file__).resolve().parent
def graph():return json.loads((ROOT/'data/deep_course_relations.json').read_text(encoding='utf-8'))
def check_rules(code,completed):
    rule=graph()['verified_rules'].get(code,{});done=set(completed)
    conflict=sorted(done&set(rule.get('exclusive_courses',[])))
    alternatives=rule.get('completion_alternatives')
    return {'course_code':code,'known_prerequisites_satisfied':None if alternatives is None else any(set(a)<=done for a in alternatives),
      'source_conflict_courses_needing_confirmation':sorted(done&set(rule.get('uncertain_exclusions',[]))),
      'missing_alternatives':None if alternatives is None else [sorted(set(a)-done) for a in alternatives],
      'exclusive_conflicts':conflict,'source':rule.get('source'),'registration_verified':False}
def finance_audit(major,completed,profile=None):
    from cm_background_policy import waives_prerequisites
    major=programme(major);done=set(completed);rows=[]
    profile={**(profile or {}),'programme':major,'completed_courses':sorted(done)}
    for code in ['EF3320','EF4821']:
        rule=check_rules(code,done);alts=graph()['verified_rules'][code]['completion_alternatives']
        blocked=[sorted(c for c in a if c not in done and not allowed(major,c)) for a in alts]
        rows.append({**rule,'document_allowed':allowed(major,code),'outside_allowlist_in_each_missing_route':blocked,
          'prerequisite_waiver_assumed':waives_prerequisites(profile,code),
          'additional_missing_prerequisite_penalty':0.,
          'no_currently_allowed_prerequisite_route':not waives_prerequisites(profile,code) and not rule['known_prerequisites_satisfied'] and all(bool(a) for a in blocked)})
    return {'EF_options':rows,'GE2260_CB3410_conflict_if_both_passed':{'GE2260','CB3410'}<=done,
      'usual_CB3410_route_conflicts_with_passed_finance_GE':'GE2260' in done,
      'financial_stream_completion_verified':False,
      'warning':'CM EF/CS prerequisites are assumed waived for advisory planning when enabled by the user policy. Source facts, eligible sections and exclusions remain separate; university approval is not verified.'}
