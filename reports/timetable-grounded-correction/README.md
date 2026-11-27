# Timetable-grounded fine-tuning and rerun

Actual supervised QLoRA training completed: initial 263/24 train/validation, 2 epochs; corrective 213/16, 1 epoch(s). Previous checkpoints and simulations remain preserved.

Strict source rule: exact saved terms and CM/CS-compatible sections from the supplied MA/CS folders; source hashes verified. No opposite-semester/future-year substitution. This run does not import separate GE folders.

EF surcharge: lambda_background * 1.5 without passed or declared finance study; zero with finance study. This is additional to ordinary mismatch, never a missing-prerequisite fee.

## Evaluation

{
  "before": {
    "heldout_policy": {
      "passed": 12,
      "total": 20
    },
    "familiar_schedule_diagnostics": {
      "passed": 7,
      "total": 10
    },
    "historical_regression": {
      "passed": 5,
      "total": 6
    }
  },
  "after": {
    "heldout_policy": {
      "passed": 20,
      "total": 20
    },
    "familiar_schedule_diagnostics": {
      "passed": 10,
      "total": 10
    },
    "historical_regression": {
      "passed": 4,
      "total": 6
    }
  }
}

## Entering Year-1 CM rerun

Incomplete: the eligible source pool contains only MA1300, MA2509. Five courses cannot be selected. No courses or credits were committed and graduation requirements were not fulfilled.

Raw model response: `{"status": "infeasible", "selected_option_ids": [], "course_count": 0}`

Missing compatible timetable evidence for mandatory courses: CHEM1200, CS1302, CS2360, CS2468, CSCI1001, CSCI1002, GE1401, GE1501, GE1601, GE2401, MA4530, PHY1201.

This is not proof that the real programme cannot be completed. The snapshot/section scope is incomplete; future offerings and official registration are unverified.

Run the new checkpoint: `.\.venv\Scripts\python.exe grounded_model.py degree --profile data/markov-repair/year1_CM.json --output reports/timetable-grounded/user_degree.json`

Inspect EF with `grounded_model.py assess --profile <profile.json> --course EF3320 --output <result.json>`; the profile term must match the intended semester.

The report, actual raw decodes, guarded reruns, training progress, snapshots and hashes are all retained in this run folder.
