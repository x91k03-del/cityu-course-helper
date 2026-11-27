"""Document allowlists and a single-stream potential reward; no eligibility bypass."""
import json,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PATH=ROOT/'data/programme-v6/policy.json'
def policy():
    active=ROOT/'data/active_timetable_evidence.json'
    path=ROOT/json.loads(active.read_text())['policy_path'] if active.exists() else PATH
    return json.loads(path.read_text(encoding='utf-8'))
def programme(value):
    aliases={'CM':'CM','BSCM':'CM','Computing Mathematics':'CM','computing math':'CM','CS':'CS','Computer Science':'CS','CSC':'CS','CSC1':'CS'}
    if value not in aliases:raise ValueError('Programme must be CM or CS')
    return aliases[value]
def allowed(major,code):
    code={'MA4530:A':'MA4530','MA4530:B':'MA4530'}.get(code,code)
    p=programme(major);return code in policy()['allowlists'][p] or code in policy()['GE_codes']
def progress(rule,completed):
    done=set(completed);fixed=set(rule.get('required',[]));n=len(fixed&done)
    if 'core_choice' in rule:
        # AI core and elective slots cannot reuse the same passed course.
        return max([0]+[1+min(rule['choose'],len((done&set(rule['options']))-{c})) for c in done&set(rule['core_choice'])]) if done&set(rule['core_choice']) else min(rule['choose'],len(done&set(rule['options'])))
    return n+min(rule.get('choose',0),len((done&set(rule.get('options',[])))-fixed))
def stream_result(major,completed,selected=None):
    rules=policy()['streams'][programme(major)];done=set(completed)
    if selected is not None and selected not in rules:raise ValueError('Stream not available for this programme')
    if selected is None:selected=max(sorted(rules),key=lambda k:progress(rules[k],done)/rules[k]['slots'])
    rule=rules[selected];before=progress(rule,done)
    def potential(n):return 2*n+(6 if n>=rule['slots'] else 0)
    members=set(rule.get('required',[])+rule.get('options',[])+rule.get('core_choice',[]))
    bonuses={c:potential(progress(rule,done|{c}))-potential(before) for c in sorted(members-done) if allowed(major,c)}
    return {'selected_stream':selected,'completed_slots':before,'required_slots':rule['slots'],'stream_complete':before>=rule['slots'],
        'course_chain_bonus':bonuses,'completion_bonus':6,'progress_bonus_per_slot':2,'maximum_streams_rewarded':1}
def context(major,completed,selected=None):
    p=programme(major)
    return {'programme':p,'completed_courses':sorted(set(completed)),'selected_stream':selected,'stream_definitions':policy()['streams'][p],
        'reward_policy':{'per_new_slot':2,'completion':6,'only_one_stream':True,'no_repeat_credit':True}}
def potential_result(info):return 2*info['completed_slots']+(6 if info['stream_complete'] else 0)
def chain_reward(major,completed,selected,courses):
    before=stream_result(major,completed,selected);after=stream_result(major,set(completed)|set(courses),before['selected_stream'])
    return potential_result(after)-potential_result(before)
def exact(expected,value):
    if isinstance(expected,bool):return isinstance(value,bool) and value==expected
    if isinstance(expected,dict):return isinstance(value,dict) and set(expected)==set(value) and all(exact(v,value[k]) for k,v in expected.items())
    if isinstance(expected,list):return isinstance(value,list) and len(expected)==len(value) and all(exact(a,b) for a,b in zip(expected,value))
    if type(expected) in (int,float):return type(value) in (int,float) and expected==value
    return type(expected)==type(value) and expected==value
