"""Export every fictional transcript, semester plan and audited Markov-profit result."""
import csv,json
from four_year_markov import *
from markov_training import TRAIN_REPORT

def export_transcript(run):
    folder=ROOT/'output/four-year-transcripts';folder.mkdir(parents=True,exist_ok=True)
    path=folder/(run['profile_id']+'.csv')
    rows=sorted(run['transcript'],key=lambda r:(r['term'],r['id']))
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['FICTIONAL TEST TRANSCRIPT - NOT AN OFFICIAL CITYU RECORD'])
        writer.writerow(['cohort','academic_year','semester','course_id_or_project_component','course_code','course_title',
                         'attempted_credits','grade','earned_credits','category','distribution_GE_area'])
        for r in rows:writer.writerow(['2025',f"{2024+r['year']}/{str(2025+r['year'])[-2:]}",r['semester'],r['id'],r['course_code'],r['title'],
                                     r['credits'],r['grade'],r['credits'] if r['grade'] in PASS else 0,r['kind'],r['area']])
    lines=['# FICTIONAL CM transcript - '+run['profile_id'],'','Not an official university record. Future enrolment/approval, actual class times, all prerequisites and assessment rules are not verified.','',
           '| Year / semester | Course | Title | Credits attempted | Grade | Credits earned |','| --- | --- | --- | --- | --- | --- |']
    for r in rows:lines.append(f"| {r['year']} {r['semester']} | {r['id']} | {r['title']} | {r['credits']} | {r['grade']} | {r['credits'] if r['grade'] in PASS else 0} |")
    lines += ['',f"Final earned credits: {run['audit']['earned_credits']}. Distribution GE: {run['audit']['distribution_GE_count']}. "
              f"Elective maths credits: {run['audit']['elective_math_credits']}. Encoded requirements met: {run['audit']['all_encoded_requirements_met']}."]
    (folder/(run['profile_id']+'.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return path

def main():
    rule=read(REPORT/'rule_rollouts.json')
    models=read(TRAIN_REPORT/'model_rollouts.json') if (TRAIN_REPORT/'model_rollouts.json').exists() else []
    all_runs=rule+models
    for run in all_runs:export_transcript(run)
    index=['# Fictional four-year CM transcripts','',
           '**Synthetic test data, not official CityU records.** Every file includes all attempted courses and grades across eight semesters.','']
    folder=ROOT/'output/four-year-transcripts'
    for r in all_runs:
        index.append(f"- {r['profile_id']}: [Readable transcript]({(folder/(r['profile_id']+'.md')).as_posix()}) · [CSV]({(folder/(r['profile_id']+'.csv')).as_posix()})")
    (folder/'INDEX.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
    lines=['# Four-year 2025-entry CM Markov-profit experiment','',
      '**All transcripts and future semester plans are fictional. Passing the encoded checks is not university-certified graduation or a verified timetable.**','',
      'The supplied 2025-entry normative study path is the base. Its minimum is **122 credits**, which is stricter than the requested 121-credit floor. '
      'The experiment enforces 122–144 credits, at least four distributional GE courses, at least one GE in each of Areas 1/2/3, and at least 20 credits of elective maths. '
      'Maths core and the capstone are excluded from that last measure. The model path supplies the 45-credit major core; these mandatory courses, two zero-credit soft-skills courses and a six-credit final-year project are also enforced.','',
      '## Source and scope','',
      'The 2025 PDF expressly permits MA3526 Analysis in Year 1 Semester B; its usual slot is Year 2 Semester B. '
      'GE areas were read from the actual Area column in the user-saved GE availability PDFs, not guessed from course codes. '
      'Year 4 in the supplied path has four-course / twelve-credit semesters, so the previous five-course minimum is waived for Year 4.','',
      'Elective choices use candidate titles/credits from the saved 2026 handbook and CS catalogue, with **2025-cohort approval unverified**. '
      'Future availability and several precedence rules are simulation assumptions. The 2026/27 Semester A class snapshot is not reused as proof of future timetables. '
      'The FYP is simulated as two three-credit components totalling six credits; this is not a claim about official interim transcript posting. '
      'Elective maths may occupy major-elective or free-elective slots, but each earned credit is counted once.','',
      'The prior generated NEW00007 example was a 2024-entry partial history. It is preserved as a negative compatibility case, not relabelled as a 2025 student. '
      'Its GE1359 completion would also conflict with required MA2508 if the saved exclusion rule were applied to this curriculum.','',
      '## Markov state and profit','',
      'Each semester begins from passed course/component IDs, earned credits, failed attempts, GE count, GE-area counts, elective-maths credits, core progress and current semester. '
      'The model generates reward coefficients from that state and the complete fictional transcript so far. The solver then forecasts the remaining semesters, executes only the current semester, observes grades and replans. '
      'Forecasts assume future passes; resit examples reveal a failure only after the attempt.','',
      '`net_profit = course_profit + newly_covered_GE_area_bonus + capped_GE/math/credit_progress_bonus + on_path_completion_bonus - course_cost - Year4_overload`','',
      'GE from an area already passed receives **0.1 times base course profit**. Only the first newly covered area gets the new-area bonus, including within a single semester. '
      'A fourth GE remains compulsory even after all three areas are covered. F/IP/W do not earn credit or satisfy area coverage. '
      'The fourth-course and elective-maths progress bonuses stop at their quota; total-credit progress stops at 122. '
      'An F receives no academic profit, while its attempted credits still contribute to load.','',
      '**Overload:** Years 1–3 have zero overload penalty. In Year 4 only, `0.25 × max(0, attempted semester credits − 12)²`. '
      'At 9 or 12 credits the penalty is zero; at 15 it is 2.25; at 18 it is 9. Five courses are not required in Year 4. '
      'An 18-credit semester cap still applies throughout the mock.','',
      'This is rule-distilled academic utility, not learned monetary profit or a fitted student-outcome reward model. '
      'The source-constrained rolling-horizon MILP uses a 0.98 discount and exact GE coverage/progress and Year 4 load terms. '
      'The neural model supplies parameters; it cannot waive the terminal graduation constraints.','',
      '## Full eight-semester rollouts','',
      '| Profile | Mode | Earned credits | GE count | GE areas 1 / 2 / 3 | Elective maths credits | All encoded requirements |',
      '| --- | --- | --- | --- | --- | --- | --- |']
    for r in all_runs:
        a=audit(r['transcript']);areas=' / '.join(str(a['GE_area_counts'][str(x)]) for x in [1,2,3])
        lines.append(f"| {r['profile_id']} | {'Model parameters + solver' if r['profile_id'].startswith('MODEL') else 'Rule parameters + solver'} | {a['earned_credits']} | {a['distribution_GE_count']} | {areas} | {a['elective_math_credits']} | {'PASS' if a['all_encoded_requirements_met'] else 'FAIL'} |")
    evaluation=TRAIN_REPORT/'evaluation.json'
    if evaluation.exists():
        e=read(evaluation);lines += ['','## Actual model parameter tests','',
          f"Exact configured-parameter matches on twelve fixed, held-out state vectors: **before {e['before']['passed']}/{e['before']['total']}; after {e['after']['passed']}/{e['after']['total']}**. "
          'Boundary states include three GE covering all areas versus the required fourth course, elective maths at 19/20 credits and total credits at 121/122. '
          'Test vectors were excluded from training. These are conditional rule-adherence tests, not empirical student-benefit estimates.']
    calls=TRAIN_REPORT/'rollout_parameter_calls.json'
    if calls.exists():
        c=read(calls);good=sum(x['accepted'] for x in c)
        lines += ['',f"During the model-assisted transcript rollouts, **{good}/{len(c)} parameter calls passed validation**, with {len(c)-good} explicit rule-parameter fallbacks. "
                  'Raw answers and fallback flags are saved. Fallbacks are not model passes. '
                  'These rollout demonstrations share the taught curriculum and may revisit training-state patterns; only the separate state-vector test is held out.']
    training=TRAIN_REPORT/'training.json'
    if training.exists() and read(training)['status']=='complete':
        t=read(training);lines += ['',f"The separate `{ADAPTER}` adapter was trained for {t['args']['epochs']} epochs from `adapters/bscm-profit-v3`. "
                                  f"Selected epoch {t['selected_epoch']}; training time {t['seconds']/60:.1f} minutes. "
                                  'Assistant-token cross-entropy teaches parameter rules; no discrete profit was falsely added as a differentiable token loss.']
    if models:
        sample=models[0];lines += ['','### Generated parameter progression: '+sample['profile_id'],'',
          '| Semester | GE count before | GE areas covered before | Elective maths credits before | GE quota bonus | Maths-credit bonus | Year 4 overload coefficient |',
          '| --- | --- | --- | --- | --- | --- | --- |']
        for s in sample['steps']:
            state=s['state_before'];p=s['parameters'];areas=', '.join(a for a,n in state['GE_area_counts'].items() if n) or 'None'
            if p is not None:lines.append(f"| {state['year']} {state['semester']} | {state['distribution_GE_count']} | {areas} | {state['elective_math_credits']} | {p['GE_count_progress_bonus']} | {p['math_credit_progress_bonus']} | {p['year4_overload_weight']} |")
        lines += ['', 'Other generated coefficients: base course profit 3; covered-area GE multiplier 0.1; new-area bonus 5; credit-progress bonus 0.05 until 122; overload threshold 12 credits; discount 0.98. '
                  'The engine applies the multiplier to the actual completed-area state and computes the resulting net profit.']
    validation=REPORT/'validation.json'
    if validation.exists():
        checks=read(validation);lines += ['','## Independent validation','',
            f"**{checks['automated_tests']} software checks passed.** All six exported transcripts were re-audited from course IDs and grades. "
            'Tests include duplicate-credit rejection, language-GE exclusion from distribution counts, 45-credit core versus elective maths, project-credit accounting, held-out state separation, '
            'GE state-dependent profit, credit-based MILP versus exhaustive search and final-term failure.']
    lines += ['','## Semester progression and profits','']
    for r in all_runs:
        lines += ['### '+r['profile_id'],'',
          '| Year / semester | Chosen course/component IDs | Attempted credits | Earned cumulative credits | Net profit | Overload penalty |',
          '| --- | --- | --- | --- | --- | --- |']
        for s in r['steps']:
            p=s['profit'];lines.append(f"| {s['state_before']['year']} {s['state_before']['semester']} | {', '.join(s['selection'])} | {p['planned_credits']} | {s['state_after']['earned_credits']} | {p['net_profit']:.2f} | {p['overload_penalty']:.2f} |")
    lines += ['','## Files and reruns','',
      '- Complete grade-bearing transcripts: `output/four-year-transcripts/` (one CSV and Markdown file per profile).',
      '- Rule-generated full trajectories: `reports/four-year/rule_rollouts.json`.',
      '- Actual model-assisted trajectories: `reports/markov-v4/model_rollouts.json`.',
      '- Raw generated parameter responses: `parameter_predictions.json` and `rollout_parameter_calls.json` in `reports/markov-v4/`.',
      '- Editable rule configuration: `data/four_year_policy.json`. The production semester-profit settings are in `data/profit_objective_policy.json`.',
      '- Source provenance and GE-area map: `reports/four-year/sources.json` and `data/four-year/GE_areas.json`.','',
      '```powershell','cd F:/CODEX/cityu-course-helper','./four_year.cmd prepare','./four_year.cmd evaluate',
      './four_year.cmd rollout','./four_year.cmd report','```','',
      'The path’s curriculum minimum and source assumptions remain visible. Unknown AIMS restrictions, all actual prerequisites, elective approvals, clash-free meetings and official graduation eligibility are not asserted.']
    source=read(REPORT/'sources.json')
    lines += ['', 'Source: [supplied 2025-entry study path](<'+Path(source['study_path']).as_posix()+'>). '
              'Physical PDF page 1 gives the 122-credit minimum; page 3 permits early Analysis; pages 4–8 provide the remaining suggested path.']
    (ROOT/'FOUR_YEAR_MARKOV_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Wrote FOUR_YEAR_MARKOV_REPORT.md and',len(all_runs),'complete fictional transcript files in each format')

if __name__=='__main__':raise SystemExit('Historical v4 report retained. Use preparation_report.py or four_year.cmd report for v5.')
