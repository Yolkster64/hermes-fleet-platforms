$runtimeRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $runtimeRoot
. (Join-Path $PSScriptRoot "helpers.ps1")

$composeArgs = Get-HermesComposeArgs
docker compose @composeArgs up -d --no-build --remove-orphans
docker compose @composeArgs ps

$gatewayPort = if ($env:MCP_DOCKER_PORT) { $env:MCP_DOCKER_PORT } else { "8788" }
$guiPort = if ($env:HERMES_GUI_PORT) { $env:HERMES_GUI_PORT } else { "8501" }
$gateway = "http://localhost:$gatewayPort"
$gatewayKey = if ($env:HERMES_GATEWAY_KEY) { $env:HERMES_GATEWAY_KEY } else { "local-hermes-ui-key" }
$headers = Get-HermesGatewayHeaders -GatewayKey $gatewayKey
Wait-HermesGatewayHealth -GatewayUrl $gateway -Headers $headers -Attempts 20 -DelaySeconds 2 | Out-Null
Invoke-HermesLearningPulse -GatewayUrl $gateway -Headers $headers | Out-Null

Write-Host "Hermes MCP Gateway: $gateway"
Write-Host "Hermes GUI: http://localhost:$guiPort"
Write-Host "Unified config: $gateway/unified-config"
Write-Host "Gateway API key: $gatewayKey"

Start-Process "http://localhost:$guiPort" | Out-Null
Start-Process "$gateway/unified-config" | Out-Null
