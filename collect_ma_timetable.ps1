param(
    [string]$Term='202609',
    [string]$Subject='MA',
    [switch]$AllSubjects,
    [string]$CoursesFile='',
    [switch]$Resume,
    [ValidateSet('msedge','chrome','chromium')][string]$Browser='msedge'
)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$taskPython=Join-Path $PSScriptRoot '.collector-venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {throw 'Run setup_ma_collector.ps1 once first.'}
Push-Location $PSScriptRoot
try {
    $taskArgs=@('collect_banweb_timetable.py','--term',$Term,'--subject',$Subject,'--channel',$Browser)
    if ($AllSubjects) {$taskArgs+='--all-subjects'}
    if ($CoursesFile) {$taskArgs+=@('--courses-file',$CoursesFile)}
    if ($Resume) {$taskArgs+='--resume'}
    & $taskPython @taskArgs
    if ($LASTEXITCODE -ne 0) {throw "Collector stopped with exit code $LASTEXITCODE. Previously saved courses remain available for -Resume."}
} finally {Pop-Location}
