$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
. .\start-common.ps1

Write-Host "Starting Hermes Fleet (advanced + simple mode)..."
$composeArgs = Get-HermesComposeArgs
docker compose @composeArgs up -d --no-build --remove-orphans

$gateway = "http://127.0.0.1:8788"
$gui = "http://127.0.0.1:8501"
$key = "local-hermes-ui-key"

Write-Host ""
Write-Host "Hermes Fleet is starting."
Write-Host "GUI: $gui"
Write-Host "Gateway: $gateway"
Write-Host "Key: $key"
Write-Host ""
Write-Host "Quick checks:"
Write-Host "  curl -H ""X-Hermes-Key: $key"" $gateway/unified-config"
Write-Host "  curl -H ""X-Hermes-Key: $key"" -H ""Content-Type: application/json"" -d ""{\""prompt\"":\""optimize fleet immediately\""}"" $gateway/llm-chat"
