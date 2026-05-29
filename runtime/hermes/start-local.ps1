Set-Location $PSScriptRoot
docker compose up -d --build
docker compose ps

$gatewayPort = if ($env:MCP_DOCKER_PORT) { $env:MCP_DOCKER_PORT } else { "8788" }
$guiPort = if ($env:HERMES_GUI_PORT) { $env:HERMES_GUI_PORT } else { "8501" }
$gateway = "http://localhost:$gatewayPort"
$gatewayKey = if ($env:HERMES_GATEWAY_KEY) { $env:HERMES_GATEWAY_KEY } else { "local-hermes-ui-key" }
$headers = @{}
if ($gatewayKey) { $headers["X-Hermes-Key"] = $gatewayKey }

for ($i = 0; $i -lt 20; $i++) {
    try {
        Invoke-RestMethod -Uri "$gateway/health" -Headers $headers -Method Get | Out-Null
        break
    } catch {
        Start-Sleep -Seconds 2
    }

}

try {
    Invoke-RestMethod -Uri "$gateway/learning-pulse" -Headers $headers -Method Post -ContentType "application/json" -Body '{"specialty":"fleet","steps":60,"candidates":40}' | Out-Null
} catch {
    Write-Host "Warm-start pulse skipped."
}

Write-Host "Hermes MCP Gateway: $gateway"
Write-Host "Hermes GUI: http://localhost:$guiPort"
Write-Host "Unified config: $gateway/unified-config"
Write-Host "Gateway API key: $gatewayKey"

Start-Process "http://localhost:$guiPort" | Out-Null
Start-Process "$gateway/unified-config" | Out-Null
