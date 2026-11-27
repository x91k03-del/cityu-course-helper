$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
Push-Location $PSScriptRoot
try {
    $taskPython=Join-Path $PSScriptRoot '.collector-venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $taskPython)) {
        & '.\.venv\Scripts\python.exe' -m venv '.collector-venv'
        if ($LASTEXITCODE -ne 0) {throw 'Could not create collector environment.'}
    }
    & $taskPython -m pip install -r collector-requirements.txt
    if ($LASTEXITCODE -ne 0) {throw 'Could not install collector libraries.'}
    Write-Host 'Ready. Uses installed Microsoft Edge; no separate browser download is required.'
    Write-Host 'Run .\collect_ma_timetable.ps1 to open CityU login.'
} finally {Pop-Location}
