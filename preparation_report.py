"""Export v5 evidence, complete fictional transcripts and honest evaluation results."""
import csv,hashlib
from four_year_markov import *
from preparation_training import TRAIN_REPORT
def main():
    runs=read(REPORT/'rule_rollouts.json')+read(TRAIN_REPORT/'model_rollouts.json')
    out=ROOT/'output/preparation-v5-transcripts';out.mkdir(parents=True,exist_ok=True)
    lines=['# Qwen3-8B preparation and GE-cap fine-tuning report','',
      'The new checkpoint continues bscm-markov-v4. It generates academic-profit policy parameters; a hard-constrained solver selects the courses. '
      'All transcripts, grades and future plans here are fictional. Passing these checks does not certify university graduation, enrolment eligibility or class-time compatibility. '
      'Source coverage in this round is six course summaries and three provisional preparation edges; full current syllabus coverage remains pending public access or locally supplied PDFs.','',
      '## Rules and profit chain','',
      'At most **one distributional GE attempt per semester**, including failed attempts. Compulsory GE1401/GE1501/GE1601/GE2401 are outside this cap, as confirmed by the user. '
      'The four-course GE minimum and coverage of all three areas remain hard constraints. Total credits remain at least 122 (the supplied 2025 path is stricter than the requested 121), with at least 20 elective maths credits, mandatory core, capstone and category requirements.','',
      '`net profit = course profit + capped graduation progress + on-path bonus + direct preparation benefit − course cost − Year-4 overload`','',
      'Years 1–3 have no overload penalty. Year 4 uses `0.25 × max(0, semester credits − 12)^2`. '
      'An already-covered GE area still receives only 10% of base academic course profit. Preparation is a small separate benefit, not an exemption or increase in earned credits.','',
      '| Prior pass | Later target | Preparation utility | Deduction |','| --- | --- | --- | --- |']
    for e in graph()['edges']:lines.append(f"| {e['source']} | {e['target']} | {e['benefit']} | {e['reason']} |")
    lines += ['', 'These coefficients are conservative editable hypotheses, not estimated grade improvements or measured hours saved. '
      'Only direct prior passes count; F/IP/W and same-semester courses do not. Repeated records cannot multiply benefits and indirect chains do not propagate. '
      'Forecasts award a benefit only when the source is selected in an earlier semester; the next real step recomputes it from observed passes. '
      'Published contact hours and assessment demands are retained. A later course still needs its formal prerequisites. '
      'The indexed catalogue confirms that MA3511 needs (MA2508 and MA2503) or MA2001; the mock uses the first branch. MA3512/MA3514 need MA3511 and MA3515 needs MA2503. '
      'These checks are recorded separately from the preparation graph in `data/preparation-v5-prerequisites.json`; they do not replace verification of every course rule.','',
      '## Source access and workload interpretation','',
      '**Full current PDFs could not be downloaded:** CityU returned an access challenge. No challenge page was treated as syllabus text. '
      'The deductions use indexed excerpts of official CityU PDFs. MA2509 uses a 2020/21 version and MA3512 a 2023/24 version, so those links are provisional pending a current syllabus. '
      'The other sources below use 2025/26 versions. The downloader is provided and stops on an access challenge; locally supplied PDFs can be retained in `sources/preparation-v5/`.','',
      '| Course | Evidence and workload interpretation | Source |','| --- | --- | --- |']
    for code,c in graph()['courses'].items():lines.append(f"| {code} ({c['version']}) | {c['evidence']} Self-study hours remain unknown. | [Official PDF]({c['source_url']}) |")
    lines += ['', 'GE2134 is not classified as easy simply because its exam weighting is zero: workshops, projects, writing, discussion and a quiz remain work. '
      'MA2508 is not classified by credit count alone: its mathematical breadth and published lecture allocation inform a quantitative problem-solving workload description. '
      'No source supplies reliable student-specific total effort or assessment-week peaks here; those are not invented.','',
      '## Training and held-out model evaluation','']
    tr=read(TRAIN_REPORT/'training.json');ev=read(TRAIN_REPORT/'evaluation.json');ds=read(TRAIN_REPORT/'dataset.json')
    lines += [f"Training examples: {ds['examples']['train']}; validation: {ds['examples']['validation']}; held-out pool: {ds['examples']['test']}. "
      f"Best validation epoch: {tr.get('selected_epoch')}. The 222 training examples comprise 206 current-policy examples and 16 older task-replay examples. "
      'Training uses supervised assistant-token cross-entropy on synthetic policy labels, not a measured human workload reward.', '',
      '| Adapter | Exact new-schema answers | GE-cap field | Preparation map | Original nine parameters |','| --- | --- | --- | --- | --- |']
    for label,desc in [('before','Previous v4'),('after','New v5')]:
        e=ev[label];n=e['total'];lines.append(f"| {desc} | {e['passed']}/{n} | {e['GE_cap_passed']}/{n} | {e['preparation_map_passed']}/{n} | {e['original_nine_parameters_passed']}/{n} |")
    calls=read(TRAIN_REPORT/'rollout_parameter_calls.json');accepted=sum(c['accepted'] for c in calls)
    lines += ['', 'Twenty evaluation state queries were fixed before training; train/validation/test state vectors are disjoint. '
      'The prompt states the policy, so this checks faithful conditional policy execution with the supplied rules, not independent discovery of academic causal effects. '
      'The old adapter was not trained for the additional output schema; its exact-schema result must be interpreted with the field-level results above. Both adapters use the same prompts and greedy decoding, with independent evaluation prompts batched four at a time.', '',
      f"Actual model calls in three full rollouts: **{accepted}/{len(calls)} accepted**; rejected answers fall back to the visible rule policy. Raw answers are retained in the reports.",'',
      '## Complete fictional four-year plans','',
      '| Profile | Credits | Distribution GE | Elective maths credits | All encoded checks |','| --- | --- | --- | --- | --- |']
    for r in runs:
        a=audit(r['transcript']);pid=r['profile_id'];lines.append(f"| [{pid}](output/preparation-v5-transcripts/{pid}.md) | {a['earned_credits']} | {a['distribution_GE_count']} | {a['elective_math_credits']} | {a['all_encoded_requirements_met']} |")
        rows=r['transcript'];headers=['term','year','semester','id','title','credits','grade','kind','area']
        with (out/(pid+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f);w.writerow(['FICTIONAL TEST TRANSCRIPT - NOT AN OFFICIAL RECORD']);w.writerow(headers+['earned_credits'])
            for row in rows:w.writerow([row.get(k) for k in headers]+[row['credits'] if row['grade'] in PASS else 0])
        detail=['# FICTIONAL transcript: '+pid,'','Not an official university record. Future offerings, complete eligibility and meeting times remain unverified.','',
          '| Year/semester | Course | Attempted credits | Grade | Earned credits |','| --- | --- | --- | --- | --- |']
        for row in rows:detail.append(f"| {row['year']} {row['semester']} | {row['id']} {row['title']} | {row['credits']} | {row['grade']} | {row['credits'] if row['grade'] in PASS else 0} |")
        detail+=['','## Semester profits','','| Term | Courses | Credits | Net profit | Preparation | Overload |','| --- | --- | --- | --- | --- | --- |']
        for s in r['steps']:
            p=s['profit'];detail.append(f"| {s['term']} | {', '.join(s['selection'])} | {p['planned_credits']} | {p['net_profit']:.3f} | {p['preparation_benefit']:.3f} | {p['overload_penalty']:.3f} |")
        (out/(pid+'.md')).write_text('\n'.join(detail)+'\n',encoding='utf-8')
    validation=read(TRAIN_REPORT/'validation.json')
    paired=read(TRAIN_REPORT/'counterfactual_predictions.json')
    lines+=['','## Paired transcript diagnostics','',
      f"Additional diagnostics passed {sum(r['passed'] for r in paired)}/{len(paired)}. These hold the other Year-2-A attempts fixed and change MA2508 or MA2509 to B/F/IP/W, then recompute the state totals. These are diagnostic probes, separate from the predeclared 20-state holdout.",'',
      '| Changed course | Grade | Expected preparation map | Exact model response |','| --- | --- | --- | --- |']
    for r in paired:lines.append(f"| {r['changed_course']} | {r['grade']} | {json.dumps(r['expected']['preparation_bonus_by_course'])} | {r['passed']} |")
    lines+=['',f"Automated checks: {validation['automated_tests']} passed. Tests cover failed passes, GE limits, no same-semester transfer, reward bounds, profit arithmetic, unchanged contact requirements, terminal audits and existing timetable/prerequisite checks.",'',
      'Prerequisite grades, approval for the 2025 elective pool, offerings in later academic years and actual timetable clashes still require university confirmation. '
      'The saved timetable evidence remains a separate source; inferred preparation never creates an eligible class section.','',
      'Rerun: `four_year.cmd prepare`, `four_year.cmd evaluate`, `four_year.cmd rollout`, `four_year.cmd report`. '
      'Rebuild training examples with `preparation_training.py build`. Previous v4 model and report files are retained.','',
      '## Storage check','',
      'The model weights, adapters, datasets and reports are on F:. The completed training run used the F: checkpoint directory. '
      'A storage audit found no large project model cache on C:, but the default Windows temporary directory was on C:. '
      'Both project Python environments now redirect temporary files and model/library/GPU/package caches to `F:/CODEX/cityu-course-helper/.cache/`. '
      'An actual temporary file was verified there, including when launching Python from another working directory. '
      'The small existing app-managed preview on C: was retained and copied to `output/visualizations/` on F:. '
      'Windows paging, global settings and unrelated files were not changed. Details: [storage audit](reports/storage-audit.json).']
    (ROOT/'PREPARATION_V5_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (out/'INDEX.md').write_text('\n'.join(['# Fictional v5 transcripts','']+[f'- [{r["profile_id"]}]({r["profile_id"]}.md)' for r in runs])+'\n',encoding='utf-8')
    print('Wrote PREPARATION_V5_REPORT.md and',len(runs),'full transcripts')
if __name__=='__main__':main()
