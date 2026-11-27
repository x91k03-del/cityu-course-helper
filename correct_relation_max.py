import itertools,json,random,shutil,sys
from pathlib import Path
import project_runtime
import gpt_course_teacher as t
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data/gpt-course-relations-max';REPORT=ROOT/'reports/gpt-course-relations-max';ADAPTER='adapters/gpt-course-relations-max'
def build():
    DATA.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    if (DATA/'train.jsonl').exists():raise RuntimeError('Correction dataset frozen')
    g=json.loads((t.DATA/'reward_graph.json').read_text());rows=[]
    sources=['MA2503','MA2510','MA3515','MA3518','GE2340']
    for n in [2,3,4]:
      for group in itertools.combinations(sources,n):
       for grade in ['P','B+']:
        h=[{'course_code':c,'grade':grade} for c in group]
        rows.append({'id':f'max:{grade}:{group}','task':'GPT_preparation_reward','messages':t.messages(h,'CS4487',g)+[{'role':'assistant','content':json.dumps(t.target(h,'CS4487',g))}]})
    replay=[json.loads(x) for x in (t.DATA/'train.jsonl').read_text().splitlines()];random.Random(42).shuffle(replay)
    rows+=[{**r,'id':'replay:'+r['id']} for r in replay[:32]]
    (DATA/'train.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    shutil.copyfile(t.DATA/'validation.jsonl',DATA/'validation.jsonl')
    for name in ['evaluation_cases.json','after_evaluation.json','after_predictions.json']:
        shutil.copyfile(t.REPORT/name,REPORT/name.replace('after_','before_'))
    protocol=json.loads((t.REPORT/'protocol.json').read_text());protocol.update(parent_adapter=t.ADAPTER,corrective_train_examples=len(rows),
      scope='Corrective max-versus-sum teaching with P/B+ combinations; original held-out prompts unchanged; fresh observed failure is now a familiar diagnostic.')
    t.save(REPORT/'protocol.json',protocol)
    print(len(rows),flush=True)
def finish():
    import torch
    from inference import load,generate
    from programme_policy import exact
    torch.set_num_threads(8);sys.setrecursionlimit(5000)
    tok,model=load(ADAPTER);g=json.loads((t.DATA/'reward_graph.json').read_text())
    h=[{'course_code':c,'grade':'P'} for c in ['MA2503','MA2510','MA3515']]
    raw=generate(tok,model,t.messages(h,'CS4487',g),max_tokens=180)
    try:parsed=json.loads(raw)
    except ValueError:parsed=None
    expected=t.target(h,'CS4487',g);passed=exact(expected,parsed)
    t.save(REPORT/'corrected_probe.json',{'raw':raw,'expected':expected,'model_output_accepted':passed,'seen_in_correction_training':True})
    if not passed:raise RuntimeError('Corrective probe failed; prior adapter retained with guard.')
    del model
    t.REPORT=REPORT;t.ADAPTER=ADAPTER;t.release()
if __name__=='__main__':
    if sys.argv[1]=='build':build()
    elif sys.argv[1]=='after':t.REPORT=REPORT;t.ADAPTER=ADAPTER;t.evaluate('after')
    else:finish()
