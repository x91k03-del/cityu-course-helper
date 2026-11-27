# CM MA timetable and requirement report

The 17 supplied AIMS course PDFs were imported locally for Semester A 2026/27 (term 202609). The source pages were captured on 15 November 2026. This snapshot does not establish current registration availability.

**Model-memory limitation:** the fine-tuned adapter still gives incorrect ungrounded course facts. The default helper answers schedule and requirement questions from exact saved records. Fine-tuning completion is not proof of factual memorization.

The import selected **16 sections / 20 meetings across 11 courses** and excluded 52 section records. Every selected section explicitly includes the exact major token CM. Shared lists containing CM are retained, alongside their programme/cohort conditions. No other-major-only, not-for-CM, minor-only or unspecified section clocks are included in the new MA training targets.

## Captured CM schedules

Each row is a section/component record. Multiple tutorial options are alternatives; valid lecture/tutorial bundles have not been verified. Date ranges do not establish teaching weeks or holiday exceptions.

| Course | CRN / section | Meetings | Date range(s) | Additional restrictions |
| --- | --- | --- | --- | --- |
| MA1300 | 12244 / C01 | Fri 12:00-13:50 YEUNG LT-18; Wed 17:00-18:50 BOC R4057 | 2026-08-31 to 2026-11-28 | Major CM listed; other individual eligibility not verified |
| MA1300 | 12245 / T01 | Mon 18:00-18:50 YEUNG P4302 | 2026-08-31 to 2026-11-28 | Major CM listed; other individual eligibility not verified |
| MA1300 | 12246 / T02 | Tue 18:00-18:50 YEUNG B5-211 | 2026-08-31 to 2026-11-28 | Major CM listed; other individual eligibility not verified |
| MA1502 | 12609 / CB1 | Wed 09:00-11:50 YEUNG LT-18 | 2026-08-31 to 2026-11-28 | only for programme: BSCSIU4; only for cohort: 2026 |
| MA2503 | 13697 / CA1 | Thu 16:00-18:50 YEUNG LT-3 | 2026-08-31 to 2026-11-28 | only for programme: BSCSIU2, BSCSIU3, BSCSIU4 |
| MA2508 | 13701 / CA1 | Sat 11:00-12:50 YEUNG LT-3; Tue 16:00-16:50 YEUNG LT-11 | 2026-08-31 to 2026-12-05 | only for programme: BSCCBU4, BSCSIU2, BSCSIU3, BSCSIU4 |
| MA2508 | 13704 / TA1 | Tue 15:00-15:50 YEUNG LT-11 | 2026-08-31 to 2026-11-28 | only for programme: BSCCBU4, BSCSIU2, BSCSIU3, BSCSIU4 |
| MA2509 | 12041 / CA1 | Mon 10:00-10:50 YEUNG LT-15; Wed 10:00-11:50 YEUNG LT-15 | 2026-08-31 to 2026-11-28 | only for programme: BDSI, BSCSIU2, BSCSIU3, BSCSIU4 |
| MA2509 | 12042 / TA1 | Mon 11:00-11:50 YEUNG LT-15 | 2026-08-31 to 2026-11-28 | only for programme: BDSI, BSCSIU2, BSCSIU3, BSCSIU4 |
| MA3512 | 10430 / CA1 | Fri 15:00-17:50 YEUNG G4702 | 2026-08-31 to 2026-11-28 | only for programme: BSCSIU2, BSCSIU3, BSCSIU4 |
| MA3518 | 10613 / CA1 | Tue 16:00-18:50 LI 4307 | 2026-08-31 to 2026-11-28 | only for programme: BSCSIU2, BSCSIU3, BSCSIU4, DLLBBSC |
| MA3521 | 11880 / CA1 | Mon 09:00-11:50 YEUNG LT-13 | 2026-08-31 to 2026-11-28 | only for programme: BSCSIU2, BSCSIU3, BSCSIU4, DLLBBSC |
| MA3525 | 11213 / CA1 | Thu 13:00-14:50 LI 1614; Tue 14:00-14:50 LI 1614 | 2026-08-31 to 2026-11-28 | only for programme: BSCCBU4, BSCSIU2, BSCSIU3, BSCSIU4, DBSCBSC1, DLLBBSC |
| MA3525 | 11219 / TA1 | Tue 15:00-15:50 LI 1614 | 2026-08-31 to 2026-11-28 | only for programme: BSCCBU4, BSCSIU2, BSCSIU3, BSCSIU4, DBSCBSC1, DLLBBSC |
| MA4542 | 11513 / CA1 | Thu 15:00-17:50 YEUNG P4701 | 2026-08-31 to 2026-11-28 | only for programme: BSCCBU4, BSCSIU2, BSCSIU3, BSCSIU4 |
| MA4545 | 11882 / CA1 | Wed 12:00-14:50 YEUNG P4703 | 2026-08-31 to 2026-11-28 | only for programme: BSCSIU2, BSCSIU3, BSCSIU4 |

No explicitly CM-listed timetable is present in these six saved pages: MA1508, MA2001, MA2158, MA2172, MA2185, MA2510. Their rules remain queryable. This does not establish a permanent ban or the absence of another authorized offering.

## Prerequisites/precursors and exclusive courses

The source uses a combined **Pre-requisites/precursors** heading. It does not distinguish strict prerequisites from precursors. The helper preserves the wording and Boolean logic without claiming that distinction is verified. An exclusive course is a separate registration condition; passing a preparation expression does not override it.

| Course | Source requirement wording | Exclusive courses | CM sections |
| --- | --- | --- | --- |
| [MA1300](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA1300.pdf) | Nil | MA1006, MA1400, MA1508 | C01, T01, T02 |
| [MA1502](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA1502.pdf) | Nil | MA2508 | CB1 |
| [MA1508](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA1508.pdf) | Nil | MA1200, MA1201, MA1300, MA1301, MA1400, MA1401 | None captured |
| [MA2001](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA2001.pdf) | MA1201 or MA1301 | MA2158 | None captured |
| [MA2158](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA2158.pdf) | MA1201 or MA1301 | MA2001, MA2170 | None captured |
| [MA2172](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA2172.pdf) | Nil | MA2177, MA2506, MA2510 | None captured |
| [MA2185](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA2185.pdf) | Nil | MA2144, MA2504, MA2509 | None captured |
| [MA2503](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA2503.pdf) | MA1201 or MA1301 | MA1503 | CA1 |
| [MA2508](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA2508.pdf) | MA1201 or MA1301 or (MA1503 and MA1508) | GE1359, MA1502 | CA1, TA1 |
| [MA2509](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA2509.pdf) | Nil | MA2144, MA2185, MA2504 | CA1, TA1 |
| [MA2510](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA2510.pdf) | MA1201 or MA1301 or (MA1503 and MA1508) | MA2172, MA2177, MA2506 | None captured |
| [MA3512](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA3512.pdf) | MA3511 | Nil | CA1 |
| [MA3518](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA3518.pdf) | MA2506 or MA2510 | Nil | CA1 |
| [MA3521](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA3521.pdf) | MA2506 or MA2510 | Nil | CA1 |
| [MA3525](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA3525.pdf) | MA1503 or MA2503 | Nil | CA1, TA1 |
| [MA4542](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA4542.pdf) | MA2508 and (MA3526 or MA3524) | Nil | CA1 |
| [MA4545](F:/CODEX/cityu-course-helper/GE_SEMA/MA/MA4545.pdf) | MA3511 | Nil | CA1 |

MA2508/MA2510 require **MA1201 OR MA1301 OR (MA1503 AND MA1508)**. MA4542 requires **MA2508 AND (MA3526 OR MA3524)**. The local rule evaluator does not flatten these into a single OR list. Missing completion data remain unknown, and a BSCM major or year never supplies a passed-course history. A Nil preparation expression is satisfied without completed courses, but exclusive-course conflicts still remain unknown without a completion history.

## Training

Dataset sizes: 331 training, 39 validation and 137 test examples. The new MA facts are mixed with 160 prior GE/BSCM examples. The previous datasets and adapters remain intact. All captured facts are intentionally taught; the evaluation tests learned-fact paraphrases and evidence extraction, not unseen-fact generalization.

Completed 2 continued-training epochs on Qwen3-8B with rank-8 LoRA, initialized from `adapters/bscm-timetable`. The selected checkpoint is epoch 2, saved separately as `adapters/bscm-ma-timetable`. Training took 4.7 minutes; peak GPU allocation was 17.52 GiB.

| Epoch | Training loss | Validation loss |
| --- | --- | --- |
| 1 | 0.1909 | 0.3346 |
| 2 | 0.0636 | 0.1866 |

## Raw model evaluation

Prior = the existing GE/BSCM timetable adapter. New = the MA-continued adapter. A pass requires exact decoded JSON equality, without fixing answers or substituting the lookup. Recall prompts omit source context; grounded prompts supply it. Reworded evaluation prompts do not prove that source facts were unseen.

| Task | Prior | New |
| --- | --- | --- |
| ge_grounded_replay | 2/2 | 2/2 |
| grounded_rules | 2/2 | 2/2 |
| grounded_schedule | 2/4 | 4/4 |
| guard | 0/6 | 1/6 |
| requirement_check | 3/10 | 10/10 |
| rules_recall | 0/4 | 0/4 |
| schedule_recall | 0/4 | 0/4 |

The new raw model failed 13 exact-output checks. Exact source lookup and deterministic rule evaluation are the deployed path for schedule/requirement questions. Unchecked model memory is diagnostic, not an authority for registration planning. Full responses and fixed test IDs are saved in `predictions.json` and `evaluation_plan.json`.

For example, its ungrounded MA2508 requirement answer was `MA1201 or MA1301`, while the source requires `MA1201 or MA1301 or (MA1503 and MA1508)`. The source lookup retains the complete expression.

31 prior-adapter results were reused after matching the unchanged prompt fingerprints, expected targets and adapter weights hash. The added Nil/unknown-history case and all final-adapter checks were generated fresh.

Automated parser/rule regression checks: **42 passed**, recorded in `reports/ma-timetable/validation.json`. These check imported evidence and software behavior; they are separate from generated model answers.

## Reproducible example checks

The local source/rule examples passed **11/11**. These are software/source checks, not raw-model accuracy. Commands and expected/actual results are in `reports/ma-timetable/test_examples.json`.

| Example | Expected result | Result |
| --- | --- | --- |
| Is MA1503 alone sufficient for the MA2508 preparation expression? | `false` | PASS |
| Does the MA1503 + MA1508 branch satisfy MA2508? | `true` | PASS |
| Does MA1201 satisfy a MA2508 preparation branch? | `true` | PASS |
| Is MA3526 alone sufficient for MA4542? | `false` | PASS |
| Do MA2508 and MA3524 satisfy the MA4542 preparation expression? | `true` | PASS |
| Does completed MA1502 conflict with MA2508? | `["MA1502"]` | PASS |
| Does cohort 2025 pass the MA1502 CB1 cohort condition? | `false` | PASS |
| Does being a CM student establish MA2508 prerequisite completion? | `null` | PASS |
| Is a Nil preparation expression satisfied even when course history is unknown? | `true` | PASS |
| Is an explicitly CM-listed section absent from this saved MA2510 page? | `true` | PASS |
| Are all CM alternatives for MA1300 retained? | `["C01", "T01", "T02"]` | PASS |

## Source traceability and limits

Every normalized course has its source PDF path and SHA-256 hash. Section and meeting records preserve physical PDF page numbers. CM-only filtering can be rebuilt from the original files. Source URLs embedded in those PDFs were read as term evidence; no CityU requests were made.

Programme/cohort restrictions are retained; identity and completed-course evidence are not inferred. Current seats, permission overrides, component linkage, holidays, teaching weeks and complete university eligibility remain unverified. Historical FULL/availability values are source metadata and are not taught as current seat availability. The importer does not auto-register courses or pass unverified section bundles into the optimizer.

Usage: [MA_CM_UPDATE.md](MA_CM_UPDATE.md). Parsed data: `data/ma-timetable/courses.json` and `sections.json`. Provenance: `reports/ma-timetable/import.json`. Raw training and model outputs remain separate from exact lookup results.
