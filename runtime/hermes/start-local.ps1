Set-Location $PSScriptRoot
docker compose up -d --build
docker compose ps

$gatewayPort = if ($env:MCP_DOCKER_PORT) { $env:MCP_DOCKER_PORT } else { "8788" }
$guiPort = if ($env:HERMES_GUI_PORT) { $env:HERMES_GUI_PORT } else { "8501" }
$gateway = "http://localhost:$gatewayPort"

for ($i = 0; $i -lt 20; $i++) {
    try {
        Invoke-RestMethod -Uri "$gateway/health" -Method Get | Out-Null
        break
    } catch {
        Start-Sleep -Seconds 2
    }

}

try {
    Invoke-RestMethod -Uri "$gateway/learning-pulse" -Method Post -ContentType "application/json" -Body '{"specialty":"fleet","steps":60,"candidates":40}' | Out-Null
} catch {
    Write-Host "Warm-start pulse skipped."
}

Write-Host "Hermes MCP Gateway: $gateway"
Write-Host "Hermes GUI: http://localhost:$guiPort"
Write-Host "Unified config: $gateway/unified-config"
