param(
    [ValidateSet("Always", "AtLogon", "AtStartup")]
    [string]$Trigger = "Always"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "runtime_watchdog.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "runtime_watchdog.ps1 not found at $scriptPath"
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
$taskTriggers = @()
if ($Trigger -in @("Always", "AtStartup")) {
    $taskTriggers += New-ScheduledTaskTrigger -AtStartup
}
if ($Trigger -in @("Always", "AtLogon")) {
    $taskTriggers += New-ScheduledTaskTrigger -AtLogOn
}
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask `
    -TaskName "HermesRuntimeAutostart" `
    -Action $action `
    -Trigger $taskTriggers `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null
Start-ScheduledTask -TaskName "HermesRuntimeAutostart"
$taskState = (Get-ScheduledTask -TaskName "HermesRuntimeAutostart").State

Write-Host "Hermes autostart watchdog enabled with trigger: $Trigger"
Write-Host "Task name: HermesRuntimeAutostart"
Write-Host "Task state: $taskState"
