"""Twenty seeded fictional post-core profiles, random GE, user-selected streams."""
import argparse,copy,json,random
from pathlib import Path
import project_runtime
from programme_policy import *
from ge_pathways import recommend
from stream_path import plan_stream
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'reports/desired-stream';DATA=ROOT/'data/desired-stream'
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def generate():
    rng=random.Random(20261121);DATA.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    cm=['MA2503','MA2508','MA2509','MA2507','MA2510','MA3511','MA3526','MA3512','MA3514','MA3515','MA3517','MA3518','MA3525','CS2360','CS2468']
    cs=['CS2115','CS2310','CS2312','CS2402','CS2613','CS3103','CS3201','CS3334','CS3342','CS4335','MA2185']
    known={'GE1105':'Chinese Music Appreciation','GE1113':'Visual Storytelling and Cultural Thinking','GE1202':'Managing Your Personal Finance',
      'GE1305':'Foundation Physics','GE2134':'Critical and Creative Thinking','GE2260':'Introduction to Finance','GE2340':'Artificial Intelligence - Past, Present, and Future'}
    profiles=[];results=[]
    for major,core in [('CM',cm),('CS',cs)]:
        streams=list(policy()['streams'][major])
        for i in range(10):
            desired=streams[i%len(streams)]
            # One sampled GE per semester; avoid contradictory finance GE pair.
            ge=rng.sample(sorted(known),rng.randint(1,3))
            if 'GE2260' in ge and 'GE1202' in ge:ge.remove('GE1202')
            history=[{'course_code':c,'title':known[c],'grade':rng.choice(['A','B+','B','C+']),
              'year':1+j//2,'semester':'A' if j%2==0 else 'B'} for j,c in enumerate(ge)]
            support=['MA1300','MA1301','CS1302'] if major=='CM' else ['CS1302A','MA1503','MA1508']
            p={'profile_id':f'{major}_{i+1:02d}','programme':major,'desired_stream':desired,'stream_reward_multiplier':rng.choice([2.,3.,4.]),
              'academic_stage':'Fictional taught-core completed; capstone/project and internships are not assumed completed.',
              'completed_taught_core':core,'completed_courses':sorted(set(core+support+ge)),
              'GE_history':history,'fictional':True,'future_term':'unverified','random_seed':20261121,
              'weights':{'background_mismatch':1.,'difficulty':1.,'workload':1.}}
            route=plan_stream(p)
            assert route['selected_stream']==desired
            assert route['all_path_courses_programme_allowed']
            save(DATA/(p['profile_id']+'.json'),p);profiles.append(p)
            results.append({'profile':p,'pathway':recommend(p),'stream_plan':route})
    save(DATA/'profiles.json',profiles);save(OUT/'plans.json',results)
    save(OUT/'generation_protocol.json',{'seed':20261121,'CM':10,'CS':10,'core_policy':'All listed taught core passed; grade and degree-award rules not inferred. Capstone/internships excluded from the completed set.',
      'randomization':'GE courses, passing GE grades and explicit preference weights vary. Stream choices are balanced across each programme, not sampled by chance.',
      'no_mock_future_times':True,'profile_year_not_inferred_from_core':True})
    print([(r['profile']['profile_id'],r['stream_plan']['selected_stream'],r['stream_plan']['path']['status']) for r in results])
def model():
    import torch
    from inference import load,generate_batch
    from programme_training_v6 import SYSTEM,ADAPTER
    results=json.loads((OUT/'plans.json').read_text(encoding='utf-8'));requests=[]
    for row in results:
        p=row['profile'];s=p['desired_stream'];rule=policy()['streams'][p['programme']][s]
        members=set(rule.get('required',[])+rule.get('options',[])+rule.get('core_choice',[]))
        relevant=sorted(set(p['completed_courses'])&members)
        query={'task':'stream',**context(p['programme'],relevant,s),
          'background_courses_not_stream_slots':sorted(set(p['completed_courses'])-members),
          'user_desired_stream':s,'solver_preference_multiplier':p['stream_reward_multiplier'],
          'note':'Only completed_courses intersects stream membership. Background core/GE is not stream credit. Return original base rewards; solver applies preference multiplier separately.'}
        requests.append([{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(query)}])
    torch.set_num_threads(8);tok,network=load(ADAPTER);outputs=[]
    for i in range(0,len(results),4):
        group=results[i:i+4];raws=generate_batch(tok,network,requests[i:i+4],max_tokens=900)
        for row,messages,raw in zip(group,requests[i:i+4],raws):
            p=row['profile'];expected=stream_result(p['programme'],p['completed_courses'],p['desired_stream'])
            try:parsed=json.loads(raw)
            except ValueError:parsed=None
            ok=exact(expected,parsed)
            outputs.append({'profile_id':p['profile_id'],'messages':messages,'raw_model_response':raw,
              'accepted':ok,'fallback_used':not ok,'validated_policy':expected,'complete_path':row['stream_plan'],
              'note':'Existing v6 weights; source/policy-conditioned illustration, not an independent held-out evaluation.'})
        save(OUT/'model_outputs.json',outputs);print('MODEL',len(outputs),'accepted',sum(x['accepted'] for x in outputs),flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['generate','model']);v=a.parse_args();globals()[v.command]()
