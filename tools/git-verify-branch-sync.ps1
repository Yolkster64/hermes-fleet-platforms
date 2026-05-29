param(
    [string]$RepoPath = "C:\Windows\System32\hermes-fleet-platforms",
    [string]$Branch = "integration/helios-website-consolidation",
    [string]$Remote = "origin"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RepoPath)) {
    throw "Repository path not found: $RepoPath"
}

$localStatus = git -C $RepoPath --no-pager status --short
$localHead = (git -C $RepoPath --no-pager rev-parse HEAD).Trim()
$remoteInfo = (git -C $RepoPath ls-remote --heads $Remote $Branch).Trim()

if ([string]::IsNullOrWhiteSpace($remoteInfo)) {
    throw "Remote branch not found: $Remote/$Branch"
}

$remoteHead = ($remoteInfo -split "\s+")[0]
$inSync = $localHead -eq $remoteHead

[pscustomobject]@{
    repository = $RepoPath
    branch = $Branch
    remote = $Remote
    local_head = $localHead
    remote_head = $remoteHead
    in_sync = $inSync
    clean_worktree = [string]::IsNullOrWhiteSpace(($localStatus -join ""))
    status_lines = @($localStatus)
} | ConvertTo-Json -Depth 4
