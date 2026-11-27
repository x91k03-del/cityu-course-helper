param(
    [ValidateSet('score','evaluate','baseline','demo','test','train')]
    [string]$Action = 'score',
    [string]$Course = 'CS3334'
)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:HF_HUB_OFFLINE = '1'
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
Push-Location $PSScriptRoot
try {
    switch ($Action) {
        score { & $taskPython inference.py score --course $Course }
        evaluate {
            & $taskPython inference.py evaluate
            if ($LASTEXITCODE -eq 0) { & $taskPython summarize_predictions.py }
        }
        baseline { & $taskPython inference.py baseline-schedule }
        demo { & $taskPython scheduler.py data/five_course_schedule_demo.json }
        test { & $taskPython -m unittest test_scheduler test_five_course_policy test_cm_planning_update }
        train { & $taskPython train.py --epochs 2 }
    }
    if ($LASTEXITCODE -ne 0) { throw "Action failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }
