"""Summarize the completed handbook adaptation without inventing performance."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
train=read('reports/bscm/training.json');data=read('reports/bscm/dataset.json');ev=read('reports/bscm/evaluation.json');audit=read('reports/bscm/audit.json')
assert train['status']=='complete'
assert audit['original_adapter_sha256']==hashlib.sha256((ROOT/'adapters/bootstrap/adapter_model.safetensors').read_bytes()).hexdigest()
text=r'''# Computing Mathematics (BSCM) model update

The local Qwen3-8B now has a separate handbook-trained adapter at `adapters/bscm/`. The previous adapter and its historical evaluation remain intact. The source is the user-supplied Student Handbook 2026-27_updated.pdf, copied with a SHA-256 record into `sources/bscm/`.

## Use it

```powershell
cd F:\CODEX\cityu-course-helper
.\run_bscm.ps1 -Action ask -Question "Which core computing courses are listed for BSCM?"
.\run_bscm.ps1 -Action ask -Question "What are the credit requirements for Advanced Standing I in this handbook?"
.\run_bscm.ps1 -Action score -Course CS2360
```

The score command uses an explicitly synthetic year-two BSCM example. Edit `data/bscm/example_student.json` or pass `-Profile` with a real local JSON profile. The user's actual year, entry route, cohort and completed courses have not been inferred. A year or major is never proof that a prerequisite was passed.

The existing `inference.py score` and `recommend` commands also select the BSCM adapter automatically when `--profile` identifies Computing Mathematics or one of its aliases. Other profiles retain the original default adapter. Example:

```powershell
.\.venv\Scripts\python.exe inference.py score --course CS2360 --profile data/bscm/example_student.json
```

Programme questions in the `ask` command use a verified local handbook fact lookup, not unchecked model generation. Each answer identifies this mode, physical source pages and the handbook hash. Unmatched questions require confirmation. ASI credit answers retain the conflicting elective totals. This guard was added because the trained model still made material handbook-recall errors. The `score` command does use the trained BSCM model; its numeric scores remain estimates.

The live score command exposes the raw model estimate separately and computes the delivered synthetic rubric values in ordinary code. A fuller-syllabus CS2360 smoke test produced a raw model mismatch of 0.15 where the rubric target was 0.00. The arithmetic guard serves 0.00; this correction is not counted as model accuracy. BSCM recommendations likewise use calculated synthetic scores. The 4/4 scoring result below concerns only the fixed short-context test fixtures, not all future syllabus inputs.

## What was added

- BSCM identity and aliases, including Computing Mathematics, computing math and 計算數學.
- Mathematical modelling and scientific computing as programme background, without treating BSCM as identical to Computer Science.
- Cohort-specific degree credits and Normative versus Advanced Standing I differences.
- Core-course names, credits and route footnotes; CS2360 and CS2468 are recognised as programme core computing courses.
- Missing-route, missing-transcript, missing-timetable and inconsistent-source examples.
- Previous-task replay to reduce loss of existing behavior.

## Source caveats that the model was trained to recognise

Physical PDF page 4 gives ASI minimum graduation credits as 92. It gives ASI major electives as 18, also shown on PDF page 10; page 11 instead says 21. This inconsistency is flagged for departmental/ARRO confirmation, not silently resolved. The handbook applies to the 2026/27 intake; do not automatically apply it to other cohorts. Its suggested plans do not establish current AIMS sections, available seats, or a student's completed coursework.

Programme rules are source facts. Added workload/difficulty/background numbers remain synthetic estimates. The BSCM heuristic removes the blanket non-CS penalty for CS1302, CS2360 and CS2468 and uses a smaller heuristic penalty for other CS courses; this is not a reviewed student-suitability label or a prerequisite exemption.

## Measured run

'''
text+=f"- Handbook facts: {data['facts']}; core-course rows: {data['core_course_records']}.\n- Dataset sizes: {data['examples']}.\n- Training: {train['args']['epochs']} continued-training epochs from the original adapter; selected epoch {train['selected_epoch']}.\n- Time: {train['seconds']/60:.1f} minutes; peak allocated GPU memory {train['peak_gpu_allocated_gb']:.2f} GiB.\n\n"
text+='| Test task | Original adapter | BSCM adapter |\n| --- | --- | --- |\n'
for task in ['handbook','student_profile','bscm_score']:
    a,b=ev['original'][task],ev['bscm'][task]
    text+=f"| {task} | {a['passed']}/{a['total']} | {b['passed']}/{b['total']} |\n"
text+='''
Handbook and profile checks use exact JSON equality, including source-page fields and wording; semantically similar answers may fail. Scoring checks require valid structured scores within 0.02 of synthetic targets. All test prompts are separate from training prompts, but the handbook fact targets are intentionally shared across paraphrases. This measures recall of taught facts and profile handling, not generalization to an unseen handbook. No real workload labels or live registration data were used.

Full measured outputs: `reports/bscm/predictions.json`. Configuration and losses: `reports/bscm/training.json`. Source-linked teaching facts: `data/bscm/handbook_facts.json`. The original reports have not been replaced.
'''
(ROOT/'BSCM_UPDATE.md').write_text(text,encoding='utf-8')
print(text)
