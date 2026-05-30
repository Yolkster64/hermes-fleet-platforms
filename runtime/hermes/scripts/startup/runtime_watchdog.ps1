$ErrorActionPreference = "Stop"
$runtimeRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $runtimeRoot
. (Join-Path $PSScriptRoot "helpers.ps1")

$composeArgs = Get-HermesComposeArgs
$gatewayPort = if ($env:MCP_DOCKER_PORT) { $env:MCP_DOCKER_PORT } else { "8788" }
$gateway = "http://localhost:$gatewayPort"
$gatewayKey = if ($env:HERMES_GATEWAY_KEY) { $env:HERMES_GATEWAY_KEY } else { "local-hermes-ui-key" }
$headers = Get-HermesGatewayHeaders -GatewayKey $gatewayKey
$warmed = $false

while ($true) {
    try {
        docker compose @composeArgs up -d --no-build --remove-orphans | Out-Null
        $healthy = Wait-HermesGatewayHealth -GatewayUrl $gateway -Headers $headers -Attempts 20 -DelaySeconds 2
        if ($healthy -and -not $warmed) {
            Invoke-HermesLearningPulse -GatewayUrl $gateway -Headers $headers | Out-Null
            $warmed = $true
        } elseif (-not $healthy) {
            docker compose @composeArgs restart hermes-api hermes-gateway hermes-trainer hermes-gui | Out-Null
            $warmed = $false
        }
    } catch {
        $warmed = $false
    }
    Start-Sleep -Seconds 30
}
