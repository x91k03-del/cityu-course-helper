# Computing Mathematics MA schedules and requirements

The 17 user-saved AIMS PDFs in `GE_SEMA/MA` are the source for Semester A 2026/27 (`202609`), captured on 15 November 2026. Import uses local PDF text only, without a CityU connection, browser session or login.

Only sections whose **only-for-Major** list contains the exact token **CM** are selected. CM means Computing Mathematics / BSCM. Lists such as `CFFT, CM` count; `CRM1`, `not for Major: CM`, minor-only sections and unspecified major permissions do not. All CM alternatives are preserved. This does not imply that every section is available to every CM student: programme, cohort and other restrictions remain attached.

The snapshot contains **16 selected sections and 20 meetings across 11 courses**. The other six saved courses have no explicitly CM-listed section: **MA1508, MA2001, MA2158, MA2172, MA2185 and MA2510**. Their requirements are retained, but their meeting times do not enter the MA training targets or lookup results. This is a statement about these saved pages, not a claim that a course can never be offered to CM students.

## Use

These commands avoid PowerShell script-policy changes:

```powershell
cd F:\CODEX\cityu-course-helper
.\ma_timetable.cmd lookup --course MA1300
.\ma_timetable.cmd rules --course MA2508
.\ma_timetable.cmd check --course MA2508 --completed MA1503
.\ma_timetable.cmd check --course MA2508 --completed MA1503,MA1508
.\ma_timetable.cmd check --course MA1502 --section CB1 --no-completed-courses --programme BSCSIU4 --cohort 2026
.\ma_timetable.cmd predict --course MA2508 --section CA1
```

`lookup` and `rules` return exact local source records. `check` evaluates the supplied completed-course list against the combined requirement expression and exclusive courses. Omitted completion data mean unknown; `--no-completed-courses` explicitly means none. Programme/cohort values are checked when supplied; missing values remain unknown. A passed encoded condition is not university approval or proof of current seats.

`predict` loads the continued-training Qwen3-8B adapter at `adapters/bscm-ma-timetable`, supplies the selected saved section as context and shows its raw answer beside the exact snapshot. Specify a section when several exist. `--memory-only` is a diagnostic that omits the source context; use exact lookup records for planning.

After training and evaluation, `data/active_timetable_adapter.json` records the activated timetable adapter and its weights hash. GE model predictions also use that timetable adapter. Exact GE/MA lookups continue to read the source snapshots.

The existing BSCM `ask` command now routes MA timetable and requirement questions to this source lookup. For example:

```powershell
.\.venv\Scripts\python.exe bscm.py ask --question "What are the prerequisites for MA4542?"
.\.venv\Scripts\python.exe bscm.py ask --question "When does MA1300 section T02 meet in Sem A 2026/27?"
```

## Requirements

The source heading combines **Pre-requisites/precursors**. It does not identify which listed course is a strict prerequisite versus a precursor. The dataset retains that distinction as unverified rather than relabelling every condition as a strict prerequisite. AND/OR parentheses and exclusive courses are preserved.

- MA2508 and MA2510: `MA1201 OR MA1301 OR (MA1503 AND MA1508)`. MA1503 alone does not satisfy the last branch.
- MA4542: `MA2508 AND (MA3526 OR MA3524)`. Either MA3526 or MA3524 must accompany MA2508.
- MA1502 has a CM section CB1 restricted to programme BSCSIU4 and cohort 2026. A CM major alone is insufficient.
- MA1300 retains C01 and both tutorial options T01/T02. They are alternative component records; the pages do not verify the allowed registration bundles.

Being a BSCM student or being in a particular year does not prove completion of any course. Exclusive-course credits may block registration even when the preparation expression is satisfied. The helper does not automatically mark these records as eligible scheduler options.

## Rebuild and verification

```powershell
.\.venv\Scripts\python.exe ma_timetable.py build
.\.venv\Scripts\python.exe -m unittest test_ma_timetable test_ge_timetable
.\.venv\Scripts\python.exe ma_timetable.py evaluate
```

The importer validates source course/term, hashes each PDF, reads continuation meetings and wrapped room/restriction text, and rejects unsupported requirement syntax. Exact data are in `data/ma-timetable/courses.json` and `sections.json`. Training, dataset and evaluation records are in `reports/ma-timetable`. The human-readable results are in [MA_CM_REPORT.md](MA_CM_REPORT.md).

The new dataset uses 331 training, 39 validation and 137 test examples, including earlier GE/BSCM examples to retain prior tasks. All captured facts are intentionally taught. Validation/test examples use different prompt wording and supplied-evidence checks; they do not measure unseen-fact or real-student generalization.

Saved seat counts are historical. Date ranges do not specify holidays or teaching weeks. Lecture/tutorial linkage, complete registration eligibility, current seats and schedule changes require confirmation with CityU.
