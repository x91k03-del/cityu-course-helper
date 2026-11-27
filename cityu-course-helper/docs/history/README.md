# CityU course helper: local Qwen3-8B prototype

Dependency experiment: `output/pdf/Course_Dependency_Experiment.pdf` describes a controlled before/after study and reports 12 executed source-course/target-course comparisons, grade and repeat controls, a two-source reward interaction and four live model probes. Rewards are decomposed into GE-area base profit, preparation, stream and prerequisite-bridge components. Prerequisite permission is measured separately from numerical utility. Scripts: `dependency_experiment.py build`, `dependency_experiment.py model`, `report_dependency_experiment.py`. Exact inputs, predeclared expectations, raw model answers and CSV effects are in `reports/dependency-experiment/`. The observed values validate configured software behavior, not empirical student workload savings or causal learning effects. The PDF also specifies the next end-to-end schedule experiment and the separate educational validation study.

Desired streams: users can set `desired_stream` in their profile or use `--desired-stream "Artificial Intelligence" --stream-weight 4`. This overrides automatic GE suggestions and scales the selected stream reward. `programme_v6.cmd stream-path --profile data/desired-stream/CS_01.json` returns the remaining course requirements, prerequisite layers, current progress and blocked/provisional conditions. `plan` also includes this path; its normal semester limits remain separate from the academic dependency layers. Model reward responses are checked against exact rules.

Twenty fictional post-core examples (10 CM, 10 CS), random GE and passing grades: `data/desired-stream/profiles.json`. Results, raw model messages, CSV and reproducible seed: `reports/desired-stream/`. Readable PDF: `output/pdf/Desired_Stream_20_Examples.pdf`. Source checks yield 11 academic dependency paths, 4 needing current-rule confirmation, and 5 blocked finance routes. Raw model rewards passed 0/10 CM and 10/10 CS examples; policy fallback was required for the CM examples. Layers are not semesters or official registration approvals. Final projects and internships are not included in the completed taught-core sets.

Finance route correction: GE2260 and CB3410 have mutual exclusion evidence, while EF3320 requires CB3410 or FB3410. EF4821 requires EF4820, which in turn requires EF3520 and EF4321. Those bridge courses are outside the current CM document allowlist. A finance GE can justify a strong interest preference, but it does not establish an achievable Financial Mathematics stream for that profile. The planner now returns a finance-route audit and blocks known missing EF prerequisites even in reviewed option fixtures. The four-year mock also retains those prerequisites instead of treating EF electives as having no prerequisites.

Typed links and sources: `data/deep_course_relations.json`. Verified prerequisites, advisory precursors, confirmed exclusions, unresolved source conflicts and inferred preparation links are separate. CS4335's data-structure preparation is a published precursor, not a compulsory prerequisite. GE2260's 2024/25 PDF and catalogue page disagree on exclusions; the GE1202 combination is marked for confirmation rather than declared compatible. Eight new relationship checks plus the existing suite pass (84 checks total). No additional neural training was performed for these source and policy corrections.

GE pathways and lambda comparisons: `output/pdf/GE_Pathways_and_Lambda_Comparison.pdf`. Passed GE2260 recommends the CM Financial Mathematics stream; passed GE2340 recommends the CS AI stream. These are advisory 3x reward preferences, with smaller source-supported prerequisite-bridge rewards. GE never earns a stream slot or bypasses programme/minor restrictions. CS is excluded from the AI minor; the CM AI-minor-interest example remains blocked by the current CM document allowlist.

The programme planner now forwards the three original proposal penalties using `--lambda-b`, `--lambda-d` and `--lambda-w` (background mismatch, difficulty and workload). Per-course scores are editable synthetic estimates; they are fixed across each comparison. For example:

```powershell
./programme_v6.cmd plan --profile data/ge-pathway-lambda/CM_Y2_FINANCE_GE.json --assume-component-linkage --lambda-b 1 --lambda-d 20 --lambda-w 1
```

Inputs and comparisons are in `data/ge-pathway-lambda/` and `reports/ge-pathway-lambda/`. Controlled comparisons use explicitly synthetic conflict times/scores; saved-timetable comparisons retain hypothetical component linkage and weeks. The existing v6 model failed both new GE-profile stream-count tests; exact policy validation/fallback supplies the correct zero completed stream slots. This update changes the planning policy and tests; it does not retrain neural weights.

Current programme model: `adapters/cm-cs-programme-v6`. See the CM and CS update below and `reports/programme-v6/release.json`. Earlier v5 examples are historical; their outside-document free electives are rejected by the new policy.

Historical v5: [GE cap and preparation-chain fine-tuning report](PREPARATION_V5_REPORT.md). The separate `adapters/bscm-preparation-v5` controller adds a hard limit of one distributional GE attempt per semester and bounded preparation benefits from prior passes. Compulsory language/development GE is excluded from the cap. Source limitations, indexed official PDF versions, model results and full fictional transcripts are disclosed in the report. Run `four_year.cmd rollout` for actual model-assisted plans; `four_year.cmd prepare` is the deterministic rule baseline. `four_year.cmd evaluate` and `four_year.cmd report` now use the v5 protocol.

Previous: [2025-entry four-year Markov-profit simulation](FOUR_YEAR_MARKOV_REPORT.md), including the historical v4 transcripts and metrics. Normal production overload applies only in Year 4 above 12 credits; earlier course-count-penalty experiments remain available as historical modes.

Previous branch: [profit and overload experiments](PROFIT_OBJECTIVE_UPDATE.md), using `adapters/bscm-profit-v3`. Its course-count overload mode is retained for historical comparison. The new `adapters/bscm-markov-v4` controller generates state-dependent reward parameters for the four-year curriculum solver; Year 4 may use fewer than five courses.

Latest additions: [CM-only MA schedules and requirements](MA_CM_UPDATE.md), [Computing Mathematics support](BSCM_UPDATE.md), [Semester A GE timetable support](GE_TIMETABLE_UPDATE.md), and the [complete captured GE timetable](GE_SEMA_TIMETABLE.md). Exact meeting times and MA requirements are read from the dated local snapshots; the timetable adapters can also be tested separately.

The [five-course planning update](FIVE_COURSE_UPDATE.md) adds a five-course minimum, year-focused maths core weights and failure-correction training. The [historical fictional transcript test](CM_PROFILE_TEST_REPORT.md) passed every check in only 2 of 12 catalogue-supplied model plans. Its failed profiles are now training examples; new transcript groups provide the later holdout evaluation.

The historical planning-v2 model refused all four feasible five-course holdout cases. Its course-admission decisions improved from 5/8 to 8/8, but final schedules still require the constraint solver. The latest Markov controller is evaluated on reward-parameter rules rather than unconstrained course generation.

This project implements the public-data bootstrap stage of the supplied proposal. It uses the user-selected **Qwen/Qwen3-8B**, a local LoRA adapter, and a mixed-integer scheduler. The training run, weights and measured results are recorded in `reports/` and `adapters/bootstrap/`.

**The initial adapter is experimental. Its numerical targets are synthetic rubric estimates, not reviewed CityU workload ratings.** It must not be presented as a validated course recommender. The repository also contains supervised course-fact extraction examples from official sources.

## Use the installed model

From PowerShell:

```powershell
cd F:\CODEX\cityu-course-helper
.\run.ps1 -Action score -Course CS3334
.\run.ps1 -Action demo
```

The first command loads the base weights and trained adapter on the RTX 5090 and prints a course score with a source link. It uses a synthetic year-two Computer Science profile by default. The second runs an explicitly synthetic five-course policy example without loading the LLM.

Use a personal profile without uploading it:

```powershell
.\.venv\Scripts\python.exe inference.py score --course CS3334 --profile data/my_profile.json
```

Profile format:

```json
{"major":"Computer Science","year":2,"interests":["AI","data"],"completed_courses":["CS1302"]}
```

No accounts, paid APIs, transcript uploads or external inference services are used. GPU memory is released when the command exits. The adapter is separate from the original model; load both for inference.

## What was collected

- 77 parsed courses from the 2026/27 public catalogue: 37 CS and 40 GE. Original syllabus PDFs for all 80 selected candidates are retained locally; three variable-credit seminar courses are excluded from the normalized fixed-credit prototype.
- Titles, credit units, course aims, prerequisite/precursor/exclusion wording and assessment percentages, with original URLs, timestamps and SHA-256 hashes.
- One legacy syllabus has no automatically parsed assessment percentage; this remains null. Null means unknown, not zero.
- The catalogue year and a syllabus's effective term do not establish that the course is offered in Semester A. Real course offerings, sections and meetings must come from the appropriate AIMS term.

`data/courses.jsonl` contains the normalized records. `data/raw/syllabi/` contains source files. `sources/README.md` records source and reuse checks. No UIUC/CMU evaluation rows were used: their reuse permission was not established. Cross-university matching remains pending those authorized data.

## Training and evaluation

- Immutable official model revision: recorded in `sources/model.json`.
- BF16 base weights, frozen; rank-8 LoRA on all linear layers; dropout 0.05, learning rate 0.0001, gradient accumulation 4, two epochs. Only assistant answer tokens contribute to loss. No silent truncation of training targets is allowed.
- 434 training, 49 validation and 56 test examples. Courses with identical normalized aims stay in the same split. Test examples do not select the checkpoint; the best validation epoch does.
- Tasks: copying supported course facts into structured JSON and predicting background mismatch, difficulty and workload from a deliberately simple synthetic rubric. All three scores range from 0 to 1; higher means greater mismatch/difficulty/workload.
- The rubric uses course level, student year/major, credits, assessment percentage and project mentions. It does **not** establish actual weekly hours, perceived difficulty, interest satisfaction or real student suitability.
- `reports/training.json`: run configuration, training losses, validation losses, selected epoch, duration and peak GPU allocation.
- `reports/evaluation.json`: base versus tuned typed output-schema success and MSE against synthetic targets. Exact typed extractions and factual matches after numeric-string normalization are reported separately, so formatting gains are not counted as factual gains. `reports/predictions.jsonl` preserves every tested response. This is not real workload MSE. `summarize_predictions.py` recomputes these metrics from saved responses without another GPU run.
- `reports/method_comparison.json`: pure base-LLM scheduling versus tuned scoring + MILP on identical synthetic profiles and simulated constraints. Human/senior-student rankings and real-student outcomes are not available.
- `reports/data_audit.json`: source hashes, split separation and assistant-only loss mask checks. `reports/scheduler_tests.json`: scheduler checks, including exhaustive-search comparisons.

Re-run the installed checks:

```powershell
.\run.ps1 -Action test
.\run.ps1 -Action evaluate
.\run.ps1 -Action baseline
.\.venv\Scripts\python.exe compare_methods.py
```

Re-training overwrites `adapters/bootstrap/` and its reports:

```powershell
.\run.ps1 -Action train
```

## Connect real semester data

The optimizer selects **complete section bundles**: one option must include all required lectures, tutorials and labs for that selection. Do not supply a lecture alone if a tutorial/lab is required. A course can have multiple alternative options; at most one is selected.

Start with the schema in `data/synthetic_schedule_demo.json`, replacing its simulated records with verified term data. Each option needs:

- `option_id`, `course_code`, exact `term`, numeric `credits`.
- `rules_reviewed: true` only after checking the actual catalogue rules, programme restrictions, permission requirements and eligibility for this student. An empty prerequisite list is an affirmative reviewed statement, not a default for unknown requirements.
- `prerequisites_all` (all must have been completed), `prerequisites_any_groups` (at least one completed course per group), `corequisites` (completed or selected together), and `exclusive_courses` (cannot be previously completed or jointly selected).
- `timetable_verified: true` only with term-specific evidence; `meetings` with day 1–7, start/end minute of the day, and an explicit list of teaching weeks. Registration restrictions not represented by these fields must be resolved in the eligibility review.
- Non-negative objective weights, required courses, credit limits and verified completed courses at the problem level.

Use the trained model to score the courses and pass those scores to the solver:

```powershell
.\.venv\Scripts\python.exe inference.py recommend --profile data/my_profile.json --problem data/my_verified_term.json
```

Missing timetable/rule evidence excludes the option. Missing required courses or incompatible constraints yield an explicit infeasible result. If reliable assessment timing exists, add `workload_by_week` to every option and `weekly_workload_caps` to the problem. Without those data, the system does not claim to verify weekly workload balance. The optimizer guarantees only its encoded constraints; it cannot guarantee seats, score accuracy, complete university eligibility, or registration.

## Complete the proposal's reviewed-label stage

`data/label_review.csv` is an empty review worksheet for the collected courses and synthetic profiles. Obtain authorized reviews or measurements of mismatch, difficulty and workload; record reviewer, evidence and date. Keep genuine labels distinct from bootstrap estimates. A future supervised run should replace the bootstrap labels and rubric instructions, retain the existing course-group split, select settings on validation data and report held-out MSE plus student/senior-student rankings. Do not relabel synthetic scores as human reviews.

Access the current Master Class Schedule through the CityU Portal/AIMS and export normalized term data locally. No credentials have been requested or stored. Optional transcript text extraction is available with:

```powershell
.\.venv\Scripts\python.exe transcript.py C:\path\to\transcript.pdf
```

This reads text locally and prints candidate course codes. It does not save the transcript, perform OCR or infer that every listed course was passed. Confirm grades/completion before adding codes to `completed_courses`.

## Environment

This project's Python environments redirect temporary files, Hugging Face, Torch, CUDA, pip, uv and Python bytecode caches to `F:/CODEX/cityu-course-helper/.cache/`. The environment-local startup hook applies to commands launched from another working directory as well. Model weights, checkpoints and reports are on F:. See `reports/storage-audit.json` for the storage check; no Windows-wide environment or paging settings were changed.

The project has a separate `.venv`. It reuses the existing CUDA Torch runtime in `F:\CODEX\sr-models\envs\dinov3\Lib\site-packages` through a read-only search-path entry; that existing environment was not changed. Keep that directory if you use this installation. New training packages are installed only in this project's environment.

For a clean installation on another compatible NVIDIA Windows machine, create a Python 3.11 environment, install CUDA-enabled Torch 2.7.1 and matching torchvision from the official CUDA 12.8 wheel index, then install `requirements.txt`. A default CPU Torch wheel cannot train this model on the GPU. The installed project's runtime versions are captured in its reports. Weight downloads use immutable model revisions and verified SHA-256 hashes; source refresh is separate from offline training/inference.

## CM and CS programme update (21 November 2026)

### Current flexible-load and terminal-degree policy (24 November 2026)

The current search aims for a high-reward path without requiring proof of the
global optimum. A complete feasible result still requires at least 122 credits
and the other encoded graduation checks. If the hard problem cannot be solved,
the planner returns its best found valid candidate for review, marked as below
the graduation target, instead of discarding the path.

The fallback ranking is discounted academic reward minus
`terminal_credit_shortfall_penalty * max(0, 122 - final_credits)`; the default
penalty is 1,000,000 per missing credit. This penalty does not replace the hard
graduation check. Capacity-aware and credit-progress beams explore different
paths and retain the better penalised candidate. The result exposes the reward,
penalty, shortfall, path validity and graduation status separately.

The latest run reaches the current source-pool ceiling of 70 distinct credits,
with 52 missing credits and a 52,000,000 penalty. Evidence is in
`reports/penalised-chain/`; prior diagnostics remain preserved.

The fixed five-course minimum is removed. Production semester problems default
to zero minimum courses and retain six maximum courses and 18 maximum credits.
Old profile `course_min` values do not silently restore the old policy; an
explicit new `semester_min_courses` preference is separate. The complete
eight-semester CM chain is accepted only at 122 credits or more, also satisfying
the user's 121-credit minimum, and with all encoded GE, core, project, elective
and selected-stream requirements met. Terminal acceptance is a hard constraint,
not a shortfall penalty that can be traded against profit.

The user authorised repeating the saved Semester A/B timetables for this
simulation. The snapshots remain labelled 202609 and 202702; no real future
offering is claimed and no course is credited twice. `terminal_markov.py`
implements whole-chain search with terminal constraints. A source-coverage
failure prevents accepting a complete chain; partial rollouts are diagnostics.

EF3320's Semester B section CA1, CRN 11425, is valid for the non-CB CM profile:
its restriction is **not for College CB**, not an ONLY FOR CM requirement.
The old importer wrongly discarded it. Section C01 remains restricted to CB.
Semester-A `EF3320:10000` remains invalid: its term and CRN do not match the PDF.
Shared general sections now have their explicit restrictions evaluated; known
CM-specific sections remain preferred when compatible. Source files are
assessed for each document-allowed programme regardless of which folder holds
the PDF. Unknown restriction fields still fail closed.

The new timetable checkpoint is selected in `data/active_grounded_adapter.json`.
Training, source analysis, credit-boundary tests and the repeating-A/B rollout
are retained in `reports/degree-chain-policy/`. Earlier five-course benchmarks
and reports remain historical evidence; their feasibility labels must not be
reinterpreted as results under this new policy.

### GPT course-relation teacher

`data/active_preparation_graph.json` now selects the GPT-authored direct
preparation policy in `data/gpt-course-relations/reward_graph.json`. Its 26
relationships are content-based hypotheses, not measured correlations, saved
hours or prerequisite substitutions. Each target receives only the strongest
direct prior-pass benefit, capped at 0.35; duplicates, failed/IP/W records,
recursive chains and same-semester study do not earn extra preparation credit.
Introductory vocabulary typically earns 0.10, moderate transferable preparation
0.15-0.20 and stronger topic foundations 0.25-0.30. These are editable utility
assumptions, not empirically fitted coefficients.

The GPT teacher is the assistant in this session. The separate relation adapter
is distilled with supervised examples; its activation is recorded in
`data/active_relation_adapter.json`. Timetable and general-model checkpoints
retain their separate roles. The reward calculator uses the validated policy
and exposes `preparation_by_course` in its profit breakdown.

Examples, controlled selection changes, source references and evaluation:
`reports/gpt-course-relations/README.md` and `reward_examples.json`.

```powershell
.\.venv\Scripts\python.exe gpt_course_teacher.py infer --profile data/cm-finance-background/examples/no_finance.json --course CS4487
```

### Minimum-load diagnosis and Markov planning (24 November 2026)

The subsequent source-grounded fine-tune teaches exact saved-semester
availability and an extra EF cost of `1.5 * lambda_background` without finance
study. Passed or declared finance study removes that extra cost; failed or
in-progress finance study does not. The cost is unrelated to a missing formal
prerequisite. It is included once in the student-cost total and shown separately
as `ef_finance_mismatch_penalty` in the profit breakdown.

The active source snapshot is selected by `data/active_timetable_evidence.json`.
Production options must match a hashed PDF in the supplied MA/CS folders, term
and major-compatible section. Opposite semesters and future years cannot reuse
the source time. Separate GE folders are outside this literal MA/CS-only run.
The preceding 127-credit output is preserved as curriculum-only evidence; it
does not pass this stronger timetable requirement. The strict entering Year-1
source pool has only MA1300 and MA2509 and cannot form a five-course semester.

```powershell
.\.venv\Scripts\python.exe grounded_model.py degree --profile data/markov-repair/year1_CM.json --output reports/timetable-grounded/user_degree.json
.\.venv\Scripts\python.exe grounded_model.py assess --profile data/cm-finance-background/examples/no_finance.json --course EF3320 --output reports/timetable-grounded/user_EF.json
```

For `assess`, set the profile's `term` to the semester being checked (EF3320's
saved snapshot is Semester B, `202702`). The selected grounded checkpoint and
its validation status are recorded in `data/active_grounded_adapter.json` when
accepted. Both fine-tuning trials and their unchanged evaluation prompts remain
in `reports/timetable-grounded*` and `adapters/timetable-grounded*`. The corrective
trial covers finance input types, penalty scaling and over-refusal of feasible
plans. Raw model outputs are always retained separately from policy fallback.

The short timetables in the saved blind comparison are raw Qwen proposals.
They bypassed the constrained planner and violate its five-course minimum;
they are not feasible optima. Historical raw answers and reports are preserved.
`programme_v6.py plan` now defaults to a deterministic Markov decision search,
without invoking MILP. Its state contains passed courses and the currently
selected section bundles. Adding a course earns the change in net profit;
STOP is unavailable below five credit-bearing courses in Years 1-3. A sixth
course is chosen when its marginal reward, after overload, improves the result.
Year 4 has no minimum. Programme membership, prerequisites (with the authorised
CM EF/CS waiver), exclusions, corequisites, meetings, credits and the one-GE
limit remain binding. Exact searches report optimality; bounded searches only
report feasibility or search exhaustion. The old MILP stays as a reference.

Pass `--proposal saved_qwen_answer.json` to the plan command to validate a
neural timetable before using it. Rejected proposals trigger an explicitly
labelled planner fallback; this does not count as raw-model success. No neural
weights were changed in this repair.

```powershell
.\.venv\Scripts\python.exe run_markov_repair.py
.\.venv\Scripts\python.exe -m unittest test_markov_planner test_programme_v6 test_year_specific_overload test_cm_background_policy
```

The first command rechecks six historical proposals and simulates all eight
semesters for the entering Year-1 CM profile in
`data/markov-repair/year1_CM.json`. Results, hypothetical full transcript and
independent encoded-requirement audit are in `reports/markov-repair/`.
Future course availability and actual full-degree meeting compatibility are
unverified; this is a curriculum simulation, not registration certification.

### CM finance background and EF/CS prerequisite planning

Following the user's CM-specific correction, document-listed EF and CS courses
default to an assumed prerequisite waiver for advisory planning. Missing those
formal prerequisite passes adds no extra penalty and no longer expands the path
through otherwise forbidden EF/CB/FB bridge courses. Source requirements are
preserved, and `registration_verified` remains false. Programme membership,
exclusions, section restrictions, semester, actual meetings and credit rules
continue to apply. The saved EF timetable snapshots currently contain no
matching CM sections; the waiver does not create an offered section.

Set `"cm_ef_cs_prerequisite_waiver": false` in a profile for the original strict
prerequisite check. The waiver applies only to CM, and only to EF/CS candidates
already allowed by its document. Mathematics course prerequisites and the CS
programme's prerequisites remain enforced.

Finance preparation uses passed GE1202/GE2260, passed EF courses, the listed
finance MA/CB/FB courses, or an explicit study declaration. For example:

```json
{"programme":"CM", "year":2, "term":"202702",
 "completed_courses":["MA1301","MA2503","MA2510"],
 "finance_background":{"studied":true,"topics":["bonds","personal finance"]},
 "desired_stream":"Financial Mathematics"}
```

Finance background mismatch is an editable synthetic rubric: no evidence 0.45,
introductory study 0.15, advanced passed study 0.05. Failed, withdrawn and
in-progress finance records do not count. Finance evidence can infer a finance
preference, but an explicit desired stream still wins. Missing formal EF/CS
prerequisites are not used as a difficulty-depth feature in waived CM mode.

```powershell
./programme_v6.cmd model-background --profile data/cm-finance-background/examples/finance_GE.json --course EF3320
./programme_v6.cmd stream-path --profile data/cm-finance-background/examples/finance_GE.json
```

The new fine-tuning protocol and its separate before/after results are in
`reports/cm-finance-background/`. The current active checkpoint is selected by
`data/active_programme_adapter.json`, with exact policy validation and fallback.
The finance-background checkpoint completed two training epochs and selected
epoch 1 by validation loss. New synthetic policy queries improved from 0/20 to
18/20 exact, six historical regression checks remained 5/6, and six default-input
diagnostics passed 6/6. Two raw waiver-applicability errors remain guard-rejected;
fallback does not count as model accuracy. The previous adapter is preserved.
Matched synthetic examples in `background_examples.json` isolate background
effects; their single-course timetable is a test fixture, not a real registration
recommendation. The policy is a user-authorised assumption, not independently
verified university waiver approval.

Previous combined checkpoint: `adapters/cm-cs-programme-v6`. Training: NF4 frozen base with BF16 compute and rank-8 QLoRA; init adapter: `bscm-preparation-v5`. The 15 preselected source-conditioned test queries passed 14 after training versus 3 before, with the same quantized base in both tests. These tests use supplied source context, not unseen-document recall. Raw results: `reports/programme-v6/predictions.json`.

Imported 86 course/term/programme records and 128 explicitly matching-major sections. 7 files with unrecognized meeting times are quarantined. MA Semester B is 202702; Semester A is 202609. Duplicate PDF copies are deduplicated by hash.

CM course candidates must occur in `GE_SEMA/MA/CMcourses.pdf`, or the captured GE list. CS candidates must occur in `GE_SEMA/CS/programme discription/Majors.pdf`, or the captured GE list. Document membership is not registration approval. The CM PDF is historical 2022/23; the CS major page is 2026/27 while the suggested CS plan is for cohort 2025. These versions are retained separately.

A single selected stream receives 2 utility units per new distinct slot and a one-time 6-unit completion bonus. The semester optimizer accounts for joint selections exactly, so two alternative courses cannot collect the same slot/completion reward twice. A stream preference never bypasses course restrictions or prerequisites. University stream declaration remains optional. The special CS ACT/JS1070 route is recorded, but is not auto-assigned without admission-route evidence.

70 software checks passed. The document-filtered CM mock earns 124 credits, meets the encoded graduation requirements, and completes one stream. The example CS plans are semester experiments, not full-degree graduation certification. The CM Semester A example is explicitly infeasible under its five-course minimum.

```powershell
./programme_v6.cmd lookup --programme CM --term 202702 --course MA3511
./programme_v6.cmd lookup --programme CS --term 202702 --course CS3334
./programme_v6.cmd model-stream --profile data/programme-v6/example_CS.json
./programme_v6.cmd plan --profile data/programme-v6/example_CS.json --assume-component-linkage
```

The final command explicitly enables experimental section pairing and assumed weeks. Without that flag, unknown component linkage fails closed. Exact course facts remain available without loading the model. Evidence, caveats, examples and model metrics: `reports/programme-v6/release.json`. The new task activation is `data/active_programme_adapter.json`; the previous v5 profit controller is retained separately.

A corrective trial taught the observed completed-stream failure with balanced source-task replay. It passed 14/15 post-correction diagnostic queries, fixing the original error but introducing a different stream error. Its replay validation loss worsened from 0.00462 to 0.00921, so the initial v6 checkpoint remains active. The trial is preserved separately as `adapters/cm-cs-programme-v6-correction-trial`. The diagnostic is not independent: the original failed case was used for teaching. All raw stream outputs still require exact policy validation and fallback. See `reports/programme-v6/correction_protocol.json` and `correction_diagnostic.json`.
