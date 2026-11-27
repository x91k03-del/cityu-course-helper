# CityU MA timetable import

The automated login/deep-link collector is retired after AIMS rejected access. The old `collect_ma_timetable.cmd` now runs the offline importer and does not open a browser.

Follow [MA_OFFLINE_IMPORT.md](MA_OFFLINE_IMPORT.md) for the current instructions: sign in normally through CityU Portal, open Master Class Schedule, save the actual MA meeting tables as HTML or MHTML, and import those files locally.

```powershell
cd F:\CODEX\cityu-course-helper
.\import_ma_timetable.cmd
```

Save pages in `F:\CODEX\cityu-course-helper\MA_SAVED_PAGES`. The default term is Semester A 2026/27 (`202609`). Output is in `data\banweb-offline\202609\MA`.

Dependencies are already installed in `.collector-venv`. For a fresh copy, install `collector-requirements.lock.txt` into that environment. The offline importer requires Beautiful Soup; it does not require browser installation or a browser session.

Local parser checks:

```powershell
.\.collector-venv\Scripts\python.exe -m unittest test_ma_offline_import test_banweb_collector
```

These checks use synthetic saved pages. A real saved CityU timetable is still required to validate its layout and collect actual MA meetings. No model training runs automatically.
