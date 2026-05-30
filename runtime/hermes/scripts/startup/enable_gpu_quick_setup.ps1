param(
    [ValidateSet("local", "super")]
    [string]$Mode = "local"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Max-out GPU profile for this startup session.
$env:NVIDIA_VISIBLE_DEVICES = "all"
$env:NVIDIA_DRIVER_CAPABILITIES = "compute,utility"
$env:HERMES_GPU_TARGET_UTILIZATION = "1.00"
$env:HERMES_CPU_TARGET_UTILIZATION = "1.00"
$env:HERMES_MAX_MODE = "true"

Write-Host "GPU quick setup enabled:"
Write-Host "  NVIDIA_VISIBLE_DEVICES=$($env:NVIDIA_VISIBLE_DEVICES)"
Write-Host "  NVIDIA_DRIVER_CAPABILITIES=$($env:NVIDIA_DRIVER_CAPABILITIES)"
Write-Host "  HERMES_GPU_TARGET_UTILIZATION=$($env:HERMES_GPU_TARGET_UTILIZATION)"
Write-Host "  HERMES_CPU_TARGET_UTILIZATION=$($env:HERMES_CPU_TARGET_UTILIZATION)"

& (Join-Path $scriptDir "start_runtime.ps1") -Mode $Mode
