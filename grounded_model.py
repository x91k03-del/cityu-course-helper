"""Use the grounded checkpoint with explicit source/rule acceptance checks."""
import argparse,json,sys
from pathlib import Path
import project_runtime
from timetable_grounded_training import ADAPTER,REPORT,messages,assessment,problem_for,schedule_messages
from programme_policy import exact

def selected_run():
    root=Path(__file__).resolve().parent;active=root/'data/active_grounded_adapter.json'
    if active.exists():return json.loads(active.read_text())
    for report in ['reports/timetable-grounded-correction','reports/timetable-grounded']:
        release=root/report/'release.json'
        if release.exists():
            r=json.loads(release.read_text());return {'adapter':r['adapter'],'report_dir':report,'accepted_for_activation':r['accepted_for_activation']}
    return {'adapter':ADAPTER,'report_dir':'reports/timetable-grounded','accepted_for_activation':False}

def provider(adapter=None):
    if adapter is None:adapter=selected_run()['adapter']
    import torch
    from inference import load,generate
    torch.set_num_threads(8);sys.setrecursionlimit(5000)
    tok,model=load(adapter)
    def call(ms):
        raw=generate(tok,model,ms,max_tokens=300)
        try:value=json.loads(raw)
        except ValueError:value=None
        return raw,value
    return call

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['degree','plan','assess']);p.add_argument('--profile',required=True)
    p.add_argument('--course');p.add_argument('--output',required=True);a=p.parse_args()
    profile=json.loads(Path(a.profile).read_text(encoding='utf-8'));profile.setdefault('programme_code','BSCSIU4' if profile['programme']=='CM' else 'BSCCCU4')
    profile.setdefault('term','202609');call=provider()
    if a.command=='degree':
        from grounded_degree import simulate
        result=simulate(profile,call)
    elif a.command=='plan':
        from markov_planner import plan_from_proposal
        problem=problem_for(profile);raw,parsed=call(schedule_messages(problem));result=plan_from_proposal(problem,parsed);result['raw_model_response']=raw
    else:
        if not a.course:raise ValueError('--course is required for assess')
        raw,parsed=call(messages(profile,a.course));expected=assessment(profile,a.course);passed=exact(expected,parsed)
        result={'raw_model_response':raw,'model_output_accepted':passed,'verified_policy_output':expected,'policy_fallback_used':not passed}
    result['model_adapter']=selected_run()['adapter']
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    print(result.get('status',result.get('model_output_accepted')),flush=True)

if __name__=='__main__':main()
