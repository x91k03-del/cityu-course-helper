"""Retain transcript parameter exports while correcting the old English route."""
import argparse,copy,json,random,shutil
from pathlib import Path
import project_runtime
import transcript_parameter_pipeline as p

ROOT=p.ROOT;DATA=ROOT/'data/objective-parameters';REPORT=p.OUT/'english-correction'
ADAPTER='adapters/objective-parameters'

def build():
    if (DATA/'train.jsonl').exists():raise RuntimeError('English correction dataset already frozen')
    DATA.mkdir(parents=True);REPORT.mkdir(parents=True,exist_ok=True)
    replay=[json.loads(s) for s in (p.DATA/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    source=[json.loads(s) for s in (ROOT/'data/natural-language-students-corrected/train.jsonl').read_text(encoding='utf-8').splitlines() if json.loads(s).get('task')=='natural_student_profile']
    rng=random.Random(20261129);rng.shuffle(source)
    english=[]
    for i,r in enumerate(source[:32]):
        profile=json.loads(r['messages'][-1]['content'])
        preferences={'desired_stream':profile['desired_stream'],'weights':profile['weights'],
          'stream_reward_multiplier':3.,'include_fixture_planning_context':False}
        english.append({'id':'english:'+str(i),'task':'objective_parameters_only','mode':'english',
          'messages':p.model_messages(r['messages'][0]['content'],preferences)+[{'role':'assistant','content':json.dumps(p.parameter_target(preferences['weights']),separators=(',',':'))}]})
    # The observed compatibility failure is a familiar corrective example.
    text=(ROOT/'reports/natural-language-students-corrected/student_message.txt').read_text(encoding='utf-8')
    preferences={'desired_stream':'Financial Mathematics','weights':{'background_mismatch':1.,'difficulty':1.,'workload':1.},'stream_reward_multiplier':3.,'include_fixture_planning_context':False}
    for i in range(4):english.append({'id':'compatibility-failure:'+str(i),'task':'objective_parameters_only','mode':'english',
      'messages':p.model_messages(text,preferences)+[{'role':'assistant','content':json.dumps(p.parameter_target(),separators=(',',':'))}]})
    rows=replay+english;rng.shuffle(rows)
    (DATA/'train.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    validation=[json.loads(s) for s in (p.DATA/'validation.jsonl').read_text(encoding='utf-8').splitlines()][:4]
    old_val=[json.loads(s) for s in (ROOT/'data/natural-language-students-corrected/validation.jsonl').read_text(encoding='utf-8').splitlines()][:4]
    for i,r in enumerate(old_val):
        prof=json.loads(r['messages'][-1]['content']);pref={**preferences,'desired_stream':prof['desired_stream'],'weights':prof['weights']}
        validation.append({'id':'english-validation:'+str(i),'task':'objective_parameters_only','mode':'english',
          'messages':p.model_messages(r['messages'][0]['content'],pref)+[{'role':'assistant','content':json.dumps(p.parameter_target(pref['weights']),separators=(',',':'))}]})
    (DATA/'validation.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in validation),encoding='utf-8')
    shutil.copyfile(p.DATA/'test.jsonl',DATA/'test.jsonl')
    controls=[
      ('E1','I am a Year 2 Computing Mathematics student. CS1302: B, MA1300: B+, GE2260: A-. I prefer the Financial Mathematics stream.',preferences),
      ('E2','My programme is Computing Mathematics, year 3. MA2503 (B+), MA2510 (P), MA3515 (A-), GE2340 (B). I want Enriched Mathematics.',{**preferences,'desired_stream':'Enriched Mathematics'}),
      ('E3','I study Computer Science in Year 2. I passed CS1302A with A and CS2310 with B+, and failed GE2340. I want Artificial Intelligence.',{**preferences,'desired_stream':'Artificial Intelligence'}),
      ('E4','I am a Year 2 CM student. CS1302: B, GE2260: F. I want Financial Mathematics. Use background mismatch weight 2, difficulty weight 0.5, and workload weight 1.',{**preferences,'weights':{'background_mismatch':2.,'difficulty':.5,'workload':1.}})]
    p.save(REPORT/'controls.json',[{'id':i,'messages':p.model_messages(t,w),'expected':p.parameter_target(w['weights'])} for i,t,w in controls])
    p.save(REPORT/'protocol.json',{'parent':'adapters/transcript-parameters','new_adapter':ADAPTER,'train':len(rows),'validation':len(validation),
       'layout_replay_rows':len(replay),'english_rows':len(english),'old_failure_taught':True,
       'new_english_control_messages':4,'real_source_transcript_in_training':False})
    print({'train':len(rows),'validation':len(validation)},flush=True)

def evaluate():
    import torch
    from inference import load,generate_batch
    torch.set_num_threads(8);tok,model=load(ADAPTER);rows=json.loads((REPORT/'controls.json').read_text());results=[]
    for start in range(0,len(rows),2):
        group=rows[start:start+2];raws=generate_batch(tok,model,[r['messages'] for r in group],max_tokens=1900)
        for r,raw in zip(group,raws):
            try:p.validate_parameters(json.loads(raw),r['expected']);passed=True;error=None
            except (ValueError,TypeError) as e:passed=False;error=str(e)
            results.append({**r,'raw':raw,'passed':passed,'error':error})
        p.save(REPORT/'control_predictions.json',results);print('english',len(results),sum(r['passed'] for r in results),flush=True)
    p.save(REPORT/'control_evaluation.json',{'passed':sum(r['passed'] for r in results),'total':len(results),'scope':'New ordinary-English wordings with the same reviewed objective policy; no custom system prompt.'})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','evaluate','paired','heldout']);a=ap.parse_args()
    if a.command=='build':build()
    elif a.command=='evaluate':evaluate()
    elif a.command=='paired':p.evaluate('after',ADAPTER)
    else:
        import train_transcript_parameters as teaching
        teaching.p.ADAPTER=ADAPTER;teaching.evaluate_holdout()
