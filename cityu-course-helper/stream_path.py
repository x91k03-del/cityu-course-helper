"""Stream paths over source rules and explicit CM planning waivers; no invented offerings."""
import itertools,json
from pathlib import Path
from programme_policy import *
from ge_pathways import recommend
from course_relations import graph as relation_graph
ROOT=Path(__file__).resolve().parent
def model_messages(profile,system):
    route=recommend(profile);major=programme(profile['programme'])
    selected=route['selected_stream'] or stream_result(major,profile['completed_courses'])['selected_stream']
    rule=policy()['streams'][major][selected]
    members=set(rule.get('required',[])+rule.get('options',[])+rule.get('core_choice',[]))
    done=set(profile['completed_courses']);relevant=sorted(done&members)
    query={'task':'stream',**context(major,relevant,selected),
      'background_courses_not_stream_slots':sorted(done-members),'user_desired_stream':selected,
      'solver_preference_multiplier':route['stream_reward_multiplier'],
      'note':'completed_courses contains only passed stream-member courses. Background core and GE are not stream credits. Return base rewards; solver scales them separately.'}
    return [{'role':'system','content':system},{'role':'user','content':json.dumps(query)}]
def rules():
    result={}
    for c in json.loads((ROOT/'data/programme-v6/courses.json').read_text(encoding='utf-8')):
        result[c['course_code']]={'completion_alternatives':c['completion_alternatives'],'exclusive_courses':c['exclusive_courses'],
          'source':c['source_pdf'],'label':'saved_combined_prerequisites_precursors'}
    # Explicit catalogue prerequisite fields are preferable to combined labels.
    for code,value in relation_graph()['verified_rules'].items():
        result[code]={**result.get(code,{}),**value,'label':'catalogue_prerequisite_or_exclusion'}
    supplemental=ROOT/'data/stream_dependency_sources.json'
    if supplemental.exists():
        for code,value in json.loads(supplemental.read_text(encoding='utf-8')).items():result[code]={**value,'label':'additional_official_source'}
    result['CS4486']={'completion_alternatives':[['CS2310'],['CS2311'],['CS2313'],['CS2315'],['CS2334'],['CS2360']],
       'source':'https://www.cityu.edu.hk/catalogue/ug/202526/course/CS4486.pdf','label':'2025_26_catalogue_prerequisites'}
    return result
def completion_sets(rule):
    if 'core_choice' in rule:
        return [set([core,*rest]) for core in rule['core_choice'] for rest in itertools.combinations([c for c in rule['options'] if c!=core],rule['choose'])]
    return [set(rule.get('required',[]))|set(choice) for choice in itertools.combinations(rule.get('options',[]),rule.get('choose',0))]
def plan_stream(profile):
    from cm_background_policy import waives_prerequisites
    route=recommend(profile);major=programme(profile['programme']);done=set(profile['completed_courses'])
    selected=route['selected_stream'] or stream_result(major,done)['selected_stream']
    rule=policy()['streams'][major][selected];known=rules()
    planned_targets=set()
    def expand(code,ancestry):
        if code in done:return set(),[],[]
        if code in ancestry:return set(),[{'course':code,'reason':'dependency_cycle'}],[]
        if not allowed(major,code):return set(),[{'course':code,'reason':'outside_programme_allowlist'}],[]
        fact=known.get(code)
        if fact and set(fact.get('exclusive_courses',[]))&done:
            return set(),[{'course':code,'reason':'exclusive_course_passed','conflicts':sorted(set(fact['exclusive_courses'])&done)}],[]
        if fact and set(fact.get('uncertain_exclusions',[]))&done:
            return set(),[{'course':code,'reason':'source_conflict_requires_confirmation'}],[]
        if waives_prerequisites(profile,code):return {code},[],[]
        if not fact or 'completion_alternatives' not in fact:
            return {code},[],[{'course':code,'reason':'prerequisites_not_available_in_source'}]
        choices=[]
        for alternative in fact['completion_alternatives']:
            needed={code};blocked=[];unknown=[]
            if fact.get('requires_current_confirmation'):unknown.append({'course':code,'reason':'historical_source_needs_current_confirmation'})
            for pre in alternative:
                n,b,u=expand(pre,ancestry|{code});needed|=n;blocked+=b;unknown+=u
            choices.append((needed,blocked,unknown))
        return min(choices,key=lambda x:(bool(x[1]),len(x[1]),len(x[2]),len(x[0]-planned_targets),len(x[0]),sorted(x[0])))
    candidates=[]
    for target in completion_sets(rule):
        planned_targets=target
        needed=set();blocked=[];unknown=[]
        for code in sorted(target-done):
            n,b,u=expand(code,set());needed|=n;blocked+=b;unknown+=u
        # No candidate may claim completion from a forbidden/missing course.
        predicted=stream_result(major,done|needed,selected)
        remaining=set(needed);layers=[];assumed=set(done)
        while remaining:
            ready=[]
            for code in sorted(remaining):
                fact=known.get(code,{});alts=fact.get('completion_alternatives')
                if waives_prerequisites(profile,code) or alts is None or any(set(a)<=assumed for a in alts):ready.append(code)
            if not ready:blocked.append({'courses':sorted(remaining),'reason':'no_verified_dependency_order'});break
            layers.append(ready);assumed.update(ready);remaining-=set(ready)
        status='blocked' if blocked or not predicted['stream_complete'] else 'provisional_missing_rules' if unknown else 'academic_dependency_path'
        waived=sorted(c for c in needed if waives_prerequisites(profile,c))
        if status=='academic_dependency_path' and waived:status='academic_path_assuming_CM_prerequisite_waiver'
        candidates.append({'target_stream_courses':sorted(target),'remaining_courses':sorted(needed),'dependency_layers':layers,
           'prerequisite_waivers_assumed':waived,
           'course_sources':{c:known.get(c,{}).get('source') for c in sorted(needed)},
           'offering_warnings':{c:known[c]['offering_note'] for c in sorted(needed) if c in known and known[c].get('offering_note')},
           'blocked':blocked,'unknown_rules':unknown,'status':status,'stream_complete_if_all_passed':not bool(blocked) and predicted['stream_complete'],
           'base_chain_reward':chain_reward(major,done,selected,needed) if status!='blocked' else 0})
    best=min(candidates,key=lambda c:(c['status']=='blocked',len(c['blocked']),len(c['unknown_rules']),len(c['remaining_courses']),c['remaining_courses']))
    return {'selected_stream':selected,'selection_source':route['selection_source'],'stream_reward_multiplier':route['stream_reward_multiplier'],
      'current_progress':stream_result(major,done,selected),'path':best,'alternatives_evaluated':len(candidates),
      'scaled_chain_reward':best['base_chain_reward']*route['stream_reward_multiplier'],
      'course_reward_adjustments':{c:v*route['stream_reward_multiplier'] for c,v in stream_result(major,done,selected)['course_chain_bonus'].items()},
      'all_path_courses_programme_allowed':all(allowed(major,c) for c in best['remaining_courses']),
      'future_offerings_and_timetables_verified':False,'declaration_or_graduation_verified':False,
      'note':'Layers show academic planning order, not semester assignments. CM EF/CS prerequisites may be assumed waived by user policy; source requirements and university approval are not changed. Other unknown or blocked rules remain explicit.'}
