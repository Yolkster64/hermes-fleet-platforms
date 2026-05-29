Set-Location $PSScriptRoot

$output = Join-Path $PSScriptRoot "dist\hermes-gateway"
New-Item -ItemType Directory -Force -Path $output | Out-Null

dotnet publish .\gateway\HermesGateway.csproj `
  -c Release `
  -r win-x64 `
  --self-contained false `
  -p:PublishSingleFile=true `
  -o $output

if ($LASTEXITCODE -ne 0) {
  throw "Failed to publish Hermes single EXE gateway."
}

Write-Host "Single EXE published:"
Get-ChildItem (Join-Path $output "*.exe") | ForEach-Object { Write-Host $_.FullName }
