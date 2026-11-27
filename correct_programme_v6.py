"""Train on the observed stream failure; retain the original evaluation as historical."""
import json,itertools,shutil,random
from pathlib import Path
from programme_training_v6 import SYSTEM,row,DATA,REPORT,ADAPTER
from programme_policy import *
def main():
    folder=ROOT/'data/programme-v6-correction';folder.mkdir(exist_ok=True)
    prior=ROOT/'adapters/cm-cs-programme-v6-initial';prior.mkdir(exist_ok=True)
    for p in (ROOT/ADAPTER).iterdir():
        if p.is_file():shutil.copy2(p,prior/p.name)
    shutil.copy2(REPORT/'evaluation.json',REPORT/'initial_evaluation.json')
    shutil.copy2(REPORT/'predictions.json',REPORT/'initial_predictions.json')
    shutil.copy2(REPORT/'training.json',REPORT/'initial_training.json')
    corrections=[]
    for major in ['CM','CS']:
        for name,rule in policy()['streams'][major].items():
            members=sorted(set(rule.get('required',[])+rule.get('options',[])+rule.get('core_choice',[])))
            complete=[]
            for n in range(len(members)+1):
                for done in itertools.combinations(members,n):
                    target=stream_result(major,done,name)
                    if target['stream_complete']:complete.append((done,target))
            for i,(done,target) in enumerate(complete[:8]):
                query=context(major,done,name)
                query['correction_note']='The selected stream is already complete. Additional alternatives must earn zero new stream reward. Correct the proposal that it still needs another option.'
                corrections.append(row(f'correct:{major}:{name}:{i}','stream',query,target))
    replay=[json.loads(x) for x in (DATA/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    rng=random.Random(20261122);rng.shuffle(replay)
    train=corrections+replay[:48]
    for split,rows in [('train',train),('validation',replay[48:60])]:
        (folder/(split+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    (REPORT/'correction_protocol.json').write_text(json.dumps({'corrective_examples':len(corrections),'replay':48,
        'original_evaluation_retained':True,'failed_test_case_now_used_for_teaching':True,
        'subsequent_evaluation_is_diagnostic_not_independent_holdout':True},indent=2),encoding='utf-8')
    print('Correction examples',len(train))
if __name__=='__main__':main()
