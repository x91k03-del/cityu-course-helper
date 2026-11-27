# Four-year 2025-entry CM Markov-profit experiment

**All transcripts and future semester plans are fictional. Passing the encoded checks is not university-certified graduation or a verified timetable.**

The supplied 2025-entry normative study path is the base. Its minimum is **122 credits**, which is stricter than the requested 121-credit floor. The experiment enforces 122–144 credits, at least four distributional GE courses, at least one GE in each of Areas 1/2/3, and at least 20 credits of elective maths. Maths core and the capstone are excluded from that last measure. The model path supplies the 45-credit major core; these mandatory courses, two zero-credit soft-skills courses and a six-credit final-year project are also enforced.

## Source and scope

The 2025 PDF expressly permits MA3526 Analysis in Year 1 Semester B; its usual slot is Year 2 Semester B. GE areas were read from the actual Area column in the user-saved GE availability PDFs, not guessed from course codes. Year 4 in the supplied path has four-course / twelve-credit semesters, so the previous five-course minimum is waived for Year 4.

Elective choices use candidate titles/credits from the saved 2026 handbook and CS catalogue, with **2025-cohort approval unverified**. Future availability and several precedence rules are simulation assumptions. The 2026/27 Semester A class snapshot is not reused as proof of future timetables. The FYP is simulated as two three-credit components totalling six credits; this is not a claim about official interim transcript posting. Elective maths may occupy major-elective or free-elective slots, but each earned credit is counted once.

The prior generated NEW00007 example was a 2024-entry partial history. It is preserved as a negative compatibility case, not relabelled as a 2025 student. Its GE1359 completion would also conflict with required MA2508 if the saved exclusion rule were applied to this curriculum.

## Markov state and profit

Each semester begins from passed course/component IDs, earned credits, failed attempts, GE count, GE-area counts, elective-maths credits, core progress and current semester. The model generates reward coefficients from that state and the complete fictional transcript so far. The solver then forecasts the remaining semesters, executes only the current semester, observes grades and replans. Forecasts assume future passes; resit examples reveal a failure only after the attempt.

`net_profit = course_profit + newly_covered_GE_area_bonus + capped_GE/math/credit_progress_bonus + on_path_completion_bonus - course_cost - Year4_overload`

GE from an area already passed receives **0.1 times base course profit**. Only the first newly covered area gets the new-area bonus, including within a single semester. A fourth GE remains compulsory even after all three areas are covered. F/IP/W do not earn credit or satisfy area coverage. The fourth-course and elective-maths progress bonuses stop at their quota; total-credit progress stops at 122. An F receives no academic profit, while its attempted credits still contribute to load.

**Overload:** Years 1–3 have zero overload penalty. In Year 4 only, `0.25 × max(0, attempted semester credits − 12)²`. At 9 or 12 credits the penalty is zero; at 15 it is 2.25; at 18 it is 9. Five courses are not required in Year 4. An 18-credit semester cap still applies throughout the mock.

This is rule-distilled academic utility, not learned monetary profit or a fitted student-outcome reward model. The source-constrained rolling-horizon MILP uses a 0.98 discount and exact GE coverage/progress and Year 4 load terms. The neural model supplies parameters; it cannot waive the terminal graduation constraints.

## Full eight-semester rollouts

| Profile | Mode | Earned credits | GE count | GE areas 1 / 2 / 3 | Elective maths credits | All encoded requirements |
| --- | --- | --- | --- | --- | --- | --- |
| CM2025_NORMAL | Rule parameters + solver | 124 | 4 | 2 / 1 / 1 | 24 | PASS |
| CM2025_EARLY_ANALYSIS | Rule parameters + solver | 124 | 4 | 2 / 1 / 1 | 24 | PASS |
| CM2025_ANALYSIS_RESIT | Rule parameters + solver | 124 | 4 | 2 / 1 / 1 | 21 | PASS |
| CM2025_GE_RESIT | Rule parameters + solver | 124 | 4 | 2 / 1 / 1 | 24 | PASS |
| MODEL_CM2025 | Model parameters + solver | 124 | 4 | 2 / 1 / 1 | 24 | PASS |
| MODEL_CM2025_RESIT | Model parameters + solver | 124 | 4 | 2 / 1 / 1 | 21 | PASS |

## Actual model parameter tests

Exact configured-parameter matches on twelve fixed, held-out state vectors: **before 0/12; after 12/12**. Boundary states include three GE covering all areas versus the required fourth course, elective maths at 19/20 credits and total credits at 121/122. Test vectors were excluded from training. These are conditional rule-adherence tests, not empirical student-benefit estimates.

During the model-assisted transcript rollouts, **16/16 parameter calls passed validation**, with 0 explicit rule-parameter fallbacks. Raw answers and fallback flags are saved. Fallbacks are not model passes. These rollout demonstrations share the taught curriculum and may revisit training-state patterns; only the separate state-vector test is held out.

The separate `adapters/bscm-markov-v4` adapter was trained for 2 epochs from `adapters/bscm-profit-v3`. Selected epoch 1; training time 4.3 minutes. Assistant-token cross-entropy teaches parameter rules; no discrete profit was falsely added as a differentiable token loss.

### Generated parameter progression: MODEL_CM2025

| Semester | GE count before | GE areas covered before | Elective maths credits before | GE quota bonus | Maths-credit bonus | Year 4 overload coefficient |
| --- | --- | --- | --- | --- | --- | --- |
| 1 A | 0 | None | 0 | 2.0 | 1.5 | 0.0 |
| 1 B | 0 | None | 0 | 2.0 | 1.5 | 0.0 |
| 2 A | 3 | 1, 2, 3 | 0 | 2.0 | 1.5 | 0.0 |
| 2 B | 4 | 1, 2, 3 | 0 | 0.0 | 1.5 | 0.0 |
| 3 A | 4 | 1, 2, 3 | 0 | 0.0 | 1.5 | 0.0 |
| 3 B | 4 | 1, 2, 3 | 9 | 0.0 | 1.5 | 0.0 |
| 4 A | 4 | 1, 2, 3 | 18 | 0.0 | 1.5 | 0.25 |
| 4 B | 4 | 1, 2, 3 | 24 | 0.0 | 0.0 | 0.25 |

Other generated coefficients: base course profit 3; covered-area GE multiplier 0.1; new-area bonus 5; credit-progress bonus 0.05 until 122; overload threshold 12 credits; discount 0.98. The engine applies the multiplier to the actual completed-area state and computes the resulting net profit.

## Independent validation

**106 software checks passed.** All six exported transcripts were re-audited from course IDs and grades. Tests include duplicate-credit rejection, language-GE exclusion from distribution counts, 45-credit core versus elective maths, project-credit accounting, held-out state separation, GE state-dependent profit, credit-based MILP versus exhaustive search and final-term failure.

## Semester progression and profits

### CM2025_NORMAL

| Year / semester | Chosen course/component IDs | Attempted credits | Earned cumulative credits | Net profit | Overload penalty |
| --- | --- | --- | --- | --- | --- |
| 1 A | GE1401, GE1501, GE1601, MA1300, CS1302, PHY1201, CSCI1001 | 16 | 16 | 19.80 | 0.00 |
| 1 B | GE2401, MA1301, CHEM1200, CSCI1002, GE1113, GE1202, GE1305 | 18 | 34 | 37.90 | 0.00 |
| 2 A | MA2503, MA2508, MA2509, CS2360, GE1105 | 17 | 51 | 14.15 | 0.00 |
| 2 B | MA2507, MA2510, MA3511, MA3526, CS2468 | 13 | 64 | 15.65 | 0.00 |
| 3 A | MA3512, MA3518, MA3525, MA3521, MA4524, MA4546 | 18 | 82 | 29.40 | 0.00 |
| 3 B | MA3514, MA3515, MA3517, MA4542, MA4545, MA4550 | 18 | 100 | 29.40 | 0.00 |
| 4 A | MA4530:A, MA3523, MA4535, CS2115 | 12 | 112 | 12.60 | 0.00 |
| 4 B | MA4530:B, CS2116, CS2117, CS2204 | 12 | 124 | 9.50 | 0.00 |
### CM2025_EARLY_ANALYSIS

| Year / semester | Chosen course/component IDs | Attempted credits | Earned cumulative credits | Net profit | Overload penalty |
| --- | --- | --- | --- | --- | --- |
| 1 A | GE1401, GE1501, GE1601, MA1300, CS1302, PHY1201, CSCI1001 | 16 | 16 | 19.80 | 0.00 |
| 1 B | GE2401, MA1301, CHEM1200, CSCI1002, MA3526, GE1113, GE1202 | 18 | 34 | 31.90 | 0.00 |
| 2 A | MA2503, MA2508, MA2509, CS2360, GE1305 | 17 | 51 | 21.85 | 0.00 |
| 2 B | MA2507, MA2510, MA3511, CS2468, GE1105 | 13 | 64 | 13.95 | 0.00 |
| 3 A | MA3512, MA3518, MA3525, MA3521, MA4524, MA4546 | 18 | 82 | 29.40 | 0.00 |
| 3 B | MA3514, MA3515, MA3517, MA4542, MA4545, MA4550 | 18 | 100 | 29.40 | 0.00 |
| 4 A | MA4530:A, MA3523, MA4535, CS2115 | 12 | 112 | 12.60 | 0.00 |
| 4 B | MA4530:B, CS2116, CS2117, CS2204 | 12 | 124 | 9.50 | 0.00 |
### CM2025_ANALYSIS_RESIT

| Year / semester | Chosen course/component IDs | Attempted credits | Earned cumulative credits | Net profit | Overload penalty |
| --- | --- | --- | --- | --- | --- |
| 1 A | GE1401, GE1501, GE1601, MA1300, CS1302, PHY1201, CSCI1001 | 16 | 16 | 19.80 | 0.00 |
| 1 B | GE2401, MA1301, CHEM1200, CSCI1002, GE1113, GE1202, GE1305 | 18 | 34 | 37.90 | 0.00 |
| 2 A | MA2503, MA2508, MA2509, CS2360, GE1105 | 17 | 51 | 14.15 | 0.00 |
| 2 B | MA2507, MA2510, MA3511, MA3526, CS2468 | 13 | 61 | 11.50 | 0.00 |
| 3 A | MA3526, MA3512, MA3518, MA3525, MA4524, MA4550 | 18 | 79 | 24.90 | 0.00 |
| 3 B | MA3514, MA3515, MA3517, MA3521, MA4545, MA4535 | 18 | 97 | 29.40 | 0.00 |
| 4 A | MA4530:A, MA4523, MA4525, CS2117 | 12 | 109 | 17.10 | 0.00 |
| 4 B | MA4530:B, CS2066, CS2115, CS2116, CS2204 | 15 | 124 | 9.40 | 2.25 |
### CM2025_GE_RESIT

| Year / semester | Chosen course/component IDs | Attempted credits | Earned cumulative credits | Net profit | Overload penalty |
| --- | --- | --- | --- | --- | --- |
| 1 A | GE1401, GE1501, GE1601, MA1300, CS1302, PHY1201, CSCI1001 | 16 | 16 | 19.80 | 0.00 |
| 1 B | GE2401, MA1301, CHEM1200, CSCI1002, GE1113, GE1202, GE1305 | 18 | 34 | 37.90 | 0.00 |
| 2 A | MA2503, MA2508, MA2509, CS2360, GE1105 | 17 | 48 | 11.70 | 0.00 |
| 2 B | MA2507, MA2510, MA3511, MA3526, CS2468, GE1128 | 16 | 64 | 17.10 | 0.00 |
| 3 A | MA3512, MA3518, MA3525, MA3521, MA4524, MA4546 | 18 | 82 | 29.40 | 0.00 |
| 3 B | MA3514, MA3515, MA3517, MA4542, MA4545, MA4550 | 18 | 100 | 29.40 | 0.00 |
| 4 A | MA4530:A, MA3523, MA4535, CS2115 | 12 | 112 | 12.60 | 0.00 |
| 4 B | MA4530:B, CS2116, CS2117, CS2204 | 12 | 124 | 9.50 | 0.00 |
### MODEL_CM2025

| Year / semester | Chosen course/component IDs | Attempted credits | Earned cumulative credits | Net profit | Overload penalty |
| --- | --- | --- | --- | --- | --- |
| 1 A | GE1401, GE1501, GE1601, MA1300, CS1302, PHY1201, CSCI1001 | 16 | 16 | 19.80 | 0.00 |
| 1 B | GE2401, MA1301, CHEM1200, CSCI1002, GE1113, GE1202, GE1305 | 18 | 34 | 37.90 | 0.00 |
| 2 A | MA2503, MA2508, MA2509, CS2360, GE1105 | 17 | 51 | 14.15 | 0.00 |
| 2 B | MA2507, MA2510, MA3511, MA3526, CS2468 | 13 | 64 | 15.65 | 0.00 |
| 3 A | MA3512, MA3518, MA3525, MA3521, MA4524, MA4546 | 18 | 82 | 29.40 | 0.00 |
| 3 B | MA3514, MA3515, MA3517, MA4542, MA4545, MA4550 | 18 | 100 | 29.40 | 0.00 |
| 4 A | MA4530:A, MA3523, MA4535, CS2115 | 12 | 112 | 12.60 | 0.00 |
| 4 B | MA4530:B, CS2116, CS2117, CS2204 | 12 | 124 | 9.50 | 0.00 |
### MODEL_CM2025_RESIT

| Year / semester | Chosen course/component IDs | Attempted credits | Earned cumulative credits | Net profit | Overload penalty |
| --- | --- | --- | --- | --- | --- |
| 1 A | GE1401, GE1501, GE1601, MA1300, CS1302, PHY1201, CSCI1001 | 16 | 16 | 19.80 | 0.00 |
| 1 B | GE2401, MA1301, CHEM1200, CSCI1002, GE1113, GE1202, GE1305 | 18 | 34 | 37.90 | 0.00 |
| 2 A | MA2503, MA2508, MA2509, CS2360, GE1105 | 17 | 51 | 14.15 | 0.00 |
| 2 B | MA2507, MA2510, MA3511, MA3526, CS2468 | 13 | 61 | 11.50 | 0.00 |
| 3 A | MA3526, MA3512, MA3518, MA3525, MA4524, MA4550 | 18 | 79 | 24.90 | 0.00 |
| 3 B | MA3514, MA3515, MA3517, MA3521, MA4545, MA4535 | 18 | 97 | 29.40 | 0.00 |
| 4 A | MA4530:A, MA4523, MA4525, CS2117 | 12 | 109 | 17.10 | 0.00 |
| 4 B | MA4530:B, CS2066, CS2115, CS2116, CS2204 | 15 | 124 | 9.40 | 2.25 |

## Files and reruns

- Complete grade-bearing transcripts: `output/four-year-transcripts/` (one CSV and Markdown file per profile).
- Rule-generated full trajectories: `reports/four-year/rule_rollouts.json`.
- Actual model-assisted trajectories: `reports/markov-v4/model_rollouts.json`.
- Raw generated parameter responses: `parameter_predictions.json` and `rollout_parameter_calls.json` in `reports/markov-v4/`.
- Editable rule configuration: `data/four_year_policy.json`. The production semester-profit settings are in `data/profit_objective_policy.json`.
- Source provenance and GE-area map: `reports/four-year/sources.json` and `data/four-year/GE_areas.json`.

```powershell
cd F:/CODEX/cityu-course-helper
./four_year.cmd prepare
./four_year.cmd evaluate
./four_year.cmd rollout
./four_year.cmd report
```

The path’s curriculum minimum and source assumptions remain visible. Unknown AIMS restrictions, all actual prerequisites, elective approvals, clash-free meetings and official graduation eligibility are not asserted.

Source: [supplied 2025-entry study path](<F:/CODEX/cityu-course-helper/GE_SEMA/MA/Department of Mathematics Bachelor of Science in Computing Mathematics Normative 4-year Degree – 2025 Entry (BSCSIU4_CM_2025) _ Department of Mathematics.pdf>). Physical PDF page 1 gives the 122-credit minimum; page 3 permits early Analysis; pages 4–8 provide the remaining suggested path.
