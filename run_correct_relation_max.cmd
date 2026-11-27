@echo off
setlocal
cd /d "%~dp0"
set "CITYU_QUANTIZE_4BIT=1"
set "PYTHONUTF8=1"
set "OPENBLAS_NUM_THREADS=1"
.venv\Scripts\python.exe correct_relation_max.py build
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u train.py --epochs 1 --accumulation 4 --max-length 4096 --lr 0.00004 --data-dir data/gpt-course-relations-max --output-dir adapters/gpt-course-relations-max --report-dir reports/gpt-course-relations-max --init-adapter adapters/gpt-course-relations --assistant-logits-only > reports\gpt-course-relations-max\train.log 2>&1
if errorlevel 1 exit /b 1
copy /y adapters\gpt-course-relations\base_loading.json adapters\gpt-course-relations-max\base_loading.json > nul
.venv\Scripts\python.exe -u correct_relation_max.py after > reports\gpt-course-relations-max\after.log 2>&1
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u correct_relation_max.py finish > reports\gpt-course-relations-max\release.log 2>&1
exit /b %errorlevel%
