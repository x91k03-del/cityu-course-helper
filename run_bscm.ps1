param(
    [ValidateSet('ask','score','evaluate')][string]$Action='ask',
    [string]$Question='Which core computing courses are listed for BSCM?',
    [string]$Course='CS2360',
    [string]$Profile=''
)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$env:HF_HUB_OFFLINE='1'
$taskPython=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
Push-Location $PSScriptRoot
try {
    if ($Action -eq 'ask') { & $taskPython bscm.py ask --question $Question }
    elseif ($Action -eq 'evaluate') { & $taskPython bscm.py evaluate }
    elseif ($Profile) { & $taskPython bscm.py score --course $Course --profile $Profile }
    else { & $taskPython bscm.py score --course $Course }
    if ($LASTEXITCODE -ne 0) { throw "BSCM command failed: $LASTEXITCODE" }
} finally { Pop-Location }
