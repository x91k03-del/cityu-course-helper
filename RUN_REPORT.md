# Completed local run

Model: Qwen/Qwen3-8B with a locally trained BF16 LoRA adapter. Hardware: NVIDIA GeForce RTX 5090.

**Status: bootstrap training and local evaluation completed. Reviewed-label validation and real-semester scheduling remain pending.**

## Measured results

- Course data: 77 parsed records; 77 source hashes verified.
- Training: 434 examples, 2 epochs, 218 optimizer steps.
- Trainable adapter parameters: 21,823,488.
- Selected epoch: 1; initial validation loss 0.50952.
- Validation loss after each pass: pass 1: 0.03021; pass 2: 0.03842.
- Training time: 8.7 minutes; peak Torch GPU allocation 17.73 GiB (excludes other applications and some reserved memory).
- Held-out examples: 56. Valid output schemas: base 48, tuned 56.
- Exact typed source-fact extractions: base 0/8, tuned 8/8.
- Fact value matches after converting numeric strings: base 8/8, tuned 8/8. This separates formatting gains from factual gains.
- Synthetic-target MSE (base → tuned): background mismatch: 0.063438 → 0.016927; difficulty: 0.031250 → 0.000469; workload: 0.013100 → 0.000525.
- Scheduler: 8 tests passed, including 15 exhaustive-search comparisons.

All numeric training labels and MSE targets are synthetic rubric estimates. Valid-only MSE excludes invalid responses; the invalid count is reported alongside it. These numbers do not establish real CityU workload prediction quality.

## Proposal coverage

| Requirement | Result |
| --- | --- |
| Local Qwen model and task adaptation | Installed official pinned base weights; trained a separate local adapter |
| Public CityU course information | Collected syllabus sources and extracted fields |
| LLM scoring + MILP | Implemented and tested; real term data still required |
| Pure LLM baseline and same synthetic profiles | Compared on six profiles using the same simulated constraint fixtures |
| Hard prerequisites, credits, required courses, clashes | Solver supports reviewed rules and complete section bundles; missing evidence fails closed |
| Workload balance by assessment week | Cap constraints implemented; real timing data unavailable |
| UIUC/CMU topic matching | Deferred: underlying data reuse permissions unverified |
| Reviewed workload labels / real workload MSE | Not available; blank label review worksheet provided |
| Student/senior-student rankings | Not collected |
| Optional transcript | Local text extraction only; completion must be confirmed |

## Synthetic schedule comparison

The comparison uses real course descriptions but simulated eligibility and meetings, explicitly labelled as synthetic. No result is an actual CityU schedule.

- pure_llm_base: 6/6 schedules with constraint violations; 6 total violations.
- fine_tuned_scores_milp: 0/6 schedules with constraint violations; 0 total violations.

## Run it

```powershell
cd F:\CODEX\cityu-course-helper
.\run.ps1 -Action score -Course CS3334
.\run.ps1 -Action demo
```

See README.md for custom profiles, verified semester data, review labels, provenance and reproducibility.
