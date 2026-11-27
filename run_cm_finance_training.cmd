@echo off
setlocal
cd /d "%~dp0"
set "CITYU_QUANTIZE_4BIT=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "OPENBLAS_NUM_THREADS=1"
set "TOKENIZERS_PARALLELISM=false"
.venv\Scripts\python.exe -u cm_finance_training.py before > reports\cm-finance-background\before.log 2>&1
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u train.py --epochs 2 --accumulation 4 --max-length 4096 --lr 0.00006 --data-dir data/cm-finance-background --output-dir adapters/cm-finance-background --report-dir reports/cm-finance-background --init-adapter adapters/cm-cs-programme-v6 --assistant-logits-only > reports\cm-finance-background\train.log 2>&1
if errorlevel 1 exit /b 1
copy /y adapters\cm-cs-programme-v6\base_loading.json adapters\cm-finance-background\base_loading.json > nul
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u cm_finance_training.py after > reports\cm-finance-background\after.log 2>&1
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -u cm_finance_training.py release
