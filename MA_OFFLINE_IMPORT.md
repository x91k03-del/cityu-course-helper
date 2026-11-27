# MA timetable collection without automated AIMS access

The previous automated deep-link approach was rejected by AIMS. It is now disabled. The `.cmd` launchers import local saved files only; they do not launch a browser, navigate to Banner, make HTTP requests, inspect browser sessions or collect credentials.

## 1. Get the data through normal CityU access

In your normal browser, open [CityU Portal](https://www.cityu.edu.hk/portal/), sign in, and follow:

**Academic & Research > Academic Services > Master Class Schedule**

Select **Semester A 2026/27 / 202609**, subject **MA**, and all course numbers, then search. Use the site's normal controls to show the timetable details. Do not start from the previously rejected deep link. This Portal route is documented by [CityU ARRO](https://www.cityu.edu.hk/arro/creg/schd_main.htm).

If the normal Portal route also displays the security message, stop there and use CityU's support service. This importer does not bypass access restrictions.

## 2. Save the displayed timetable

Create/save files into:

```text
F:\CODEX\cityu-course-helper\MA_SAVED_PAGES
```

Use your browser's **Save page as** command (usually Ctrl+S). If available, choose **Webpage, single file / MHTML** (`.mhtml` or `.mht`); otherwise save HTML (`.html` or `.htm`). Keep these saved pages local.

- A bulk result table can contain many MA courses. Save every results page needed to cover the full subject.
- If the timetable is inside a frame, MHTML may include the frame content. If the import report finds only a portal wrapper, use the browser's normal frame/open-page controls and save the actual timetable page.
- Individual course pages can be named `MA1502.html`, `MA2508.html`, etc. Bulk pages can have any filename when their tables include Subject/Course or Course Code columns.
- Saving a page that merely links to the course detail pages does not capture those linked timetables. Open/save the actual displayed meeting tables.
- PDFs and screenshots are not parsed by this importer. Use HTML/MHTML for table structure.

The existing `GE_SEMA/sampleGE/GE1101.html` demonstrates the type of saved page, but is a Summer GE example and is not MA Semester A data.

## 3. Import

Double-click **`import_ma_timetable.cmd`**, or run:

```powershell
cd F:\CODEX\cityu-course-helper
.\import_ma_timetable.cmd
```

The old `collect_ma_timetable.cmd` now uses this same offline method. Both avoid PowerShell execution-policy changes.

Other folders/subjects:

```powershell
.\import_ma_timetable.cmd --input "D:\My saved timetable pages"
.\import_ma_timetable.cmd --all-subjects
.\import_ma_timetable.cmd --expected-courses .\expected_ma_courses.txt
```

The optional expected-course file contains one code per line. It lets the importer report missing codes; it does not establish which sections should exist or whether every university course was exported.

## Output and checks

Output is under `data\banweb-offline\202609\MA\`:

- `meeting_rows.json`: course, CRN, section, weekday(s), clock times, room and date ranges where available.
- `sections.json`: grouped section meetings.
- `offline_import.json`: source-file hashes, imported counts, unrecognized tables, term evidence and missing expected courses.
- `run.json`: coverage and unknown-time/date counts.

The importer expands rowspans, filters explicit subject/course columns and explicit numeric term columns, and removes duplicate saved meeting rows. Embedded source-term conflicts are rejected. Missing times/dates remain unknown. Where a saved file has no source-term evidence, the term is labelled as your selection rather than independently verified.

Only course-table records are written to the output. Login HTML, cookies, hidden form values and full authenticated pages are not copied into the parsed JSON. Your original saved files may still contain private portal information; they stay local and are excluded from Git.

Coverage is limited to what the saved files actually contain. The importer never assumes an incomplete export contains all MA courses. No model training runs automatically. Real timetable data are still needed before further MA timetable training.

## Validation

The offline importer is tested on multi-course tables, MHTML frames, term/subject filtering, duplicate pages, missing coverage, source conflicts and error pages. It has not yet been validated on a saved page from your authenticated Master Class Schedule; unsupported layouts are reported for correction rather than treated as valid data.
