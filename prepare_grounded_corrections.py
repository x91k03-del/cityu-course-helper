"""Add the preceding simulation's explicitly labelled corrections before training."""
import hashlib,json
from pathlib import Path
import project_runtime
from timetable_grounded_training import DATA,REPORT,messages,assessment,save

def main():
    if (REPORT/'corrections_frozen.json').exists():raise RuntimeError('Training corrections already frozen.')
    root=Path(__file__).resolve().parent
    old=json.loads((root/'reports/markov-repair/year1_simulation.json').read_text());profile=old['input_profile'];done=[];rows=[];mismatches=[]
    for s in old['steps']:
        term='202609' if s['semester']=='A' else '202702'
        p={**profile,'programme_code':'BSCSIU4','year':s['year'],'term':term,'completed_courses':done.copy()}
        for code in s['selected_courses']:
            code={'MA4530:A':'MA4530','MA4530:B':'MA4530'}.get(code,code)
            target=assessment(p,code)
            rows.append({'id':f"old-rollout-correction:{s['term']}:{code}",'task':'timetable_EF_policy',
                'messages':messages(p,code)+[{'role':'assistant','content':json.dumps(target)}]})
            if not target['timetable_available']:mismatches.append({'original_term':s['term'],'course_code':code,
                'same_semester_snapshot':term,'reason':'No compatible saved timetable; do not select.'})
        done+=s['selected_courses']
    train=DATA/'train.jsonl'
    with train.open('a',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r)+'\n')
    protocol=json.loads((REPORT/'protocol.json').read_text());protocol['splits']['train']+=len(rows)
    protocol['previous_rollout_corrections']=len(rows);save(REPORT/'protocol.json',protocol)
    save(REPORT/'prior_simulation_offering_audit.json',{'scope':'Repeating the source year only to diagnose prior A/B errors; not future offering evidence.',
        'unsupported_selections':mismatches,'unsupported_count':len(mismatches),'prior_graduation_result_not_timetable_verified':True})
    from transformers import AutoTokenizer
    from train import tokenize_rows
    tok=AutoTokenizer.from_pretrained(root/'models/Qwen3-8B',local_files_only=True)
    lengths={}
    for name in ['train','validation']:
        rows=tokenize_rows(DATA/(name+'.jsonl'),tok,4096);lengths[name]={'count':len(rows),'max_tokens':max(len(r['input_ids']) for r in rows)}
    save(REPORT/'corrections_frozen.json',{'token_lengths':lengths,
        'sha256':{name:hashlib.sha256((DATA/(name+'.jsonl')).read_bytes()).hexdigest() for name in ['train','validation','test']}})
    print(json.dumps(lengths),flush=True)

if __name__=='__main__':main()
