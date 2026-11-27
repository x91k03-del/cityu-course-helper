"""Matched finance-background examples, preserving synthetic/live-data boundaries."""
import copy
import json
from pathlib import Path
from cm_background_policy import finance_background,target
from ge_pathways import course_scores,recommend
from stream_path import plan_stream
from scheduler import solve
from test_scheduler import option

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reports/cm-finance-background'

def main():
    core=['MA1300','MA1301','MA2503','MA2508','MA2509','MA2510','CS1302']
    base={'programme':'CM','programme_code':'BSCSIU4','cohort':2025,'year':2,'term':'202702',
          'completed_courses':core,'desired_stream':'Financial Mathematics','stream_reward_multiplier':1.}
    profiles=[]
    for name,extra in [('no_finance',{}),('finance_GE',{'completed_courses':core+['GE2260']}),
                       ('self_reported_finance',{'finance_background':{'studied':True,'topics':['personal finance']}}),
                       ('advanced_finance',{'completed_courses':core+['MA3521']}),
                       ('failed_finance_GE',{'completed_courses':core+['GE2260'],'GE_history':[{'course_code':'GE2260','grade':'F'}]}),
                       ('strict_prerequisites',{'completed_courses':core+['GE2260'],'cm_ef_cs_prerequisite_waiver':False})]:
        profiles.append({'profile_id':name,**copy.deepcopy(base),**extra})
    folder=ROOT/'data/cm-finance-background/examples';folder.mkdir(parents=True,exist_ok=True)
    rows=[]
    # Same artificial course option and meetings in every comparison. No seats or
    # current CM EF section is fabricated by this fixture.
    candidate={'course_code':'EF3320','completion_alternatives':[['CB3410'],['FB3410']],'sections':[]}
    for p in profiles:
        (folder/(p['profile_id']+'.json')).write_text(json.dumps(p,indent=2),encoding='utf-8')
        o=option('EF3320');o['scores']=course_scores(p,candidate);o['prerequisites_any_groups']=[['CB3410','FB3410']]
        problem={'programme':'CM','selected_stream':'Financial Mathematics','stream_reward_multiplier':1.,
          'student_year':2,'term':'DEMO','completed_courses':p['completed_courses'],'required_courses':['EF3320'],
          'course_min':1,'course_max':1,'credit_min':3,'credit_max':3,'options':[o],
          'cm_ef_cs_prerequisite_waiver':p.get('cm_ef_cs_prerequisite_waiver',True),
          'weights':{'background_mismatch':1.,'difficulty':1.,'workload':1.},
          'data_mode':'matched_single_course_synthetic_timetable_and_scores_for_background_comparison'}
        rows.append({'profile':p,'finance_background':finance_background(p),'policy_target':target(p,'EF3320'),
          'scores':o['scores'],'controlled_solver_result':solve(problem),
          'stream_path':plan_stream(p),
          'actual_EF_CM_matching_sections_in_saved_term':0,
          'note':'The controlled option is synthetic. Saved CM EF snapshots currently contain no matching CM sections; waiver does not create an actual offered section.'})
    (OUT/'background_examples.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    choices=[]
    for p in profiles[:2]:
        auto={k:v for k,v in p.items() if k not in ['desired_stream','stream_reward_multiplier']}
        route=recommend(auto)
        options=[]
        for code,day in [('EF3320',1),('MA3523',2)]:
            o=option(code,day=day)
            o['scores']=course_scores(auto,{'course_code':code,'completion_alternatives':[['CB3410']] if code.startswith('EF') else [['MA2503']],'sections':[]})
            o['prerequisites_all']=['CB3410'] if code.startswith('EF') else ['MA2503']
            options.append(o)
        fixture={'programme':'CM','selected_stream':route['selected_stream'],
           'stream_reward_multiplier':route['stream_reward_multiplier'],'student_year':2,'term':'DEMO',
           'completed_courses':auto['completed_courses'],'required_courses':[],
           'course_min':1,'course_max':1,'credit_min':3,'credit_max':3,'options':options,
           'data_mode':'synthetic_one_elective_fixture_for_finance_background_interest_comparison'}
        choices.append({'profile':auto,'pathway':route,'result':solve(fixture)})
    (OUT/'automatic_interest_comparison.json').write_text(json.dumps(choices,indent=2),encoding='utf-8')
    for r in rows:print(r['profile']['profile_id'],r['finance_background']['level'],r['controlled_solver_result']['status'],r['controlled_solver_result'].get('objective'),r['stream_path']['path']['status'])
    for r in choices:print('automatic',r['profile']['profile_id'],r['result']['course_codes'])

if __name__=='__main__':main()
