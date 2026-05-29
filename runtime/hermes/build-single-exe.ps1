Set-Location $PSScriptRoot

$output = Join-Path $PSScriptRoot "dist\hermes-gateway"
$single = Join-Path $PSScriptRoot "dist\HermesUnified.exe"
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

$exe = Get-ChildItem (Join-Path $output "*.exe") | Select-Object -First 1
if (-not $exe) {
  throw "No EXE was produced by publish."
}

Copy-Item $exe.FullName $single -Force

Write-Host "Single clean EXE published:"
Write-Host $single
