Phase 1 — DevDrive Layout and Windows Environment Setup
FILE: 01_phase1_devdrive_layout.ps1
#Requires -Version 7.0
#Requires -RunAsAdministrator
# =============================================================
# 01_phase1_devdrive_layout.ps1
# Phase 1: DevDrive Layout and Windows Environment Setup
# PURPOSE: Establish D:\DevDrive ReFS volume, relocate WSL2 and
#          Docker, set developer cache environment variables.
# NOT FOR BLIND EXECUTION — Review all placeholder values first.
# =============================================================

$ErrorActionPreference = "Stop"
$LogFile = "D:\DevDrive\logs\phase1_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss")
function Log($msg) { $line = "[$(Get-Date -Format 's')] $msg"; Write-Host $line; $line | Out-File -FilePath $LogFile -Append }

# -----------------------------------------------------------
# PREREQUISITE CHECKS
# -----------------------------------------------------------
Log "=== PREREQUISITE CHECKS ==="

# Windows 11 build check (minimum 22621)
$build = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").CurrentBuildNumber
if ([int]$build -lt 22621) {
    throw "FATAL: Windows build $build is below minimum 22621. Upgrade before proceeding."
}
Log "Windows build check PASSED: $build"

# PowerShell version check
if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "FATAL: PowerShell 7+ required. Current: $($PSVersionTable.PSVersion)"
}
Log "PowerShell version PASSED: $($PSVersionTable.PSVersion)"

# Admin rights check (belt-and-suspenders)
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]$identity
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "FATAL: Script must run as Administrator."
}
Log "Admin rights check PASSED"

# -----------------------------------------------------------
# PRE-BOOTSTRAP SNAPSHOT
# -----------------------------------------------------------
Log "=== PRE-BOOTSTRAP SNAPSHOT ==="
$snapshotFile = "D:\pre_bootstrap_snapshot_{0}.txt" -f (Get-Date -Format "yyyyMMdd_HHmmss")
Get-PSDrive | Out-File $snapshotFile
Get-WmiObject Win32_DiskPartition | Out-File $snapshotFile -Append
Log "Snapshot written to $snapshotFile"

# -----------------------------------------------------------
# C: FREE SPACE CHECK
# -----------------------------------------------------------
Log "=== C: FREE SPACE CHECK ==="
$cDrive = Get-PSDrive C
$cFreeGB = [math]::Round($cDrive.Free / 1GB, 2)
if ($cFreeGB -lt 40) {
    Log "WARNING: C: free space is ${cFreeGB} GB — below recommended 40 GB. Proceeding with caution."
} else {
    Log "C: free space OK: ${cFreeGB} GB"
}

# -----------------------------------------------------------
# CREATE ReFS DevDrive ON D:
# -----------------------------------------------------------
Log "=== FORMAT D: AS ReFS DevDrive ==="
# REVIEW: Confirm D: is the correct drive letter for your NVMe.
# Format-Volume -DriveLetter D -FileSystem ReFS -AllocationUnitSize 65536 -DevDrive -NewFileSystemLabel "DevDrive" -Confirm:$false
Log "PSEUDO: Format-Volume D: ReFS DevDrive 64K cluster — REVIEW BEFORE EXECUTING"

# -----------------------------------------------------------
# FOLDER TREE CREATION
# -----------------------------------------------------------
Log "=== CREATING FOLDER TREE ON D:\DevDrive\ ==="
$folders = @(
    "D:\DevDrive\ai-hub\models",
    "D:\DevDrive\ai-hub\embeddings",
    "D:\DevDrive\ai-hub\checkpoints",
    "D:\DevDrive\ai-hub\venvs",
    "D:\DevDrive\ai-hub\cuda",
    "D:\DevDrive\hermes\nodes",
    "D:\DevDrive\hermes\orchestrator",
    "D:\DevDrive\hermes\configs",
    "D:\DevDrive\hermes\logs",
    "D:\DevDrive\data\raw",
    "D:\DevDrive\data\processed",
    "D:\DevDrive\data\features",
    "D:\DevDrive\data\exports",
    "D:\DevDrive\postgres",
    "D:\DevDrive\qdrant",
    "D:\DevDrive\wsl2",
    "D:\DevDrive\docker",
    "D:\DevDrive\caches\pip",
    "D:\DevDrive\caches\conda",
    "D:\DevDrive\caches\npm",
    "D:\DevDrive\caches\nuget",
    "D:\DevDrive\caches\cargo",
    "D:\DevDrive\caches\gradle",
    "D:\DevDrive\caches\tmp",
    "D:\DevDrive\caches\delivery",
    "D:\DevDrive\sandbox",
    "D:\DevDrive\repos",
    "D:\DevDrive\scripts",
    "D:\DevDrive\logs"
)
foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Log "Created: $folder"
    } else {
        Log "Exists (skipped): $folder"
    }
}

# Symlink D:\DevDrive\ai-hub\models -> E:\ if E: drive is present
if (Test-Path "E:\") {
    Log "E: drive detected — creating symlink D:\DevDrive\ai-hub\models -> E:\models"
    New-Item -ItemType Junction -Path "D:\DevDrive\ai-hub\models" -Target "E:\models" -Force | Out-Null
    Log "Symlink created."
} else {
    Log "E: drive not present — models directory will remain on D:\DevDrive\ai-hub\models"
}

# -----------------------------------------------------------
# MOVE USER CACHES OFF C:
# -----------------------------------------------------------
Log "=== SETTING DEVELOPER CACHE ENVIRONMENT VARIABLES ==="
$envVars = @{
    "PIP_CACHE_DIR"       = "D:\DevDrive\caches\pip"
    "CONDA_PKGS_DIRS"     = "D:\DevDrive\caches\conda\pkgs"
    "npm_config_cache"    = "D:\DevDrive\caches\npm"
    "NUGET_PACKAGES"      = "D:\DevDrive\caches\nuget"
    "CARGO_HOME"          = "D:\DevDrive\caches\cargo"
    "GRADLE_USER_HOME"    = "D:\DevDrive\caches\gradle"
    "TEMP"                = "D:\DevDrive\caches\tmp"
    "TMP"                 = "D:\DevDrive\caches\tmp"
}
foreach ($key in $envVars.Keys) {
    [System.Environment]::SetEnvironmentVariable($key, $envVars[$key], [System.EnvironmentVariableTarget]::Machine)
    Log "Set [Machine] $key = $($envVars[$key])"
}

# -----------------------------------------------------------
# WSL2 RELOCATION TO D:\DevDrive\wsl2\
# -----------------------------------------------------------
Log "=== WSL2 RELOCATION ==="
# Stop WSL2 before export
wsl --shutdown
Log "WSL2 shut down."

# Export each distro — REVIEW: replace {distro} with actual distro names (wsl --list --quiet)
$distros = @("Ubuntu-22.04")  # <-- data-id="150" Replace with your actual distros
foreach ($distro in $distros) {
    $exportPath = "D:\DevDrive\wsl2\$distro.tar"
    Log "Exporting $distro to $exportPath"
    # wsl --export $distro $exportPath
    Log "PSEUDO: wsl --export $distro $exportPath"
    # Unregister old and import to new location
    # wsl --unregister $distro
    # wsl --import $distro "D:\DevDrive\wsl2\$distro" $exportPath --version 2
    Log "PSEUDO: wsl --import $distro D:\DevDrive\wsl2\$distro $exportPath --version 2"
}

# Write .wslconfig to %USERPROFILE%
Log "Writing .wslconfig to $env:USERPROFILE\.wslconfig"
$wslconfig = @"
[wsl2]
memory=32GB
processors=16
swap=8GB
swapFile=D:\\DevDrive\\wsl2\\swap.vhd
localhostForwarding=true
nestedVirtualization=true
kernelCommandLine=quiet splash
"@
$wslconfig | Set-Content "$env:USERPROFILE\.wslconfig" -Encoding UTF8
Log ".wslconfig written."

# -----------------------------------------------------------
# DOCKER DATA-ROOT RELOCATION
# -----------------------------------------------------------
Log "=== DOCKER DATA-ROOT RELOCATION ==="
# Stop Docker Desktop
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
Log "Docker Desktop stopped."

# Edit daemon.json — path: C:\ProgramData\docker\config\daemon.json
$daemonJsonPath = "C:\ProgramData\docker\config\daemon.json"
$daemonConfig = @"
{
  "data-root": "D:\\DevDrive\\docker"
}
"@
if (Test-Path $daemonJsonPath) {
    Copy-Item $daemonJsonPath "$daemonJsonPath.bak_{0}" -Force
    Log "Backup of daemon.json created."
}
$daemonConfig | Set-Content $daemonJsonPath -Encoding UTF8
Log "daemon.json updated with data-root = D:\DevDrive\docker"

# Robocopy existing Docker data to new location
$robocopyArgs = @(
    "C:\ProgramData\docker", "D:\DevDrive\docker",
    "/COPYALL", "/MIR", "/LOG:D:\DevDrive\logs\docker_robocopy.log", "/TEE"
)
try {
    # robocopy @robocopyArgs
    Log "PSEUDO: robocopy C:\ProgramData\docker D:\DevDrive\docker /COPYALL /MIR"
} catch {
    Log "ERROR: robocopy failed — see D:\DevDrive\logs\bootstrap_errors.log"
    $_ | Out-File "D:\DevDrive\logs\bootstrap_errors.log" -Append
    throw
}

Log "Phase 1 COMPLETE. Restart Docker Desktop and WSL2 to verify."
Phase 2 — Core Dev Tools and SDK Installation
FILE: 02_phase2_tools_sdks.ps1
#Requires -Version 7.0
#Requires -RunAsAdministrator
# =============================================================
# 02_phase2_tools_sdks.ps1
# Phase 2: Core Developer Tools and SDK Installation
# PURPOSE: Install all required tools via winget, set up Conda,
#          validate CUDA, configure Docker GPU runtime.
# NOT FOR BLIND EXECUTION — Review before running.
# =============================================================

$ErrorActionPreference = "Stop"
$LogFile = "D:\DevDrive\logs\phase2_install_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss")
function Log($msg) { $line = "[$(Get-Date -Format 's')] $msg"; Write-Host $line; $line | Out-File -FilePath $LogFile -Append }
function LogWarn($msg) { Log "WARNING: $msg" }
function LogFatal($msg) { Log "FATAL: $msg"; throw $msg }

Log "=== PHASE 2: CORE TOOLS AND SDK INSTALLATION ==="

# -----------------------------------------------------------
# WINGET PACKAGE INSTALLS
# -----------------------------------------------------------
$packages = @(
    @{ Id = "Git.Git";                  Name = "Git";             Fatal = $true  },
    @{ Id = "Microsoft.VisualStudioCode"; Name = "VSCode";        Fatal = $false },
    @{ Id = "Microsoft.WindowsTerminal"; Name = "Windows Terminal"; Fatal = $false },
    @{ Id = "Python.Python.3.12";       Name = "Python 3.12";     Fatal = $true  },
    @{ Id = "OpenJS.NodeJS.LTS";        Name = "Node.js LTS";     Fatal = $false },
    @{ Id = "Rustlang.Rustup";          Name = "Rust/Rustup";     Fatal = $false },
    @{ Id = "GoLang.Go";                Name = "Go";              Fatal = $false },
    @{ Id = "Microsoft.AzureCLI";       Name = "Azure CLI";       Fatal = $true  },
    @{ Id = "GitHub.cli";               Name = "GitHub CLI";      Fatal = $true  },
    @{ Id = "Docker.DockerDesktop";     Name = "Docker Desktop";  Fatal = $true  },
    @{ Id = "Microsoft.PowerShell";     Name = "PowerShell 7";    Fatal = $false }
)

foreach ($pkg in $packages) {
    try {
        Log "Installing $($pkg.Name) [$($pkg.Id)]..."
        winget install --id $pkg.Id --silent --accept-package-agreements --accept-source-agreements
        Log "$($pkg.Name) installed OK"
    } catch {
        if ($pkg.Fatal) {
            LogFatal "$($pkg.Name) installation FAILED (fatal). Error: $_"
        } else {
            LogWarn "$($pkg.Name) installation failed (non-fatal, continuing). Error: $_"
        }
    }
}

# -----------------------------------------------------------
# CONDA / MINIFORGE INSTALLATION
# -----------------------------------------------------------
Log "=== CONDA / MINIFORGE INSTALLATION ==="
$miniforgeInstaller = "$env:TEMP\Miniforge3-Windows-x86_64.exe"
$miniforgeTarget    = "D:\DevDrive\caches\conda\miniforge"
try {
    Invoke-WebRequest -Uri "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe" -OutFile $miniforgeInstaller
    Start-Process -FilePath $miniforgeInstaller -ArgumentList "/InstallationType=JustMe /RegisterPython=0 /S /D=$miniforgeTarget" -Wait
    Log "Miniforge installed at $miniforgeTarget"
} catch {
    LogWarn "Miniforge installation failed: $_"
}

# -----------------------------------------------------------
# CUDA TOOLKIT VERIFICATION AND INSTALLATION
# -----------------------------------------------------------
Log "=== CUDA TOOLKIT VALIDATION ==="
try {
    $nvidiaSmi = & nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    Log "nvidia-smi output: $nvidiaSmi"
    $cudaVersion = & nvcc --version 2>&1
    Log "nvcc output: $cudaVersion"
} catch {
    LogFatal "CUDA validation FAILED — nvidia-smi or nvcc not found. Install NVIDIA driver and CUDA Toolkit 12.x before continuing."
}
# If CUDA not at expected version, prompt for manual install:
Log "PSEUDO: If CUDA 12.x not present, install via: winget install --id Nvidia.CUDA"
Log "PSEUDO: Or download installer to D:\DevDrive\ai-hub\cuda and run manually."

# -----------------------------------------------------------
# CUDNN VERIFICATION
# -----------------------------------------------------------
Log "=== CUDNN VERIFICATION ==="
$cudaInclude = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\include\cudnn.h"
if (Test-Path $cudaInclude) {
    Log "cuDNN header found at $cudaInclude — cuDNN appears installed."
} else {
    LogWarn "cuDNN header NOT found. Download cuDNN 9.x from developer.nvidia.com and copy to CUDA directory."
}

# -----------------------------------------------------------
# NVIDIA CONTAINER TOOLKIT FOR DOCKER
# -----------------------------------------------------------
Log "=== NVIDIA CONTAINER TOOLKIT FOR DOCKER ==="
# This is configured in daemon.json (see Phase 3 and Deliverable 3 for full daemon.json)
# Verify Docker can access GPU:
Log "PSEUDO: docker run --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi"
Log "PSEUDO: If this fails, ensure NVIDIA Container Toolkit is installed and daemon.json sets default-runtime=nvidia"

# -----------------------------------------------------------
# GPU VALIDATION IN WSL2
# -----------------------------------------------------------
Log "=== GPU VALIDATION IN WSL2 ==="
Log "PSEUDO (run in WSL2 bash):"
Log "  ls /dev/dxg                     # Must exist for CUDA-on-WSL2"
Log "  python3 -c 'import torch; print(torch.cuda.is_available())'"
Log "  Expected output: True"

# -----------------------------------------------------------
# GITHUB CLI AUTHENTICATION
# -----------------------------------------------------------
Log "=== GITHUB CLI AUTHENTICATION ==="
Log "PSEUDO: gh auth login --web"
Log "  NOTE: Token stored in Windows Credential Manager (wincred) — never in a file."
Log "  Verify: gh auth status"

# -----------------------------------------------------------
# AZURE CLI AUTHENTICATION
# -----------------------------------------------------------
Log "=== AZURE CLI AUTHENTICATION ==="
Log "PSEUDO: az login --use-device-code"
Log "PSEUDO: az account set --subscription {your-subscription-id}"
Log "PSEUDO: az account show   # Verify correct subscription is active"

# -----------------------------------------------------------
# COPILOT / AI SDK VIRTUAL ENVIRONMENT
# -----------------------------------------------------------
Log "=== COPILOT SDK VENV SETUP ==="
$copilotVenv = "D:\DevDrive\ai-hub\venvs\copilot-sdk"
try {
    python -m venv $copilotVenv
    & "$copilotVenv\Scripts\pip.exe" install azure-ai-inference openai semantic-kernel
    Log "Copilot SDK venv created at $copilotVenv"
} catch {
    LogWarn "Copilot SDK venv creation failed: $_"
}

Log "Phase 2 COMPLETE. Review log at $LogFile"
Phase 3 — Hyper-V, Sandbox, Postgres, Qdrant, and Hermes Runtime Skeleton
FILE: 03_phase3_hyperv_services.ps1
#Requires -Version 7.0
#Requires -RunAsAdministrator
# =============================================================
# 03_phase3_hyperv_services.ps1
# Phase 3: Hyper-V, Windows Sandbox, Postgres, Qdrant,
#          and Hermes Runtime Skeleton
# NOT FOR BLIND EXECUTION — Review placeholder values first.
# =============================================================

$ErrorActionPreference = "Stop"
$LogFile = "D:\DevDrive\logs\phase3_services_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss")
function Log($msg) { $line = "[$(Get-Date -Format 's')] $msg"; Write-Host $line; $line | Out-File $LogFile -Append }

Log "=== PHASE 3: HYPER-V, SANDBOX, POSTGRES, QDRANT, HERMES ==="

# -----------------------------------------------------------
# ENABLE HYPER-V
# -----------------------------------------------------------
Log "=== ENABLING HYPER-V ==="
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
Log "Hyper-V enabled. Reboot may be required."

# -----------------------------------------------------------
# ENABLE WINDOWS SANDBOX
# -----------------------------------------------------------
Log "=== ENABLING WINDOWS SANDBOX ==="
Enable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -NoRestart
Log "Windows Sandbox enabled."

# -----------------------------------------------------------
# HYPER-V VIRTUAL SWITCHES
# -----------------------------------------------------------
Log "=== HYPER-V VIRTUAL SWITCHES ==="
$physicalNic = "{your-physical-nic-adapter-name}"  # REVIEW: Get-NetAdapter to find name
# External vSwitch (for internet/Azure testing in Mode A)
New-VMSwitch -Name "HermesNet" -NetAdapterName $physicalNic -AllowManagementOS $true -ErrorAction SilentlyContinue
Log "External vSwitch 'HermesNet' created (bound to $physicalNic)"
# Internal vSwitch (isolated VM communication, used in Mode B)
New-VMSwitch -Name "HermesInternal" -SwitchType Internal -ErrorAction SilentlyContinue
Log "Internal vSwitch 'HermesInternal' created"

# -----------------------------------------------------------
# POSTGRES SETUP (Docker)
# -----------------------------------------------------------
Log "=== POSTGRES SETUP ==="
# Pull image
docker pull postgres:16
Log "postgres:16 image pulled."

# Create data directory
New-Item -ItemType Directory -Path "D:\DevDrive\postgres\data" -Force | Out-Null

# NOTE: POSTGRES_PASSWORD must be set as an environment variable before running this script.
# Never hardcode credentials. Set via: $env:POSTGRES_PASSWORD = (Read-Host -AsSecureString "Postgres Password")
docker run -d `
    --name hermes-postgres `
    --restart unless-stopped `
    -e POSTGRES_PASSWORD=$env:POSTGRES_PASSWORD `
    -v "D:\DevDrive\postgres\data:/var/lib/postgresql/data" `
    -p 127.0.0.1:5432:5432 `
    postgres:16
Log "Postgres container 'hermes-postgres' started."

# Create databases
Start-Sleep -Seconds 8
$dbs = @("hermes_logs", "hermes_features", "hermes_models", "hermes_feedback")
foreach ($db in $dbs) {
    docker exec hermes-postgres psql -U postgres -c "CREATE DATABASE $db;"
    Log "Database created: $db"
}
Log "PSEUDO: Apply DDL from Deliverable 2.1 to initialize table schemas."
Log "PSEUDO: Edit pg_hba.conf in D:\DevDrive\postgres\data to restrict to local access only."

# -----------------------------------------------------------
# QDRANT SETUP (Docker)
# -----------------------------------------------------------
Log "=== QDRANT SETUP ==="
docker pull qdrant/qdrant
Log "qdrant/qdrant image pulled."

New-Item -ItemType Directory -Path "D:\DevDrive\qdrant\storage" -Force | Out-Null
New-Item -ItemType Directory -Path "D:\DevDrive\qdrant\config" -Force | Out-Null

# Write Qdrant config
$qdrantConfig = @"
storage:
  storage_path: /qdrant/storage
service:
  host: 127.0.0.1
  http_port: 6333
  grpc_port: 6334
log_level: INFO
"@
$qdrantConfig | Set-Content "D:\DevDrive\qdrant\config\config.yaml" -Encoding UTF8
Log "Qdrant config written."

docker run -d `
    --name hermes-qdrant `
    --restart unless-stopped `
    -p 127.0.0.1:6333:6333 `
    -p 127.0.0.1:6334:6334 `
    -v "D:\DevDrive\qdrant\storage:/qdrant/storage" `
    -v "D:\DevDrive\qdrant\config:/qdrant/config" `
    qdrant/qdrant
Log "Qdrant container 'hermes-qdrant' started."

# Create collections
Start-Sleep -Seconds 5
$collectionsPayload = @(
    @{ name = "embeddings_v1";       vectors = @{ size = 128; distance = "Cosine" } },
    @{ name = "routing_contexts";    vectors = @{ size = 128; distance = "Cosine" } },
    @{ name = "feature_signatures";  vectors = @{ size = 768; distance = "Cosine" } }
)
foreach ($col in $collectionsPayload) {
    $body = $col | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Uri "http://127.0.0.1:6333/collections/$($col.name)" -Method Put -Body $body -ContentType "application/json"
    Log "Qdrant collection created: $($col.name)"
}

# -----------------------------------------------------------
# HERMES RUNTIME SKELETON
# -----------------------------------------------------------
Log "=== HERMES RUNTIME SKELETON ==="
$hermesBase = "D:\DevDrive\hermes"

# Orchestrator skeleton
$orchestratorPy = @"
# orchestrator.py — Hermes XCore Orchestrator Skeleton
# See Deliverable 2.9 for full class design.
import logging
import asyncio
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hermes.orchestrator")

class HermesOrchestrator:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.nodes = {}
        self.running = False
        logger.info("HermesOrchestrator initialized from %s", config_path)

    async def run_orchestration_loop(self):
        self.running = True
        logger.info("Orchestration loop started.")
        while self.running:
            await asyncio.sleep(1)

if __name__ == "__main__":
    orch = HermesOrchestrator("D:/DevDrive/hermes/configs/hermes_global.yaml")
    asyncio.run(orch.run_orchestration_loop())
"@
$orchestratorPy | Set-Content "$hermesBase\orchestrator\orchestrator.py" -Encoding UTF8
Log "Skeleton written: orchestrator.py"

# Node template
New-Item -ItemType Directory -Path "$hermesBase\nodes\node_template" -Force | Out-Null
$nodeRunner = @"
# runner.py — Hermes Node Runner Template
# See Deliverable 2.9 for full design.
import logging
import torch
from fastapi import FastAPI

logger = logging.getLogger("hermes.node")
app = FastAPI()

@app.get("/health")
def health():
    gpu_ok = torch.cuda.is_available()
    mem = torch.cuda.memory_reserved() if gpu_ok else 0
    return {"status": "ok", "gpu": gpu_ok, "gpu_mem_reserved_bytes": mem}

@app.post("/v1/infer")
async def infer(payload: dict):
    # Task execution stub
    logger.info("Received inference task: %s", payload.get("task_id"))
    return {"status": "accepted", "task_id": payload.get("task_id")}
"@
$nodeRunner | Set-Content "$hermesBase\nodes\node_template\runner.py" -Encoding UTF8
Log "Skeleton written: nodes\node_template\runner.py"

# Global Hermes config YAML
$globalConfig = @"
hermes:
  version: "1.0.0"
  orchestrator:
    host: "127.0.0.1"
    port: 8700
    log_level: INFO
  nodes:
    - id: node_01
      type: inference
      backend: wsl2
      gpu: true
      port: 8701
    - id: node_02
      type: feature_eng
      backend: wsl2
      gpu: false
      port: 8702
    - id: node_03
      type: training
      backend: hyper-v
      gpu: true
      port: 8703
  postgres:
    host: "127.0.0.1"
    port: 5432
    db: hermes_logs
  qdrant:
    host: "127.0.0.1"
    port: 6333
"@
$globalConfig | Set-Content "$hermesBase\configs\hermes_global.yaml" -Encoding UTF8
Log "hermes_global.yaml written."

Log "Phase 3 COMPLETE. Review log at $LogFile"
Deliverable 2 — Hermes XCore Training Loop Design
This deliverable provides the complete software design for the Hermes XCore continuous training pipeline. All modules are Python pseudo-code intended to be implemented, tested, and deployed by a qualified engineer. Module files are deployed to D:\DevDrive\hermes\ and installed into the D:\DevDrive\ai-hub\venvs\hermes-core virtual environment.

2.1 — Logging Schema (SQL DDL)
FILE: hermes_schema.sql — Apply to hermes_logs, hermes_features, hermes_models, hermes_feedback databases
-- =============================================================
-- Hermes XCore PostgreSQL Schema — DDL
-- Apply via: psql -h 127.0.0.1 -U postgres -d hermes_logs -f hermes_schema.sql
-- =============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------
-- hermes_run_log: one row per task run across any node
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_run_log (
    run_id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id         VARCHAR(64) NOT NULL,
    start_ts        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_ts          TIMESTAMPTZ,
    status          VARCHAR(32) NOT NULL CHECK (status IN ('started','success','failed','timeout')),
    error_msg       TEXT,
    payload_hash    CHAR(64),           -- SHA-256 of serialized task payload
    duration_ms     INTEGER GENERATED ALWAYS AS
                    (EXTRACT(EPOCH FROM (end_ts - start_ts)) * 1000) STORED
) PARTITION BY RANGE (start_ts);

-- Monthly partitions for hermes_run_log
CREATE TABLE hermes_run_log_2026_06 PARTITION OF hermes_run_log
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE hermes_run_log_2026_07 PARTITION OF hermes_run_log
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
-- (Continue pattern for additional months)

-- -----------------------------------------------------------
-- hermes_feature_log: features extracted per run
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_feature_log (
    feature_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID        NOT NULL REFERENCES hermes_run_log(run_id) ON DELETE CASCADE,
    feature_name    VARCHAR(256) NOT NULL,
    feature_type    VARCHAR(64) CHECK (feature_type IN ('numeric','categorical','text_embedding','composite')),
    correlation_score FLOAT,
    p_value         FLOAT,
    source_table    VARCHAR(256),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------
-- hermes_model_registry: champion/challenger model inventory
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_model_registry (
    model_id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name      VARCHAR(256) NOT NULL,
    version         VARCHAR(64) NOT NULL,
    artifact_path   TEXT NOT NULL,      -- D:/DevDrive/ai-hub/checkpoints/{file}
    training_run_id UUID        REFERENCES hermes_run_log(run_id),
    eval_score      FLOAT,
    deployed_at     TIMESTAMPTZ,
    is_active       BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (model_name, version)
);

-- -----------------------------------------------------------
-- hermes_feedback_log: reward signals from downstream
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_feedback_log (
    feedback_id     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      VARCHAR(128) NOT NULL,
    model_id        UUID        REFERENCES hermes_model_registry(model_id),
    input_hash      CHAR(64)    NOT NULL,   -- SHA-256 of serialized input
    output_hash     CHAR(64)    NOT NULL,   -- SHA-256 of serialized output
    reward_signal   FLOAT       NOT NULL CHECK (reward_signal BETWEEN -1.0 AND 1.0),
    context_vector  JSONB,                  -- compressed context (128-dim latent)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE hermes_feedback_log_2026_06 PARTITION OF hermes_feedback_log
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

-- -----------------------------------------------------------
-- hermes_routing_decisions: bandit arm selection log
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_routing_decisions (
    decision_id     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      VARCHAR(128) NOT NULL,
    input_context   JSONB       NOT NULL,
    selected_arm    VARCHAR(128) NOT NULL,
    confidence      FLOAT       NOT NULL,
    actual_reward   FLOAT,                  -- populated async after feedback
    ts              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------
-- hermes_secondary_vars: discovered secondary feature variables
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_secondary_vars (
    var_id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    var_name            VARCHAR(256) NOT NULL,
    discovered_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_chain   JSONB,              -- interaction path from source to target
    significance_score  FLOAT,
    included_in_model   BOOLEAN     NOT NULL DEFAULT FALSE
);

-- -----------------------------------------------------------
-- INDEXES
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_run_log_node_id    ON hermes_run_log (node_id);
CREATE INDEX IF NOT EXISTS idx_run_log_start_ts   ON hermes_run_log (start_ts);
CREATE INDEX IF NOT EXISTS idx_run_log_status     ON hermes_run_log (status);
CREATE INDEX IF NOT EXISTS idx_feature_run_id     ON hermes_feature_log (run_id);
CREATE INDEX IF NOT EXISTS idx_feature_created_at ON hermes_feature_log (created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_model_id  ON hermes_feedback_log (model_id);
CREATE INDEX IF NOT EXISTS idx_feedback_session   ON hermes_feedback_log (session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created   ON hermes_feedback_log (created_at);
CREATE INDEX IF NOT EXISTS idx_routing_session    ON hermes_routing_decisions (session_id);
CREATE INDEX IF NOT EXISTS idx_routing_ts         ON hermes_routing_decisions (ts);
CREATE INDEX IF NOT EXISTS idx_routing_arm        ON hermes_routing_decisions (selected_arm);
CREATE INDEX IF NOT EXISTS idx_secondary_score    ON hermes_secondary_vars (significance_score DESC);
2.2 — Feature Extraction Pipeline
MODULE: feature_pipeline.py
# feature_pipeline.py — Hermes XCore Feature Extraction Pipeline
# Pseudo-code: review and implement before use.

from __future__ import annotations
import hashlib
import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

logger = logging.getLogger("hermes.feature_pipeline")

@dataclass
class FeatureSet:
    numeric_features:      pd.DataFrame
    text_embeddings:       Optional[np.ndarray]  # shape (N, 768)
    categorical_features:  pd.DataFrame
    metadata:              dict = field(default_factory=dict)
    run_id:                str  = ""

class FeaturePipeline:
    """
    Orchestrates raw feature extraction, statistics computation,
    text embedding, and DB logging for one input batch.
    """

    def __init__(self, config_path: str, db_conn, gpu_device: str = "cuda"):
        import yaml
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.db_conn   = db_conn
        self.device    = torch.device(gpu_device if torch.cuda.is_available() else "cpu")
        self.qdrant    = QdrantClient(
            host=self.config["qdrant"]["host"],
            port=self.config["qdrant"]["port"]
        )
        model_name = self.config.get("embedding_model", "all-MiniLM-L6-v2")
        self.embedder  = SentenceTransformer(model_name, device=str(self.device))
        logger.info("FeaturePipeline initialized on device=%s", self.device)

    def extract_raw(self, input_batch: pd.DataFrame) -> dict:
        """
        Splits input columns into numeric, text, and categorical buckets
        based on dtype inference and config column type mappings.
        """
        text_cols        = self.config.get("text_columns", [])
        categorical_cols = self.config.get("categorical_columns", [])
        numeric_cols     = [
            c for c in input_batch.columns
            if c not in text_cols + categorical_cols
               and pd.api.types.is_numeric_dtype(input_batch[c])
        ]
        return {
            "numeric":     input_batch[numeric_cols],
            "text":        input_batch[text_cols],
            "categorical": input_batch[categorical_cols]
        }

    def compute_statistics(self, features: dict) -> pd.DataFrame:
        """
        Computes descriptive statistics for numeric and categorical features.
        Numeric: mean, std, skew, kurtosis, p25, p50, p75.
        Categorical: mode, entropy (normalized), frequency table.
        """
        from scipy.stats import skew, kurtosis, entropy as sp_entropy

        rows = []
        numeric_df = features.get("numeric", pd.DataFrame())
        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            rows.append({
                "feature_name":  col,
                "feature_type":  "numeric",
                "mean":          series.mean(),
                "std":           series.std(),
                "skew":          skew(series),
                "kurtosis":      kurtosis(series),
                "p25":           series.quantile(0.25),
                "p50":           series.quantile(0.50),
                "p75":           series.quantile(0.75),
                "null_rate":     numeric_df[col].isnull().mean()
            })
        cat_df = features.get("categorical", pd.DataFrame())
        for col in cat_df.columns:
            series   = cat_df[col].dropna()
            vc       = series.value_counts(normalize=True)
            ent      = float(sp_entropy(vc.values, base=2)) if len(vc) > 1 else 0.0
            rows.append({
                "feature_name":  col,
                "feature_type":  "categorical",
                "entropy_bits":  ent,
                "top_category":  vc.index[0] if len(vc) > 0 else None,
                "n_unique":      int(vc.nunique()),
                "null_rate":     cat_df[col].isnull().mean()
            })
        return pd.DataFrame(rows)

    def embed_text_fields(self, texts: list[str]) -> np.ndarray:
        """
        Encodes list of text strings to (N, 768) embeddings using
        sentence-transformers on GPU; upserts into Qdrant.
        GPU OOM is caught and falls back to CPU.
        """
        if not texts:
            return np.empty((0, 768), dtype=np.float32)
        try:
            embeddings = self.embedder.encode(
                texts,
                batch_size=64,
                show_progress_bar=False,
                device=str(self.device),
                convert_to_numpy=True
            )
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                warnings.warn("CUDA OOM in embed_text_fields — falling back to CPU.")
                logger.warning("GPU OOM: falling back to CPU for embedding step.")
                torch.cuda.empty_cache()
                embeddings = self.embedder.encode(
                    texts, batch_size=32, device="cpu", convert_to_numpy=True
                )
            else:
                raise
        finally:
            torch.cuda.empty_cache()
        return embeddings.astype(np.float32)

    def log_features_to_db(self, feature_df: pd.DataFrame, run_id: str):
        """
        Inserts one row per feature into hermes_feature_log.
        Uses batch INSERT for efficiency.
        """
        cursor = self.db_conn.cursor()
        rows = [
            (
                run_id,
                row.get("feature_name"),
                row.get("feature_type"),
                row.get("correlation_score"),
                row.get("p_value"),
                row.get("source_table")
            )
            for _, row in feature_df.iterrows()
        ]
        cursor.executemany(
            """
            INSERT INTO hermes_feature_log
                (run_id, feature_name, feature_type, correlation_score, p_value, source_table)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            rows
        )
        self.db_conn.commit()
        logger.info("Logged %d features for run_id=%s", len(rows), run_id)

    def run(self, input_batch: pd.DataFrame, run_id: str = "") -> FeatureSet:
        """
        Master orchestration method. Extracts, stats, embeds, logs.
        Returns populated FeatureSet.
        """
        import uuid
        if not run_id:
            run_id = str(uuid.uuid4())
        logger.info("FeaturePipeline.run() start — run_id=%s, batch_rows=%d", run_id, len(input_batch))

        raw     = self.extract_raw(input_batch)
        stats   = self.compute_statistics(raw)

        text_cols = self.config.get("text_columns", [])
        texts = []
        if text_cols:
            for col in text_cols:
                if col in input_batch.columns:
                    texts.extend(input_batch[col].fillna("").tolist())
        embeddings = self.embed_text_fields(texts)

        self.log_features_to_db(stats, run_id)

        return FeatureSet(
            numeric_features     = raw["numeric"],
            text_embeddings      = embeddings if embeddings.size > 0 else None,
            categorical_features = raw["categorical"],
            metadata             = {"stats": stats.to_dict(orient="records")},
            run_id               = run_id
        )
2.3 — Correlation and Secondary Variable Search
MODULE: correlation_search.py
YAML: correlation config block
correlation:
  pearson_threshold:  0.20
  spearman_threshold: 0.15
  mi_threshold:       0.10
  p_value_cutoff:     0.05
  max_secondary_vars: 20
  lasso_alpha_range:  [0.001, 0.01, 0.1]
Python pseudo-code:
# correlation_search.py — Hermes XCore Correlation and Secondary Variable Search
# Pseudo-code: review and implement before use.

from __future__ import annotations
import logging
import json
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import LassoCV

logger = logging.getLogger("hermes.correlation_search")

@dataclass
class SecondaryVar:
    var_name:          str
    correlation_score: float       # composite score
    p_value:           float
    method:            str         # "pearson" | "spearman" | "mi" | "partial"
    interaction_chain: list        # ordered chain of variable interactions

class CorrelationSearch:
    """
    Discovers secondary variables correlated with target that are
    not currently in the model. Uses multiple statistical methods
    and ranks by composite significance. All computations are performed
    ONLY on the training split to prevent data leakage.
    """

    def __init__(self, db_conn, threshold: float = 0.15, p_threshold: float = 0.05):
        self.db_conn     = db_conn
        self.threshold   = threshold
        self.p_threshold = p_threshold
        logger.info("CorrelationSearch initialized (threshold=%.2f, p=%.2f)",
                    threshold, p_threshold)

    def compute_pearson_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pearson r for all numeric column pairs. Returns (n_cols x n_cols) DataFrame."""
        return df.corr(method="pearson")

    def compute_spearman_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Spearman rank correlation for non-normal or ordinal features."""
        return df.corr(method="spearman")

    def compute_mutual_information(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pairwise mutual information for mixed-type features.
        For each column pair, estimate MI using sklearn.
        Returns DataFrame with columns: [feature_a, feature_b, mi_score].
        """
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        records = []
        for i, col_a in enumerate(numeric_cols):
            X = df[numeric_cols].drop(columns=[col_a]).values
            y = df[col_a].values
            mi_scores = mutual_info_regression(X, y, random_state=42)
            for j, col_b in enumerate([c for c in numeric_cols if c != col_a]):
                records.append({"feature_a": col_a, "feature_b": col_b, "mi_score": mi_scores[j]})
        return pd.DataFrame(records)

    def search_secondary_variables(
        self, target: str, feature_df: pd.DataFrame
    ) -> list[SecondaryVar]:
        """
        Finds variables correlated with target that are not currently
        in the model. Uses LASSO path to identify important interactions.
        Operates ONLY on training split — caller is responsible for split.
        """
        if target not in feature_df.columns:
            raise ValueError(f"Target '{target}' not found in feature_df columns.")

        candidates = [c for c in feature_df.select_dtypes(include="number").columns if c != target]
        y = feature_df[target].values
        X = feature_df[candidates].fillna(0).values

        # LASSO path for variable importance
        lasso = LassoCV(alphas=[0.001, 0.01, 0.1], cv=5, max_iter=5000, random_state=42)
        lasso.fit(X, y)
        lasso_selected = [candidates[i] for i, c in enumerate(lasso.coef_) if abs(c) > 1e-6]
        logger.info("LASSO selected %d candidates: %s", len(lasso_selected), lasso_selected)

        results = []
        for var in lasso_selected:
            r, p   = sp_stats.pearsonr(feature_df[var].fillna(0), feature_df[target].fillna(0))
            rho, _ = sp_stats.spearmanr(feature_df[var].fillna(0), feature_df[target].fillna(0))
            if abs(r) >= self.threshold and p <= data-id="174" self.p_threshold:
                results.append(SecondaryVar(
                    var_name          = var,
                    correlation_score = float(abs(r)),
                    p_value           = float(p),
                    method            = "pearson+lasso",
                    interaction_chain = [var, target]
                ))
        return results

    def compute_partial_correlations(
        self, df: pd.DataFrame, target: str, candidates: list[str]
    ) -> pd.DataFrame:
        """
        Computes partial correlations between each candidate and target,
        controlling for all other candidates (OLS residuals method).
        Returns DataFrame: [var, partial_r, p_value].
        """
        from sklearn.linear_model import LinearRegression
        records = []
        y = df[target].fillna(0).values
        for var in candidates:
            controls = [c for c in candidates if c != var]
            if not controls:
                continue
            Xc = df[controls].fillna(0).values
            # Residualize target
            lm_y = LinearRegression().fit(Xc, y)
            res_y = y - lm_y.predict(Xc)
            # Residualize candidate
            xv = df[var].fillna(0).values
            lm_x = LinearRegression().fit(Xc, xv)
            res_x = xv - lm_x.predict(Xc)
            r, p = sp_stats.pearsonr(res_x, res_y)
            records.append({"var": var, "partial_r": r, "p_value": p})
        return pd.DataFrame(records)

    def rank_and_filter(self, results: list[SecondaryVar]) -> list[SecondaryVar]:
        """
        Ranks by composite score (MI + Spearman + partial r),
        filters by significance, caps at max_secondary_vars.
        """
        filtered = [v for v in results if v.p_value <= data-id="175" self.p_threshold
                    and v.correlation_score >= self.threshold]
        filtered.sort(key=lambda v: v.correlation_score, reverse=True)
        return filtered[:20]  # max_secondary_vars from config

    def persist_findings(self, vars: list[SecondaryVar], run_id: str):
        """Writes findings to hermes_secondary_vars and hermes_feature_log."""
        cursor = self.db_conn.cursor()
        for var in vars:
            cursor.execute(
                """
                INSERT INTO hermes_secondary_vars
                    (var_name, correlation_chain, significance_score, included_in_model)
                VALUES (%s, %s, %s, %s)
                """,
                (var.var_name, json.dumps(var.interaction_chain),
                 var.correlation_score, False)
            )
            cursor.execute(
                """
                INSERT INTO hermes_feature_log
                    (run_id, feature_name, feature_type, correlation_score, p_value)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (run_id, var.var_name, "numeric", var.correlation_score, var.p_value)
            )
        self.db_conn.commit()
        logger.info("Persisted %d secondary variable findings.", len(vars))

    def generate_correlation_report(self, vars: list[SecondaryVar]) -> dict:
        """Returns JSON-serializable report of all secondary variable findings."""
        return {
            "secondary_variables": [
                {
                    "var_name":          v.var_name,
                    "correlation_score": v.correlation_score,
                    "p_value":           v.p_value,
                    "method":            v.method,
                    "interaction_chain": v.interaction_chain
                }
                for v in vars
            ],
            "total_found": len(vars)
        }
Data Leakage Prevention
All correlation and MI computations in CorrelationSearch must be performed exclusively on the training split of data. Never pass the full dataset including validation or test rows. The caller (ContinuousRetrainingOrchestrator.prepare_training_data()) is responsible for enforcing the train/test split before calling any CorrelationSearch method.
2.4 — Autoencoder Shape and Compression Pipeline
YAML: autoencoder config block
autoencoder:
  input_dim:                 1024
  latent_dim:                128
  hidden_dims:               [512, 256]
  dropout:                   0.2
  batch_size:                512
  epochs:                    100
  learning_rate:             0.001
  weight_decay:              0.0001
  early_stopping_patience:   10
  device:                    cuda
  checkpoint_dir:            D:/DevDrive/ai-hub/checkpoints
MODULE: autoencoder_pipeline.py
# autoencoder_pipeline.py — Hermes XCore Autoencoder + Compression Pipeline
# Pseudo-code: review and implement before use.

from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from feature_pipeline import FeatureSet

logger = logging.getLogger("hermes.autoencoder")

@dataclass
class CompressedFeatures:
    latent_vectors: np.ndarray   # shape (N, latent_dim)
    original_ids:   list
    metadata:       dict

# -----------------------------------------------------------
# HermesAutoencoder: Encoder-Decoder Architecture
# -----------------------------------------------------------
class HermesAutoencoder(nn.Module):
    """
    Symmetric encoder-decoder network for unsupervised feature compression.
    Encoder: input_dim -> hidden_dims -> latent_dim
    Decoder: latent_dim -> hidden_dims[::-1] -> input_dim
    """

    def __init__(
        self,
        input_dim:   int,
        latent_dim:  int,
        hidden_dims: list[int] = None,
        dropout:     float     = 0.2
    ):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [512, 256]

        # Build encoder
        enc_layers = []
        in_dim = input_dim
        for h in hidden_dims:
            enc_layers += [
                nn.Linear(in_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(dropout)
            ]
            in_dim = h
        enc_layers.append(nn.Linear(in_dim, latent_dim))
        self.encoder = nn.Sequential(*enc_layers)

        # Build decoder (mirror)
        dec_layers = []
        in_dim = latent_dim
        for h in reversed(hidden_dims):
            dec_layers += [
                nn.Linear(in_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(dropout)
            ]
            in_dim = h
        dec_layers += [nn.Linear(in_dim, input_dim), nn.Sigmoid()]
        self.decoder = nn.Sequential(*dec_layers)

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z    = self.encode(x)
        recon = self.decode(z)
        return recon, z

# -----------------------------------------------------------
# AutoencoderTrainer
# -----------------------------------------------------------
class AutoencoderTrainer:
    def __init__(
        self,
        model:     HermesAutoencoder,
        optimizer: torch.optim.Optimizer,
        loss_fn,
        device:    torch.device,
        db_conn
    ):
        self.model     = model.to(device)
        self.optimizer = optimizer
        self.loss_fn   = loss_fn
        self.device    = device
        self.db_conn   = db_conn
        self.best_val_loss = float("inf")
        self.patience_counter = 0

    def train_epoch(self, dataloader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        for batch in dataloader:
            x = batch.to(self.device)
            self.optimizer.zero_grad()
            recon, z = self.model(x)
            loss = self.loss_fn(recon, x)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item() * x.size(0)
        return total_loss / len(dataloader.dataset)

    def validate(self, dataloader: DataLoader) -> dict:
        self.model.eval()
        total_loss = 0.0
        latent_vecs = []
        with torch.no_grad():
            for batch in dataloader:
                x = batch.to(self.device)
                recon, z = self.model(x)
                total_loss += self.loss_fn(recon, x).item() * x.size(0)
                latent_vecs.append(z.cpu().numpy())
        avg_loss  = total_loss / len(dataloader.dataset)
        latents   = np.vstack(latent_vecs)
        var_ratio = float(np.var(latents, axis=0).sum())
        return {
            "val_loss":              avg_loss,
            "latent_variance_total": var_ratio
        }

    def fit(
        self,
        train_dl: DataLoader,
        val_dl:   DataLoader,
        epochs:   int = 50,
        early_stopping_patience: int = 5
    ):
        for epoch in range(1, epochs + 1):
            train_loss = self.train_epoch(train_dl)
            val_metrics = self.validate(val_dl)
            val_loss = val_metrics["val_loss"]
            logger.info("Epoch %d/%d — train_loss=%.4f, val_loss=%.4f",
                        epoch, epochs, train_loss, val_loss)
            if val_loss < self.best_val_loss - 1e-5:
                self.best_val_loss    = val_loss
                self.patience_counter = 0
                self.save_checkpoint(
                    path=f"D:/DevDrive/ai-hub/checkpoints/ae_best.pt",
                    epoch=epoch, metrics=val_metrics
                )
            else:
                self.patience_counter += 1
                if self.patience_counter >= early_stopping_patience:
                    logger.info("Early stopping at epoch %d (patience=%d)",
                                epoch, early_stopping_patience)
                    break

    def save_checkpoint(self, path: str, epoch: int, metrics: dict):
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        versioned_path = path.replace(".pt", f"_{ts}.pt")
        torch.save({
            "epoch":       epoch,
            "model_state": self.model.state_dict(),
            "optim_state": self.optimizer.state_dict(),
            "metrics":     metrics
        }, versioned_path)
        logger.info("Checkpoint saved: %s", versioned_path)

    def load_checkpoint(self, path: str):
        ckpt = torch.load(path, map_location=self.device)
        self.model.load_state_dict(ckpt["model_state"])
        self.optimizer.load_state_dict(ckpt["optim_state"])
        logger.info("Checkpoint loaded from %s (epoch=%d)", path, ckpt.get("epoch", "?"))

# -----------------------------------------------------------
# CompressionPipeline
# -----------------------------------------------------------
class CompressionPipeline:
    def __init__(self, model: HermesAutoencoder, qdrant: QdrantClient,
                 device: torch.device, collection: str = "embeddings_v1"):
        self.model      = model.eval()
        self.qdrant     = qdrant
        self.device     = device
        self.collection = collection

    def compress(self, feature_set: FeatureSet) -> CompressedFeatures:
        """Encodes all numeric features into unified 128-dim latent space."""
        x = torch.tensor(
            feature_set.numeric_features.fillna(0).values,
            dtype=torch.float32
        ).to(self.device)
        with torch.no_grad():
            z = self.model.encode(x).cpu().numpy()
        return CompressedFeatures(
            latent_vectors = z,
            original_ids   = list(range(len(z))),
            metadata       = {"run_id": feature_set.run_id}
        )

    def index_in_qdrant(self, compressed: CompressedFeatures, metadata: dict):
        """Batch upsert latent vectors into Qdrant embeddings_v1 collection."""
        points = [
            PointStruct(
                id      = f"{compressed.metadata.get('run_id','')}-{i}",
                vector  = compressed.latent_vectors[i].tolist(),
                payload = {**compressed.metadata, **metadata, "vector_index": i}
            )
            for i in range(len(compressed.latent_vectors))
        ]
        self.qdrant.upsert(collection_name=self.collection, points=points)
        logger.info("Upserted %d vectors into Qdrant collection '%s'",
                    len(points), self.collection)

    def retrieve_similar(
        self, query_latent: np.ndarray, top_k: int = 10
    ) -> list:
        results = self.qdrant.search(
            collection_name = self.collection,
            query_vector    = query_latent.tolist(),
            limit           = top_k
        )
        return results
2.5 — Contextual Bandit Meta-Learning Routing Policy
YAML: routing_policy config block
routing_policy:
  algorithm:  linucb
  alpha:      1.0
  context_dim: 128
  arms:
    - node_01_inference
    - node_02_feature_eng
    - node_03_training
    - local_llm
    - azure_openai
  update_interval_seconds: 300
  meta_learning:
    enabled:         true
    inner_lr:        0.01
    outer_lr:        0.001
    task_batch_size: 8
  policy_path: D:/DevDrive/hermes/configs/routing_policy.json
MODULE: routing_policy.py
# routing_policy.py — Hermes XCore Contextual Bandit Routing Policy
# LinUCB algorithm with MAML-style meta-learning wrapper.
# Pseudo-code: review and implement before use.

from __future__ import annotations
import json
import logging
import uuid
from dataclasses import dataclass
from typing import Optional

import numpy as np
import httpx

logger = logging.getLogger("hermes.routing_policy")

@dataclass
class TaskEpisode:
    support_contexts: np.ndarray   # (K, context_dim)
    support_rewards:  np.ndarray   # (K,)
    arm_selected:     list[str]

@dataclass
class Experience:
    context: np.ndarray
    arm:     str
    reward:  float

# -----------------------------------------------------------
# ContextualBanditRouter (LinUCB)
# -----------------------------------------------------------
class ContextualBanditRouter:
    """
    LinUCB contextual bandit. Maintains per-arm ridge regression
    parameters (A matrix, b vector) for upper confidence bound selection.
    Sherman-Morrison rank-1 update for efficient online learning.
    """

    def __init__(
        self,
        arms:        list[str],
        context_dim: int,
        db_conn,
        qdrant_client,
        alpha:       float = 1.0
    ):
        self.arms        = arms
        self.d           = context_dim
        self.alpha       = alpha
        self.db_conn     = db_conn
        self.qdrant      = qdrant_client
        # Per-arm parameters
        self.A      = {arm: np.eye(self.d, dtype=np.float64)        for arm in arms}
        self.A_inv  = {arm: np.eye(self.d, dtype=np.float64)        for arm in arms}
        self.b      = {arm: np.zeros((self.d, 1), dtype=np.float64) for arm in arms}
        logger.info("ContextualBanditRouter initialized: %d arms, context_dim=%d", len(arms), context_dim)

    def select_arm(self, context: np.ndarray) -> tuple[str, float]:
        """
        Computes UCB score for each arm:
            theta_hat = A^-1 @ b
            p_t(a) = theta_hat.T @ x + alpha * sqrt(x.T @ A^-1 @ x)
        Returns (arm_name, confidence).
        """
        x = context.reshape(-1, 1).astype(np.float64)
        ucb_scores = {}
        for arm in self.arms:
            theta_hat  = self.A_inv[arm] @ self.b[arm]
            mean       = float(theta_hat.T @ x)
            variance   = float(x.T @ self.A_inv[arm] @ x)
            ucb_scores[arm] = mean + self.alpha * np.sqrt(max(variance, 0.0))
        best_arm    = max(ucb_scores, key=ucb_scores.__getitem__)
        confidence  = float(ucb_scores[best_arm])
        logger.debug("UCB selected arm=%s confidence=%.4f", best_arm, confidence)
        return best_arm, confidence

    def update(self, arm: str, context: np.ndarray, reward: float):
        """
        Online update using Sherman-Morrison rank-1 formula for A_inv.
        A <- data-id="192" A + x x^T
        b <- b + r x
        A_inv <- A_inv - (A_inv x)(A_inv x)^T / (1 + x^T A_inv x)
        """
        x   = context.reshape(-1, 1).astype(np.float64)
        Ax  = self.A_inv[arm] @ x
        denom = 1.0 + float(x.T @ Ax)
        self.A_inv[arm] -= (Ax @ Ax.T) / denom
        self.b[arm]     += reward * x
        logger.debug("Updated arm=%s reward=%.4f", arm, reward)

    def log_decision(
        self, session_id: str, context: np.ndarray,
        arm: str, confidence: float, reward: Optional[float] = None
    ):
        cursor = self.db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO hermes_routing_decisions
                (session_id, input_context, selected_arm, confidence, actual_reward)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (session_id, json.dumps(context.tolist()), arm, confidence, reward)
        )
        self.db_conn.commit()

    def save_policy(self, path: str):
        state = {
            "arms":  self.arms,
            "alpha": self.alpha,
            "d":     self.d,
            "A_inv": {k: v.tolist() for k, v in self.A_inv.items()},
            "b":     {k: v.tolist() for k, v in self.b.items()}
        }
        with open(path, "w") as f:
            json.dump(state, f, indent=2)
        logger.info("Policy saved to %s", path)

    def load_policy(self, path: str):
        with open(path) as f:
            state = json.load(f)
        self.arms   = state["arms"]
        self.alpha  = state["alpha"]
        self.d      = state["d"]
        self.A_inv  = {k: np.array(v) for k, v in state["A_inv"].items()}
        self.b      = {k: np.array(v) for k, v in state["b"].items()}
        logger.info("Policy loaded from %s", path)

    def export_for_deployment(self) -> dict:
        return {
            "arms":  self.arms,
            "alpha": self.alpha,
            "d":     self.d,
            "A_inv": {k: v.tolist() for k, v in self.A_inv.items()},
            "b":     {k: v.tolist() for k, v in self.b.items()}
        }

def deploy_policy(policy_dict: dict, node_endpoints: list[str]):
    """
    POST updated policy to each node's /policy/update endpoint.
    Rolls back if any node returns non-200.
    """
    successful = []
    for endpoint in node_endpoints:
        url = f"{endpoint}/policy/update"
        try:
            r = httpx.post(url, json=policy_dict, timeout=10.0)
            r.raise_for_status()
            successful.append(endpoint)
            logger.info("Policy deployed to %s", endpoint)
        except Exception as e:
            logger.error("Policy deployment FAILED for %s: %s", endpoint, e)
            logger.warning("Rolling back successfully deployed nodes: %s", successful)
            # Rollback: POST previous policy (caller should pass previous_policy_dict)
            raise RuntimeError(f"Policy deployment failed at {endpoint}. Rollback required.") from e

# -----------------------------------------------------------
# MetaLearningWrapper (MAML-style)
# -----------------------------------------------------------
class MetaLearningWrapper:
    """
    Wraps ContextualBanditRouter with MAML-style fast adaptation.
    Inner loop: few-step gradient on support set.
    Outer loop: meta-gradient over task batch.
    """

    def __init__(self, base_router: ContextualBanditRouter, inner_lr=0.01, outer_lr=0.001):
        self.base_router = base_router
        self.inner_lr    = inner_lr
        self.outer_lr    = outer_lr

    def meta_update(self, task_batch: list[TaskEpisode]):
        """
        For each task episode: compute fast-adapted policy params,
        evaluate on query set, accumulate meta-gradient, apply outer update.
        (Simplified placeholder — full MAML requires differentiable inner loop.)
        """
        meta_grads = {arm: np.zeros_like(self.base_router.b[arm])
                      for arm in self.base_router.arms}
        for episode in task_batch:
            for i, arm in enumerate(episode.arm_selected):
                ctx    = episode.support_contexts[i]
                reward = episode.support_rewards[i]
                meta_grads[arm] += self.outer_lr * reward * ctx.reshape(-1, 1)
        for arm in self.base_router.arms:
            self.base_router.b[arm] += meta_grads[arm]
        logger.info("Meta-update applied over %d task episodes.", len(task_batch))

    def adapt(self, support_set: list[Experience]) -> ContextualBanditRouter:
        """Few-shot adapts a copy of the base policy to the support set distribution."""
        import copy
        adapted = copy.deepcopy(self.base_router)
        for exp in support_set:
            adapted.update(exp.arm, exp.context, exp.reward)
        logger.info("Policy adapted on %d support experiences.", len(support_set))
        return adapted
2.6 — Continuous Retraining Loop
YAML: retraining config block
retraining:
  drift_psi_threshold:       0.20
  reward_decline_threshold:  0.10
  schedule_interval_hours:   24
  lookback_days:             30
  champion_challenger_margin: 0.02
  max_concurrent_jobs:       2
  training_backend:          wsl2
  gpu_passthrough:           true
  model_checkpoint_dir:      D:/DevDrive/ai-hub/checkpoints
  rollback_enabled:          true
  rollback_versions_to_keep: 3
MODULE: retraining_loop.py
# retraining_loop.py — Hermes XCore Continuous Retraining Orchestrator
# Pseudo-code: review and implement before use.

from __future__ import annotations
import logging
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("hermes.retraining_loop")

@dataclass
class DriftReport:
    feature_psi_scores:   dict[str, float]
    categorical_chi2:     dict[str, float]
    embedding_drift:      float
    overall_drift_detected: bool

@dataclass
class DataSplit:
    X_train: pd.DataFrame
    X_val:   pd.DataFrame
    X_test:  pd.DataFrame
    y_train: pd.Series
    y_val:   pd.Series
    y_test:  pd.Series

@dataclass
class TrainingResult:
    model_id:      str
    artifact_path: str
    train_loss:    float
    val_loss:      float
    eval_score:    float

@dataclass
class EvalReport:
    champion_score:   float
    challenger_score: float
    improvement:      float
    promote:          bool

class ContinuousRetrainingOrchestrator:
    """
    Monitors for data drift and reward decline; triggers retraining
    when conditions are met; promotes or rejects challenger models.
    """

    def __init__(self, config: dict, db_conn, model_registry):
        self.config         = config
        self.db_conn        = db_conn
        self.model_registry = model_registry
        self._shutdown      = False
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT,  self._handle_shutdown)
        logger.info("ContinuousRetrainingOrchestrator initialized.")

    def _handle_shutdown(self, signum, frame):
        logger.info("Shutdown signal received — completing current iteration then stopping.")
        self._shutdown = True

    def check_drift(
        self,
        new_data:        pd.DataFrame,
        reference_stats: dict
    ) -> DriftReport:
        """
        PSI for numeric features, Chi-square for categorical,
        cosine drift for text embeddings.
        PSI formula: PSI = sum((actual% - expected%) * ln(actual% / expected%))
        """
        psi_scores = {}
        for col, ref_dist in reference_stats.get("numeric", {}).items():
            if col not in new_data.columns:
                continue
            bins   = ref_dist["bins"]
            ref_pct = np.array(ref_dist["pct"]) + 1e-8
            act_counts, _ = np.histogram(new_data[col].dropna(), bins=bins)
            act_pct = act_counts / (act_counts.sum() + 1e-8) + 1e-8
            psi = float(np.sum((act_pct - ref_pct) * np.log(act_pct / ref_pct)))
            psi_scores[col] = psi

        chi2_scores = {}
        for col, ref_freq in reference_stats.get("categorical", {}).items():
            if col not in new_data.columns:
                continue
            from scipy.stats import chi2_contingency
            actual_freq = new_data[col].value_counts()
            cats = list(set(list(ref_freq.keys()) + list(actual_freq.index)))
            obs  = np.array([actual_freq.get(c, 0) for c in cats])
            exp  = np.array([ref_freq.get(c, 1e-6)  for c in cats])
            exp  = exp / exp.sum() * obs.sum()
            stat, p, *_ = chi2_contingency(np.vstack([obs, exp]))
            chi2_scores[col] = float(stat)

        emb_drift = reference_stats.get("embedding_cosine_drift", 0.0)
        psi_threshold = self.config.get("drift_psi_threshold", 0.20)
        drift_detected = any(v > psi_threshold for v in psi_scores.values())

        return DriftReport(
            feature_psi_scores     = psi_scores,
            categorical_chi2       = chi2_scores,
            embedding_drift        = emb_drift,
            overall_drift_detected = drift_detected
        )

    def trigger_condition(
        self, drift_report: DriftReport, feedback_stats: dict
    ) -> bool:
        psi_trigger    = drift_report.overall_drift_detected
        reward_trigger = feedback_stats.get("mean_reward", 1.0) < (
            1.0 - self.config.get("reward_decline_threshold", 0.10)
        )
        return psi_trigger or reward_trigger

    def prepare_training_data(self, lookback_days: int = 30) -> DataSplit:
        """
        Queries Postgres for recent features + feedback.
        Performs stratified train/val/test split (70/15/15).
        """
        from sklearn.model_selection import train_test_split
        cursor = self.db_conn.cursor()
        cursor.execute(
            """
            SELECT fl.feature_name, fl.correlation_score, fb.reward_signal
            FROM hermes_feature_log fl
            JOIN hermes_feedback_log fb ON fl.run_id = fb.session_id
            WHERE fl.created_at >= NOW() - INTERVAL '%s days'
            """,
            (lookback_days,)
        )
        rows = cursor.fetchall()
        df   = pd.DataFrame(rows, columns=["feature_name", "correlation_score", "reward"])
        X    = df.drop(columns=["reward"])
        y    = df["reward"]
        X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.30, random_state=42)
        X_va, X_te, y_va, y_te   = train_test_split(X_tmp, y_tmp, test_size=0.50, random_state=42)
        return DataSplit(X_train=X_tr, X_val=X_va, X_test=X_te,
                         y_train=y_tr, y_val=y_va,   y_test=y_te)

    def run_training_job(
        self, data: DataSplit, model_config: dict
    ) -> TrainingResult:
        """
        Launches training subprocess in WSL2 or Hyper-V VM with GPU passthrough.
        Monitors exit code; returns TrainingResult on success.
        """
        training_script = "D:/DevDrive/hermes/scripts/train_job.py"
        backend = self.config.get("training_backend", "wsl2")
        if backend == "wsl2":
            cmd = ["wsl", "python3", training_script,
                   "--config", model_config.get("config_path", ""),
                   "--run-id", model_config.get("run_id", "")]
        else:
            cmd = ["powershell", "-Command",
                   f"Start-VM HermesTrainer; Invoke-Command ..."]  # Hyper-V variant
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if result.returncode != 0:
            logger.error("Training job FAILED: %s", result.stderr)
            raise RuntimeError("Training job failed.")
        return TrainingResult(
            model_id      = model_config.get("run_id", ""),
            artifact_path = f"D:/DevDrive/ai-hub/checkpoints/{model_config.get('run_id','')}.pt",
            train_loss    = 0.0,  # parsed from stdout in real implementation
            val_loss      = 0.0,
            eval_score    = 0.0
        )

    def evaluate_candidate(self, result: TrainingResult) -> EvalReport:
        """
        Compares challenger to current champion on holdout set.
        Promotes if challenger beats champion by champion_challenger_margin.
        """
        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT eval_score FROM hermes_model_registry WHERE is_active = TRUE LIMIT 1"
        )
        row = cursor.fetchone()
        champion_score   = row[0] if row else 0.0
        challenger_score = result.eval_score
        margin           = self.config.get("champion_challenger_margin", 0.02)
        improvement      = challenger_score - champion_score
        return EvalReport(
            champion_score   = champion_score,
            challenger_score = challenger_score,
            improvement      = improvement,
            promote          = improvement >= margin
        )

    def promote_or_reject(self, eval_report: EvalReport, result: TrainingResult):
        if eval_report.promote:
            cursor = self.db_conn.cursor()
            cursor.execute("UPDATE hermes_model_registry SET is_active=FALSE WHERE is_active=TRUE")
            cursor.execute(
                """
                UPDATE hermes_model_registry SET is_active=TRUE, deployed_at=NOW()
                WHERE model_id=%s
                """,
                (result.model_id,)
            )
            self.db_conn.commit()
            logger.info("Challenger PROMOTED: model_id=%s improvement=%.4f",
                        result.model_id, eval_report.improvement)
        else:
            logger.info("Challenger REJECTED: improvement=%.4f below margin=%.4f",
                        eval_report.improvement,
                        self.config.get("champion_challenger_margin", 0.02))

    def rollback(self, to_model_id: str):
        cursor = self.db_conn.cursor()
        cursor.execute("UPDATE hermes_model_registry SET is_active=FALSE WHERE is_active=TRUE")
        cursor.execute(
            "UPDATE hermes_model_registry SET is_active=TRUE WHERE model_id=%s",
            (to_model_id,)
        )
        self.db_conn.commit()
        logger.info("ROLLBACK: restored champion model_id=%s", to_model_id)

    def run_loop(self, interval_seconds: int = 3600):
        """Main scheduling loop. Runs until shutdown signal received."""
        logger.info("Retraining loop started. Interval: %ds", interval_seconds)
        while not self._shutdown:
            try:
                logger.info("--- Retraining loop tick ---")
                # (1) Pull reference stats from last known good run
                # (2) Fetch recent serving data
                # (3) Check drift + feedback
                # (4) If trigger: prepare data, run job, evaluate, promote/reject
                # Abbreviated here — full implementation follows module design above
            except Exception as e:
                logger.error("Retraining loop error: %s", e, exc_info=True)
            time.sleep(interval_seconds)
        logger.info("Retraining loop shut down gracefully.")
2.7 — Model Scoring and Feedback Ingestion
MODULE: scoring_feedback.py
# scoring_feedback.py — Hermes XCore Scoring and Feedback Ingestion
# Pseudo-code: review and implement before use.

from __future__ import annotations
import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from feature_pipeline import FeatureSet

logger = logging.getLogger("hermes.scoring_feedback")

@dataclass
class ScoringResult:
    model_id:    str
    output:      dict
    confidence:  float
    input_hash:  str
    output_hash: str

@dataclass
class FeedbackStats:
    mean_reward_per_model: dict[str, float]
    mean_reward_per_arm:   dict[str, float]
    total_feedback_count:  int
    lookback_hours:        int

class HermesScorer:
    def __init__(self, model_registry, device: str = "cuda"):
        self.model_registry = model_registry
        self.device         = device
        self._cache         = {}

    def _load_model(self, model_id: str):
        if model_id not in self._cache:
            artifact_path = self.model_registry.get_artifact_path(model_id)
            import torch
            model = torch.load(artifact_path, map_location=self.device)
            model.eval()
            self._cache[model_id] = model
        return self._cache[model_id]

    def hash_io(self, input_features: FeatureSet, output: dict) -> tuple[str, str]:
        """SHA-256 of serialized input and output for audit trail."""
        in_bytes  = json.dumps(
            input_features.numeric_features.to_dict(), sort_keys=True
        ).encode()
        out_bytes = json.dumps(output, sort_keys=True).encode()
        in_hash   = hashlib.sha256(in_bytes).hexdigest()
        out_hash  = hashlib.sha256(out_bytes).hexdigest()
        return in_hash, out_hash

    def score(self, input_features: FeatureSet, model_id: str) -> ScoringResult:
        import torch
        model = self._load_model(model_id)
        x     = torch.tensor(
            input_features.numeric_features.fillna(0).values,
            dtype=torch.float32
        ).to(self.device)
        with torch.no_grad():
            raw_output = model(x)
        output     = {"predictions": raw_output.cpu().numpy().tolist()}
        confidence = float(raw_output.softmax(dim=-1).max().item()) if raw_output.ndim > 1 else 1.0
        in_h, out_h = self.hash_io(input_features, output)
        return ScoringResult(
            model_id   = model_id,
            output     = output,
            confidence = confidence,
            input_hash = in_h,
            output_hash= out_h
        )

    def batch_score(
        self, batch: list[FeatureSet], model_id: str
    ) -> list[ScoringResult]:
        return [self.score(fs, model_id) for fs in batch]

class FeedbackIngester:
    def __init__(self, db_conn, bandit_router):
        self.db_conn      = db_conn
        self.bandit_router = bandit_router

    def validate_reward(self, reward: float) -> bool:
        import math
        return isinstance(reward, (int, float)) and not math.isnan(reward) and -1.0 <= data-id="201" reward <= 1.0

    def ingest(
        self,
        session_id:     str,
        model_id:       str,
        input_hash:     str,
        output_hash:    str,
        reward_signal:  float,
        context_vector: list
    ):
        if not self.validate_reward(reward_signal):
            raise ValueError(f"Invalid reward signal: {reward_signal}")
        cursor = self.db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO hermes_feedback_log
                (session_id, model_id, input_hash, output_hash, reward_signal, context_vector)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (session_id, model_id, input_hash, output_hash,
             reward_signal, json.dumps(context_vector))
        )
        self.db_conn.commit()
        logger.info("Feedback ingested: session=%s reward=%.4f", session_id, reward_signal)

    def aggregate_feedback(self, lookback_hours: int = 24) -> FeedbackStats:
        cursor = self.db_conn.cursor()
        cursor.execute(
            """
            SELECT model_id, AVG(reward_signal), COUNT(*)
            FROM hermes_feedback_log
            WHERE created_at >= NOW() - INTERVAL '%s hours'
            GROUP BY model_id
            """,
            (lookback_hours,)
        )
        rows = cursor.fetchall()
        mean_by_model = {str(r[0]): float(r[1]) for r in rows}
        cursor.execute(
            """
            SELECT rd.selected_arm, AVG(fb.reward_signal)
            FROM hermes_routing_decisions rd
            JOIN hermes_feedback_log fb ON rd.session_id = fb.session_id
            WHERE rd.ts >= NOW() - INTERVAL '%s hours'
            GROUP BY rd.selected_arm
            """,
            (lookback_hours,)
        )
        arm_rows = cursor.fetchall()
        mean_by_arm = {r[0]: float(r[1]) for r in arm_rows}
        return FeedbackStats(
            mean_reward_per_model = mean_by_model,
            mean_reward_per_arm   = mean_by_arm,
            total_feedback_count  = sum(int(r[2]) for r in rows),
            lookback_hours        = lookback_hours
        )

    def trigger_policy_update(self, stats: FeedbackStats):
        """
        Calls ContextualBanditRouter.update() for each recent arm decision
        with its resolved reward signal.
        """
        cursor = self.db_conn.cursor()
        cursor.execute(
            """
            SELECT rd.selected_arm, fb.reward_signal, fb.context_vector
            FROM hermes_routing_decisions rd
            JOIN hermes_feedback_log fb ON rd.session_id = fb.session_id
            WHERE rd.actual_reward IS NULL
            LIMIT 500
            """
        )
        rows = cursor.fetchall()
        for arm, reward, ctx_json in rows:
            ctx = np.array(json.loads(ctx_json))
            self.bandit_router.update(arm, ctx, reward)
        logger.info("Policy update triggered for %d unresolved decisions.", len(rows))
2.8 — Vector DB Indexing and Retrieval (Qdrant)
YAML: Qdrant collection schema — embeddings_v1
collection: embeddings_v1
vectors:
  size:     128
  distance: Cosine
payload_schema:
  run_id:        keyword
  node_id:       keyword
  feature_type:  keyword
  created_at:    datetime
  model_version: keyword
MODULE: vector_store.py
# vector_store.py — Hermes XCore Vector Store (Qdrant)
# Pseudo-code: review and implement before use.

from __future__ import annotations
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)

logger = logging.getLogger("hermes.vector_store")

@dataclass
class SearchResult:
    id:      str
    score:   float
    payload: dict

class HermesVectorStore:
    """
    Manages all Qdrant interactions for the Hermes fleet:
    upsert, ANN search, soft delete, and collection management.
    """

    def __init__(self, qdrant_url: str, collection_name: str, vector_size: int):
        self.client          = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self.vector_size     = vector_size
        self.create_collection_if_missing(vector_size)

    def create_collection_if_missing(
        self, vector_size: int, distance_metric: str = "Cosine"
    ):
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in existing:
            dist = Distance.COSINE if distance_metric == "Cosine" else Distance.DOT
            self.client.create_collection(
                collection_name = self.collection_name,
                vectors_config  = VectorParams(size=vector_size, distance=dist)
            )
            logger.info("Created Qdrant collection '%s' (dim=%d, metric=%s)",
                        self.collection_name, vector_size, distance_metric)
        else:
            logger.debug("Collection '%s' already exists.", self.collection_name)

    def upsert_embeddings(
        self,
        ids:      list,
        vectors:  np.ndarray,
        payloads: list[dict],
        max_retries: int = 3
    ):
        """Batch upsert with exponential backoff retry on failure."""
        points = [
            PointStruct(
                id      = str(ids[i]),
                vector  = vectors[i].tolist(),
                payload = payloads[i]
            )
            for i in range(len(ids))
        ]
        for attempt in range(max_retries):
            try:
                self.client.upsert(collection_name=self.collection_name, points=points)
                logger.info("Upserted %d vectors into '%s'", len(points), self.collection_name)
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning("Upsert attempt %d failed (%s) — retrying in %ds", attempt+1, e, wait)
                    time.sleep(wait)
                else:
                    logger.error("Upsert FAILED after %d attempts: %s", max_retries, e)
                    raise

    def search(
        self,
        query_vector:   np.ndarray,
        top_k:          int = 10,
        filter_payload: Optional[dict] = None
    ) -> list[SearchResult]:
        query_filter = None
        if filter_payload:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_payload.items()
            ]
            query_filter = Filter(must=conditions)
        hits = self.client.search(
            collection_name = self.collection_name,
            query_vector    = query_vector.tolist(),
            limit           = top_k,
            query_filter    = query_filter
        )
        return [SearchResult(id=str(h.id), score=h.score, payload=h.payload) for h in hits]

    def delete_by_id(self, ids: list):
        """Soft delete: set deleted=True in payload rather than physical removal."""
        for pid in ids:
            self.client.set_payload(
                collection_name = self.collection_name,
                payload         = {"deleted": True},
                points          = [str(pid)]
            )
        logger.info("Soft-deleted %d vectors from '%s'", len(ids), self.collection_name)

    def get_collection_stats(self) -> dict:
        info = self.client.get_collection(self.collection_name)
        return {
            "vectors_count":     info.vectors_count,
            "indexed_vectors":   info.indexed_vectors_count,
            "segments_count":    info.segments_count,
            "status":            str(info.status)
        }
2.9 — Orchestration Across Hermes Fleet Nodes
MODULE: orchestrator.py (expanded)
# orchestrator.py — Hermes XCore Orchestrator (Full Design)
# Pseudo-code: review and implement before use.

from __future__ import annotations
import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

import httpx

from routing_policy import ContextualBanditRouter

logger = logging.getLogger("hermes.orchestrator")

@dataclass
class HermesTask:
    task_id:         str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type:       str = "inference"   # "inference" | "training" | "feature_eng"
    payload:         dict = field(default_factory=dict)
    priority:        int  = 5            # 1 (highest) to 10 (lowest)
    timeout_seconds: int  = 60

@dataclass
class DispatchResult:
    task_id:      str
    node_id:      str
    node_endpoint: str
    sent_at:      float

@dataclass
class TaskResult:
    task_id:   str
    node_id:   str
    status:    str          # "success" | "failed" | "timeout"
    output:    Optional[dict] = None
    error:     Optional[str]  = None

class HermesOrchestrator:
    """
    Central coordination point for the Hermes fleet.
    Maintains node registry, dispatches tasks via bandit policy,
    aggregates results, and triggers retraining on schedule.
    """

    def __init__(
        self,
        config_path:   str,
        db_conn,
        qdrant_client,
        policy:        ContextualBanditRouter
    ):
        import yaml
        with open(config_path) as f:
            self.config   = yaml.safe_load(f)
        self.db_conn       = db_conn
        self.qdrant        = qdrant_client
        self.policy        = policy
        self.node_registry = {}      # node_id -> {endpoint, capabilities, healthy}
        self.task_queue    = asyncio.Queue()
        self.running       = False

    def register_node(self, node_id: str, endpoint: str, capabilities: dict):
        self.node_registry[node_id] = {
            "endpoint":     endpoint,
            "capabilities": capabilities,
            "healthy":      True,
            "failure_count": 0
        }
        logger.info("Node registered: %s at %s (caps=%s)", node_id, endpoint, capabilities)

    async def health_check_all(self) -> dict[str, bool]:
        results = {}
        async with httpx.AsyncClient(timeout=5.0) as client:
            for node_id, info in self.node_registry.items():
                try:
                    r = await client.get(f"{info['endpoint']}/health")
                    healthy = r.status_code == 200
                except Exception:
                    healthy = False
                self.node_registry[node_id]["healthy"] = healthy
                results[node_id] = healthy
                if not healthy:
                    logger.warning("Node %s is UNHEALTHY", node_id)
        return results

    async def dispatch_task(self, task: HermesTask) -> DispatchResult:
        import numpy as np, time
        # Build context vector from task payload
        context = np.zeros(self.policy.d, dtype=np.float64)
        context[0] = {"inference": 0, "training": 1, "feature_eng": 2}.get(task.task_type, 0)
        context[1] = task.priority / 10.0
        arm, confidence = self.policy.select_arm(context)
        node_id  = arm.split("_inference")[0].split("_training")[0].split("_feature_eng")[0]
        node_info = self.node_registry.get(node_id, {})
        endpoint  = node_info.get("endpoint", "")
        async with httpx.AsyncClient(timeout=task.timeout_seconds) as client:
            r = await client.post(
                f"{endpoint}/v1/{task.task_type}",
                json={"task_id": task.task_id, "payload": task.payload}
            )
            r.raise_for_status()
        self.policy.log_decision(
            session_id = task.task_id,
            context    = context,
            arm        = arm,
            confidence = confidence
        )
        return DispatchResult(
            task_id       = task.task_id,
            node_id       = node_id,
            node_endpoint = endpoint,
            sent_at       = time.time()
        )

    async def handle_node_failure(self, node_id: str, task: HermesTask) -> DispatchResult:
        self.node_registry[node_id]["failure_count"] += 1
        self.node_registry[node_id]["healthy"] = False
        logger.error("Node %s FAILED for task %s — re-routing.", node_id, task.task_id)
        # Exclude failed node by zeroing its arm's confidence
        return await self.dispatch_task(task)

    async def run_orchestration_loop(self):
        self.running = True
        logger.info("Orchestration loop started.")
        while self.running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=5.0)
                try:
                    result = await self.dispatch_task(task)
                    logger.info("Task %s dispatched to node %s", task.task_id, result.node_id)
                except Exception as e:
                    logger.error("Dispatch error for task %s: %s", task.task_id, e)
            except asyncio.TimeoutError:
                await self.health_check_all()
Deliverable 3 — Security Mode Scripts (C / B / A)
3.1 — Security Philosophy and Mode Definitions
The Hermes workstation operates across three security modes. Mode selection is driven by operational context: full air-gap-like lockdown for sensitive data handling (Mode C), normal developer workflow with curated outbound access (Mode B), and full cloud integration for Azure/GitHub operations (Mode A). All three modes maintain local-only inbound access at all times — no RDP, WinRM, or inbound SSH is permitted under any mode.

Feature    Mode C — Locked    Mode B — Balanced (Default)    Mode A — Active
Outbound Network    Windows Update + Defender only    Curated allowlist (GitHub, Azure, PyPI, Docker)    Standard outbound (allow established)
Inbound Network    Blocked (all)    Localhost + WSL2 adapter only    Localhost only; no public inbound
WSL2    Shutdown + adapter disabled    Running, internal network only    Running, full localhost forwarding
Docker    Stopped; network=none    Running, internal bridge only    Running, bridge + localhost port exposure
Hyper-V VMs    Powered off or no NIC    HermesInternal vSwitch only    HermesNet (external) for Azure testing
BitLocker    TPM + PIN (startup PIN required)    TPM-only unlock    TPM-only unlock
Windows Sandbox    Disabled    Enabled (restricted folders)    Enabled (full config)
GitHub / Azure CLI    Tokens revoked and cleared    Authenticated, outbound only    Fully active
Purview / Entra    Offline (no cloud reach)    Read-only context cached    Fully active
Defender    Maximum protection + maximum audit    Default + enhanced real-time    Default protection
3.2 — Mode Toggle Script
FILE: set_security_mode.ps1
#Requires -Version 7.0
#Requires -RunAsAdministrator
# =============================================================
# set_security_mode.ps1
# Usage: .\set_security_mode.ps1 -Mode C|B|A
# Toggles Hermes workstation between security operating modes.
# NOT FOR BLIND EXECUTION — Review all firewall rules before use.
# =============================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("C","B","A")]
    [string]$Mode
)

$ErrorActionPreference = "Stop"
$LogPath = "D:\DevDrive\logs\security_mode_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss")
function Log($msg) { $line = "[$(Get-Date -Format 's')] $msg"; Write-Host $line; $line | Tee-Object -FilePath $LogPath -Append }

# -----------------------------------------------------------
# SNAPSHOT CURRENT STATE BEFORE ANY CHANGE
# -----------------------------------------------------------
Log "Snapshotting current firewall and service state..."
Get-NetFirewallRule | Where-Object Enabled -eq True | Select-Object DisplayName,Direction,Action |
    Out-File "D:\DevDrive\logs\firewall_snapshot_{0}.txt" -f (Get-Date -Format "yyyyMMdd_HHmmss")
Get-Service | Where-Object Status -eq Running | Select-Object Name,Status |
    Out-File "D:\DevDrive\logs\services_snapshot_{0}.txt" -f (Get-Date -Format "yyyyMMdd_HHmmss")
Log "Snapshot complete."

# -----------------------------------------------------------
function Set-ModeC {
    Log "Entering Mode C — Maximum Security (Locked)"

    # Block all outbound firewall rules except Windows Update and Defender
    Get-NetFirewallRule -Direction Outbound -Action Allow | Where-Object {
        $_.DisplayName -notmatch "Windows Update|Windows Defender|MpsSvc"
    } | Disable-NetFirewallRule
    Log "All non-system outbound firewall rules DISABLED."

    # Allow only Windows Update FQDN list (create explicit rules if not present)
    New-NetFirewallRule -DisplayName "Allow-WindowsUpdate-ModeC" `
        -Direction Outbound -Action Allow -Protocol TCP `
        -RemoteAddress "13.107.4.50","13.107.5.88","13.107.9.79","40.73.5.206" `
        -ErrorAction SilentlyContinue

    # Shutdown WSL2
    wsl --shutdown
    Log "WSL2 shut down."

    # Disable HermesNet external vSwitch (blocks VM external access)
    Set-VMSwitch -Name "HermesNet" -NetAdapterName "" -ErrorAction SilentlyContinue
    Log "HermesNet external vSwitch disconnected."

    # Stop Docker Desktop
    Stop-Service "com.docker.service" -ErrorAction SilentlyContinue
    Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
    Log "Docker Desktop stopped."

    # Enforce BitLocker TPM+PIN on C:
    # manage-bde -protectors -add C: -TPMAndPIN
    Log "PSEUDO: manage-bde -protectors -add C: -TPMAndPIN  (requires interactive PIN entry)"

    # Revoke GitHub CLI token
    gh auth logout --hostname github.com -ErrorAction SilentlyContinue
    Log "GitHub CLI token revoked."

    # Revoke Azure CLI token
    az account clear -ErrorAction SilentlyContinue
    Log "Azure CLI context cleared."

    # Disable Windows Sandbox
    Disable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -NoRestart -ErrorAction SilentlyContinue
    Log "Windows Sandbox disabled."

    # Set Defender to high protection
    Set-MpPreference -MAPSReporting Advanced
    Set-MpPreference -SubmitSamplesConsent SendSafeSamples
    Set-MpPreference -RealTimeProtectionEnabled $true
    Log "Defender set to maximum protection."

    # Enable maximum audit policies
    auditpol /set /category:"Logon/Logoff" /success:enable /failure:enable
    auditpol /set /category:"Account Logon" /success:enable /failure:enable
    auditpol /set /category:"Policy Change" /success:enable /failure:enable
    auditpol /set /category:"Privilege Use"  /success:enable /failure:enable
    Log "Audit policies maximized."

    Log "Mode C APPLIED. System is in LOCKED state."
}

# -----------------------------------------------------------
function Set-ModeB {
    Log "Entering Mode B — Balanced Developer (Default)"

    # Reset all firewall rules to Mode B allowlist
    Get-NetFirewallRule -DisplayName "Allow-*-ModeC" | Remove-NetFirewallRule -ErrorAction SilentlyContinue

    $allowedDomains = @(
        "github.com", "*.github.com",
        "*.microsoft.com", "*.azure.com",
        "pypi.org", "*.pypi.org",
        "registry-1.docker.io", "*.docker.io",
        "*.huggingface.co", "*.anaconda.org"
    )
    # PSEUDO: Create outbound allow rules per domain group
    # (Windows Firewall does not natively filter by FQDN; use DNS-based filtering or Windows Defender Application Control)
    Log "PSEUDO: Apply Mode B outbound allowlist (GitHub, Azure, PyPI, Docker, Hugging Face)"

    # Block all inbound except localhost and WSL2 adapter
    New-NetFirewallRule -DisplayName "Block-Inbound-ModeB" `
        -Direction Inbound -Action Block -Protocol Any `
        -RemoteAddress "0.0.0.0-127.0.0.0","128.0.0.0-255.255.255.255" `
        -ErrorAction SilentlyContinue
    Log "Inbound blocked except localhost."

    # Ensure WSL2 running with internal networking
    wsl --distribution Ubuntu-22.04 -- echo "WSL2 active" 2>&1 | Out-Null
    Log "WSL2 running."

    # Set Hyper-V VMs to HermesInternal only (disconnect HermesNet)
    Get-VM | ForEach-Object { Set-VMNetworkAdapter -VMName $_.Name -SwitchName "HermesInternal" -ErrorAction SilentlyContinue }
    Log "Hyper-V VMs set to HermesInternal vSwitch."

    # BitLocker TPM-only on C:
    # manage-bde -protectors -add C: -TPM
    Log "PSEUDO: manage-bde -protectors -add C: -TPM"

    # Enable Windows Sandbox with restricted config
    Enable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -NoRestart -ErrorAction SilentlyContinue
    Log "Windows Sandbox enabled."

    # Re-authenticate if tokens missing
    $ghStatus = gh auth status 2>&1
    if ($ghStatus -match "not logged") {
        Log "GitHub CLI not authenticated — run: gh auth login --web"
    }
    $azStatus = az account show 2>&1
    if ($azStatus -match "error") {
        Log "Azure CLI not authenticated — run: az login --use-device-code"
    }

    Log "Mode B APPLIED. Developer mode active."
}

# -----------------------------------------------------------
function Set-ModeA {
    Log "Entering Mode A — Active Cloud-Connected"

    # Reset firewall to default Windows profile
    netsh advfirewall reset
    Log "Windows Firewall reset to defaults."

    # Enable full WSL2 networking
    # Update .wslconfig: localhostForwarding=true (already set in Phase 1)
    Log "WSL2 full networking with localhost forwarding enabled."

    # Re-enable HermesNet external vSwitch for Azure integration testing
    # manage-bde should already be TPM-only from Mode B
    Set-VMSwitch -Name "HermesNet" -NetAdapterName "{your-physical-nic}" -ErrorAction SilentlyContinue
    Log "HermesNet external vSwitch re-enabled."

    # Verify Entra device compliance
    dsregcmd /status | Out-File "D:\DevDrive\logs\entra_status_modeA.txt"
    Log "Entra device status written to logs."

    # Confirm Azure CLI subscription context
    az account show | Out-File "D:\DevDrive\logs\azure_subscription_modeA.txt"
    Log "Azure CLI subscription context confirmed."

    # Activate Purview DLP policies (via Azure CLI or Purview CLI)
    Log "PSEUDO: az purview account show --name hermes-purview --resource-group hermes-rg"

    Log "Mode A APPLIED. Cloud integration fully active."
}

# -----------------------------------------------------------
# DISPATCH
# -----------------------------------------------------------
switch ($Mode) {
    "C" { Set-ModeC }
    "B" { Set-ModeB }
    "A" { Set-ModeA }
}
Log "Security mode script complete. Mode=$Mode. Log at $LogPath"
3.3 — BitLocker Configuration Script
FILE: configure_bitlocker.ps1
#Requires -Version 7.0
#Requires -RunAsAdministrator
# =============================================================
# configure_bitlocker.ps1
# Configures BitLocker on C:, D:, and optionally E:.
# Recovery keys are stored in Azure AD/Entra — NOT local files.
# NOT FOR BLIND EXECUTION — Review mode and drive letters first.
# =============================================================

$ErrorActionPreference = "Stop"
$LogFile = "D:\DevDrive\logs\bitlocker_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss")
function Log($msg) { $line = "[$(Get-Date -Format 's')] $msg"; Write-Host $line; $line | Out-File $LogFile -Append }

param(
    [ValidateSet("C","B","A")]
    [string]$SecurityMode = "B"
)

Log "=== BITLOCKER CONFIGURATION — Security Mode $SecurityMode ==="

# -----------------------------------------------------------
# CHECK TPM 2.0
# -----------------------------------------------------------
$tpm = Get-Tpm
if (-not $tpm.TpmPresent -or -not $tpm.TpmReady) {
    throw "FATAL: TPM 2.0 not present or not ready. Enable in BIOS firmware settings."
}
Log "TPM 2.0 present and ready: SpecVersion=$($tpm.ManufacturerVersionFull)"

# -----------------------------------------------------------
# CONFIGURE C:
# -----------------------------------------------------------
Log "Configuring BitLocker on C:..."
if ($SecurityMode -eq "C") {
    # Mode C: TPM + PIN
    Log "PSEUDO: manage-bde -on C: -UsedSpaceOnly -TpmAndPin"
    Log "PSEUDO: manage-bde -protectors -add C: -TPMAndPIN  (will prompt for PIN)"
} else {
    # Mode B / A: TPM only
    manage-bde -on C: -UsedSpaceOnly -TpmOnly 2>&1 | Out-File $LogFile -Append -ErrorAction SilentlyContinue
    Log "BitLocker TPM-only enabled on C:"
}
# Save recovery key to Azure AD (Entra) — NOT to local file
# PSEUDO: BackupToAAD-BitLockerKeyProtector -MountPoint C: -KeyProtectorId (Get-BitLockerVolume C:).KeyProtector[0].KeyProtectorId
Log "PSEUDO: BackupToAAD-BitLockerKeyProtector C: — saves recovery key to Entra (not local)"

# -----------------------------------------------------------
# CONFIGURE D: (DevDrive)
# -----------------------------------------------------------
Log "Configuring BitLocker on D: (DevDrive)..."
manage-bde -on D: -UsedSpaceOnly -TpmOnly 2>&1 | Out-File $LogFile -Append -ErrorAction SilentlyContinue
Log "PSEUDO: BackupToAAD-BitLockerKeyProtector D: — saves recovery key to Entra"

# -----------------------------------------------------------
# CONFIGURE E: (if present)
# -----------------------------------------------------------
if (Test-Path "E:\") {
    Log "E: drive detected — configuring BitLocker on E:..."
    manage-bde -on E: -UsedSpaceOnly -TpmOnly 2>&1 | Out-File $LogFile -Append -ErrorAction SilentlyContinue
    Log "PSEUDO: BackupToAAD-BitLockerKeyProtector E:"
}

# -----------------------------------------------------------
# VERIFY STATUS
# -----------------------------------------------------------
Log "=== BITLOCKER STATUS ==="
manage-bde -status | Out-File $LogFile -Append
Log "Full status written to $LogFile. Reboot to verify TPM unlock."

# Store recovery key ID (NOT the key) in hermes_run_log for audit
$keyId = (Get-BitLockerVolume C:).KeyProtector |
    Where-Object { $_.KeyProtectorType -eq "RecoveryPassword" } |
    Select-Object -First 1 -ExpandProperty KeyProtectorId
Log "C: Recovery Key Protector ID: $keyId  (logged for audit — key stored in Entra only)"
3.4 — Secrets Management Policy
All secrets used by the Hermes system follow a strict tiered management policy. No secret is ever stored in plaintext on disk, committed to Git, or passed as a command-line argument visible in process listings.

Secret Type    Storage Location    Access Method    Rotation Schedule
GitHub PAT    Windows Credential Manager (wincred)    gh auth token    Every 90 days
Azure SP Client Secret    Azure Key Vault (hermes-kv)    az keyvault secret show    Every 180 days
Postgres Password    Windows Credential Manager or Key Vault    PowerShell SecretManagement module    Every 90 days
Qdrant API Key    Azure Key Vault (hermes-kv)    az keyvault secret show    Every 90 days
OpenAI / Azure OpenAI Key    Azure Key Vault (hermes-kv)    SDK key vault reference    Every 90 days
Docker secrets.env    D:\DevDrive\hermes\configs\secrets.env    Docker --env-file; chmod 600; never committed    Per-component schedule
PowerShell: Secret helper functions using SecretManagement module
# Install SecretManagement and SecretStore modules (one-time)
# Install-Module Microsoft.PowerShell.SecretManagement -Scope CurrentUser
# Install-Module Microsoft.PowerShell.SecretStore       -Scope CurrentUser
# Register-SecretVault -Name HermesLocalVault -ModuleName Microsoft.PowerShell.SecretStore

function Get-HermesSecret {
    param([string]$SecretName)
    return Get-Secret -Name $SecretName -Vault HermesLocalVault -AsPlainText
}

function Set-HermesSecret {
    param([string]$SecretName, [string]$SecretValue)
    Set-Secret -Name $SecretName -Secret $SecretValue -Vault HermesLocalVault
    Write-Host "Secret '$SecretName' stored in HermesLocalVault."
}

# Example usage:
# $pgPass = Get-HermesSecret -SecretName "postgres-password"
# $env:POSTGRES_PASSWORD = $pgPass
.gitignore entries (add to D:\DevDrive\repos\hermes\.gitignore):
# Secrets — never commit
secrets.env
*.key
*.pem
*.p12
*.pfx
*.env.local
credentials.json
service_account.json

# DevDrive paths — exclude large artifacts
/data/raw/
/data/processed/
/ai-hub/models/
/ai-hub/checkpoints/
/caches/
/postgres/
/qdrant/
3.5 — WSL2 and Docker Isolation Configuration
FILE: .wslconfig additions for Mode C and B (in %USERPROFILE%\.wslconfig)
[wsl2]
memory=32GB
processors=16
swap=8GB
swapFile=D:\\DevDrive\\wsl2\\swap.vhd
localhostForwarding=true
nestedVirtualization=true
kernelCommandLine=quiet splash

# Mode B: mirrored networking with host firewall enforcement
networkingMode=mirrored
firewall=true
dnsTunneling=false

# Mode C override (applied via registry + reboot):
# networkingMode=none
# Set: HKLM\SYSTEM\CurrentControlSet\Services\WslService\Parameters\NetworkingMode = 0
FILE: daemon.json — Full hardened Docker configuration (C:\ProgramData\docker\config\daemon.json)
{
  "data-root": "D:\\DevDrive\\docker",
  "userns-remap": "default",
  "no-new-privileges": true,
  "live-restore": true,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "features": {
    "buildkit": true
  },
  "ip": "127.0.0.1",
  "ipv6": false,
  "fixed-cidr": "172.20.0.0/16"
}
3.6 — Windows Sandbox Config for Hermes Testing
FILE: hermes_sandbox.wsb
<Configuration>
  <VGpu>Enable</VGpu>
  <Networking>Disable</Networking>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>D:\DevDrive\sandbox</HostFolder>
      <SandboxFolder>C:\SandboxShare</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>powershell -ExecutionPolicy Bypass -File C:\SandboxShare\sandbox_init.ps1</Command>
  </LogonCommand>
</Configuration>
Sandbox Notes
The sandbox VHD is ephemeral — all state is lost on Sandbox closure. Use D:\DevDrive\sandbox\ as the read-only share for scripts and test data. sandbox_init.ps1 should install only the minimum Python environment needed for the test, then run the target module. Never map the full DevDrive read-write into the Sandbox.
Deliverable 4 — Wiring Diagrams (Text-Based)
The following ASCII wiring diagrams document the primary data flows and integration paths in the Hermes XCore system. These diagrams represent the logical flow, not network topology. All connections operate on localhost (127.0.0.1) in Mode B. External connections (Azure, GitHub) are only active in Mode A.

4.1 — Log Flow: Hermes Nodes to SQL and Vector DB
[Hermes Node n (WSL2 / Hyper-V VM)]
  |
  |-- Task executes (inference | training | feature_eng)
  |
  +--[Python structlog StructuredLogHandler]
        |-- Serializes log record to JSON (level, msg, run_id, node_id, ts, payload_hash)
        |
        +--[Local file sink]
        |     --> D:/DevDrive/hermes/nodes/node_n/logs/current.log  (rotated daily, max 100 MB)
        |
        +--[LogForwarder thread (async queue, non-blocking)]
              |
              +--[TCP socket --> Orchestrator 127.0.0.1:8700 (persistent connection)]
                    |
                    +--[Orchestrator LogAggregator (asyncio consumer)]
                          |
                          +--[DB Writer (psycopg2, connection pool)]
                          |     --> PostgreSQL 127.0.0.1:5432
                          |         hermes_logs.hermes_run_log     (per-run status)
                          |         hermes_logs.hermes_feature_log  (per-feature stats)
                          |
                          +--[Embedding Writer (sentence-transformers on GPU/CPU)]
                                |-- Encodes log payload context field to 128-dim latent
                                |
                                +--[Qdrant Upsert --> 127.0.0.1:6333]
                                      Collection: embeddings_v1
                                      Payload: {run_id, node_id, task_type, ts, model_version}

FAILURE HANDLING:
  If DB write fails:
    --> Buffer log in local SQLite at D:\DevDrive\hermes\nodes\node_n\logs\fallback.db
    --> Orchestrator LogAggregator retries DB write on reconnect (exponential backoff)
    --> Fallback.db is drained and then replayed to Postgres on reconnect success

  If Qdrant write fails:
    --> Log payload is queued in memory (max 10,000 entries)
    --> Retry every 30 seconds until success
    --> If queue > 10,000: oldest entries are discarded, WARNING logged to hermes_run_log
4.2 — Routing Policy Update and Deployment Flow
[Feedback Ingester]
  Receives reward signal from user action or downstream evaluation system
  |
  +--> FeedbackIngester.validate_reward(reward)
  |       Checks: float, not NaN, range [-1.0, 1.0]
  |
  +--> INSERT INTO hermes_feedback_log (session_id, model_id, input_hash, output_hash, reward, context)
  |
  +--> [FeedbackStats aggregator — runs every 5 minutes via scheduled asyncio task]
          |
          +--> SELECT recent unresolved routing decisions JOIN feedback_log
          |
          +--> ContextualBanditRouter.update(arm, context_vector, reward)
          |       LinUCB Sherman-Morrison update:
          |         A_inv[arm] -= (A_inv x)(A_inv x)^T / (1 + x^T A_inv x)
          |         b[arm]     += reward * x
          |
          +--> [Trigger condition check]
                 if accumulated_updates >= N  (config: update_interval_seconds = 300)
                 OR scheduled policy refresh time reached:
                 |
                 +--> policy_manager.save_policy(path)
                 |         --> JSON to D:/DevDrive/hermes/configs/routing_policy.json
                 |
                 +--> deploy_policy(policy_dict, node_endpoints=[
                 |         "http://127.0.0.1:8701",
                 |         "http://127.0.0.1:8702",
                 |         "http://127.0.0.1:8703"
                 |     ])
                 |         --> POST /policy/update to each node
                 |         --> Each node validates JSON schema (pydantic)
                 |         --> Hot-reloads ContextualBanditRouter in-process
                 |         --> Returns HTTP 200 OK | 422 Validation Error
                 |
                 +--> health_check_all()
                 |         --> If any node returns non-200:
                 |             --> deploy_policy(previous_policy_dict, all_endpoints)  [ROLLBACK]
                 |             --> Log CRITICAL to hermes_run_log
                 |
                 +--> INSERT INTO hermes_model_registry (policy version, deployed_at)
4.3 — Copilot / Agent / Azure AI Foundry Integration Flow
[User / Copilot Chat / Semantic Kernel Agent]
  |
  +--> HermesRouterPlugin.route_task(context_vector, task_type, payload)
        (Semantic Kernel plugin, registered in kernel.add_plugin())
        |
        +--> HTTP POST http://127.0.0.1:8700/v1/route   (localhost only in Mode B)
              Body: { "context_vector": [...128 floats...], "task_type": "inference", "payload": {...} }
              |
              +--> Orchestrator.dispatch_task(HermesTask)
                    |
                    +--> ContextualBanditRouter.select_arm(context)
                    |         Returns: arm="node_01_inference", confidence=0.87
                    |
                    +--> POST http://127.0.0.1:8701/v1/infer
                                { task_id, payload }
                                |
                                +--> node_01 GPU inference (HermesAutoencoder / loaded LLM)
                                +--> Returns ScoringResult {output, confidence, output_hash}
              |
              +--> Orchestrator returns JSON result to SK plugin
                    { "result": {...}, "node_used": "node_01", "confidence": 0.87 }
              |
              +--> SK plugin returns structured result into Semantic Kernel context window
  |
  +--> [Optional feedback] Agent POSTs reward to http://127.0.0.1:8700/v1/feedback
              --> FeedbackIngester.ingest(session_id, model_id, input_hash, output_hash, reward, context)

---

[Azure AI Foundry Tool Registration — Mode A only]
  |
  +--> Foundry function tool schema registered in Azure AI Foundry project:
        {
          "tool_name":   "hermes_route",
          "description": "Route a task to the optimal Hermes node based on context",
          "parameters":  { "context_vector": "array[float]", "task_type": "string" }
        }
  |
  +--> Foundry invokes tool --> Semantic Kernel function call
  +--> SK --> HTTP POST to local Hermes endpoint (via ngrok secure tunnel or VPN in Mode A)
  +--> Returns structured JSON back into Foundry conversation context

---

[GitHub Actions CI/CD — triggered on push]
  |
  +--> git push to D:\DevDrive\repos\hermesxcore\ (main branch via PR)
        |
        +--> git hook: pre-push runs local lint + type-check (mypy, ruff)
        |
        +--> gh workflow run hermes-test.yml
              Steps:
                1. Set up Python 3.12 in WSL2 (ubuntu-22.04)
                2. pip install -r requirements.txt (from D:\DevDrive\ai-hub\venvs\hermes-core)
                3. pytest tests/ --cov=hermes --cov-report=xml
                4. mypy hermes/ --strict
                5. ruff check hermes/
              On success:
                +--> Trigger model staging: retraining_loop.py --mode=stage --run-id=ci-{commit_sha}
                +--> Artifacts pushed to D:\DevDrive\ai-hub\checkpoints\ci\{commit_sha}\
              On failure:
                +--> Block PR merge (branch protection rule: require status checks)
                +--> Notify via GitHub notification
4.4 — Azure and GitHub Integration Provisioning Flow
[Initial Setup — Mode A or Mode B]

STEP 1: Authentication
  +--> az login --use-device-code
        --> Browser: https://microsoft.com/devicelogin -> Enter code
        --> Select subscription from list
        --> az account set --subscription {subscription-id}
  |
  +--> gh auth login --web
        --> Browser OAuth flow
        --> Token stored in Windows Credential Manager (wincred keychain)
        --> Verify: gh auth status

STEP 2: Azure Resource Provisioning
  +--> az group create --name hermes-rg --location eastus
  +--> az keyvault create --name hermes-kv --resource-group hermes-rg --enable-rbac-authorization true
  +--> az keyvault secret set --vault-name hermes-kv --name postgres-password --value {from-env-not-cli}
  +--> az keyvault secret set --vault-name hermes-kv --name qdrant-api-key    --value {from-env-not-cli}
  +--> az keyvault secret set --vault-name hermes-kv --name openai-api-key    --value {from-env-not-cli}

STEP 3: Purview Integration
  +--> az purview account create --name hermes-purview --resource-group hermes-rg --location eastus
  +--> Register local data sources:
        hermes-purview scan D:\DevDrive\data\ as custom data source
        Apply sensitivity labels: "Internal", "Confidential" to model artifacts
        Enable DLP policies for Mode A: prevent exfiltration of labeled files
  +--> Weekly Purview scan scheduled via az purview scan create

STEP 4: Entra ID Integration
  +--> Device registration:
        dsregcmd /join  (joins workstation to Entra tenant)
        dsregcmd /status  (verify: AzureAdJoined=YES, DeviceAuthStatus=SUCCESS)
  +--> Conditional Access Policy (configured in Entra admin portal):
        Rule: Only Entra-joined devices with compliant posture can access hermes-kv and Azure OpenAI
  +--> Service Principal for Hermes orchestrator:
        az ad sp create-for-rbac --name "hermes-orchestrator-sp" --role "Key Vault Secrets User"
                                  --scopes /subscriptions/{sub-id}/resourceGroups/hermes-rg/providers/...
        Store SP credentials in hermes-kv: az keyvault secret set --name sp-client-secret ...
        Never write SP secret to disk.

STEP 5: GitHub Repository Setup
  +--> gh repo create hermesxcore --private
  +--> Configure branch protection on main:
        Require PR review (1 approver)
        Require status checks: hermes-test (pytest, mypy, ruff)
        Restrict direct push to main
  +--> Add GitHub repository secrets:
        gh secret set AZURE_SP_CLIENT_ID    --body {sp-client-id}
        gh secret set AZURE_SP_CLIENT_SECRET --body {from-keyvault-not-cli}
        gh secret set AZURE_TENANT_ID       --body {tenant-id}
        gh secret set AZURE_SUBSCRIPTION_ID --body {subscription-id}
  +--> Configure .gitignore (see Deliverable 3.4)
  +--> Push initial skeleton from D:\DevDrive\repos\hermesxcore\
Deliverable 5 — Prioritized Rollout Plan
Phase 0 — Prerequisites and Hardware Validation (Day 0, 2–4 hours)
This phase confirms that the hardware and base OS are in the correct state before any software changes. No scripts are run during this phase.

Verify BIOS/UEFI settings per Deliverable 6.8 checklist: Secure Boot, TPM 2.0, VT-x/VT-d, 4G Decoding, Re-Size BAR, XMP enabled.
Confirm all NVMe drives are detected: C: (OS), D: (DevDrive target), E: (optional).
Verify Windows 11 23H2 or later (build 22631+) with all Windows Update quality updates applied.
Run nvidia-smi to confirm GPU detection and driver version.
Disable Hibernation: powercfg /h off (recovers ~64 GB on C:).
Disable Fast Startup in Power Options (ensures clean Hyper-V state on reboot).
Move page file to D: after DevDrive is created (System Properties > Advanced > Performance > Virtual Memory).
Phase 0 Checkpoints
CP-0.1: nvidia-smi output confirms correct GPU model and driver version.
CP-0.2: All NVMe drives visible in Disk Management with correct capacities.
CP-0.3: Windows build number confirmed ≥ 22631 (winver command).
CP-0.4: BIOS checklist from Deliverable 6.8 signed off (all items).
Rollback: N/A — this is a read-only validation phase. No changes made.
Phase 1 — DevDrive and Environment Setup (Day 1, 4–6 hours)
Run 01_phase1_devdrive_layout.ps1 as Administrator in PowerShell 7.

Format D: as ReFS DevDrive with 64K cluster size and label "DevDrive".
Create full folder tree under D:\DevDrive\ as specified.
Set all developer cache environment variables (machine scope).
Export and relocate WSL2 distros to D:\DevDrive\wsl2\.
Write .wslconfig with memory, processor, swap, and networking settings.
Relocate Docker data-root to D:\DevDrive\docker\ using robocopy.
If E: drive is present, create junction from D:\DevDrive\ai-hub\models to E:\models.
Phase 1 Checkpoints
CP-1.1: D:\DevDrive\ folder tree exists with all 20+ subfolders.
CP-1.2: C: free space > 40 GB after DevDrive creation.
CP-1.3: wsl --list shows distros in D:\DevDrive\wsl2\; wsl starts cleanly.
CP-1.4: Docker Desktop starts cleanly with data-root at D:\DevDrive\docker\.
CP-1.5: pip install requests in a test venv — confirm pip cache lands on D: (check PIP_CACHE_DIR).
Rollback: Restore WSL2 distros from exported .tar files at D:\DevDrive\logs\wsl_backup_*.tar. Restore daemon.json from .bak file. Restart Docker Desktop.
Phase 2 — Tools, SDKs, and GPU Setup (Day 1–2, 3–5 hours)
Run 02_phase2_tools_sdks.ps1 as Administrator in PowerShell 7.

Install all winget packages (Git, VSCode, Python 3.12, Node.js LTS, Rust, Go, Azure CLI, GitHub CLI, Docker Desktop, PowerShell 7).
Install Miniforge to D:\DevDrive\caches\conda\miniforge.
Verify CUDA Toolkit 12.x: nvidia-smi, nvcc --version.
Verify cuDNN headers present in CUDA include directory.
Configure Docker daemon for NVIDIA runtime.
Validate GPU in WSL2: /dev/dxg present, torch.cuda.is_available() = True.
Authenticate GitHub CLI and Azure CLI.
Create Copilot SDK venv at D:\DevDrive\ai-hub\venvs\copilot-sdk.
Phase 2 Checkpoints
CP-2.1: git --version, python --version (3.12.x), node --version, az --version, gh --version — all return without error.
CP-2.2: nvidia-smi shows correct GPU; CUDA 12.x displayed.
CP-2.3: In WSL2: python3 -c "import torch; print(torch.cuda.is_available())" returns True.
CP-2.4: docker run --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi succeeds.
CP-2.5: gh auth status — logged in. az account show — correct subscription.
Rollback: Use winget uninstall for specific failed packages. Roll back GPU driver via Device Manager if CUDA validation fails.
Phase 3 — Hyper-V, Postgres, Qdrant, Hermes Skeleton (Day 2, 4–6 hours)
Run 03_phase3_hyperv_services.ps1 as Administrator. A reboot may be required after Hyper-V enablement before continuing.

Enable Hyper-V (Microsoft-Hyper-V-All) and Windows Sandbox.
Create HermesNet (external) and HermesInternal vSwitches.
Deploy Postgres 16 Docker container; create all 4 databases; apply DDL from Deliverable 2.1.
Deploy Qdrant Docker container; create all 3 collections.
Create Hermes runtime skeleton: orchestrator.py, node_template/runner.py, hermes_global.yaml.
Phase 3 Checkpoints
CP-3.1: Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All shows State=Enabled.
CP-3.2: Get-VMSwitch shows HermesNet (External) and HermesInternal (Internal).
CP-3.3: docker exec hermes-postgres pg_isready -U postgres returns "accepting connections".
CP-3.4: GET http://127.0.0.1:6333/healthz returns HTTP 200 and JSON {"result":"ok"}.
CP-3.5: Qdrant collections embeddings_v1, routing_contexts, feature_signatures all present.
CP-3.6: python D:\DevDrive\hermes\orchestrator\orchestrator.py runs without error (exits cleanly from asyncio loop).
Rollback: docker stop hermes-postgres hermes-qdrant; docker rm hermes-postgres hermes-qdrant. Disable Hyper-V feature via DISM. Restore pre-Phase-3 checkpoint from D:\DevDrive\logs\.
Phase 4 — Security Modes and Hardening (Day 3, 2–4 hours)
Run configure_bitlocker.ps1 -SecurityMode B to enable BitLocker TPM-only on C: and D:.
Run set_security_mode.ps1 -Mode B to apply Mode B firewall rules and WSL2/Docker isolation.
Test Mode C toggle: run toggle script, verify network blocked, toggle back to Mode B.
Configure Docker daemon.json with full security hardening (userns-remap, no-new-privileges).
Verify secrets management: store Postgres password in Windows Credential Manager using SecretManagement module.
Phase 4 Checkpoints
CP-4.1: manage-bde -status C: shows "Protection Status: Protection On", "Encryption Method: XTS-AES 256".
CP-4.2: manage-bde -status D: shows same.
CP-4.3: Mode B active: Invoke-WebRequest https://github.com succeeds; inbound connection attempt from another host is blocked.
CP-4.4: Mode C toggle: after applying Mode C, Invoke-WebRequest https://github.com fails. Toggle back to Mode B restores access.
CP-4.5: Get-HermesSecret "postgres-password" returns correct value from SecretManagement vault.
Rollback: manage-bde -pause C: and D: to suspend BitLocker. Restore firewall defaults: netsh advfirewall reset.
Phase 5 — Hermes XCore Pipeline (Day 3–5, 8–12 hours)
Create hermes-core venv: python -m venv D:\DevDrive\ai-hub\venvs\hermes-core
Install all dependencies from requirements.txt (Appendix B).
Deploy all 8 Python modules: feature_pipeline.py, correlation_search.py, autoencoder_pipeline.py, routing_policy.py, retraining_loop.py, scoring_feedback.py, vector_store.py, orchestrator.py.
Apply SQL DDL from Deliverable 2.1 to Postgres.
Run unit tests for each module against sample data.
Run integration test: dispatch a full pipeline run from FeaturePipeline.run() through to Qdrant upsert.
Phase 5 Checkpoints
CP-5.1: FeaturePipeline.run() on 100-row sample DataFrame returns FeatureSet with non-null fields.
CP-5.2: CorrelationSearch.search_secondary_variables() identifies at least one secondary variable on synthetic data.
CP-5.3: AutoencoderTrainer.fit() completes 1 training epoch on sample data; checkpoint file saved to D:\DevDrive\ai-hub\checkpoints\.
CP-5.4: ContextualBanditRouter.select_arm() returns valid arm name from configured arm list.
CP-5.5: HermesVectorStore.upsert_embeddings() adds 10 vectors to embeddings_v1; .search() returns top-5 with scores.
CP-5.6: Orchestrator dispatches test HermesTask to node_01; TaskResult returns status="success".
Rollback: git checkout HEAD~1 in D:\DevDrive\repos\hermes\; reinstall dependencies from previous requirements.txt; re-run unit tests.
Phase 6 — Integration and Azure/GitHub Wiring (Day 5–7, 4–6 hours)
Provision Azure resources per Deliverable 4.4 flow: resource group, Key Vault, Purview, Entra SP.
Store all secrets in Azure Key Vault; verify access from Hermes orchestrator using SP credentials.
Register HermesRouterPlugin in Semantic Kernel; test route_task() call from Python script.
Configure GitHub Actions workflow file .github/workflows/hermes-test.yml and push to trigger first CI run.
Register Hermes endpoint as Azure AI Foundry tool (Mode A only).
Phase 6 Checkpoints
CP-6.1: az keyvault secret show --name postgres-password --vault-name hermes-kv returns value (from orchestrator SP context).
CP-6.2: Semantic Kernel HermesRouterPlugin.route_task() returns valid ScoringResult JSON.
CP-6.3: GitHub Actions run (hermes-test.yml) passes all steps on first test commit to branch.
CP-6.4: Purview scan completes without error on D:\DevDrive\data\ (Mode A only).
Rollback: az group delete --name hermes-rg --yes --no-wait (destroys all Azure resources). gh secret remove to clean GitHub secrets. Restore to Phase 5 checkpoint.
Phase 7 — Continuous Operation and Monitoring (Ongoing)
Verify ContinuousRetrainingOrchestrator.run_loop() starts on system boot (register as Windows Service or WSL2 systemd service).
Monitor hermes_run_log for error_rate > 5% per 24-hour window.
Weekly: review DriftReport outputs; review secondary variable candidates in hermes_secondary_vars.
Monthly: rotate GitHub PAT (90-day max), rotate Azure SP secret (180-day max), prune checkpoints beyond rollback_versions_to_keep=3.
Quarterly: review routing policy arm performance; evaluate adding or removing Hermes nodes.
Verify backup procedures from Deliverable 7.2 run weekly.
Rollback Plan — All Phases
Always maintain 3 previous champion model checkpoints in D:\DevDrive\ai-hub\checkpoints\. One-command rollback via: python orchestrator.py --rollback --to-model-id {model_id}. The rollback() method in ContinuousRetrainingOrchestrator is designed for immediate execution without restart.
Deliverable 6 — Hardware Checklist
6.1 — CPU
Requirement    Specification
Minimum    Intel Core i9-13th Gen (i9-13900K) or AMD Ryzen 9 7950X; 12+ cores, 24+ threads
Recommended    Intel Core i9-14900KS or AMD Ryzen 9 7950X3D; 24 cores, 32 threads
BIOS: Virtualization    Enable VT-x (Intel) / AMD-V; Enable VT-d (Intel) / AMD-Vi / IOMMU for GPU passthrough
BIOS: Hyper-Threading / SMT    Enable (required for full WSL2 + Hyper-V concurrency)
C-states for Training    Optional: Disable C-states (C6/C8) for reduced wake latency during sustained GPU training workloads
TDP / Power Limits    Set PL1 and PL2 to maximum motherboard-supported values for training workloads
6.2 — GPU
Requirement    Specification
Minimum    NVIDIA RTX 3090 (24 GB VRAM, GDDR6X)
Recommended    NVIDIA RTX 4090 (24 GB VRAM, GDDR6X, 1008 GB/s bandwidth)
Professional / Large Models    NVIDIA A100 80 GB SXM or H100 80 GB for models > 20B parameters
Driver    Latest Game Ready Driver (GRD) or Studio Driver; CUDA 12.x compatible (527.x or newer)
BIOS: 4G Decoding    Enable "Above 4G Memory Decoding" (required for >8 GB VRAM cards)
BIOS: Re-Size BAR    Enable Re-Size BAR / Smart Access Memory (SAM) — improves PCIe bandwidth utilization
NVIDIA Container Toolkit    Required for Docker GPU passthrough (nvidia-container-runtime)
CUDA on WSL2    NVIDIA WSL2 CUDA driver (separate from host driver; managed by NVIDIA; install via NVIDIA developer portal)
GPU Slot    Install in PCIe 5.0 x16 slot closest to CPU for maximum bandwidth
6.3 — RAM
Requirement    Specification
Minimum    64 GB DDR5
Recommended    128 GB DDR5 (ECC if supported by motherboard and workload demands it)
Speed    DDR5-5600 or higher; enable XMP 3.0 / EXPO profile in BIOS
Configuration    Dual-channel minimum; quad-channel preferred for X670E/Z790 platforms
WSL2 Allocation    Set memory= in .wslconfig to 32–64 GB; leave minimum 16 GB for Windows host
Page File    Move page file to D:\DevDrive\ after Phase 1; set 8–16 GB fixed size
6.4 — NVMe Storage
Drive    Minimum    Recommended    Suggested Model    Purpose
C: (OS)    512 GB PCIe 4.0    1 TB NVMe PCIe 4.0    Samsung 990 Pro 1 TB or WD Black SN850X 1 TB    OS and system only; keep < 60% full
D: (DevDrive)    2 TB PCIe 4.0    4 TB NVMe PCIe 4.0    Samsung 990 Pro 4 TB or WD Black SN850X 4 TB    All development, models, containers, WSL2, Docker
E: (Optional)    2 TB PCIe 5.0    8 TB NVMe PCIe 5.0    Crucial T705 8 TB or Seagate FireCuda 540    Heavy model weights > 30 GB; symlinked from D:\DevDrive\ai-hub\models
NVMe Placement
Install D: (DevDrive) in the M.2 slot closest to the CPU with PCIe 5.0 support (if available) for maximum sequential throughput during model I/O. C: (OS) can be in a PCIe 4.0 slot further from CPU. E: should be PCIe 5.0 if available for model weight loading throughput.
6.5 — Motherboard
Feature    Requirement
Chipset (Intel)    Z790 or Z790E; supports DDR5, PCIe 5.0
Chipset (AMD)    X670E; supports DDR5, PCIe 5.0 GPU + NVMe
PCIe Slots    Minimum 1x PCIe 5.0 x16 (GPU) + 1x PCIe 4.0 x16 or x4 (secondary)
M.2 Slots    Minimum 3x M.2 (for C:, D:, E: drives); prefer PCIe 5.0 for primary and secondary
TPM    TPM 2.0 firmware module (fTPM) or discrete TPM 2.0 header — required for BitLocker
USB    USB 3.2 Gen 2x2 (20 Gbps) on rear panel for external NVMe backup
Network    Intel I225-V 2.5 GbE minimum; Intel I226-V preferred; optional 10 GbE for lab network
VRM    High-quality VRM (16+ phases) for sustained CPU turbo under training load
6.6 — Power Supply
Requirement    Specification
Minimum    1000W 80+ Gold certified; fully modular
Recommended (RTX 4090)    1200W+ 80+ Platinum; fully modular; 12VHPWR connector native
Recommended (A100)    1600W+ 80+ Titanium with 12VHPWR or EPS12V
Rail Design    Single 12V rail preferred for GPU stability under transient peak loads
6.7 — Windows Post-Install Settings Checklist
Setting    Action    Why
Windows 11 23H2+    Verify build ≥ 22631 (winver)    DevDrive requires 22621+; 22631 adds performance improvements
Developer Mode    Settings > System > For Developers > ON    Required for DevDrive and symlink creation without elevation
Virtualization-Based Security    msinfo32 > Virtualization-based security = Running    Required for Hyper-V isolation and Credential Guard
Hyper-V    Enable via Phase 3 script or Windows Features    Required for WSL2 and Hermes Hyper-V nodes
WSL2 Kernel    wsl --update (get 5.15+ kernel)    Required for CUDA on WSL2 and latest mirrored networking
PowerShell 7    Set as default in Windows Terminal settings    All scripts require PS 7+
Windows Update    Apply all quality + driver updates before Phase 1    Ensures DevDrive drivers and WSL2 kernel patches are current
Disable Hibernation    powercfg /h off (Admin)    Recovers ~64 GB on C: (hiberfil.sys); also required for clean Hyper-V state
Disable Fast Startup    Control Panel > Power Options > Turn on fast startup = OFF    Prevents Hyper-V state corruption on reboot
Page File    Move to D: after Phase 1; 8–16 GB fixed    Reduces C: pressure; D: ReFS handles large page file efficiently
Delivery Optimization    Set cache to D:\DevDrive\caches\delivery    Moves Windows Update cache off C:
6.8 — BIOS/UEFI Checklist
Setting    Required Value    Notes
Secure Boot    Enabled    Required for BitLocker with TPM; use Standard key database
TPM    Enabled (TPM 2.0 / fTPM)    Must show TPM 2.0 in tpm.msc after boot
VT-x / AMD-V    Enabled    CPU virtualization — required for Hyper-V and WSL2
VT-d / AMD-Vi (IOMMU)    Enabled    Required for GPU passthrough to Hyper-V VMs and proper device isolation
Above 4G Memory Decoding    Enabled    Required for GPUs with > 8 GB VRAM to fully map BAR address space
Re-Size BAR / Smart Access Memory    Enabled    Improves CPU-GPU transfer bandwidth; requires Above 4G Decoding to be enabled first
XMP / EXPO Profile    Enabled (profile 1)    Enables rated DDR5 speed; verify POST stability before proceeding
NVMe Boot Drive Slot    PCIe 5.0 x4 (closest to CPU)    D: DevDrive gets maximum sequential bandwidth
Fan Curve    Aggressive (GPU + CPU)    Set high fan RPM at 70°C GPU for sustained training workloads
CPU Power Limits (PL1/PL2)    Maximum / Unlimited    Prevents CPU throttling during training; verify thermal headroom first
C-States    Disable C6/C8 for training (optional)    Reduces wake latency for GPU compute requests; increases idle power
6.9 — Driver Version Checklist
Component    Minimum Version    Recommended Version    How to Verify
NVIDIA GPU Driver (Windows)    527.x    Latest Studio/GRD (2024/2025)    nvidia-smi — Driver Version column
CUDA Toolkit    12.0    12.4 or 12.5    nvcc --version
cuDNN    8.9.x    9.x    Verify cudnn.h header version in CUDA include dir
WSL2 Linux Kernel    5.15.90.1    Latest (wsl --update)    uname -r inside WSL2
Docker Desktop    4.25    Latest stable    docker --version
NVIDIA Container Toolkit    1.14    Latest    nvidia-ctk --version
PowerShell    7.3    7.4 or 7.5    $PSVersionTable.PSVersion
Python    3.12.0    3.12.x latest    python --version
Azure CLI    2.60    Latest    az --version
GitHub CLI    2.40    Latest    gh --version
Deliverable 7 — Script Quality Standards and Backup Procedures
7.1 — Error Handling Standards (All Scripts)
PowerShell Scripts
Every script begins with $ErrorActionPreference = "Stop" — all errors become terminating.
Every destructive operation (format, delete, move, overwrite) is wrapped in try { ... } catch { ... } with an explicit rollback call and log write.
Non-fatal failures (e.g., optional tool install) log a WARNING and continue. Fatal failures (e.g., CUDA not found) call throw and halt the script.
All external command exit codes are checked: if ($LASTEXITCODE -ne 0) { throw "Command failed with exit $LASTEXITCODE" }.
Logs are written to timestamped files at D:\DevDrive\logs\ and echoed to console via Tee-Object.
Before any phase script runs, a state snapshot is written (disk usage, service states, firewall rules) to D:\DevDrive\logs\pre_phase_snapshot_{datetime}.txt.
Python Modules
All modules use structlog or Python logging with a JSON formatter (StructuredFormatter) — every log record includes run_id, node_id, timestamp, and level.
Training loops: catch Exception in the outer fit() loop; log full traceback with run_id; save emergency checkpoint if epoch > 0; exit with code 1.
CUDA OOM: always caught with specific handling (fall back to CPU, clear cache, log warning).
Database failures: use connection pooling (psycopg2.pool.ThreadedConnectionPool); retry with exponential backoff (max 3 attempts); if all fail, buffer to SQLite fallback.
HTTP failures (Qdrant, node endpoints): retry with exponential backoff; raise after max_retries; log full exception chain.
Python: Standard module error handling pattern
import logging
import traceback

logger = logging.getLogger("hermes.module")

def safe_execute(fn, *args, run_id: str = "", **kwargs):
    """
    Wraps any callable with structured error logging.
    Returns (result, None) on success, (None, error_msg) on failure.
    """
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(
            "Unhandled exception in %s",
            fn.__name__,
            extra={"run_id": run_id, "traceback": tb, "error": str(e)}
        )
        return None, str(e)
Docker Container Failures
Check container exit code after start: docker inspect --format '{{.State.ExitCode}}' {container}.
On non-zero exit: retrieve logs with docker logs {container}, write to D:\DevDrive\logs\docker_errors_{datetime}.log.
For persistent containers (Postgres, Qdrant): configure --restart unless-stopped for automatic recovery.
7.2 — Backup Procedures (Pre-Script Execution)
Execute the following backup steps before running any phase script. This can be wrapped in a PowerShell function Invoke-HermesBackup called at the top of each phase script.

Snapshot disk usage: Get-PSDrive output to D:\DevDrive\logs\disk_snapshot_{date}.txt.
Export WSL2 distros: wsl --export {distro} D:\DevDrive\logs\wsl_backup_{distro}_{date}.tar for each running distro.
Docker container backup: docker commit {container} hermes-backup-{date} for all running containers; docker save to D:\DevDrive\logs\docker_backup_{date}\.
Postgres dump: docker exec hermes-postgres pg_dump -U postgres -Fc hermes_logs > D:\DevDrive\logs\postgres_backup_{date}.dump — repeat for all 4 databases.
Qdrant snapshot: POST http://127.0.0.1:6333/collections/embeddings_v1/snapshots — save snapshot name returned in response.
Git commit: In D:\DevDrive\repos\, run git add -A && git commit -m "pre-phase-backup {date}" for all repos with uncommitted changes.
Write backup manifest: JSON to D:\DevDrive\logs\backup_manifest_{date}.json listing all backup file paths, sizes, and SHA-256 hashes.
7.3 — Integrity Verification
After every file move operation (WSL2 relocation, Docker data-root move, cache relocation), verify integrity by comparing SHA-256 checksums of source and destination. Mismatches must halt the script and trigger rollback.

PowerShell: SHA-256 file integrity check
function Assert-FileIntegrity {
    param(
        [string]$SourcePath,
        [string]$DestPath,
        [string]$LogFile
    )
    $srcHash  = (Get-FileHash -Algorithm SHA256 -Path $SourcePath).Hash
    $destHash = (Get-FileHash -Algorithm SHA256 -Path $DestPath).Hash
    if ($srcHash -ne $destHash) {
        $msg = "INTEGRITY FAILURE: $SourcePath vs $DestPath (src=$srcHash, dest=$destHash)"
        $msg | Out-File $LogFile -Append
        throw $msg
    }
    "OK: $DestPath matches source." | Out-File $LogFile -Append
}

# Usage example (after robocopy):
# Get-ChildItem D:\DevDrive\docker -Recurse -File | ForEach-Object {
#     $relative = $_.FullName.Replace("D:\DevDrive\docker\", "")
#     Assert-FileIntegrity `
#         -SourcePath "C:\ProgramData\docker\$relative" `
#         -DestPath   $_.FullName `
#         -LogFile    "D:\DevDrive\logs\integrity_check.log"
# }
Python: Checkpoint file integrity verification
import hashlib
from pathlib import Path

def verify_checkpoint_integrity(checkpoint_path: str, expected_hash: str = None) -> str:
    """
    Computes SHA-256 of checkpoint file.
    If expected_hash provided, asserts match.
    Returns computed hash.
    """
    h = hashlib.sha256()
    with open(checkpoint_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    computed = h.hexdigest()
    if expected_hash and computed != expected_hash:
        raise ValueError(
            f"Checkpoint integrity FAILED: {checkpoint_path}\n"
            f"  Expected: {expected_hash}\n"
            f"  Got:      {computed}"
        )
    return computed
For Postgres migrations, verify row counts in each table before and after: SELECT COUNT(*) FROM {table}. For Qdrant migrations, verify vector count before and after: GET http://127.0.0.1:6333/collections/embeddings_v1 and compare vectors_count.

7.4 — Copilot and Semantic Kernel Integration Notes
Python: Hermes SK Plugin Registration
# semantic_kernel_integration.py — Hermes XCore SK Plugin Registration
# Pseudo-code: review and implement before use.

import semantic_kernel as sk
from semantic_kernel.functions import kernel_function
from pydantic import BaseModel
import httpx

class HermesRouterPlugin:
    """
    Semantic Kernel plugin that exposes Hermes routing, feedback,
    and history query capabilities as SK functions.
    """
    def __init__(self, endpoint: str = "http://127.0.0.1:8700"):
        self.endpoint = endpoint
        self.client   = httpx.AsyncClient(base_url=endpoint, timeout=30.0)

    @kernel_function(
        name="route_task",
        description="Route a task to the optimal Hermes node based on context vector and task type"
    )
    async def route_task(self, context_vector: list, task_type: str, payload: dict) -> dict:
        r = await self.client.post("/v1/route", json={
            "context_vector": context_vector,
            "task_type":      task_type,
            "payload":        payload
        })
        r.raise_for_status()
        return r.json()

    @kernel_function(
        name="get_feedback",
        description="Submit a reward signal for a completed Hermes task"
    )
    async def get_feedback(
        self, session_id: str, reward: float, context_vector: list
    ) -> dict:
        r = await self.client.post("/v1/feedback", json={
            "session_id":     session_id,
            "reward_signal":  reward,
            "context_vector": context_vector
        })
        r.raise_for_status()
        return r.json()

    @kernel_function(
        name="query_history",
        description="Query recent routing decisions and reward statistics"
    )
    async def query_history(self, lookback_hours: int = 24) -> dict:
        r = await self.client.get(f"/v1/history?lookback_hours={lookback_hours}")
        r.raise_for_status()
        return r.json()

# --- Registration ---
# kernel = sk.Kernel()
# kernel.add_plugin(
#     plugin_name = "HermesRouter",
#     plugin      = HermesRouterPlugin(endpoint="http://127.0.0.1:8700")
# )
# result = await kernel.invoke("HermesRouter", "route_task",
#     context_vector=[...128 floats...],
#     task_type="inference",
#     payload={"input": "..."}
# )
Azure AI Foundry Tool Registration (Mode A)
In Mode A, the HermesRouterPlugin can be registered as an Azure AI Foundry function tool. Register the tool manifest in the Foundry project settings, then bind the local Hermes endpoint via a secure tunnel (e.g., Azure Application Gateway with private endpoint, or an ngrok tunnel scoped to your subscription for development purposes). Never expose the Hermes endpoint on a public IP address. The tool schema must be validated against the Foundry function tool specification before registration.
7.5 — Purview and Entra Operational Notes
Microsoft Purview
Register D:\DevDrive\data\ as a custom data source in the Purview catalog using the Purview CLI or Azure Portal.
Configure weekly automated scan: tag all .parquet, .csv, .jsonl files under D:\DevDrive\data\raw\ with sensitivity label "Internal".
Apply "Confidential" label to all files under D:\DevDrive\ai-hub\checkpoints\ that contain model weights derived from proprietary data.
Enable DLP policies in Mode A to block exfiltration of Confidential-labeled files via browser upload, email attachment, or USB copy.
Review Purview scan reports monthly; triage any new PII detections within 48 hours.
Microsoft Entra ID
All Hermes service principals must use workload identity federation (OIDC) where the backing identity provider supports it, eliminating the need for client secrets entirely.
Where client secrets are unavoidable (legacy integrations), store exclusively in Azure Key Vault (hermes-kv); never cache on disk or in environment variables beyond the current process lifetime.
Client secret rotation: automate via Azure Automation runbook triggered 14 days before expiry; new secret written to hermes-kv; old secret disabled after 7-day grace period.
Enable Entra audit log forwarding to Azure Monitor Log Analytics workspace; configure alert for: any SP login from unexpected IP, any permission escalation, any new role assignment on hermes-rg.
Conditional Access: Require MFA for all human logins to Azure resources; require Entra-joined compliant device for access to hermes-kv and Azure OpenAI endpoints.
Appendix A — Quick Reference: D:\DevDrive\ Directory Structure
D:\DevDrive\                          # ReFS DevDrive root (64K cluster, developer-optimized)
  |
  +-- ai-hub\                         # AI model and runtime artifacts
  |     +-- models\                   # Large model weights (symlink to E:\ if present)
  |     +-- embeddings\               # Pre-computed static embeddings
  |     +-- checkpoints\              # Training checkpoints (ae_*.pt, model_*.pt)
  |     |     +-- ci\                 # CI/CD-generated staging checkpoints
  |     +-- venvs\                    # Python virtual environments
  |     |     +-- hermes-core\        # Primary Hermes XCore venv
  |     |     +-- copilot-sdk\        # Azure AI / Semantic Kernel venv
  |     +-- cuda\                     # CUDA Toolkit install target (if not system-wide)
  |
  +-- hermes\                         # Hermes fleet system root
  |     +-- orchestrator\             # Orchestrator service files
  |     |     +-- orchestrator.py
  |     +-- nodes\                    # Per-node directories
  |     |     +-- node_template\      # Canonical node template
  |     |     |     +-- runner.py
  |     |     |     +-- health.py
  |     |     |     +-- config.yaml
  |     |     +-- node_01\            # Instance of node_template for inference
  |     |     +-- node_02\            # Feature engineering node
  |     |     +-- node_03\            # Training node (Hyper-V VM)
  |     +-- configs\                  # Hermes configuration files
  |     |     +-- hermes_global.yaml  # Global fleet config
  |     |     +-- routing_policy.json # Serialized LinUCB policy state
  |     |     +-- secrets.env         # [chmod 600, .gitignored] Runtime secrets
  |     +-- logs\                     # Hermes-level log aggregation
  |     +-- scripts\                  # Hermes automation scripts
  |
  +-- data\                           # Data pipeline directories
  |     +-- raw\                      # Unprocessed ingested data
  |     +-- processed\                # Post-feature-pipeline output
  |     +-- features\                 # Computed feature sets (.parquet)
  |     +-- exports\                  # Data exports for Azure / external consumers
  |
  +-- postgres\                       # Postgres Docker volume data
  |     +-- data\                     # PostgreSQL PGDATA directory
  |
  +-- qdrant\                         # Qdrant Docker volume data
  |     +-- storage\                  # Qdrant storage segments
  |     +-- config\                   # Qdrant config.yaml
  |
  +-- wsl2\                           # WSL2 distro VHDs (relocated from default)
  |     +-- Ubuntu-22.04\             # Imported distro location
  |     +-- swap.vhd                  # WSL2 swap file (8 GB)
  |     +-- .wslconfig                # [symlink or copy] WSL2 config
  |
  +-- docker\                         # Docker data-root (relocated)
  |     +-- volumes\                  # Named Docker volumes
  |     +-- overlay2\                 # Container layer storage
  |
  +-- caches\                         # Developer tool caches (off C:)
  |     +-- pip\                      # pip wheel/sdist cache
  |     +-- conda\                    # Conda packages + Miniforge install
  |     +-- npm\                      # npm global cache
  |     +-- nuget\                    # NuGet package cache
  |     +-- cargo\                    # Rust crate cache
  |     +-- gradle\                   # Gradle build cache
  |     +-- tmp\                      # TEMP / TMP (system temp files)
  |     +-- delivery\                 # Windows Delivery Optimization cache
  |
  +-- sandbox\                        # Windows Sandbox shared folder (read-only from Sandbox)
  |
  +-- repos\                          # Git repositories
  |     +-- hermesxcore\              # Primary Hermes XCore codebase
  |     +-- infrastructure\           # IaC (bicep/terraform for Azure resources)
  |
  +-- scripts\                        # System automation scripts
  |     +-- 01_phase1_devdrive_layout.ps1
  |     +-- 02_phase2_tools_sdks.ps1
  |     +-- 03_phase3_hyperv_services.ps1
  |     +-- set_security_mode.ps1
  |     +-- configure_bitlocker.ps1
  |
  +-- logs\                           # System-level logs and backups
        +-- bootstrap_errors.log      # Aggregated fatal error log
        +-- pre_bootstrap_snapshot_*.txt
        +-- backup_manifest_*.json
        +-- wsl_backup_*.tar
        +-- postgres_backup_*.dump
        +-- firewall_snapshot_*.txt
        +-- security_mode_*.log
        +-- phase1_*.log
        +-- phase2_install_*.log
        +-- phase3_services_*.log
Appendix B — Python Dependencies Manifest
FILE: requirements.txt — D:\DevDrive\ai-hub\venvs\hermes-core\requirements.txt
# Hermes XCore — Python Dependencies Manifest
# Install into D:\DevDrive\ai-hub\venvs\hermes-core
# pip install -r requirements.txt
# Generated: 2026-06-02 | Python 3.12.x | CUDA 12.4

# --- PyTorch (install separately for CUDA support) ---
# pip install torch>=2.2.0 torchvision>=0.17.0 --index-url https://download.pytorch.org/whl/cu124

# --- Core ML / Data Science ---
torch>=2.2.0
torchvision>=0.17.0
transformers>=4.40.0
sentence-transformers>=3.0.0
scikit-learn>=1.4.0
pandas>=2.2.0
numpy>=1.26.0
scipy>=1.13.0

# --- Vector Database ---
qdrant-client>=1.9.0

# --- Database ---
psycopg2-binary>=2.9.9

# --- Azure / Copilot / OpenAI ---
azure-ai-inference>=1.0.0
azure-identity>=1.16.0
azure-keyvault-secrets>=4.8.0
openai>=1.30.0
semantic-kernel>=1.0.0

# --- API / Web ---
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
httpx>=0.27.0

# --- Configuration / Secrets ---
pydantic>=2.7.0
pydantic-settings>=2.2.0
python-dotenv>=1.0.0
pyyaml>=6.0.1

# --- Logging / Observability ---
structlog>=24.1.0
rich>=13.7.0

# --- Development / Quality ---
pytest>=8.2.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
mypy>=1.10.0
ruff>=0.4.0
Appendix C — Glossary
Term    Definition
Arm    In the contextual bandit context, one selectable action — here, one Hermes node or model endpoint (e.g., node_01_inference). LinUCB maintains separate regression parameters per arm.
Champion Model    The currently deployed, production-active model in the hermes_model_registry (is_active = TRUE). Only one champion per model_name can be active at a time.
Challenger Model    A newly trained candidate model being evaluated against the champion. Promoted only if its eval_score exceeds champion by the configured margin.
Cluster Size (ReFS)    The allocation unit size for the ReFS file system on D:. Set to 64 KB (65,536 bytes) to optimize large-file sequential I/O for model weight files and checkpoint archives.
Context Vector    A 128-dimensional floating-point vector representing the current task context, derived from the latent space of the HermesAutoencoder. Used as input to the LinUCB routing policy.
DevDrive    Windows 11 feature enabling a ReFS-formatted volume with antivirus filter bypass for trusted paths, optimized for developer I/O. Requires Windows 11 22621+ and Developer Mode.
Drift (Data)    Statistical change in the distribution of input features between training time and serving time. Measured by PSI (numeric), Chi-square (categorical), and cosine similarity (embeddings).
DKMS    Dynamic Kernel Module Support — Linux framework allowing kernel modules (e.g., NVIDIA drivers) to automatically rebuild when the kernel is updated, maintaining CUDA on WSL2 across kernel upgrades.
Entra ID    Microsoft's cloud identity and access management platform (formerly Azure Active Directory). Used for device registration, conditional access, and service principal authentication.
Feature Signature    A compact representation of a feature set's statistical properties, stored in Qdrant's feature_signatures collection for fast similarity lookup during drift detection.
Fleet    The collective set of Hermes nodes (node_01, node_02, node_03, etc.) managed by the HermesOrchestrator. Each node is a specialized compute unit.
GPU Passthrough    Mechanism by which a physical NVIDIA GPU is accessible inside a Hyper-V VM or WSL2 environment, enabling GPU-accelerated training within virtualized compute.
Hermes    The custom multi-node AI orchestration framework that routes inference, training, and feature engineering tasks across named compute nodes using a contextual bandit policy.
HermesInternal vSwitch    Hyper-V internal virtual network switch used to interconnect Hermes nodes in isolation, without external network access. Used in Mode B and Mode C.
HermesNet vSwitch    Hyper-V external virtual network switch bound to the physical NIC, providing full internet/Azure access for VMs. Used in Mode A only.
Latent Space    The compressed representation produced by the HermesAutoencoder encoder; a 128-dimensional space capturing the essential structure of raw feature inputs.
LinUCB    Linear Upper Confidence Bound — a contextual bandit algorithm that models reward as a linear function of context features, selecting arms with the highest upper confidence bound on predicted reward.
MAML    Model-Agnostic Meta-Learning — a meta-learning algorithm that optimizes model initialization parameters for fast adaptation to new tasks with few gradient steps.
Mode A / B / C    The three security operating modes of the Hermes workstation: A (Active/Cloud), B (Balanced/Developer, default), C (Locked/Air-gap-like). Toggled via set_security_mode.ps1.
PSI    Population Stability Index — a metric quantifying distributional shift between two samples. PSI > 0.20 indicates significant drift and triggers retraining in the Hermes pipeline.
Purview    Microsoft Purview — cloud-based data governance platform used to catalog, classify, and enforce compliance policies on data assets in the D:\DevDrive\data\ and model artifact directories.
Qdrant    Open-source vector database engine providing ANN (approximate nearest neighbor) similarity search over dense float vectors. Used by Hermes for embedding storage and retrieval.
ReFS    Resilient File System — Microsoft's modern file system used for the DevDrive. Supports large cluster sizes, data integrity checksums, and virtual disk scenarios, but does not support all NTFS features.
Reward Signal    A scalar value in [-1.0, 1.0] representing the quality of a model output as judged by downstream evaluation or user action. Used to update the LinUCB policy and trigger retraining.
SecretManagement    PowerShell module (Microsoft.PowerShell.SecretManagement) providing a unified API for storing and retrieving secrets from various vaults (SecretStore, Windows Credential Manager, Azure Key Vault).
Sherman-Morrison    Matrix identity used for efficient rank-1 updates of the inverse of A in the LinUCB algorithm, avoiding full matrix inversion on each update step.
VHD / VHDX    Virtual Hard Disk format used by Hyper-V and WSL2 to store VM disk images. WSL2 distros are stored as VHDX files relocated to D:\DevDrive\wsl2\ in this build.
Workload Identity Federation    Entra ID feature that allows a service principal to authenticate using a trusted external OIDC token (e.g., from GitHub Actions), eliminating the need for a client secret.
WSL2    Windows Subsystem for Linux 2 — a Hyper-V-backed, full Linux kernel environment on Windows. Used for GPU-accelerated Python training and inference workloads in Hermes nodes.
XCore    The Hermes variant described in this document: the cross-core continuous training loop integrating feature pipeline, autoencoder compression, contextual bandit routing, and feedback-driven retraining.
Appendix D — Change Log
Version    Date    Author    Description
1.0    02 June 2026    John    Initial release. All 7 deliverables complete.
Phase 0–7 rollout plan with checkpoints and rollback steps.
Full pseudo-script bundle (Phases 1–3).
Hermes XCore pipeline design (Sections 2.1–2.9).
Security mode framework (Modes A, B, C) with toggle script.
ASCII wiring diagrams for all major data flows.
Hardware checklist with BIOS, driver, and Windows settings.
Error handling standards, backup procedures, and integrity checks.
Appendices A–D: directory structure, requirements, glossary, change log.
Bootstrap and Hermes XCore Training Loop — X-Tier Build Implementation Plan
Version 1.0  |  02 June 2026  |  John  |  Austin, TX  |  Internal Engineering Reference
This docume