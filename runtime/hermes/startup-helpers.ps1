function Get-HermesComposeArgs {
    $composeArgs = @("-f", "docker-compose.yml")
    docker run --rm -v /dev:/hostdev alpine sh -lc "test -e /hostdev/dri" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $composeArgs += @("-f", "docker-compose.intel.yml")
        Write-Host "Intel Arc/NPU path detected (/dev/dri). Intel acceleration overlay enabled."
    } else {
        Write-Host "Intel Arc/NPU path not detected (/dev/dri missing). Running standard Hermes profile."
    }
    return ,$composeArgs
}

function Get-HermesGatewayHeaders {
    param([string]$GatewayKey)
    $headers = @{}
    if (-not [string]::IsNullOrWhiteSpace($GatewayKey)) {
        $headers["X-Hermes-Key"] = $GatewayKey
    }
    return $headers
}

function Wait-HermesGatewayHealth {
    param(
        [string]$GatewayUrl,
        [hashtable]$Headers,
        [int]$Attempts = 20,
        [int]$DelaySeconds = 2
    )
    for ($i = 0; $i -lt $Attempts; $i++) {
        try {
            Invoke-RestMethod -Uri "$GatewayUrl/health" -Headers $Headers -Method Get | Out-Null
            return $true
        } catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    return $false
}

function Invoke-HermesLearningPulse {
    param(
        [string]$GatewayUrl,
        [hashtable]$Headers,
        [string]$Payload = '{"specialty":"fleet","steps":60,"candidates":40}'
    )
    try {
        Invoke-RestMethod -Uri "$GatewayUrl/learning-pulse" -Headers $Headers -Method Post -ContentType "application/json" -Body $Payload | Out-Null
        return $true
    } catch {
        Write-Host "Warm-start pulse skipped."
        return $false
    }
}
