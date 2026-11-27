@echo off
setlocal
cd /d "%~dp0"
set "TEMP=F:\CODEX\cityu-course-helper\.cache\tmp"
set "TMP=%TEMP%"
set "TEXMFVAR=F:\CODEX\cityu-course-helper\.cache\texlive\var"
set "TEXMFCONFIG=F:\CODEX\cityu-course-helper\.cache\texlive\config"
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error Phase2_Report.tex
if errorlevel 1 exit /b 1
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error Phase2_Report.tex
if errorlevel 1 exit /b 1
echo Compiled Phase2_Report.pdf
