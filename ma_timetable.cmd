@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
pushd "%~dp0"
if errorlevel 1 exit /b 1
if "%~1"=="" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0ma_timetable.py" lookup --course MA2508
) else (
    "%~dp0.venv\Scripts\python.exe" "%~dp0ma_timetable.py" %*
)
set "ma_exit=%errorlevel%"
popd
if "%~1"=="" pause
exit /b %ma_exit%
