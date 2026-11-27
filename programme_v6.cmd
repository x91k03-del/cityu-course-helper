@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "OPENBLAS_NUM_THREADS=1"
pushd "%~dp0"
"%~dp0.venv\Scripts\python.exe" "%~dp0programme_v6.py" %*
set "programme_exit=%errorlevel%"
popd
exit /b %programme_exit%
