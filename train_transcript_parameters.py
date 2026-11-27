"""Teach raw synthetic grade displays to return objective parameters only."""
import argparse,copy,hashlib,json,random
from pathlib import Path
import project_runtime
import transcript_parameter_pipeline as p

ROOT=p.ROOT;DATA=p.DATA;REPORT=p.OUT/'training'

def build():
    if (DATA/'train.jsonl').exists():raise RuntimeError('Dataset frozen')
    DATA.mkdir(parents=True);REPORT.mkdir(parents=True,exist_ok=True)
    rng=random.Random(20261127);splits={'train':[],'validation':[],'test':[]}
    bases=[json.loads((ROOT/f'reports/llm-reward-external-search/{name}_profile.json').read_text()) for name in ['F','N','M']]
    for split,count in [('train',72),('validation',8),('test',8)]:
        for i in range(count):
            base=copy.deepcopy(bases[i%3]);history=base['historical_transcript']
            for r in history:r['grade']=rng.choice(['A-','B+','B','C+','P','F'])
            prefs={'desired_stream':base['desired_stream'],
              'weights':{k:rng.choice([0.,.5,1.,2.,3.]) for k in ['background_mismatch','difficulty','workload']},
              'stream_reward_multiplier':rng.choice([1.,2.,3.,4.])}
            if i%3==0:prefs['weights']={k:1. for k in prefs['weights']};prefs['stream_reward_multiplier']=3.
            text=p.fixture_text(f'{split.upper()}-{i:03d}',history,prefs)
            expected=p.parameter_target(prefs['weights'],prefs['stream_reward_multiplier'])
            # The transcript-only mode has one USER turn, no task/schema instruction.
            mode='prompted' if i%4==0 else 'transcript'
            messages=p.model_messages(text,prefs,mode)
            splits[split].append({'id':split+':'+str(i),'task':'objective_parameters_only','mode':mode,
              'messages':messages+[{'role':'assistant','content':json.dumps(expected,separators=(',',':'))}]})
    # Correct the exact observed failure prompts. Report these as familiar retests.
    cases=json.loads((p.OUT/'cases.json').read_text())
    for c in cases:
        for mode in ['transcript','prompted']:
            for repeat in range(2):
                splits['train'].append({'id':f'failure:{c["id"]}:{mode}:{repeat}','task':'objective_parameters_only','mode':mode,
                  'messages':p.model_messages(c['text'],c['preferences'],mode)+[{'role':'assistant','content':json.dumps(c['expected_parameters'],separators=(',',':'))}]})
    for name,rows in splits.items():
        rng.shuffle(rows);(DATA/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    p.save(REPORT/'protocol.json',{'parent_adapter':p.PARENT,'new_adapter':p.ADAPTER,
      'splits':{k:len(v) for k,v in splits.items()},'familiar_failure_prompts_in_training':6,
      'familiar_repetitions':2,'real_sample_transcript_in_training':False,'identities_synthetic':True,
      'course_relation_policy_is_fixed_and_familiar':True,'scope':'Export reviewed objective configuration and explicit user weights. Generalisation to new reward policies is not claimed.',
      'LLM_output_keys':sorted(p.PARAMETER_KEYS),'natural_input_has_system_prompt':False,
      'parent_sha256':hashlib.sha256((ROOT/p.PARENT/'adapter_model.safetensors').read_bytes()).hexdigest()})
    print({k:len(v) for k,v in splits.items()},flush=True)

def evaluate_holdout():
    import torch
    from inference import load,generate_batch
    torch.set_num_threads(8);tok,model=load(p.ADAPTER)
    rows=[json.loads(s) for s in (DATA/'test.jsonl').read_text(encoding='utf-8').splitlines()];results=[]
    for start in range(0,len(rows),2):
        group=rows[start:start+2];raws=generate_batch(tok,model,[r['messages'][:-1] for r in group],max_tokens=1900)
        for r,raw in zip(group,raws):
            expected=json.loads(r['messages'][-1]['content'])
            try:p.validate_parameters(json.loads(raw),expected);passed=True;error=None
            except (ValueError,TypeError) as exc:passed=False;error=str(exc)
            results.append({'id':r['id'],'mode':r['mode'],'input':r['messages'][:-1],'raw':raw,'passed':passed,'error':error})
        p.save(REPORT/'heldout_predictions.json',results)
        print('heldout',len(results),sum(r['passed'] for r in results),flush=True)
    p.save(REPORT/'heldout_evaluation.json',{'passed':sum(r['passed'] for r in results),'total':len(results),
      'scope':'New synthetic record and explicit weight combinations; reviewed policy and formatting families are familiar.'})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','heldout']);a=ap.parse_args()
    build() if a.command=='build' else evaluate_holdout()
