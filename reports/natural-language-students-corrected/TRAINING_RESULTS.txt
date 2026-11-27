NATURAL-LANGUAGE QWEN UPDATE
Status: ENABLED
Active adapter: adapters/natural-language-students-corrected
The model receives one ordinary-English user message. No custom system prompt,
teacher edge list, examples or output-schema instructions are supplied to it.
Its deployed output is the interpreted student profile. External software
calculates state-dependent rewards from reviewed course-relation parameters,
selects courses and checks timetable/degree constraints. Raw numeric reward
proposals from the language model are retained for auditing and are not used.

Actual fine tuning
Initial adaptation: 396 training rows, 32 validation rows, three epochs.
Corrective adaptation: 728 training rows, 32 validation rows, 2 epochs.
Selected corrective epoch: 2. Rank-8 QLoRA, frozen NF4 base, BF16 computation.
GPU: NVIDIA GeForce RTX 5090; recorded corrective peak allocated VRAM 8.08 GiB.
The original relation adapter and its active manifest are unchanged.

Deployed natural-language interpretation (raw profile fields)
heldout: 48/48 exact student-profile matches.
familiar_failures: 12/12 exact student-profile matches.
fresh_manual: 6/6 exact student-profile matches.
Paraphrase pairs with the same interpreted student profile: 24/24.

Whole raw answer, including numeric proposals (not the activation criterion)
heldout: 34/48 exact matches.
familiar_failures: 12/12 exact matches.
legacy_relations: 20/20 exact matches.
fresh_manual: 4/6 exact matches.
Paraphrase pairs with the same interpreted data: 21/24.
Paraphrase pairs with both answers fully correct: 16/24.

Interpretation of the groups
heldout: 48 messages from 24 new profile records, disjoint from training and
validation. Course codes, reviewed preparation relations and wording templates
are familiar. These are synthetic policy tests, not independent student outcomes.
familiar_failures: 12 earlier natural-language cases explicitly used in training.
This is a corrective retest and is not pooled with heldout accuracy.
legacy_relations: 20 earlier structured-relation regression checks.
fresh_manual: six new handwritten phrasings; some underlying student profiles
are familiar from correction training. Reported separately.

Why a correction round was needed
The initial candidate matched 24/48 on its development test and 9/12 familiar failures.
Those 48 initial test messages became corrective teaching examples. The final
48 heldout messages were newly generated and frozen before corrective training.

What changed
The update teaches natural-language transcript parsing, P versus F/IP/W,
completed-course preservation, programme/year/semester/cohort extraction,
desired streams, explicit penalty weights, target-course recognition and
preparation reward proposals. The deployed external calculator performs
maximum-direct-link arithmetic and identifies missing planning context.
The local command validates the output, rejects contradicted explicit grades
or unmentioned courses/context, and reads displayed course titles from the
saved sources. Profile scores above use raw neural profile fields, before
these checks. The external numeric calculation is reported separately and
does not turn a wrong raw reward proposal into a model success. The user
should review the interpreted profile before using it to plan registration.

How to use
Double-click run_natural_student_input.cmd in the project folder and paste
your student message. Alternatively, save a longer message in a text file.
Edit student_message.txt in this folder. From F:\CODEX\cityu-course-helper run:
.\run_natural_student_input.cmd "reports\natural-language-students-corrected\student_message.txt"

Saved examples and results
all_natural_test_inputs.txt: exact natural-language test inputs.
natural_test_outputs.txt: exact raw model answers.
after_predictions.json: inputs, targets and raw responses, including failures.
release.json: activation decision.
latest-input/: demonstration with raw output, reviewed profile and readable summary.
