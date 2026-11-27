# Qwen3-8B preparation and GE-cap fine-tuning report

The new checkpoint continues bscm-markov-v4. It generates academic-profit policy parameters; a hard-constrained solver selects the courses. All transcripts, grades and future plans here are fictional. Passing these checks does not certify university graduation, enrolment eligibility or class-time compatibility. Source coverage in this round is six course summaries and three provisional preparation edges; full current syllabus coverage remains pending public access or locally supplied PDFs.

## Rules and profit chain

At most **one distributional GE attempt per semester**, including failed attempts. Compulsory GE1401/GE1501/GE1601/GE2401 are outside this cap, as confirmed by the user. The four-course GE minimum and coverage of all three areas remain hard constraints. Total credits remain at least 122 (the supplied 2025 path is stricter than the requested 121), with at least 20 elective maths credits, mandatory core, capstone and category requirements.

`net profit = course profit + capped graduation progress + on-path bonus + direct preparation benefit − course cost − Year-4 overload`

Years 1–3 have no overload penalty. Year 4 uses `0.25 × max(0, semester credits − 12)^2`. An already-covered GE area still receives only 10% of base academic course profit. Preparation is a small separate benefit, not an exemption or increase in earned credits.

| Prior pass | Later target | Preparation utility | Deduction |
| --- | --- | --- | --- |
| MA2508 | MA3512 | 0.25 | Partial differentiation and multivariate modelling provide preparation for PDE formulation; the PDE syllabus still introduces new methods. |
| MA2508 | MA3515 | 0.2 | Multivariate differentiation may help interpret smooth nonlinear optimization. It does not cover the full linear/integer programming or computational workload. |
| MA2509 | GE2134 | 0.15 | Practice with formal logic may help evaluate arguments. Ethical reasoning, cognitive biases, creativity, group work and writing remain distinct demands. |

These coefficients are conservative editable hypotheses, not estimated grade improvements or measured hours saved. Only direct prior passes count; F/IP/W and same-semester courses do not. Repeated records cannot multiply benefits and indirect chains do not propagate. Forecasts award a benefit only when the source is selected in an earlier semester; the next real step recomputes it from observed passes. Published contact hours and assessment demands are retained. A later course still needs its formal prerequisites. The indexed catalogue confirms that MA3511 needs (MA2508 and MA2503) or MA2001; the mock uses the first branch. MA3512/MA3514 need MA3511 and MA3515 needs MA2503. These checks are recorded separately from the preparation graph in `data/preparation-v5-prerequisites.json`; they do not replace verification of every course rule.

## Source access and workload interpretation

**Full current PDFs could not be downloaded:** CityU returned an access challenge. No challenge page was treated as syllabus text. The deductions use indexed excerpts of official CityU PDFs. MA2509 uses a 2020/21 version and MA3512 a 2023/24 version, so those links are provisional pending a current syllabus. The other sources below use 2025/26 versions. The downloader is provided and stops on an access challenge; locally supplied PDFs can be retained in `sources/preparation-v5/`.

| Course | Evidence and workload interpretation | Source |
| --- | --- | --- |
| MA1300 (2025/26) | Course overview identifies enhanced first calculus/linear algebra, three credits; prerequisite includes specified HKDSE mathematics results. Self-study hours remain unknown. | [Official PDF](https://www.cityu.edu.hk/catalogue/ug/202526/course/MA1300.pdf) |
| MA2508 (2025/26) | CILOs cover partial derivatives, multiple integrals, vector integration and mathematical modelling. Lecture allocation is 39 total hours; two shown tutorial rows list four hours each; the indexed excerpt is incomplete and is not treated as a total workload figure. Self-study hours remain unknown. | [Official PDF](https://www.cityu.edu.hk/catalogue/ug/202526/course/MA2508.pdf) |
| MA2509 (2020/21 historical; current content unverified) | Keyword syllabus includes propositional/predicate logic, sets, relations, counting and graphs. Self-study hours remain unknown. | [Official PDF](https://www.cityu.edu.hk/catalogue/ug/202021/course/MA2509.pdf) |
| MA3512 (2023/24 historical; current content unverified) | CILOs address second-order PDEs, heat/wave/Laplace equations, eigenfunction expansions and modelling. Lectures total 39 hours. Self-study hours remain unknown. | [Official PDF](https://www.cityu.edu.hk/catalogue/ug/202324/course/MA3512.pdf) |
| MA3515 (2025/26) | Linear, integer and nonlinear optimization with mathematical modelling, computational methods and take-home problem work. Lectures total 39 hours; assignment hours unspecified. Self-study hours remain unknown. | [Official PDF](https://www.cityu.edu.hk/catalogue/ug/202526/course/MA3515.pdf) |
| GE2134 (2025/26) | Area 1, three credits, Nil prerequisites/precursors. Rational reasoning, fallacies and creative thinking use workshops, presentations/projects, individual work and a quiz. Average lecture time two hours/week and workshop one hour/week; an individual assignment carries 20% in the indexed excerpt. Other current component weights were not recovered. Self-study hours remain unknown. | [Official PDF](https://www.cityu.edu.hk/catalogue/ug/202526/course/GE2134.pdf) |

GE2134 is not classified as easy simply because its exam weighting is zero: workshops, projects, writing, discussion and a quiz remain work. MA2508 is not classified by credit count alone: its mathematical breadth and published lecture allocation inform a quantitative problem-solving workload description. No source supplies reliable student-specific total effort or assessment-week peaks here; those are not invented.

## Training and held-out model evaluation

Training examples: 222; validation: 24; held-out pool: 28. Best validation epoch: 2. The 222 training examples comprise 206 current-policy examples and 16 older task-replay examples. Training uses supervised assistant-token cross-entropy on synthetic policy labels, not a measured human workload reward.

| Adapter | Exact new-schema answers | GE-cap field | Preparation map | Original nine parameters |
| --- | --- | --- | --- | --- |
| Previous v4 | 16/20 | 20/20 | 16/20 | 20/20 |
| New v5 | 20/20 | 20/20 | 20/20 | 20/20 |

Twenty evaluation state queries were fixed before training; train/validation/test state vectors are disjoint. The prompt states the policy, so this checks faithful conditional policy execution with the supplied rules, not independent discovery of academic causal effects. The old adapter was not trained for the additional output schema; its exact-schema result must be interpreted with the field-level results above. Both adapters use the same prompts and greedy decoding, with independent evaluation prompts batched four at a time.

Actual model calls in three full rollouts: **24/24 accepted**; rejected answers fall back to the visible rule policy. Raw answers are retained in the reports.

## Complete fictional four-year plans

| Profile | Credits | Distribution GE | Elective maths credits | All encoded checks |
| --- | --- | --- | --- | --- |
| [CM2025_NORMAL](output/preparation-v5-transcripts/CM2025_NORMAL.md) | 124 | 4 | 24 | True |
| [CM2025_EARLY_ANALYSIS](output/preparation-v5-transcripts/CM2025_EARLY_ANALYSIS.md) | 124 | 4 | 24 | True |
| [CM2025_ANALYSIS_RESIT](output/preparation-v5-transcripts/CM2025_ANALYSIS_RESIT.md) | 124 | 4 | 21 | True |
| [CM2025_GE_RESIT](output/preparation-v5-transcripts/CM2025_GE_RESIT.md) | 124 | 4 | 21 | True |
| [CM2025_CALCULUS_RESIT](output/preparation-v5-transcripts/CM2025_CALCULUS_RESIT.md) | 124 | 4 | 21 | True |
| [MODEL_CM2025](output/preparation-v5-transcripts/MODEL_CM2025.md) | 124 | 4 | 24 | True |
| [MODEL_CM2025_RESIT](output/preparation-v5-transcripts/MODEL_CM2025_RESIT.md) | 124 | 4 | 21 | True |
| [MODEL_CM2025_CALCULUS_RESIT](output/preparation-v5-transcripts/MODEL_CM2025_CALCULUS_RESIT.md) | 124 | 4 | 21 | True |

## Paired transcript diagnostics

Additional diagnostics passed 8/8. These hold the other Year-2-A attempts fixed and change MA2508 or MA2509 to B/F/IP/W, then recompute the state totals. These are diagnostic probes, separate from the predeclared 20-state holdout.

| Changed course | Grade | Expected preparation map | Exact model response |
| --- | --- | --- | --- |
| MA2508 | B | {"GE2134": 0.15, "MA3512": 0.25, "MA3515": 0.2} | True |
| MA2508 | F | {"GE2134": 0.15, "MA3512": 0.0, "MA3515": 0.0} | True |
| MA2508 | IP | {"GE2134": 0.15, "MA3512": 0.0, "MA3515": 0.0} | True |
| MA2508 | W | {"GE2134": 0.15, "MA3512": 0.0, "MA3515": 0.0} | True |
| MA2509 | B | {"GE2134": 0.15, "MA3512": 0.25, "MA3515": 0.2} | True |
| MA2509 | F | {"GE2134": 0.0, "MA3512": 0.25, "MA3515": 0.2} | True |
| MA2509 | IP | {"GE2134": 0.0, "MA3512": 0.25, "MA3515": 0.2} | True |
| MA2509 | W | {"GE2134": 0.0, "MA3512": 0.25, "MA3515": 0.2} | True |

Automated checks: 119 passed. Tests cover failed passes, GE limits, no same-semester transfer, reward bounds, profit arithmetic, unchanged contact requirements, terminal audits and existing timetable/prerequisite checks.

Prerequisite grades, approval for the 2025 elective pool, offerings in later academic years and actual timetable clashes still require university confirmation. The saved timetable evidence remains a separate source; inferred preparation never creates an eligible class section.

Rerun: `four_year.cmd prepare`, `four_year.cmd evaluate`, `four_year.cmd rollout`, `four_year.cmd report`. Rebuild training examples with `preparation_training.py build`. Previous v4 model and report files are retained.

## Storage check

The model weights, adapters, datasets and reports are on F:. The completed training run used the F: checkpoint directory. A storage audit found no large project model cache on C:, but the default Windows temporary directory was on C:. Both project Python environments now redirect temporary files and model/library/GPU/package caches to `F:/CODEX/cityu-course-helper/.cache/`. An actual temporary file was verified there, including when launching Python from another working directory. The small existing app-managed preview on C: was retained and copied to `output/visualizations/` on F:. Windows paging, global settings and unrelated files were not changed. Details: [storage audit](reports/storage-audit.json).
