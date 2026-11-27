@echo off
setlocal
cd /d "%~dp0"
set "CITYU_QUANTIZE_4BIT=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "OPENBLAS_NUM_THREADS=1"
set "TOKENIZERS_PARALLELISM=false"
.venv\Scripts\python.exe -u timetable_grounded_training.py before > reports\timetable-grounded\before.log 2>&1
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u train.py --epochs 2 --accumulation 4 --max-length 4096 --lr 0.00006 --data-dir data/timetable-grounded --output-dir adapters/timetable-grounded --report-dir reports/timetable-grounded --init-adapter adapters/cm-finance-background --assistant-logits-only > reports\timetable-grounded\train.log 2>&1
if errorlevel 1 exit /b 1
copy /y adapters\cm-finance-background\base_loading.json adapters\timetable-grounded\base_loading.json > nul
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u timetable_grounded_training.py after > reports\timetable-grounded\after.log 2>&1
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u timetable_grounded_training.py release > reports\timetable-grounded\release.log 2>&1
exit /b %errorlevel%
