param(
    [ValidateSet('lookup','predict','overlap','evaluate','rules')][string]$Action='lookup',
    [string]$Course='GE1356',
    [string]$Section='',
    [string]$OtherCourse='GE2213',
    [switch]$MemoryOnly
)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$taskPython=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
Push-Location $PSScriptRoot
try {
    if ($Course -match '^MA\d{4}$') {
        if ($Action -eq 'overlap') {throw 'MA section bundles and teaching weeks are not verified. Use lookup to inspect the saved meetings.'}
        $taskArgs=@('ma_timetable.py',$Action,'--course',$Course)
    } else {
        if ($Action -eq 'rules') {throw 'Use rules with an MA course.'}
        $taskArgs=@('ge_timetable.py',$Action,'--course',$Course,'--other-course',$OtherCourse)
    }
    if ($Section) {$taskArgs+=@('--section',$Section)}
    if ($MemoryOnly) {$taskArgs+='--memory-only'}
    & $taskPython @taskArgs
    if ($LASTEXITCODE -ne 0) {throw "Timetable command failed: $LASTEXITCODE"}
} finally {Pop-Location}
