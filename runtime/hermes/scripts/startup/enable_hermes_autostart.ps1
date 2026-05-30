param(
    [ValidateSet("AtLogon", "AtStartup")]
    [string]$Trigger = "AtLogon"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "start_runtime.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "start_runtime.ps1 not found at $scriptPath"
}

$action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Mode local"
if ($Trigger -eq "AtStartup") {
    $taskTrigger = New-ScheduledTaskTrigger -AtStartup
} else {
    $taskTrigger = New-ScheduledTaskTrigger -AtLogOn
}
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "HermesRuntimeAutostart" `
    -Action $action `
    -Trigger $taskTrigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "Hermes autostart enabled with trigger: $Trigger"
Write-Host "Task name: HermesRuntimeAutostart"
