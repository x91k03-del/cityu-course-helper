# Reward maximisation subject to terminal credits

Objective: maximise discounted academic reward subject to final credits >=122 and the retained graduation requirements. A best-found approximate path is sufficient; no global-optimum proof is required.

When the hard problem is infeasible, show a separate candidate ranked by academic reward - 1,000,000 * max(0,122-final credits). This never changes graduation feasibility.

Current candidate: 70 credits; discounted academic reward 109.994228; shortfall 52; penalty 52,000,000; penalised objective -51,999,890.005772.

Path valid: True. Full graduating chain accepted: False. A/B repetition is the user-authorised simulation assumption, not verified future offerings.

| Semester | Selected courses | Credits |
|---|---|---:|
| Y1 A | CS1302, CS2360, MA1300 | 9 |
| Y1 B | CS2468, EF3320, MA1301, MA3526 | 12 |
| Y2 A | MA2503, MA2508, MA2509 | 11 |
| Y2 B | MA2507, MA2510, MA3511, MA3517, MA3523, MA3530 | 14 |
| Y3 A | MA3512, MA3518, MA3521, MA3525, MA4542, MA4545 | 18 |
| Y3 B | MA3515 | 3 |
| Y4 A | None | 0 |
| Y4 B | MA3514 | 3 |

The candidate reaches the current confirmed source-credit ceiling of 70. The credit shortfall is therefore a source-coverage limit, not something a larger penalty can remove. More compatible timetable/course evidence is required for a 122-credit feasible result.

Hard feasibility is checked before any graduation approval. The numerical fallback penalty is not used as permission to violate the 122-credit constraint. Existing GE, prerequisite, section, timing, credit and duplicate-course checks remain in effect. No neural weights were retrained for this objective-only change.
