"""Actual existing v6 model queries, with the new advisory context supplied explicitly."""
import json
import project_runtime
from programme_policy import context,stream_result,exact
from ge_pathways import recommend
from programme_training_v6 import SYSTEM,ADAPTER
from pathlib import Path
def main():
    import torch
    from inference import load,generate_batch
    root=Path(__file__).resolve().parent;folder=root/'data/ge-pathway-lambda'
    profiles=[json.loads((folder/(name+'.json')).read_text(encoding='utf-8')) for name in ['CM_Y2_FINANCE_GE','CS_Y2_AI_GE']]
    requests=[]
    for p in profiles:
        route=recommend(p);q={'task':'stream',**context(p['programme'],p['completed_courses'],route['selected_stream']),
          'advisory_GE_pathway':route,'instruction_note':'Return the original unscaled stream policy fields only. The solver separately applies the advisory multiplier; GE is not a stream credit.'}
        requests.append([{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(q)}])
    torch.set_num_threads(8);tok,model=load(ADAPTER);raws=generate_batch(tok,model,requests,max_tokens=700);rows=[]
    for p,messages,raw in zip(profiles,requests,raws):
        try:parsed=json.loads(raw)
        except ValueError:parsed=None
        route=recommend(p);expected=stream_result(p['programme'],p['completed_courses'],route['selected_stream'])
        rows.append({'profile_id':p['profile_id'],'input_messages':messages,'raw_model_output':raw,'accepted':exact(expected,parsed),
          'validated_unscaled_policy':expected,'solver_interest_multiplier':route['stream_reward_multiplier'],
          'inference_note':'Existing v6 adapter; supplied policy context. This turn changes planning policy, not model weights.'})
    out=root/'reports/ge-pathway-lambda/model_outputs.json';out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print([(r['profile_id'],r['accepted']) for r in rows])
if __name__=='__main__':main()
