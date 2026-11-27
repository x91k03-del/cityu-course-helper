NATURAL-LANGUAGE STUDENT INPUT FOR QWEN

Purpose
Give Qwen a student message in ordinary English, rather than a JSON request or
a hand-written system prompt. Include course codes and grades, and the programme,
study year, semester, entry cohort and desired stream when known.

Example
I'm a second-year Computing Mathematics student at CityUHK. I entered in 2025
and am planning semester A. I passed CS1302 with B, MA1300 with B+ and GE2260
Introduction to Finance with A-. I want the Financial Mathematics stream.
How does my completed study prepare me for EF3320?

How to use
Edit student_message.txt in this folder, then run from the project folder:

  .\run_natural_student_input.cmd "reports\natural-language-students\student_message.txt"

The command loads the validated natural-language adapter and passes ONE user
message to Qwen. It supplies no custom system message, teacher edge list,
few-shot example or output-format instruction during inference.

Results appear in reports/natural-language-students/latest-input:
  input.txt                   Your message
  raw_output.txt              Uncorrected Qwen response
  profile_and_rewards.json    Validated profile and preparation reward
  planner_profile.json        Profile for the existing external planning tools
  response.txt                Readable summary, with titles from saved sources
  validation.json             Acceptance result, without a silent fallback

The model extracts transcript facts, preferences and advisory preparation rewards.
External software handles course selection, timetable checks and the degree audit.
Missing semester/cohort information is requested before planning. Course codes
and explicit grades are checked, but the input transcript still requires review.
Course titles in the readable summary come from saved source data.

Training and evaluation
  protocol.json               Split sizes, parent checkpoint and test scope
  training.json               Actual training record and selected epoch
  after_evaluation.json       Heldout, familiar-correction and legacy results
  after_predictions.json      Exact inputs and raw post-training outputs
  release.json                Activation decision

The prior checkpoint and legacy active relation interface are preserved.
The new adapter is selected through data/active_natural_language_adapter.json
only when its release checks pass. A failing raw answer is saved and rejected.

The teaching data are synthetic examples of the existing configured policy.
They do not establish measured workload, actual registration eligibility or
reliable handling of every possible transcript format or language.
