"""Reproducible 15+15 fictional-history examples and source-only control."""
import copy,json
from pathlib import Path
import project_runtime
from degree_chain import simulate
from timetable_grounded_training import problem_for
from markov_planner import solve
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reports/ef-late-ge-examples'
GE_POOL=['GE1105','GE1113','GE1202','GE1305','GE2134','GE2260']

def history(a,b):
    rows=[]
    for term,codes in [(1,['MA1300','CS1302','PHY1201','GE1401',a]),
                       (2,['MA1301','CHEM1200','GE1501','GE2401',b])]:
        rows.extend({'id':c,'credits':3,'grade':'B','term':term,'year':1,'semester':'A' if term==1 else 'B'} for c in codes)
    assert all(sum(r['credits'] for r in rows if r['term']==t)==15 for t in (1,2))
    return rows

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    base={'programme':'CM','programme_code':'BSCSIU4','cohort':2025,'year':2,'term':'202609',
        'include_GE_snapshot':True,'ge_candidate_courses':GE_POOL,'start_semester':3,
        'chain_state_limit':800,'chain_branch_width':4,'chain_beam_width':3,'chain_credit_beam_width':3}
    specs=[('F','Finance preparation','GE2260','GE1105','Financial Mathematics'),
           ('N','No finance preparation','GE1305','GE1113','Financial Mathematics'),
           ('M','Maths and critical thinking','GE2134','GE1305','Enriched Mathematics')]
    cases=[]
    for ident,label,a,b,stream in specs:
        h=history(a,b);p={**base,'historical_transcript':h,'completed_courses':[r['id'] for r in h],'desired_stream':stream}
        r=simulate(p)
        assert r['path_valid']
        assert all(r['audit']['checks'][k] for k in ['GE_at_least_four','GE_all_areas','GE_at_most_one_per_semester'])
        assert not r['whole_chain_accepted'] or r['audit']['earned_credits']>=122
        cases.append({'id':ident,'label':label,'result':r})
        (OUT/(ident+'_profile.json')).write_text(json.dumps(p,indent=2),encoding='utf-8')
        (OUT/(ident+'_rollout.json')).write_text(json.dumps(r,indent=2),encoding='utf-8')
        print(ident,'credits',r['audit']['earned_credits'],'GE',r['audit']['GE_area_counts'],
            'count',r['audit']['distribution_GE_count'],'EF',[(s['year'],s['semester']) for s in r['diagnostic_semesters'] if 'EF3320' in s['selected_courses']],flush=True)
    p=copy.deepcopy(cases[0]['result']['input_profile']);p['ef3320_year4_bonus']=0
    before=simulate(p);(OUT/'F_without_late_bonus.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    fresh={'programme':'CM','programme_code':'BSCSIU4','year':1,'term':'202609','completed_courses':[],
        'include_GE_snapshot':True,'credit_min':15,'credit_max':15}
    qa=problem_for(fresh);a=solve(qa,state_limit=10000)
    qb=problem_for({**fresh,'term':'202702','completed_courses':a.get('course_codes',[])})
    b=solve(qb,state_limit=10000)
    b_flexible=solve({**qb,'credit_min':0},state_limit=10000)
    control={'Y1_A_exact15':a,'Y1_B_exact15_after_A':b,'Y1_B_flexible_after_A':b_flexible,
        'B_unique_available_credits':sum({o['course_code']:o['credits'] for o in qb['options']}.values()),
        'B_offered_courses':sorted({o['course_code'] for o in qb['options']}),
        'GE_B_offering_evidence_present':False}
    result={'examples':cases,'before_bonus_finance_case':before,'source_only_control':control,
        'assumptions':['Fictional completed Year-1 history; 15 credits in each semester, not a verified past timetable.',
            'Future MA/CS sections use saved PDFs; GE sections use captured Semester A weekly meetings only.',
            'A/B snapshots repeat each simulation year as authorised; future real offerings are unverified.',
            'Component linkage, GE registration eligibility and teaching weeks remain assumptions.',
            'Six named GE courses form a declared demonstration pool; no global reward optimum is claimed.',
            'This is a planner reward update and simulation, not a newly trained neural checkpoint.']}
    (OUT/'examples.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Baseline EF',[(s['year'],s['semester']) for s in before['diagnostic_semesters'] if 'EF3320' in s['selected_courses']],flush=True)
    print('Control',a['status'],a.get('credits'),b['status'],'B available',control['B_unique_available_credits'],flush=True)
    return result

if __name__=='__main__':run()
