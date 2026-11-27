"""Summarise actual training and raw-output checks without pooling test sets."""
import hashlib,json
from pathlib import Path
import project_runtime
from natural_language_training import validate_profile,PROFILE_FIELDS

ROOT=Path(__file__).resolve().parent
REPORT=ROOT/'reports/natural-language-students-corrected'
training=json.loads((REPORT/'training.json').read_text())
release=json.loads((REPORT/'release.json').read_text())
results=json.loads((REPORT/'after_predictions.json').read_text(encoding='utf-8'))
protocol=json.loads((REPORT/'protocol.json').read_text())
initial=json.loads((ROOT/'reports/natural-language-students/after_evaluation.json').read_text())
source=json.loads((ROOT/'reports/natural-language-students/protocol.json').read_text())
parent=ROOT/source['parent_adapter']/'adapter_model.safetensors'
assert hashlib.sha256(parent.read_bytes()).hexdigest()==source['parent_sha256']
legacy=json.loads((ROOT/'data/active_relation_adapter.json').read_text())
assert legacy['adapter']==source['parent_adapter']
rechecked=[]
for r in results:
    if r['group']=='legacy_relations':continue
    accepted=False;error=None
    try:validate_profile(r['parsed'],r['input'][0]['content']);accepted=True
    except (ValueError,TypeError,KeyError) as exc:error=str(exc)
    rechecked.append({'id':r['id'],'accepted':accepted,'error':error})
(REPORT/'latest_validator_audit.json').write_text(json.dumps(rechecked,indent=2),encoding='utf-8')
split_keys={}
for split in ['train','validation','test']:
    split_rows=[json.loads(line) for line in (ROOT/'data/natural-language-students-corrected'/(split+'.jsonl')).read_text(encoding='utf-8').splitlines()]
    split_keys[split]={json.dumps(json.loads(r['messages'][-1]['content']),sort_keys=True) for r in split_rows if r.get('task')=='natural_student_profile'}
assert not any(split_keys[a]&split_keys[b] for a,b in [('train','validation'),('train','test'),('validation','test')])
pairs={}
for r in results:
    if r['group']=='heldout':pairs.setdefault(r['id'].rsplit(':',1)[0],[]).append(r)
pair_audit={'pairs':len(pairs),'same_interpretation':sum(len(rs)==2 and rs[0]['parsed'] is not None and rs[0]['parsed']==rs[1]['parsed'] for rs in pairs.values()),
            'both_exact_correct':sum(len(rs)==2 and all(r['passed'] for r in rs) for rs in pairs.values()),
            'normalized_split_overlap':False}
pair_audit['same_student_profile']=sum(len(rs)==2 and all(isinstance(r['parsed'],dict) for r in rs) and {k:rs[0]['parsed'][k] for k in PROFILE_FIELDS}=={k:rs[1]['parsed'][k] for k in PROFILE_FIELDS} for rs in pairs.values())
(REPORT/'paraphrase_audit.json').write_text(json.dumps(pair_audit,indent=2),encoding='utf-8')
summaries=release['after']
lines=['NATURAL-LANGUAGE QWEN UPDATE\n',
 'Status: '+('ENABLED' if release['accepted_for_activation'] else 'NOT ENABLED')+'\n',
 'Active adapter: '+release['adapter']+'\n',
 'The model receives one ordinary-English user message. No custom system prompt,\n'
 'teacher edge list, examples or output-schema instructions are supplied to it.\n'
 'Its deployed output is the interpreted student profile. External software\n'
 'calculates state-dependent rewards from reviewed course-relation parameters,\n'
 'selects courses and checks timetable/degree constraints. Raw numeric reward\n'
 'proposals from the language model are retained for auditing and are not used.\n',
 '\nActual fine tuning\n',
 'Initial adaptation: 396 training rows, 32 validation rows, three epochs.\n',
 f"Corrective adaptation: {training['train_examples']} training rows, {training['validation_examples']} validation rows, {len(training['history'])} epochs.\n",
 f"Selected corrective epoch: {training['selected_epoch']}. Rank-8 QLoRA, frozen NF4 base, BF16 computation.\n",
 f"GPU: {training['gpu']}; recorded corrective peak allocated VRAM {training['peak_gpu_allocated_gb']:.2f} GiB.\n",
 'The original relation adapter and its active manifest are unchanged.\n',
 '\nDeployed natural-language interpretation (raw profile fields)\n']
for name,stats in release['profile_extraction'].items():lines.append(f"{name}: {stats['passed']}/{stats['total']} exact student-profile matches.\n")
lines += [f"Paraphrase pairs with the same interpreted student profile: {pair_audit['same_student_profile']}/{pair_audit['pairs']}.\n",
          '\nWhole raw answer, including numeric proposals (not the activation criterion)\n']
for name,stats in summaries.items():lines.append(f"{name}: {stats['passed']}/{stats['total']} exact matches.\n")
lines += [f"Paraphrase pairs with the same interpreted data: {pair_audit['same_interpretation']}/{pair_audit['pairs']}.\n",
          f"Paraphrase pairs with both answers fully correct: {pair_audit['both_exact_correct']}/{pair_audit['pairs']}.\n"]
lines += ['\nInterpretation of the groups\n',
 'heldout: 48 messages from 24 new profile records, disjoint from training and\n'
 'validation. Course codes, reviewed preparation relations and wording templates\n'
 'are familiar. These are synthetic policy tests, not independent student outcomes.\n',
 'familiar_failures: 12 earlier natural-language cases explicitly used in training.\n'
 'This is a corrective retest and is not pooled with heldout accuracy.\n',
 'legacy_relations: 20 earlier structured-relation regression checks.\n',
 'fresh_manual: six new handwritten phrasings; some underlying student profiles\n'
 'are familiar from correction training. Reported separately.\n',
 '\nWhy a correction round was needed\n',
 f"The initial candidate matched {initial['heldout']['passed']}/{initial['heldout']['total']} on its development test and {initial['familiar_failures']['passed']}/12 familiar failures.\n",
 'Those 48 initial test messages became corrective teaching examples. The final\n'
 '48 heldout messages were newly generated and frozen before corrective training.\n',
 '\nWhat changed\n',
 'The update teaches natural-language transcript parsing, P versus F/IP/W,\n'
 'completed-course preservation, programme/year/semester/cohort extraction,\n'
 'desired streams, explicit penalty weights, target-course recognition and\n'
 'preparation reward proposals. The deployed external calculator performs\n'
 'maximum-direct-link arithmetic and identifies missing planning context.\n',
 'The local command validates the output, rejects contradicted explicit grades\n'
 'or unmentioned courses/context, and reads displayed course titles from the\n'
 'saved sources. Profile scores above use raw neural profile fields, before\n'
 'these checks. The external numeric calculation is reported separately and\n'
 'does not turn a wrong raw reward proposal into a model success. The user\n'
 'should review the interpreted profile before using it to plan registration.\n',
 '\nHow to use\n',
 'Double-click run_natural_student_input.cmd in the project folder and paste\n'
 'your student message. Alternatively, save a longer message in a text file.\n',
 'Edit student_message.txt in this folder. From F:\\CODEX\\cityu-course-helper run:\n',
 '.\\run_natural_student_input.cmd "reports\\natural-language-students-corrected\\student_message.txt"\n',
 '\nSaved examples and results\n',
 'all_natural_test_inputs.txt: exact natural-language test inputs.\n',
 'natural_test_outputs.txt: exact raw model answers.\n',
 'after_predictions.json: inputs, targets and raw responses, including failures.\n',
 'release.json: activation decision.\n',
 'latest-input/: demonstration with raw output, reviewed profile and readable summary.\n']
(REPORT/'TRAINING_RESULTS.txt').write_text(''.join(lines),encoding='utf-8')
(REPORT/'natural_test_outputs.txt').write_text('\n\n'.join(
    'CASE '+r['id']+'\nGROUP '+r['group']+'\nINPUT\n'+r['input'][-1]['content']+
    '\nRAW OUTPUT\n'+r['raw']+'\nEXACT MATCH: '+str(r['passed']) for r in results),encoding='utf-8')
(REPORT/'README.txt').write_text(''.join(lines),encoding='utf-8')
sample=ROOT/'reports/natural-language-students/student_message.txt'
(REPORT/'student_message.txt').write_text(sample.read_text(encoding='utf-8'),encoding='utf-8')
print(json.dumps({'activation':release['accepted_for_activation'],'results':summaries,'parent_unchanged':True,
                  'latest_guard_acceptance':sum(r['accepted'] for r in rechecked),'natural_tests':len(rechecked)},indent=2))
