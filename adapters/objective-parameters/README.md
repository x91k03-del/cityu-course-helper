---
base_model: Qwen/Qwen3-8B
library_name: peft
pipeline_tag: text-generation
tags:
- lora
- qlora
- course-planning
---

# Objective-parameter checkpoint

The active rank-8 LoRA adapter for Qwen3-8B. Its raw response is restricted to four
objective-parameter groups; the external optimiser chooses the course path.
NF4 frozen base, BF16 computation, LoRA alpha 16, dropout 0.05.

The current checkpoint follows an 84-example transcript correction and a
120-example English compatibility round (including replay, not 204 unique examples).
The latter selected epoch 2 by validation loss. Labels are synthetic reviewed-policy
targets rather than empirical workload outcomes. The three original comparison
failures were taught and retested; separate synthetic export checks are in the reports.

Weights SHA-256: `62fd3c3bcb8585b36e47e806d9c3c7126801e81953e7b5448a0e11a40d7ec1e8`.
Frozen base revision: `b968826d9c46dd6066d109eabc6255188de91218`.
Use the root README to restore the frozen base and run the external-tool pipeline.
