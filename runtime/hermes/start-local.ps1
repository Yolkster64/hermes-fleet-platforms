Write-Host "start-local.ps1 is a legacy alias. Running scripts/startup/start_runtime.ps1 -Mode local"
& "$PSScriptRoot\scripts\startup\start_runtime.ps1" -Mode local
