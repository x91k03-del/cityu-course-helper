"""Publish the measured timetable adaptation and readable snapshot."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
imp=read('reports/ge-timetable/import.json');data=read('reports/ge-timetable/dataset.json');train=read('reports/ge-timetable/training.json');ev=read('reports/ge-timetable/evaluation.json');tests=read('reports/ge-timetable/parser_tests.json')
assert train['status']=='complete' and tests['errors']==tests['failures']==0
# Correct the generic trainer's legacy label description for this published-data run.
train['label_type']='published_GE_timetable_snapshot_with_BSCM_replay'
(ROOT/'reports/ge-timetable/training.json').write_text(json.dumps(train,indent=2),encoding='utf-8')
sections=read('data/ge-timetable/sections.json')
lines=['# GE timetable snapshot: Semester A 2026/27','',
       'Captured from rendered public CityU GE course pages on 15 November 2026. ARRO Master Class Schedule prevails if different. Capacity is not available seats. Calendar dates, teaching weeks, section linking and eligibility were not verified.','']
for code in sorted({s['course_code'] for s in sections}):
    ss=[s for s in sections if s['course_code']==code]
    lines += ['## '+code+' - '+ss[0]['title'],'','Source: https://www.cityu.edu.hk/ge_info/Course/'+code,'',
              '| CRN | Section | Type | Capacity | Day | Time | Building | Room |','| --- | --- | --- | --- | --- | --- | --- | --- |']
    for s in ss:
        for m in s['meetings']:
            clock=(m['start_time']+' - '+m['end_time']) if m['start_time'] else 'Not published'
            lines.append('| '+' | '.join(str(x or 'Not published') for x in [s['crn'],s['section'],s['section_type'],str(s['capacity']),m['day'],clock,m['building'],m['room']])+' |')
    lines.append('')
(ROOT/'GE_SEMA_TIMETABLE.md').write_text('\n'.join(lines),encoding='utf-8')
text=r'''# Semester A GE timetable update

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

'''
text+=f"- {imp['courses']} courses from all three user-supplied availability PDFs.\n- {imp['meeting_rows']} meeting rows grouped into {imp['sections']} CRN/section records.\n- {imp['missing_day_time_rows']} rows have no published day/time and remain null (GE1601). They are not assumed clash-free.\n- {tests['tests']} parser/coverage/boundary checks passed.\n\n"
text+=r'''The supplied `GE1101.html` example contains Summer sections, not Semester A. It is used as a negative parser control and is excluded from the Semester A dataset. Same-section multiple-room rows (for example GE1128 and GE1341) are retained because the source does not identify the corresponding calendar dates.

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

'''
text+=f"- Training / validation / test examples: {data['examples']}.\n- Two continued-training epochs from the BSCM adapter; selected epoch {train['selected_epoch']}.\n- Training time: {train['seconds']/60:.1f} minutes. Peak allocated GPU memory: {train['peak_gpu_allocated_gb']:.2f} GiB.\n\n"
text+='| Task | Prior BSCM adapter | Timetable adapter |\n| --- | --- | --- |\n'
for task in ['recall','grounded']:
    a,b=ev['bscm'][task],ev['timetable'][task]
    text+=f"| {task} | {a['passed']}/{a['total']} | {b['passed']}/{b['total']} |\n"
text+='\nWeekday/start/end matches, ignoring room ordering but requiring the correct course, section and term:\n\n'
for task in ['recall','grounded']:
    a,b=ev['bscm'][task],ev['timetable'][task]
    text+=f"- {task}: prior {a['time_fields_match']}/{a['total']}; new {b['time_fields_match']}/{b['total']}.\n"
text+='\n**Result:** this fine-tune did not produce reliable memory-only timetable recall. Both adapters passed all supplied-record extraction checks, so no extraction accuracy gain was demonstrated in this sample. Production queries therefore supply the saved record as context or return it directly. The raw memory failures remain in the evaluation files; they are not replaced by lookup answers.\n'
text+='''
Recall asks for a taught section without supplying its meeting details. Grounded extraction supplies the saved meeting record with new wording. Both use exact JSON equality, including all room rows, null date/week fields and the confirmation flag. Every snapshot fact is deliberately taught; this is not an unseen-course benchmark. Validation question wording selects the checkpoint; evaluation responses remain uncorrected in `reports/ge-timetable/predictions.json`. No claim is made that weight memory is a reliable live timetable.

## Files and provenance

- `GE_SEMA_TIMETABLE.md`: readable complete timetable.
- `data/ge-timetable/meeting_rows.json`: all original captured rows with source URLs.
- `data/ge-timetable/sections.json`: normalized sections and meeting arrays.
- `sources/ge-timetable/semester_a_browser_capture.txt`: serialized observed DOM rows, retained for reproducibility.
- `reports/ge-timetable/import.json`: coverage, snapshot date and source hash.
- `reports/ge-timetable/training.json` and `evaluation.json`: measured run results.

The source is https://www.cityu.edu.hk/ge_info/Search/ and the linked public course-detail pages. This is a dated snapshot, not a live-seat or date-specific registration guarantee. Existing handbook/graduation rules and workload labels have not been inferred from these timetable rows.
'''
(ROOT/'GE_TIMETABLE_UPDATE.md').write_text(text,encoding='utf-8')
print('TIMETABLE_REPORT_COMPLETE')
