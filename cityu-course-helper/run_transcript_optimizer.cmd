@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
if "%~1"=="" (
  .venv\Scripts\python.exe transcript_objective_input.py --interactive
  if errorlevel 1 exit /b 1
  pause
  exit /b 0
)
.venv\Scripts\python.exe transcript_objective_input.py --source "%~1"
exit /b %errorlevel%
