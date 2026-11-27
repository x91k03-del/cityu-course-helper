# GPT teacher: course preparation rewards

Teacher: GPT assistant in this conversation, using saved course aims, prior syllabus evidence and official catalogue descriptions. No separate GPT-6.1-sol call is claimed.

These are deductive preparation hypotheses, not measured statistical correlations or verified workload savings. Values are editable utility assumptions.

Reward update: net profit = existing net profit + strongest direct preparation benefit for each target. Existing preparation is replaced, not added a second time. Cap 0.35 per target; passed sources only; no stacking, recursive or same-semester transfer; completed targets earn no new benefit. Timetable, membership and prerequisites remain binding.

| Passed course(s) | Target | Added preparation reward | GPT explanation |
|---|---|---:|---|
| MA2508 | MA3512 | 0.25 | Partial differentiation and multivariate modelling provide preparation for PDE formulation; the PDE syllabus still introduces new methods. |
| MA2510 | MA3518 | 0.30 | Probability, estimation and testing foundations support applied statistical analysis. |
| MA2503 | CS4487 | 0.25 | Vectors and matrices provide representations for data and model parameters. |
| MA2503, MA2510, MA3515 | CS4487 | 0.25 | Vectors and matrices provide representations for data and model parameters. Probability and statistical reasoning support uncertainty and model evaluation. Optimisation concepts help interpret model fitting and loss minimisation. |
| GE1202 | EF3320 | 0.10 | Introductory financial planning provides investment vocabulary, not advanced valuation skills. |
| MA3515 | EF3320 | 0.25 | Constrained optimisation helps interpret portfolio weights and risk-return tradeoffs. |
| MA2509 | GE2134 | 0.15 | Practice with formal logic may help evaluate arguments. Ethical reasoning, cognitive biases, creativity, group work and writing remain distinct demands. |

The synthetic five-course comparison keeps CS3481 passed in both profiles, so ML eligibility is already satisfied. Adding passed MA2503 increases the ML option by 0.25. Its fifth-slot reward rises from 2.70 to 2.95 and overtakes a competing 2.80 option. This fixture demonstrates the reward mechanism; DEMO courses are not registerable recommendations.

## Actual saved-timetable profile ablation

| Profile | Reward change | Selected courses changed? |
|---|---:|---|
| CM_finance_analysis | 1.02 | True |
| CM_finance_no_analysis | 0.85 | False |
| CM_enriched | 0.85 | False |

A positive reward change need not change an already preferred timetable. Existing semester constraints and stream bonuses can dominate a small preparation benefit. The previously infeasible entering Year-1 source pool remains infeasible; inferred preparation cannot create offered courses.

Official content references: [Machine Learning](https://www.cityu.edu.hk/catalogue/ug/current/course/CS4487.htm), [Applied Statistics, historical 2024/25](https://www.cityu.edu.hk/catalogue/ug/202425/course/MA3518.htm). The interpretation and numeric weights come from GPT reasoning; the university did not publish these reward values.

## Qwen distillation and verification

Initial supervised training: 149 training / 20 validation examples, two epochs. Held-out source-conditioned policy checks: 17/20 before, 20/20 after.

A fresh three-source P-grade probe initially produced an invalid sum of 0.75. Validation rejected it and used 0.25. An 82-example corrective pass (one epoch) taught max-versus-sum across passed-course combinations. The corrected probe now returns 0.25; it was seen in corrective training and is not an independent test. The unchanged held-out set remains 20/20.

Active relation checkpoint: `adapters/gpt-course-relations-max`. General and timetable checkpoints are preserved. All model reward outputs still require exact validation. The production reward uses the checked teacher graph, so a neural arithmetic error cannot inflate its value.

86 focused software checks passed. The tests cover bonus caps, non-stacking, failed/IP/W inputs, no recursive/self reward, source restrictions, prerequisite separation and reward accounting. Learned utilities are policy hypotheses; these checks do not establish improved student grades or calibrated workload savings.
