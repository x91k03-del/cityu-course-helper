"""Run saved, inspectable prompts against the active course-relation adapter."""
import copy, datetime, hashlib, json, time
from pathlib import Path
import project_runtime
import gpt_course_teacher as teacher
from preparation import graph

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'reports' / 'additional-qwen-examples-20261127'

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')

def main():
    OUT.mkdir(parents=True, exist_ok=False)
    g = graph()
    specifications = [
        ('FIN_PASS', 'CM', 2, 'Finance GE passed', 'EF3320', [('CS1302','B'),('MA1300','B+'),('GE2260','A-')]),
        ('FIN_FAIL', 'CM', 2, 'Matched profile, finance GE failed', 'EF3320', [('CS1302','B'),('MA1300','B+'),('GE2260','F')]),
        ('CALC_PASS', 'CM', 2, 'Multivariable calculus passed', 'MA3515', [('MA1301','B'),('MA2508','B+')]),
        ('CALC_IP', 'CM', 2, 'Matched profile, calculus still in progress', 'MA3515', [('MA1301','B'),('MA2508','IP')]),
        ('AI_GE', 'CS', 2, 'AI GE orientation, programming background', 'CS4487', [('CS1302A','A'),('CS2310','B+'),('GE2340','B')]),
        ('AI_GE_FAILED', 'CS', 2, 'Matched profile, AI GE failed', 'CS4487', [('CS1302A','A'),('CS2310','B+'),('GE2340','F')]),
        ('AI_MAX', 'CM', 3, 'Several mathematical preparation links: take maximum, not sum', 'CS4487', [('MA2503','B+'),('MA2510','P'),('MA3515','A-'),('GE2340','B')]),
        ('ALG_PASS', 'CS', 3, 'Data structures passed before advanced algorithms', 'CS4335', [('CS2310','B'),('CS3334','A-'),('GE1305','B')]),
    ]
    cases = []
    for ident, programme, year, description, target, rows in specifications:
        transcript = [dict(course_code=code, grade=grade) for code, grade in rows]
        cases.append({'id':ident, 'profile_context':{'programme':programme,'year':year,'fictional':True},
            'description':description, 'messages':teacher.messages(transcript,target,g),
            'expected':teacher.target(transcript,target,g)})
    # The exact model input is saved BEFORE inference; no expected answers are sent.
    save('cases.json',cases)
    manifest=json.loads((ROOT/'data/active_relation_adapter.json').read_text())
    chunks=['ACTUAL QWEN TEST INPUTS\nEight fictional transcript tests.\n'
            'Programme/year labels are reader context and are not sent to this relation-task interface.\n'
            'Each exact SYSTEM and USER message below is sent to the active fine-tuned Qwen.\n'
            'Expected answers are excluded. This task predicts preparation rewards, not timetables.\n'
            'Adapter: '+manifest['adapter']+'\n']
    for c in cases:
        chunks.extend(['\n'+'='*70+'\nCASE '+c['id']+'\n'+c['description']+'\n'
            'CONTEXT (not sent): '+json.dumps(c['profile_context'])+'\n',
            *['\n'+m['role'].upper()+'\n'+m['content']+'\n' for m in c['messages']]])
    (OUT/'qwen_test_inputs.txt').write_text(''.join(chunks),encoding='utf-8')
    import torch
    from inference import load, generate
    from programme_policy import exact
    torch.set_num_threads(8)
    started=time.perf_counter()
    tok,model=load(manifest['adapter'])
    rendered=[]; results=[]
    for c in cases:
        prompt=tok.apply_chat_template(c['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=False)
        rendered.append('\n'+'='*70+'\nCASE '+c['id']+'\n'+prompt+'\n')
    (OUT/'qwen_rendered_prompts.txt').write_text(''.join(rendered),encoding='utf-8')
    for c in cases:
        raw=generate(tok,model,c['messages'],max_tokens=180)
        try:
            parsed=json.loads(raw); error=None
        except (ValueError,TypeError) as e:
            parsed=None;error=str(e)
        r={**c,'raw_model_output':raw,'parsed_model_output':parsed,
           'matches_configured_policy':exact(c['expected'],parsed),'parse_error':error,
           'repair_used':False,'fallback_used':False}
        results.append(r);save('results.json',results)
        print(c['id'],raw,'PASS' if r['matches_configured_policy'] else 'FAIL',flush=True)
    summary={'adapter':manifest['adapter'],'cases':len(results),
        'passed':sum(r['matches_configured_policy'] for r in results),
        'seconds':round(time.perf_counter()-started,2),'neural_weights_updated':False,
        'evaluation_scope':'Additional fictional transcript probes of familiar configured course relations; not unseen-course or educational-outcome evaluation.',
        'LLM_task':'Preparation bonus and strongest prior passed sources only; external software handles scheduling.',
        'input_sha256':hashlib.sha256((OUT/'qwen_test_inputs.txt').read_bytes()).hexdigest()}
    save('summary.json',summary)
    lines=['QWEN TEST RESULTS\n',f"Matched configured policy: {summary['passed']}/{summary['cases']}\n",
        'No repair, fallback or retraining. Preparation bonuses are configured utility hypotheses.\n']
    table=['# Additional Qwen test examples\n',
        f"Actual local fine-tuned Qwen run: **{summary['passed']}/{summary['cases']}** matched the configured relation policy.\n",
        '| Case | Student background | Target | Expected bonus | Qwen bonus | Match |',
        '|---|---|---|---:|---:|---|']
    for r in results:
        lines += ['\nCASE '+r['id']+'\n'+r['description']+'\nRAW OUTPUT\n'+r['raw_model_output']+'\n',
                  'EXPECTED\n'+json.dumps(r['expected'])+'\nMATCH: '+str(r['matches_configured_policy'])+'\n']
        p=r['parsed_model_output']
        observed=p.get('preparation_bonus') if isinstance(p,dict) else 'invalid JSON'
        table.append(f"| {r['id']} | {r['description']} | {r['expected']['target']} | {r['expected']['preparation_bonus']} | {observed} | {r['matches_configured_policy']} |")
    table += ['\nThe finance, calculus and AI pairs change one grade while keeping the other courses fixed.',
        'AI_MAX checks that multiple applicable links produce the strongest bonus, rather than their sum.',
        '\nThese test reward predictions, not complete course plans or university registration eligibility. '
        'The inputs include the reviewed teacher edges, as in training. Passing means following that supplied policy. '
        'The transcript probes are additional examples of familiar relations, not a frozen independent benchmark.',
        '\nFiles: qwen_test_inputs.txt contains exact system/user messages; qwen_rendered_prompts.txt includes chat-template tokens. '
        'qwen_test_outputs.txt retains raw outputs and expected answers; results.json retains the full records.']
    (OUT/'qwen_test_outputs.txt').write_text(''.join(lines),encoding='utf-8')
    (OUT/'RESULTS.md').write_text('\n'.join(table)+'\n',encoding='utf-8')
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
