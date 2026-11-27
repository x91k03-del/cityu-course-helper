# CM Markov planning simulation

The short schedules were unchecked raw Qwen proposals, not feasible constrained-planner results. No neural weights were updated.

The new default planner uses Markov subset search; Years 1-3 require 5-6 credited courses. STOP below five is masked. A sixth course must improve net profit. Years 1-3 overload begins above 15 credits; Year 4 above 12. Both weights are 0.25.

Input: synthetic entering Year-1 CM, cohort 2025, empty transcript, desired Enriched Mathematics stream. All simulated grades B.

| Semester | Courses | Credited courses | Credits | Overload |
|---|---|---:|---:|---:|
| Y1 A | GE1401, GE1601, MA1300, CS1302, PHY1201, GE1305, CSCI1001 | 6 | 16 | 0.25 |
| Y1 B | GE1501, GE2401, MA1301, CHEM1200, GE1202, CSCI1002 | 5 | 15 | 0.00 |
| Y2 A | MA2503, MA2508, MA2509, CS2360, GE1128 | 5 | 17 | 1.00 |
| Y2 B | MA2507, MA2510, MA3511, MA3526, CS2468, GE2134 | 6 | 16 | 0.25 |
| Y3 A | MA3523, MA4542, MA4545, MA4528, MA4551, MA4537 | 6 | 18 | 2.25 |
| Y3 B | MA3512, MA3525, MA3514, MA3515, MA3517, MA4550 | 6 | 18 | 2.25 |
| Y4 A | MA3518, MA4530:A, MA4535, EF3320, EF4821 | 5 | 15 | 2.25 |
| Y4 B | MA4530:B, MA4524, MA4525, MA4546 | 4 | 12 | 0.00 |

Audit: 127 credits; four distributional GE (areas 1/2/3 = 2/1/1); 33 elective mathematics credits; 27 allocated free-elective credits; all mandatory courses; six capstone credits; Enriched Mathematics 4/4 slots.

Every encoded graduation and independent sequence check passed. The source threshold is 122, meeting the user minimum 121. Free-elective allocation follows the existing audit: designated free electives plus mathematics credits above the 12-credit major-elective allocation; this is not a second contribution to total earned credits.

This is approximate Markov beam search with terminal graduation constraints, not a globally optimal or university-approved timetable. Future offerings, real full-degree meeting compatibility and cohort approval are unverified. CM EF/CS prerequisite waivers are advisory user assumptions.

Reproduce: `.\.venv\Scripts\python.exe run_markov_repair.py` then `.\.venv\Scripts\python.exe write_markov_simulation_report.py`.

Historical reports and raw answers remain unchanged. `semester_checks.json` records rejections and repaired CM plans separately.
