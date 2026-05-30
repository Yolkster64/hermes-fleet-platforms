$ErrorActionPreference = "Stop"

if (Get-ScheduledTask -TaskName "HermesRuntimeAutostart" -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName "HermesRuntimeAutostart" -Confirm:$false
    Write-Host "Hermes autostart disabled."
} else {
    Write-Host "HermesRuntimeAutostart task not found."
}
