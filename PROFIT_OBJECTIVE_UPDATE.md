# Profit and overload planning branch

The current planning-v2 LoRA checkpoint and tokenizer were copied to `adapters/bscm-profit-v3`. Every original checkpoint file was checked byte-for-byte by SHA-256. The 8B base model is shared. The copy is an inference/continued-LoRA checkpoint; optimizer state was not saved in the original run. **No new fine-tuning was performed. The copied weights are identical to the source.**

## Profit and loss

`gross_profit = sum(selected course profits) + graduation_priority_weight * sum(selected unfinished maths core weights)`

`profit_penalty = sum(selected mismatch/difficulty/workload costs) + overload_weight * max(0, distinct_course_count - reference_load)^2`

`net_profit = gross_profit - profit_penalty`

**Maximize net_profit.** The equivalent minimization loss used by the solver is `schedule_loss = profit_penalty - gross_profit = -net_profit`. This is the planning/optimization loss. The Qwen assistant-token training loss remains cross-entropy; attaching a constant/discrete schedule penalty to token loss would not train the desired policy.

Profit is a configurable academic utility, not money or a measured student outcome. Default per-course profit is 3 points; an option can override it with its `profit` field. Existing year-weighted maths core benefits remain included. Existing mismatch, difficulty and workload estimates are deductions from profit.

## Increasing overload penalty

The default reference load is five courses and overload weight is 3. The penalty is based on distinct courses, not tutorial/lecture CRNs.

| Courses | Overload penalty | Extra penalty for this course |
| --- | --- | --- |
| 5 | 0 | 0 |
| 6 | 3 | 3 |
| 7 | 12 | 9 |
| 8 | 27 | 15 |

Five remains the default hard minimum and six the default maximum. The overload penalty is an increasing soft deduction, so a sufficiently valuable sixth course can still be selected. Prerequisites, required courses, exclusions, credit bounds and verified timetable evidence remain hard constraints. A profit cannot buy permission to violate them.

The quadratic penalty is implemented exactly with binary course-count selectors. The solver remains a MILP; no approximation or floating-point penalty is substituted for a hard eligibility constraint.

## Controlled comparison

This synthetic comparison deliberately permits up to eight courses to expose the overload curve. All eight courses have non-conflicting simulated meetings, equal three-credit values and cost 0.3 each. It is not a real CityU timetable or real eligibility assessment.

| Scenario | Courses selected | Gross profit | Course-cost penalty | Overload penalty | Net profit |
| --- | --- | --- | --- | --- | --- |
| no_overload_penalty | 8 | 24.00 | 2.40 | 0.00 | 21.60 |
| default_overload_penalty | 5 | 15.00 | 1.50 | 0.00 | 13.50 |
| high_course_profit | 6 | 48.00 | 1.80 | 3.00 | 43.20 |

Validation: 86 automated tests passed, including exhaustive enumeration against the MILP, course-count/penalty accounting, per-course profit overrides and hard-constraint regressions.

## Use

Edit `data/profit_objective_policy.json` to change the default profit, reference load or overload coefficient. Per-problem fields override these values. An option may specify a non-negative finite `profit`. `objective_mode: legacy_cost` reproduces the prior cost objective for historical comparisons. Year priorities remain in `data/cm_year_priority_policy.json`.

```powershell
cd F:\CODEX\cityu-course-helper
.\profit_planning.cmd demo
.\profit_planning.cmd plan --profile data/cm-planning-v2/example_student.json
.\profit_planning.cmd predict --profile data/cm-planning-v2/example_student.json
```

`plan` enumerates source-supported hypothetical MA bundles and returns the best net-profit plan with a full penalty breakdown. Its unit per-course cost is synthetic. `predict` uses the copied adapter with the new policy in context and displays independent validation; the copy retains the prior model’s unreliable unconstrained planning behavior. Saved MA source teaching weeks and official component linkage remain unverified, so these MA-only plans remain experimental. `scheduler.py` is the production solver for reviewed complete options and verified meetings.

Model-copy hashes and complete settings: `reports/profit-v3/checkpoint_copy.json`. Controlled optimizer outputs: `demo_comparison.json`. The original checkpoint remains in `adapters/bscm-planning-v2`.
