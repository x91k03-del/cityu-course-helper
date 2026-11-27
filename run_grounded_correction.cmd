@echo off
setlocal
cd /d "%~dp0"
set "CITYU_QUANTIZE_4BIT=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "OPENBLAS_NUM_THREADS=1"
.venv\Scripts\python.exe -u grounded_correction.py build
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u train.py --epochs 1 --accumulation 4 --max-length 4096 --lr 0.00004 --data-dir data/timetable-grounded-correction --output-dir adapters/timetable-grounded-correction --report-dir reports/timetable-grounded-correction --init-adapter adapters/timetable-grounded --assistant-logits-only > reports\timetable-grounded-correction\train.log 2>&1
if errorlevel 1 exit /b 1
copy /y adapters\timetable-grounded\base_loading.json adapters\timetable-grounded-correction\base_loading.json > nul
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u grounded_correction.py after > reports\timetable-grounded-correction\after.log 2>&1
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u grounded_correction.py release > reports\timetable-grounded-correction\release.log 2>&1
exit /b %errorlevel%
