param(
    [string]$BaseUrl = "http://localhost:8787",
    [int]$Rounds = 3,
    [string]$ApiKey = ""
)

$ErrorActionPreference = "Stop"
$roundCount = [Math]::Max(1, $Rounds)
$headers = @{}
if ($ApiKey -and $ApiKey.Trim().Length -gt 0) {
    $headers["x-api-key"] = $ApiKey.Trim()
}

Write-Host "Running GPU saturation training ($roundCount rounds) against $BaseUrl ..."
for ($i = 1; $i -le $roundCount; $i++) {
    $payload = @{
        specialty = "fleet:gpu-saturation"
        steps = 1600 + (($i - 1) * 220)
        candidates = 1200 + (($i - 1) * 120)
        sql_signal = 0.98
        internet_signal = 0.10
        llm_signal = 0.99
        stability_bias = 0.93
        x5_brain_pack = $true
        x6_learning_pack = $true
        gpu_target_utilization = 1.00
    } | ConvertTo-Json

    try {
        $resp = Invoke-RestMethod -Method Post -Uri "$BaseUrl/learning-pulse" -Headers $headers -ContentType "application/json" -Body $payload -TimeoutSec 240
        Write-Host "Round $i complete." -ForegroundColor Green
        if ($null -ne $resp) {
            $resp | ConvertTo-Json -Depth 6 | Write-Host
        }
    }
    catch {
        Write-Warning "Round $i failed: $($_.Exception.Message)"
    }
}

Write-Host "GPU saturation training run finished."
