@echo off
setlocal
cd /d "%~dp0"
set "CITYU_QUANTIZE_4BIT=1"
set "PYTHONUTF8=1"
set "OPENBLAS_NUM_THREADS=1"
.venv\Scripts\python.exe -u degree_chain_training.py before > reports\degree-chain-policy\before.log 2>&1
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u train.py --epochs 2 --accumulation 4 --max-length 6144 --lr 0.00005 --data-dir data/degree-chain-policy --output-dir adapters/degree-chain-policy --report-dir reports/degree-chain-policy --init-adapter adapters/timetable-grounded-correction --assistant-logits-only > reports\degree-chain-policy\train.log 2>&1
if errorlevel 1 exit /b 1
copy /y adapters\timetable-grounded-correction\base_loading.json adapters\degree-chain-policy\base_loading.json > nul
.venv\Scripts\python.exe -u degree_chain_training.py after > reports\degree-chain-policy\after.log 2>&1
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u degree_chain_training.py release > reports\degree-chain-policy\release.log 2>&1
exit /b %errorlevel%
