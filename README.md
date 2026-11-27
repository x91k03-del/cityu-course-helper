# CityU Course Helper

Local course planning for Computing Mathematics (CM) and Computer Science (CS),
with a fine-tuned Qwen3-8B parameter model and external reward optimisation.

## Current released pipeline

Transcript PDF or natural-language input -> external fact reader -> Qwen objective
parameters -> strict validator -> external dynamic-programming optimiser.

Qwen returns only `reward_parameters`, `course_relations`, `penalty_weights` and
`stream_reward_multiplier`. It does not return a timetable or select courses.
Invalid responses are rejected before optimisation; no silent fallback is used.

## Included checkpoint and evidence

- **Current checkpoint:** `adapters/objective-parameters/`, including the exact
  trained LoRA weights, configuration and tokenizer files. This is the active
  rank-8 QLoRA adapter, not a merged standalone copy of the frozen 8B base.
- **Checkpoint hash:** `62fd3c3bcb8585b36e47e806d9c3c7126801e81953e7b5448a0e11a40d7ec1e8`.
- **Base revision:** `b968826d9c46dd6066d109eabc6255188de91218` of `Qwen/Qwen3-8B`.
  `tools/restore_base_model.py` downloads this revision and verifies recorded hashes.
- **Test inputs and outputs:** start with [`examples/`](examples/README.md).
  Full raw comparisons, training records and audits are in
  `reports/transcript-parameter-pipeline/`.
- **Training data:** `data/transcript-parameters/` and `data/objective-parameters/`.
- **Readable reports:** `output/pdf/transcript-parameter-pipeline/`.
- **Course evidence:** parsed data, source provenance, saved CM/CS/GE course PDFs,
  programme documents and A/B snapshots are included under `data/`, `sources/`
  and `GE_SEMA/`.

The package also retains historical code, datasets, reports, editable LaTeX and
presentation materials. `README.history.md` describes earlier experiments;
historical checkpoints are not bundled and earlier commands may require them.

## Setup and run

Use Python with an NVIDIA CUDA-capable GPU for live Qwen inference. The original
run used an RTX 5090 (32 GB), CUDA PyTorch 2.7.1 and four-bit NF4 base loading.
Training peaked at about 10.6 GiB allocated GPU memory; inference requirements
vary with input length. Install the CUDA PyTorch build suitable for your system
before installing `requirements.txt`.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools/verify_checkpoint.py
.\.venv\Scripts\python.exe tools/restore_base_model.py
.\run_transcript_optimizer.cmd F
```

Use `N` or `M` for the other complete fictional demonstrations. With another
transcript or English message, the interface exports parameters and parsed facts;
it requires a supported complete planning context before certifying a degree path.
Poppler `pdftotext` is preferred for PDFs; a `pypdf` layout fallback is included.
Project library caches and temporary files stay under the cloned project folder.

### Reproduce the small checks without loading base weights

```powershell
.\.venv\Scripts\python.exe -m unittest test_transcript_parameter_pipeline test_markov_planner test_llm_reward_external
```

To rerun the paired GPU comparison with the current checkpoint:

```powershell
.\.venv\Scripts\python.exe objective_english_correction.py paired
.\.venv\Scripts\python.exe objective_english_correction.py evaluate
.\.venv\Scripts\python.exe objective_english_correction.py heldout
```

These commands overwrite their generated comparison outputs. Parent adapters used
in earlier training rounds are recorded in the logs but are not needed for inference.

## Recorded results and limits

- Three transcript-versus-structured-prompt pairs returned equal parameters and
  equal external paths after corrective training. They are familiar corrective retests.
- Eight separate synthetic parameter exports and four new English controls passed.
  Policy and formatting families remain familiar; this is not real-student validation.
- Each of the three CM demonstrations reaches 122 projected credits, with four
  distributional GEs across Areas 1-3 and at least 20 mathematics-elective credits.
- Exact dynamic programming and independent enumeration of 64 allowed elective
  assignments verify the maximum **within each supplied fixed completion context**.
  This is not a global search over every possible curriculum reallocation.
- The approved repeated A/B snapshots are simulation assumptions. Twenty-five
  future credits retain pending timetable details; class times are not invented.
- The current complete-degree demonstration is CM-specific. Historical CM/CS
  datasets and policy tools remain included; full-degree CS completion is not
  claimed by the three CM transcript tests.

Actual student transcripts, credentials, browser profiles, virtual environments,
downloaded frozen base weights, temporary build dependencies and unrelated archives
are excluded. Only fictional student examples are packaged. The original transcript
was used to understand layout, not as model training data. Course materials retain
their source owners' rights; source provenance is preserved in `sources/`.
