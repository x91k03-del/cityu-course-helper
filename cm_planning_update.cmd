@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
set "OPENBLAS_NUM_THREADS=1"
pushd "%~dp0"
if errorlevel 1 exit /b 1
"%~dp0.venv\Scripts\python.exe" "%~dp0cm_planning_update.py" %*
set "planner_exit=%errorlevel%"
popd
exit /b %planner_exit%
