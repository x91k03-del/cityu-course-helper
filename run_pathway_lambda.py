"""Controlled lambda sweeps and separate saved-timetable profile tests."""
import copy,json,hashlib,itertools
from pathlib import Path
from programme_policy import *
from ge_pathways import recommend
from scheduler import solve
from test_scheduler import option
OUT=ROOT/'reports/ge-pathway-lambda';PROFILES=ROOT/'data/ge-pathway-lambda'
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def controlled_problem(major):
    if major=='CM':
        required=['MA2509','CS2360','MA3517','GE1105'];choices=['MA3521','MA3523','MA3525']
        done=['MA1300','MA1301','MA2503','MA2508','MA2510','CS1302','GE2260'];prereq=['MA2510']
    else:
        required=['CS2115','CS2402','CS3334','CS3342'];choices=['CS4486','CS3483','CS3402']
        done=['CS1302A','CS2310','CS2312','GE2340'];prereq=['CS2310']
    opts=[option(c,day=i+1,cost=.2) for i,c in enumerate(required)]
    scores=[(.05,.65,.65),(.75,.1,.55),(.6,.55,.1)]
    for code,values in zip(choices,scores):
        o=option(code,day=5);o['scores']=dict(zip(['background_mismatch','difficulty','workload'],values))
        if code==choices[0]:o['prerequisites_all']=prereq
        elif major=='CM':o['prerequisites_all']=['MA2503']
        opts.append(o)
    # Verify that this synthetic timing fixture never uses concurrent study to
    # satisfy a known prerequisite from the saved source records.
    records=json.loads((ROOT/'data/programme-v6/courses.json').read_text(encoding='utf-8'))
    for o in opts:
        source=next((r for r in records if r['programme']==major and r['course_code']==o['course_code']),None)
        if source:
            matches=[a for a in source['completion_alternatives'] if set(a)<=set(done)]
            if not matches:raise ValueError('Controlled profile lacks source prerequisite: '+o['course_code'])
            o['prerequisites_all']=matches[0];o['exclusive_courses']=source['exclusive_courses']
    route=recommend({'programme':major,'completed_courses':done})
    return {'programme':major,'selected_stream':route['selected_stream'],'stream_reward_multiplier':route['stream_reward_multiplier'],
      'student_year':2,'term':'DEMO','required_courses':required,'completed_courses':done,'credit_min':15,'credit_max':15,
      'course_min':5,'course_max':5,'options':opts,'data_mode':'controlled_synthetic_times_and_scores_for_lambda_sensitivity_not_a_CityU_timetable'}
def main():
    OUT.mkdir(parents=True,exist_ok=True);PROFILES.mkdir(parents=True,exist_ok=True)
    # Verified official GE identity expands known GE evidence only, never the non-GE CM list.
    path=ROOT/'data/programme-v6/policy.json';p=json.loads(path.read_text(encoding='utf-8'))
    p['GE_codes']=sorted(set(p['GE_codes'])|{'GE2340'})
    p.setdefault('additional_GE_evidence',{})['GE2340']='https://www.cityu.edu.hk/catalogue/ug/current/course/ge2340.htm'
    save(path,p)
    areas_path=ROOT/'data/four-year/GE_areas.json';areas=json.loads(areas_path.read_text(encoding='utf-8'))
    areas['GE2340']={'area':3,'source_url':'https://www.cityu.edu.hk/catalogue/ug/current/course/ge2340.htm'};save(areas_path,areas)
    cm={'profile_id':'CM_Y2_FINANCE_GE','programme':'CM','programme_code':'BSCSIU4','cohort':2025,'year':2,'term':'202702',
      'completed_courses':['MA1300','MA1301','CS1302','CS2360','MA2503','MA2508','MA2509','GE1401','GE1501','GE1601','GE2401','GE2260'],
      'GE_history':[{'course':'GE2260','title':'Introduction to Finance','year':1,'semester':'A','grade':'B'}]}
    cs={'profile_id':'CS_Y2_AI_GE','programme':'CS','programme_code':'BSCCCU4','cohort':2025,'year':2,'term':'202702',
      'completed_courses':['CS1302A','CS2115','CS2310','CS2312','CS2402','CS3201','CS3334','MA1503','MA1508','MA2185','GE2340'],
      'GE_history':[{'course':'GE2340','title':'Artificial Intelligence - Past, Present, and Future','year':1,'semester':'A','grade':'B'}]}
    minor={**copy.deepcopy(cm),'profile_id':'CM_Y2_AI_MINOR_INTEREST','CGPA':3.3,
      'completed_courses':[c for c in cm['completed_courses'] if c!='GE2260']+['GE2340'],'GE_history':copy.deepcopy(cs['GE_history'])}
    from programme_v6 import plan
    actual=[]
    settings=[('balanced',(1,1,1)),('background_priority',(20,1,1)),('difficulty_priority',(1,20,1)),('workload_priority',(1,1,20))]
    for profile in [cm,cs,minor]:
        save(PROFILES/(profile['profile_id']+'.json'),profile)
        route=recommend(profile);runs=[]
        for label,vals in settings:
            q=copy.deepcopy(profile);q['weights']=dict(zip(['background_mismatch','difficulty','workload'],vals))
            r=plan(q,True);runs.append({'setting':label,'lambdas':vals,'result':r})
        actual.append({'profile':profile,'pathway':route,'runs':runs})
    save(OUT/'saved_timetable_results.json',actual)
    paired=[]
    for profile,code in [(cm,'GE2260'),(cs,'GE2340')]:
        neutral=copy.deepcopy(profile);neutral['completed_courses'].remove(code);neutral['completed_courses'].append('GE1105');neutral.pop('GE_history',None)
        with_ge=plan(profile,True);without_ge=plan(neutral,True)
        paired.append({'programme':profile['programme'],'with_GE':code,'GE_route':recommend(profile),'neutral_route':recommend(neutral),
          'GE_course_plan':with_ge,'neutral_course_plan':without_ge})
    save(OUT/'GE_ablation.json',paired)
    sweep=[]
    settings += [('mismatch_low_fixed_d12',(0,12,1)),('mismatch_high_fixed_d12',(12,12,1))]
    for major in ['CM','CS']:
        p=controlled_problem(major)
        for label,vals in settings:
            q=copy.deepcopy(p);q['weights']=dict(zip(['background_mismatch','difficulty','workload'],vals));r=solve(q)
            assert r['status']=='optimal'
            # Independent enumeration of every available fifth-course choice.
            from profit_objective import components,settings as config
            from programme_policy import chain_reward
            opts=p['options'];groups=[opts[:4]+[o] for o in opts[4:]]
            objectives=[components(g,{},0,q['weights'],config(q))['net_profit']+p['stream_reward_multiplier']*chain_reward(major,p['completed_courses'],p['selected_stream'],[o['course_code'] for o in g]) for g in groups]
            assert abs(r['objective']-max(objectives))<1e-6
            chosen=[o for o in opts if o['course_code'] in r['course_codes']]
            raw={k:sum(o['scores'][k] for o in chosen) for k in q['weights']}
            sweep.append({'programme':major,'setting':label,'lambdas':vals,'result':r,'raw_score_totals':raw,
              'weighted_penalty_components':{k:raw[k]*q['weights'][k] for k in raw},'enumerated_optimum_verified':True,'fixed_input_options_hash':hashlib.sha256(json.dumps(opts,sort_keys=True).encode()).hexdigest()})
    save(OUT/'controlled_sensitivity.json',sweep);save(OUT/'controlled_inputs.json',{m:controlled_problem(m) for m in ['CM','CS']})
    save(OUT/'sources.json',{'proposal':'C:/Users/BILLY/Downloads/PP3.pdf','finance_GE':'https://www.cityu.edu.hk/catalogue/ug/202425/course/GE2260.htm',
      'AI_GE':'https://www.cityu.edu.hk/catalogue/ug/current/course/ge2340.htm','AI_minor':'https://www.cityu.edu.hk/catalogue/ug/current/Minor/MNR-AINT.htm',
      'caveat':'GE history supplies a user-requested interest multiplier, not stream/minor credit or proof of ability. Finance GE never substitutes for the saved EF3320 prerequisite CB3410 or FB3410.'})
    for r in sweep:print(r['programme'],r['setting'],r['lambdas'],r['result']['course_codes'][-1],r['result']['objective'])
if __name__=='__main__':main()
