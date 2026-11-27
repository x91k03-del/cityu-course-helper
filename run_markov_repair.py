"""Reproducible diagnostic of historical raw answers and new planner simulation."""
import argparse,json
from pathlib import Path
import project_runtime
from markov_planner import plan_from_proposal
from markov_degree import simulate,audit_sequence
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reports/markov-repair'

def run(reuse_simulation=False):
    OUT.mkdir(parents=True,exist_ok=True)
    cases=json.loads((ROOT/'reports/year3-path-comparison06/cases.json').read_text())
    raw={r['case_id']:json.loads(r['raw']) for r in json.loads((ROOT/'reports/year3-path-comparison06/qwen_raw.json').read_text())}
    checks=[]
    for case in cases:
        result=plan_from_proposal(case['problem'],raw[case['id']])
        checks.append({'case_id':case['id'],'raw_proposal':raw[case['id']],**result})
        print(case['id'],result['status'],result.get('course_codes'),result['states_by_course_count'],flush=True)
    (OUT/'semester_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    profile=json.loads((ROOT/'data/markov-repair/year1_CM.json').read_text())
    if reuse_simulation:
        result=json.loads((OUT/'year1_simulation.json').read_text())
        result['audit']=audit_sequence(profile,result['steps'],result['transcript'])
    else:result=simulate(profile)
    (OUT/'year1_simulation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('DEGREE',result['status'],result.get('audit',{}).get('earned_credits'),result.get('audit',{}).get('sequence_violations'),flush=True)
    return checks,result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reuse-simulation',action='store_true');a=p.parse_args();run(a.reuse_simulation)
