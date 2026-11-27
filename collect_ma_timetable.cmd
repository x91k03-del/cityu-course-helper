@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
if not exist "%~dp0.collector-venv\Scripts\python.exe" (
    echo Collector Python environment is missing. See MA_COLLECTOR.md for setup.
    exit /b 1
)
pushd "%~dp0"
if errorlevel 1 exit /b 1
echo Using offline import. Sign in through CityU Portal in your normal browser and save timetable pages first.
"%~dp0.collector-venv\Scripts\python.exe" "%~dp0import_ma_timetable.py" %*
set "collector_exit=%errorlevel%"
popd
if "%~1"=="" pause
exit /b %collector_exit%
