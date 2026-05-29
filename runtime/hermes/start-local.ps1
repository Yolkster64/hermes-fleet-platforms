Set-Location $PSScriptRoot
docker compose up -d --build
Write-Host "Hermes API: http://localhost:8787"
Write-Host "Hermes GUI: http://localhost:8501"
