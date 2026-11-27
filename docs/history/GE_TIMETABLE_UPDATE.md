# Semester A GE timetable update

The 2026/27 Semester A GE timetable has been collected and added to the local project. A separate continued-training adapter is saved at `adapters/bscm-timetable/`; the BSCM and original adapters remain intact.

## Use it

```powershell
cd F:\CODEX\cityu-course-helper
.\run_timetable.ps1 -Action lookup -Course GE1356
.\run_timetable.ps1 -Action overlap -Course GE1105 -OtherCourse GE1205
.\run_timetable.ps1 -Action predict -Course GE1356
.\run_bscm.ps1 -Action ask -Question "When does GE1356 meet in Sem A 2026/27?"
```

`lookup` returns exact saved records without loading the GPU model. `overlap` tests all listed section pairs using published weekdays and clock times; it does not verify teaching-week overlap or complete lecture/tutorial/lab combinations. `predict` loads the new adapter with the saved section record as context and shows its generated answer beside the verified snapshot. Use the snapshot for exact times. The optional `-MemoryOnly` switch omits that context for diagnostic testing only. The BSCM question command routes GE timetable questions to the verified lookup.

## Data collected

- 63 courses from all three user-supplied availability PDFs.
- 290 meeting rows grouped into 287 CRN/section records.
- 30 rows have no published day/time and remain null (GE1601). They are not assumed clash-free.
- 8 parser/coverage/boundary checks passed.

The supplied `GE1101.html` example contains Summer sections, not Semester A. It is used as a negative parser control and is excluded from the Semester A dataset. Same-section multiple-room rows (for example GE1128 and GE1341) are retained because the source does not identify the corresponding calendar dates.

No calendar dates or teaching weeks appear in the collected section table. Those fields remain null. Section capacity is not the number of remaining seats. Missing registration restrictions and lecture/tutorial/laboratory linkage must still be checked against AIMS. These records are not automatically marked as complete, eligibility-verified scheduler options.

## Reusable importer

```powershell
.\.venv\Scripts\python.exe ge_timetable.py import
.\.venv\Scripts\python.exe ge_timetable.py build
.\.venv\Scripts\python.exe test_ge_timetable.py
```

The importer validates course coverage against the saved availability PDFs, accepts the browser capture and optionally newer HTML files under `sources/ge-timetable/html/`, parses the section table, filters the exact term, validates clocks and groups repeated section rows. Training-data generation is explicit; it never silently retrains the model.

An optional `ge_timetable.py fetch` command downloads public course HTML at two-second intervals and checks robots rules. It stops when a page is blocked or lacks the required section table. Direct requests in this session received an access challenge, so this collection used normal browser navigation and rendered-DOM extraction instead; no challenge was bypassed and no browser cookies were exported. To refresh through saved pages, put course-code-named HTML files in the HTML directory and run `import` again. Snapshot dates should be updated together with the capture metadata when preparing a new dated collection.

## Training and measured evaluation

- Training / validation / test examples: {'train': 654, 'validation': 32, 'test': 32}.
- Two continued-training epochs from the BSCM adapter; selected epoch 2.
- Training time: 8.2 minutes. Peak allocated GPU memory: 17.36 GiB.

| Task | Prior BSCM adapter | Timetable adapter |
| --- | --- | --- |
| recall | 0/12 | 0/12 |
| grounded | 12/12 | 12/12 |

Weekday/start/end matches, ignoring room ordering but requiring the correct course, section and term:

- recall: prior 0/12; new 0/12.
- grounded: prior 12/12; new 12/12.

**Result:** this fine-tune did not produce reliable memory-only timetable recall. Both adapters passed all supplied-record extraction checks, so no extraction accuracy gain was demonstrated in this sample. Production queries therefore supply the saved record as context or return it directly. The raw memory failures remain in the evaluation files; they are not replaced by lookup answers.

Recall asks for a taught section without supplying its meeting details. Grounded extraction supplies the saved meeting record with new wording. Both use exact JSON equality, including all room rows, null date/week fields and the confirmation flag. Every snapshot fact is deliberately taught; this is not an unseen-course benchmark. Validation question wording selects the checkpoint; evaluation responses remain uncorrected in `reports/ge-timetable/predictions.json`. No claim is made that weight memory is a reliable live timetable.

## Files and provenance

- `GE_SEMA_TIMETABLE.md`: readable complete timetable.
- `data/ge-timetable/meeting_rows.json`: all original captured rows with source URLs.
- `data/ge-timetable/sections.json`: normalized sections and meeting arrays.
- `sources/ge-timetable/semester_a_browser_capture.txt`: serialized observed DOM rows, retained for reproducibility.
- `reports/ge-timetable/import.json`: coverage, snapshot date and source hash.
- `reports/ge-timetable/training.json` and `evaluation.json`: measured run results.

The source is https://www.cityu.edu.hk/ge_info/Search/ and the linked public course-detail pages. This is a dated snapshot, not a live-seat or date-specific registration guarantee. Existing handbook/graduation rules and workload labels have not been inferred from these timetable rows.
