Write-Host "start-agent-fleet.ps1 is a legacy alias. Running scripts/startup/start_runtime.ps1 -Mode super"
& "$PSScriptRoot\scripts\startup\start_runtime.ps1" -Mode super
