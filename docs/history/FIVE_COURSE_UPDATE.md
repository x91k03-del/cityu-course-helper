# Five-course planning and failure-correction update

The previous profile experiment explicitly capped plans at three courses (often nine credits). The proposal itself minimized non-negative mismatch/difficulty/workload costs under credit constraints. Neither establishes a nine-course rule.

## Updated optimization

For complete course-option variables x, minimize student cost plus a weighted penalty for leaving unfinished maths core courses unselected:

`sum_i x_i*(lambda_b*b_i + lambda_d*d_i + lambda_w*w_i) + lambda_g*sum_c priority_c(year)*(1 - y_c)`

`5 <= sum_c y_c <= course_max`, with at most one complete option per distinct course. Credit bounds, prerequisites, exclusions, required courses, component evidence and timetable constraints remain hard constraints. Zero-credit tutorials cannot pad the course count. The default maximum is six; the minimum is never silently relaxed when data are insufficient.

Year priorities are an editable advisory policy based on the supplied handbook core list/course levels, not official per-year graduation deadlines. The common maths core receives weight 1, and the selected year focus receives weight 3. Already completed courses receive no reward. The default graduation-priority multiplier is 3. A course must still be offered and eligible; a priority never invents an offering or bypasses a prerequisite. Use required_courses for an explicitly confirmed must-take course. Route-specific electives/waivers and full graduation audits are outside this policy.

| Year | Advisory focus (if applicable, offered and eligible) |
| --- | --- |
| 1 | MA1505 |
| 2 | MA2508, MA2509 |
| 3 | MA3512, MA3518 |
| 4 | MA3514, MA3515 |

Year 1 MA1505 is route-dependent and may be a Semester B course; it is not automatically rewarded as a common-core Semester A offering. The supplied Semester A MA snapshots do not include every focus course. Missing course data remain missing.

## Failure-based fine-tuning

Historical failed profiles used for correction training: CM02, CM03, CM04, CM05, CM07, CM08, CM09, CM10, CM11, CM12. Wrong answers appear only as negative input evidence. Assistant targets reject them and give the correct source-derived plan or an explicit infeasible result. This is supervised correction training, not preference/DPO training. The historical test is now training data and cannot be presented as a held-out evaluation.

New split counts: {'train': 260, 'validation': 36, 'test': 48}. New transcript groups are disjoint by year/cohort/passed-course set; new evaluation IDs were fixed before training. Shared course facts remain taught facts; the holdout measures new scenarios, not unseen course-fact generalization.

The separate adapter `adapters/bscm-planning-v2` was trained for 2 epochs from `adapters/bscm-ma-timetable`. Selected epoch: 2; time: 7.1 minutes; peak GPU allocation: 21.33 GiB.

## New held-out model results

| Task | Before | After |
| --- | --- | --- |
| five_course_plan | 0/8 | 3/8 |
| admission | 0/8 | 8/8 |
| grounded_ge | 2/2 | 2/2 |
| admission_decision_only | 5/8 | 8/8 |

Raw outputs and per-case errors are in `reports/cm-planning-v2/predictions.json`. No repair/fallback is counted as a raw-model pass.

`admission` requires both the correct decision and exact source error codes. `admission_decision_only` counts the correct boolean for the correct course without requiring identical explanation/error-code wording. This separates factual decision improvement from output-format improvement.

**Direct model planning passed 0/4 feasible-plan cases.** The aggregate plan score includes correctly reporting infeasibility and must not be read as successful five-course generation. The new model falsely refused the feasible cases. Use the constraint solver/source reference for final selection; do not let an LLM refusal override a feasible verified optimizer result.

| New profile | Year | Source-supported status | Before: status / courses | After: status / courses | After passes? |
| --- | --- | --- | --- | --- | --- |
| NEW00007 | 3 | candidate | candidate / MA2508, MA3512, MA3518, MA3525, MA4545 | infeasible /  | FAIL |
| NEW00010 | 2 | candidate | candidate / MA2509, MA3518 | infeasible /  | FAIL |
| NEW00011 | 3 | candidate | candidate / MA2503, MA3512, MA3518, MA3525 | infeasible /  | FAIL |
| NEW00013 | 4 | candidate | candidate / MA2509, MA3512, MA3525, MA4545, MA3518 | infeasible /  | FAIL |
| NEW00000 | 2 | infeasible | candidate / MA2508, MA3512, MA3525, MA3518, MA4542 | infeasible /  | PASS |
| NEW00001 | 1 | infeasible | candidate / MA2508, MA3525, MA3518, MA3521, MA4542 | infeasible /  | PASS |
| NEW00002 | 1 | infeasible | candidate / MA2503, MA2508, MA2509, MA3525, MA4545 | infeasible /  | FAIL |
| NEW00003 | 3 | infeasible | candidate / MA2509, MA3518, MA3525 | infeasible /  | PASS |
## Software verification

74 automated checks passed, including exhaustive-search comparisons, priority-versus-prerequisite tests, distinct-course counting and the loss/gradient equivalence check. The public synthetic demo selects five courses / fifteen credits, including both expensive year-three maths priorities despite cheaper optional alternatives.

## Scope and use

Production `scheduler.py` enforces five distinct courses by default and fails closed on missing verified rules/timetable evidence. BSCM recommendation requests receive the year-priority policy through `planning_policy.py`. Synthetic legacy two/three-course benchmarks explicitly retain their small test scopes; they are not full-semester recommendations.

The new real-source model experiment uses MA-only saved schedules and hypothetical C+T bundles. If fewer than five supported courses fit, the correct answer is infeasible. Additional GE/CS courses require their own verified eligibility and complete meeting data; no GE filler or teaching weeks were fabricated. Experimental weekly plans are not university-approved registration plans.

Commands: `cm_planning_update.cmd plan --profile <profile.json>` and `cm_planning_update.cmd predict --profile <profile.json>`. The plan command returns an exact source-derived experimental reference; predict shows the model answer and independent validation.

Examples: `cm_planning_update.cmd demo`, `cm_planning_update.cmd plan --profile data/cm-planning-v2/example_student.json`, `cm_planning_update.cmd predict --profile data/cm-planning-v2/example_student.json`. Edit year-focus weights in `data/cm_year_priority_policy.json`; explicit per-problem course_priority_weights override the defaults.

## Reviewable source-derived five-course example

**This is a constraint-enumerated reference, not a generated model answer.** It demonstrates the five-course minimum with actual saved MA weekdays and times under the explicitly hypothetical component rules.

| Course / component | Day | Start | End |
| --- | --- | --- | --- |
| MA1300 / C01 | Fri | 12:00 | 13:50 |
| MA1300 / C01 | Wed | 17:00 | 18:50 |
| MA1300 / T01 | Mon | 18:00 | 18:50 |
| MA2509 / CA1 | Mon | 10:00 | 10:50 |
| MA2509 / CA1 | Wed | 10:00 | 11:50 |
| MA2509 / TA1 | Mon | 11:00 | 11:50 |
| MA3512 / CA1 | Fri | 15:00 | 17:50 |
| MA3518 / CA1 | Tue | 16:00 | 18:50 |
| MA3525 / CA1 | Thu | 13:00 | 14:50 |
| MA3525 / CA1 | Tue | 14:00 | 14:50 |
| MA3525 / TA1 | Tue | 15:00 | 15:50 |
