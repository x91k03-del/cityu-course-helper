@echo off
setlocal
cd /d "%~dp0"
set "CITYU_QUANTIZE_4BIT=1"
set "PYTHONUTF8=1"
set "OPENBLAS_NUM_THREADS=1"
.venv\Scripts\python.exe -u gpt_course_teacher.py before > reports\gpt-course-relations\before.log 2>&1
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u train.py --epochs 2 --accumulation 4 --max-length 4096 --lr 0.00005 --data-dir data/gpt-course-relations --output-dir adapters/gpt-course-relations --report-dir reports/gpt-course-relations --init-adapter adapters/timetable-grounded-correction --assistant-logits-only > reports\gpt-course-relations\train.log 2>&1
if errorlevel 1 exit /b 1
copy /y adapters\timetable-grounded-correction\base_loading.json adapters\gpt-course-relations\base_loading.json > nul
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u gpt_course_teacher.py after > reports\gpt-course-relations\after.log 2>&1
exit /b %errorlevel%
