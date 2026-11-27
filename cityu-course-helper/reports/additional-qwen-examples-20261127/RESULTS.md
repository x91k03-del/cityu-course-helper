# Additional Qwen test examples

Actual local fine-tuned Qwen run: **7/8** matched the configured relation policy.

| Case | Student background | Target | Expected bonus | Qwen bonus | Match |
|---|---|---|---:|---:|---|
| FIN_PASS | Finance GE passed | EF3320 | 0.1 | 0.1 | True |
| FIN_FAIL | Matched profile, finance GE failed | EF3320 | 0.0 | 0.0 | True |
| CALC_PASS | Multivariable calculus passed | MA3515 | 0.2 | 0.2 | True |
| CALC_IP | Matched profile, calculus still in progress | MA3515 | 0.0 | 0.0 | True |
| AI_GE | AI GE orientation, programming background | CS4487 | 0.1 | 0.25 | False |
| AI_GE_FAILED | Matched profile, AI GE failed | CS4487 | 0.0 | 0.0 | True |
| AI_MAX | Several mathematical preparation links: take maximum, not sum | CS4487 | 0.25 | 0.25 | True |
| ALG_PASS | Data structures passed before advanced algorithms | CS4335 | 0.3 | 0.3 | True |

The finance, calculus and AI pairs change one grade while keeping the other courses fixed.
AI_MAX checks that multiple applicable links produce the strongest bonus, rather than their sum.

These test reward predictions, not complete course plans or university registration eligibility. The inputs include the reviewed teacher edges, as in training. Passing means following that supplied policy. The transcript probes are additional examples of familiar relations, not a frozen independent benchmark.

Files: qwen_test_inputs.txt contains exact system/user messages; qwen_rendered_prompts.txt includes chat-template tokens. qwen_test_outputs.txt retains raw outputs and expected answers; results.json retains the full records.

Observed failure: AI_GE
The input passes CS1302A, CS2310 and GE2340. Qwen instead named MA2503, MA2510 and MA3515 as strongest sources, although none appears in the transcript. It returned 0.25 instead of the configured 0.10 from GE2340. The raw response is preserved and no correction or fallback was applied.
