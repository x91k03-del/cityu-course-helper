# Fictional CM student timetable experiment

**All 12 transcripts are fictional test fixtures. No real student record was used. No model training was performed.**

The test supplies the actual local Qwen3-8B timetable adapter with raw grade-bearing transcripts. Twelve runs include the saved MA catalogue; two additional runs omit it to test model memory. Outputs below are generated model answers, graded without repairing or replacing them. Reference schedules are produced separately by exhaustive enumeration and are labelled accordingly.

**Result: 2/12 catalogue-supplied schedules passed every check; 0/2 memory-only schedules passed.** The current model is not reliable for autonomous transcript-to-timetable planning. The earlier single-course extraction tests did not test this multi-course planning task.

## Test conditions

The random seed is 20261115. Grades are randomized, while matched profiles retain identical grades on shared courses. The principal pair is Year 2, Computing Mathematics, differing only in whether MA3526 Analysis was passed in Year 1. That early completion is hypothetical accelerated progress, not the standard study plan. A current-year label does not supply missing prerequisites. F and IP grades do not count as passed.

This is the MA portion of a Semester A 2026/27 schedule, with at most three courses. The predeclared objective maximizes course count and then follows the same priority list for all profiles: MA4542, MA3512, MA4545, MA3518, MA3521, MA2508, MA3525, MA2503, MA2509, MA1300, MA1502. For this experiment only, each course uses one positive-credit C section and one T section if tutorials appear. This assumption is not CityU-verified component linkage. No teaching-week calendar, current seats, travel times, full-degree requirements or historical permission chains were verified. A reference passing these tests is an experimental weekly plan, not registration approval.

## Fictional profiles

| ID | Profile | Transcript (grade) |
| --- | --- | --- |
| CM01 | Year 2: Analysis passed in Year 1 | MA1301 B+; MA2503 A; MA2508 B; MA2509 C+; MA2510 C; CS2360 C+; MA3526 A- |
| CM02 | Year 2: Analysis not studied | MA1301 B+; MA2503 A; MA2508 B; MA2509 C+; MA2510 C; CS2360 C+ |
| CM03 | Year 2: Analysis failed | MA1301 B+; MA2503 A; MA2508 B; MA2509 C+; MA2510 C; CS2360 C+; MA3526 F |
| CM04 | Year 2: Analysis still in progress | MA1301 B+; MA2503 A; MA2508 B; MA2509 C+; MA2510 C; CS2360 C+; MA3526 IP |
| CM05 | Year 2: Analysis passed, MA2508 absent | MA1301 B+; MA2503 A; MA2509 C+; MA2510 C; CS2360 C+; MA3526 A- |
| CM06 | Year 3: Analysis and ODE passed | MA1301 B+; MA2503 A; MA2508 B; MA2509 C+; MA2510 C; CS2360 C+; MA3526 A-; MA3511 B+ |
| CM07 | Year 3: Analysis passed, ODE failed | MA1301 B+; MA2503 A; MA2508 B; MA2509 C+; MA2510 C; CS2360 C+; MA3526 A-; MA3511 F |
| CM08 | Year 2: both courses in the calculus AND branch passed | CS2360 C+; MA1503 C+; MA1508 C |
| CM09 | Year 2: MA1503 passed, MA1508 failed | CS2360 C+; MA1503 C+; MA1508 F |
| CM10 | Year 1: new cohort, no passed courses | CS1302 IP |
| CM11 | Year 1: returning earlier-cohort student | CS1302 IP |
| CM12 | Year 2: calculus branch passed plus exclusive GE1359 | CS2360 C+; MA1503 C+; MA1508 C; GE1359 A- |

## Model results

| Check | Catalogue supplied (12 runs) | Memory only (2 runs) |
| --- | --- | --- |
| json_valid | 12/12 | 2/2 |
| completed_courses_exact | 9/12 | 2/2 |
| selection_rules_passed | 2/12 | 0/2 |
| meeting_times_exact | 6/12 | 0/2 |
| no_potential_weekly_overlap | 6/12 | 0/2 |
| maximum_course_count_met | 2/12 | 0/2 |
| objective_matched | 2/12 | 0/2 |
| uncertainty_flags_correct | 12/12 | 2/2 |
| all_checks_passed | 2/12 | 0/2 |

These are held-out synthetic scenario checks, not estimates of real-student accuracy. Meeting correctness, selection rules and optimization are scored separately: a plausible course list is not sufficient. Conflict checks use the exact source meetings, not potentially invented clock times in the answer.

| Profile | Model-selected courses | Independent reference | All checks | Model errors |
| --- | --- | --- | --- | --- |
| CM01 | MA4542, MA3518, MA3521 | MA3518, MA3521, MA4542 | PASS |  |
| CM02 | MA1502, MA3518, MA3521 | MA3518, MA3521, MA3525 | FAIL | ineligible:MA1502:exclusive_course_completed; ineligible:MA1502:restriction:cohort |
| CM03 | MA1502, MA3512, MA4542 | MA3518, MA3521, MA3525 | FAIL | ineligible:MA1502:exclusive_course_completed; ineligible:MA1502:restriction:cohort; ineligible:MA3512:combined_requirement_not_satisfied; ineligible:MA4542:combined_requirement_not_satisfied |
| CM04 | MA4542, MA3518, MA3525 | MA3518, MA3521, MA3525 | FAIL | ineligible:MA4542:combined_requirement_not_satisfied; invalid_or_incomplete_component_option:MA3525 |
| CM05 | MA4542, MA3518, MA3521 | MA3518, MA3521, MA3525 | FAIL | ineligible:MA4542:combined_requirement_not_satisfied |
| CM06 | MA4542, MA3512, MA4545 | MA3512, MA4542, MA4545 | PASS |  |
| CM07 | MA4542, MA3512, MA3525 | MA3518, MA3521, MA4542 | FAIL | ineligible:MA3512:combined_requirement_not_satisfied; invalid_or_incomplete_component_option:MA3525 |
| CM08 | MA4542, MA3512, MA3525 | MA2508, MA2509 | FAIL | incorrect_completed_course_extraction; ineligible:MA4542:combined_requirement_not_satisfied; ineligible:MA3512:combined_requirement_not_satisfied; invalid_or_incomplete_component_option:MA3525 |
| CM09 | MA4542, MA3512, MA3525 | MA1300, MA2509, MA3525 | FAIL | incorrect_completed_course_extraction; ineligible:MA4542:combined_requirement_not_satisfied; ineligible:MA3512:combined_requirement_not_satisfied; invalid_or_incomplete_component_option:MA3525 |
| CM10 | MA1300, MA1502, MA2503 | MA1300, MA2509 | FAIL | invalid_or_incomplete_component_option:MA1300; ineligible:MA2503:combined_requirement_not_satisfied |
| CM11 | MA1502, MA2503, MA3512 | MA1300, MA2509 | FAIL | ineligible:MA1502:restriction:cohort; ineligible:MA2503:combined_requirement_not_satisfied; ineligible:MA3512:combined_requirement_not_satisfied |
| CM12 | MA4542, MA3512, MA3525 | MA2509, MA3525 | FAIL | incorrect_completed_course_extraction; ineligible:MA4542:combined_requirement_not_satisfied; ineligible:MA3512:combined_requirement_not_satisfied; invalid_or_incomplete_component_option:MA3525 |

## Matched-profile differences

| Comparison | Factor | Reference courses added in first profile | Reference courses removed | Model first / second | Both model answers pass? |
| --- | --- | --- | --- | --- | --- |
| CM01 vs CM02 | Analysis passed versus not studied | MA4542 | MA3525 | MA4542, MA3518, MA3521 / MA1502, MA3518, MA3521 | No |
| CM03 vs CM02 | Analysis failed versus not studied | None | None | MA1502, MA3512, MA4542 / MA1502, MA3518, MA3521 | No |
| CM04 vs CM02 | Analysis in progress versus not studied | None | None | MA4542, MA3518, MA3525 / MA1502, MA3518, MA3521 | No |
| CM01 vs CM05 | Missing MA2508 despite Analysis passed | MA4542 | MA3525 | MA4542, MA3518, MA3521 / MA4542, MA3518, MA3521 | No |
| CM06 vs CM07 | ODE passed versus failed | MA3512, MA4545 | MA3518, MA3521 | MA4542, MA3512, MA4545 / MA4542, MA3512, MA3525 | No |
| CM08 vs CM09 | Both AND-branch courses passed versus one failed | MA2508 | MA1300, MA3525 | MA4542, MA3512, MA3525 / MA4542, MA3512, MA3525 | No |
| CM08 vs CM12 | Completed GE1359 exclusive-course conflict | MA2508 | MA3525 | MA4542, MA3512, MA3525 / MA4542, MA3512, MA3525 | No |
| CM10 vs CM11 | 2026 versus 2025 cohort | None | None | MA1300, MA1502, MA2503 / MA1502, MA2503, MA3512 | No |

Passing Analysis alone is insufficient for MA4542: its source expression also requires MA2508. Passing MA3526 can open MA4542 when MA2508 is already passed. Changing a transcript does not always change the selected timetable: an unchanged optimum can be correct, and new eligibility can still be limited by an exclusion or tutorial clash.

## Actual generated schedules with catalogue context

### CM01 - Year 2: Analysis passed in Year 1

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA4542 / CA1 | Thu | 15:00 | 17:50 |
| MA3518 / CA1 | Tue | 16:00 | 18:50 |
| MA3521 / CA1 | Mon | 09:00 | 11:50 |

PASS under experiment checks.

### CM02 - Year 2: Analysis not studied

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA1502 / CB1 | Wed | 09:00 | 11:50 |
| MA3518 / CA1 | Tue | 16:00 | 18:50 |
| MA3521 / CA1 | Mon | 09:00 | 11:50 |

**Generated answer failed:** ineligible:MA1502:exclusive_course_completed; ineligible:MA1502:restriction:cohort

### CM03 - Year 2: Analysis failed

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA1502 / CB1 | Wed | 09:00 | 11:50 |
| MA3512 / CA1 | Fri | 15:00 | 17:50 |
| MA4542 / CA1 | Thu | 15:00 | 17:50 |

**Generated answer failed:** ineligible:MA1502:exclusive_course_completed; ineligible:MA1502:restriction:cohort; ineligible:MA3512:combined_requirement_not_satisfied; ineligible:MA4542:combined_requirement_not_satisfied

### CM04 - Year 2: Analysis still in progress

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA4542 / CA1 | Thu | 15:00 | 17:50 |
| MA3518 / CA1 | Tue | 16:00 | 18:50 |
| MA3525 / CA1 | Thu | 13:00 | 14:50 |
| MA3525 / CA1 | Tue | 14:00 | 14:50 |

**Generated answer failed:** ineligible:MA4542:combined_requirement_not_satisfied; invalid_or_incomplete_component_option:MA3525

### CM05 - Year 2: Analysis passed, MA2508 absent

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA4542 / CA1 | Thu | 15:00 | 17:50 |
| MA3518 / CA1 | Tue | 16:00 | 18:50 |
| MA3521 / CA1 | Mon | 09:00 | 11:50 |

**Generated answer failed:** ineligible:MA4542:combined_requirement_not_satisfied

### CM06 - Year 3: Analysis and ODE passed

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA4542 / CA1 | Thu | 15:00 | 17:50 |
| MA3512 / CA1 | Fri | 15:00 | 17:50 |
| MA4545 / CA1 | Wed | 12:00 | 14:50 |

PASS under experiment checks.

### CM07 - Year 3: Analysis passed, ODE failed

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA4542 / CA1 | Thu | 15:00 | 17:50 |
| MA3512 / CA1 | Fri | 15:00 | 17:50 |
| MA3525 / CA1 | Thu | 13:00 | 14:50 |
| MA3525 / CA1 | Tue | 14:00 | 14:50 |

**Generated answer failed:** ineligible:MA3512:combined_requirement_not_satisfied; invalid_or_incomplete_component_option:MA3525

### CM08 - Year 2: both courses in the calculus AND branch passed

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA4542 / CA1 | Thu | 15:00 | 17:50 |
| MA3512 / CA1 | Fri | 15:00 | 17:50 |
| MA3525 / CA1 | Thu | 13:00 | 14:50 |
| MA3525 / CA1 | Tue | 14:00 | 14:50 |

**Generated answer failed:** incorrect_completed_course_extraction; ineligible:MA4542:combined_requirement_not_satisfied; ineligible:MA3512:combined_requirement_not_satisfied; invalid_or_incomplete_component_option:MA3525

### CM09 - Year 2: MA1503 passed, MA1508 failed

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA4542 / CA1 | Thu | 15:00 | 17:50 |
| MA3512 / CA1 | Fri | 15:00 | 17:50 |
| MA3525 / CA1 | Thu | 13:00 | 14:50 |
| MA3525 / CA1 | Tue | 14:00 | 14:50 |

**Generated answer failed:** incorrect_completed_course_extraction; ineligible:MA4542:combined_requirement_not_satisfied; ineligible:MA3512:combined_requirement_not_satisfied; invalid_or_incomplete_component_option:MA3525

### CM10 - Year 1: new cohort, no passed courses

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA1300 / C01 | Fri | 12:00 | 13:50 |
| MA1300 / C01 | Wed | 17:00 | 18:50 |
| MA1502 / CB1 | Wed | 09:00 | 11:50 |
| MA2503 / CA1 | Thu | 16:00 | 18:50 |

**Generated answer failed:** invalid_or_incomplete_component_option:MA1300; ineligible:MA2503:combined_requirement_not_satisfied

### CM11 - Year 1: returning earlier-cohort student

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA1502 / CB1 | Wed | 09:00 | 11:50 |
| MA2503 / CA1 | Thu | 16:00 | 18:50 |
| MA3512 / CA1 | Fri | 15:00 | 17:50 |

**Generated answer failed:** ineligible:MA1502:restriction:cohort; ineligible:MA2503:combined_requirement_not_satisfied; ineligible:MA3512:combined_requirement_not_satisfied

### CM12 - Year 2: calculus branch passed plus exclusive GE1359

| Course / component | Day | Model start | Model end |
| --- | --- | --- | --- |
| MA4542 / CA1 | Thu | 15:00 | 17:50 |
| MA3512 / CA1 | Fri | 15:00 | 17:50 |
| MA3525 / CA1 | Thu | 13:00 | 14:50 |
| MA3525 / CA1 | Tue | 14:00 | 14:50 |

**Generated answer failed:** incorrect_completed_course_extraction; ineligible:MA4542:combined_requirement_not_satisfied; ineligible:MA3512:combined_requirement_not_satisfied; invalid_or_incomplete_component_option:MA3525

## Independent reference schedules

**The following times are source-derived reference outputs, not model generations.**

| Profile | Course / component | Day | Start | End |
| --- | --- | --- | --- | --- |
| CM01 | MA3518 / CA1 | Tue | 16:00 | 18:50 |
| CM01 | MA3521 / CA1 | Mon | 09:00 | 11:50 |
| CM01 | MA4542 / CA1 | Thu | 15:00 | 17:50 |
| CM02 | MA3518 / CA1 | Tue | 16:00 | 18:50 |
| CM02 | MA3521 / CA1 | Mon | 09:00 | 11:50 |
| CM02 | MA3525 / CA1 | Thu | 13:00 | 14:50 |
| CM02 | MA3525 / CA1 | Tue | 14:00 | 14:50 |
| CM02 | MA3525 / TA1 | Tue | 15:00 | 15:50 |
| CM03 | MA3518 / CA1 | Tue | 16:00 | 18:50 |
| CM03 | MA3521 / CA1 | Mon | 09:00 | 11:50 |
| CM03 | MA3525 / CA1 | Thu | 13:00 | 14:50 |
| CM03 | MA3525 / CA1 | Tue | 14:00 | 14:50 |
| CM03 | MA3525 / TA1 | Tue | 15:00 | 15:50 |
| CM04 | MA3518 / CA1 | Tue | 16:00 | 18:50 |
| CM04 | MA3521 / CA1 | Mon | 09:00 | 11:50 |
| CM04 | MA3525 / CA1 | Thu | 13:00 | 14:50 |
| CM04 | MA3525 / CA1 | Tue | 14:00 | 14:50 |
| CM04 | MA3525 / TA1 | Tue | 15:00 | 15:50 |
| CM05 | MA3518 / CA1 | Tue | 16:00 | 18:50 |
| CM05 | MA3521 / CA1 | Mon | 09:00 | 11:50 |
| CM05 | MA3525 / CA1 | Thu | 13:00 | 14:50 |
| CM05 | MA3525 / CA1 | Tue | 14:00 | 14:50 |
| CM05 | MA3525 / TA1 | Tue | 15:00 | 15:50 |
| CM06 | MA3512 / CA1 | Fri | 15:00 | 17:50 |
| CM06 | MA4542 / CA1 | Thu | 15:00 | 17:50 |
| CM06 | MA4545 / CA1 | Wed | 12:00 | 14:50 |
| CM07 | MA3518 / CA1 | Tue | 16:00 | 18:50 |
| CM07 | MA3521 / CA1 | Mon | 09:00 | 11:50 |
| CM07 | MA4542 / CA1 | Thu | 15:00 | 17:50 |
| CM08 | MA2508 / CA1 | Sat | 11:00 | 12:50 |
| CM08 | MA2508 / CA1 | Tue | 16:00 | 16:50 |
| CM08 | MA2508 / TA1 | Tue | 15:00 | 15:50 |
| CM08 | MA2509 / CA1 | Mon | 10:00 | 10:50 |
| CM08 | MA2509 / CA1 | Wed | 10:00 | 11:50 |
| CM08 | MA2509 / TA1 | Mon | 11:00 | 11:50 |
| CM09 | MA1300 / C01 | Fri | 12:00 | 13:50 |
| CM09 | MA1300 / C01 | Wed | 17:00 | 18:50 |
| CM09 | MA1300 / T01 | Mon | 18:00 | 18:50 |
| CM09 | MA2509 / CA1 | Mon | 10:00 | 10:50 |
| CM09 | MA2509 / CA1 | Wed | 10:00 | 11:50 |
| CM09 | MA2509 / TA1 | Mon | 11:00 | 11:50 |
| CM09 | MA3525 / CA1 | Thu | 13:00 | 14:50 |
| CM09 | MA3525 / CA1 | Tue | 14:00 | 14:50 |
| CM09 | MA3525 / TA1 | Tue | 15:00 | 15:50 |
| CM10 | MA1300 / C01 | Fri | 12:00 | 13:50 |
| CM10 | MA1300 / C01 | Wed | 17:00 | 18:50 |
| CM10 | MA1300 / T01 | Mon | 18:00 | 18:50 |
| CM10 | MA2509 / CA1 | Mon | 10:00 | 10:50 |
| CM10 | MA2509 / CA1 | Wed | 10:00 | 11:50 |
| CM10 | MA2509 / TA1 | Mon | 11:00 | 11:50 |
| CM11 | MA1300 / C01 | Fri | 12:00 | 13:50 |
| CM11 | MA1300 / C01 | Wed | 17:00 | 18:50 |
| CM11 | MA1300 / T01 | Mon | 18:00 | 18:50 |
| CM11 | MA2509 / CA1 | Mon | 10:00 | 10:50 |
| CM11 | MA2509 / CA1 | Wed | 10:00 | 11:50 |
| CM11 | MA2509 / TA1 | Mon | 11:00 | 11:50 |
| CM12 | MA2509 / CA1 | Mon | 10:00 | 10:50 |
| CM12 | MA2509 / CA1 | Wed | 10:00 | 11:50 |
| CM12 | MA2509 / TA1 | Mon | 11:00 | 11:50 |
| CM12 | MA3525 / CA1 | Thu | 13:00 | 14:50 |
| CM12 | MA3525 / CA1 | Tue | 14:00 | 14:50 |
| CM12 | MA3525 / TA1 | Tue | 15:00 | 15:50 |

## Saved artifacts

- Fictional transcripts: `data/cm-profile-test/transcripts/CM01.txt` through `CM12.txt`; full records in `profiles.json`.
- Complete prompts, raw answers and grading: `reports/cm-profile-test/predictions.json`.
- Independent references: `reports/cm-profile-test/reference_schedules.json`.
- Pair comparisons and totals: `pair_comparisons.json` and `summary.json`.
- Plan and model-weight fingerprints: `experiment_plan.json` and `run.json`. Weights are checked before/after to confirm this test did not train the adapter.
