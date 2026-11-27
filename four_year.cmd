@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
set "OPENBLAS_NUM_THREADS=1"
pushd "%~dp0"
if errorlevel 1 exit /b 1
if /I "%~1"=="report" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0preparation_report.py"
) else if /I "%~1"=="evaluate" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0preparation_training.py" evaluate
) else if /I "%~1"=="rollout" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0preparation_training.py" rollout
) else (
    "%~dp0.venv\Scripts\python.exe" "%~dp0four_year_markov.py" %*
)
set "four_year_exit=%errorlevel%"
popd
exit /b %four_year_exit%
