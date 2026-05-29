param(
    [ValidateSet("local", "super")]
    [string]$Mode = "local"
)

$ErrorActionPreference = "Stop"
$runtimeRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $runtimeRoot
. (Join-Path $PSScriptRoot "helpers.ps1")

$composeArgs = Get-HermesComposeArgs
docker compose @composeArgs up -d --no-build --remove-orphans
if ($Mode -eq "local") {
    docker compose @composeArgs ps
}

$gatewayPort = if ($env:MCP_DOCKER_PORT) { $env:MCP_DOCKER_PORT } else { "8788" }
$guiPort = if ($env:HERMES_GUI_PORT) { $env:HERMES_GUI_PORT } else { "8501" }
$gateway = "http://localhost:$gatewayPort"
$gatewayKey = if ($env:HERMES_GATEWAY_KEY) { $env:HERMES_GATEWAY_KEY } else { "local-hermes-ui-key" }

if ($Mode -eq "local") {
    $headers = Get-HermesGatewayHeaders -GatewayKey $gatewayKey
    Wait-HermesGatewayHealth -GatewayUrl $gateway -Headers $headers -Attempts 20 -DelaySeconds 2 | Out-Null
    Invoke-HermesLearningPulse -GatewayUrl $gateway -Headers $headers | Out-Null
    Write-Host "Hermes MCP Gateway: $gateway"
    Write-Host "Hermes GUI: http://localhost:$guiPort"
    Write-Host "Unified config: $gateway/unified-config"
    Write-Host "Gateway API key: $gatewayKey"
    Start-Process "http://localhost:$guiPort" | Out-Null
    Start-Process "$gateway/unified-config" | Out-Null
    return
}

Write-Host ""
Write-Host "Hermes Super Fleet is starting."
Write-Host "GUI: http://localhost:$guiPort"
Write-Host "Gateway: $gateway"
Write-Host "Key: $gatewayKey"
Write-Host ""
Write-Host "Quick checks:"
Write-Host "  curl -H ""X-Hermes-Key: $gatewayKey"" $gateway/unified-config"
Write-Host "  curl -H ""X-Hermes-Key: $gatewayKey"" -H ""Content-Type: application/json"" -d ""{\""prompt\"":\""optimize fleet immediately\""}"" $gateway/llm-chat"
