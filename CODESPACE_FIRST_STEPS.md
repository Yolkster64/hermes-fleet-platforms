# GitHub Codespace First Steps Guide

## Complete Setup After Launch

After your Codespace finishes initializing (green checkmark appears), follow these steps to get everything ready for development.

## Phase 1: Verify Development Environment (2-3 minutes)

### 1.1 Open Terminal
In VS Code (Codespace):
1. Press `Ctrl + `` (backtick) to open integrated terminal
2. Or: Click **Terminal** → **New Terminal**
3. You should see PowerShell prompt: `PS /workspaces/helios-platform-repo>`

### 1.2 Verify All Tools Are Installed

```powershell
# Check .NET SDK
dotnet --version
# Expected: 8.x.x

# Check Python
python --version
# Expected: Python 3.x.x

# Check Node.js
node --version
npm --version
# Expected: v18.x.x or later

# Check Git
git --version
# Expected: git version 2.x

# Check GitHub CLI
gh --version
# Expected: gh version X.X.x

# Check Azure CLI
az --version
# Expected: azure-cli version X.X.x

# Check Docker
docker --version
# Expected: Docker version 24.x or later
```

### 1.3 Verify VS Code Extensions
1. Click the **Extensions** icon (left sidebar)
2. Search for "HELIOS" or "@installed"
3. Verify these 11 extensions are installed:
   - ✅ PowerShell
   - ✅ C# Dev Kit
   - ✅ .NET Runtime Installer
   - ✅ Azure Functions
   - ✅ Azure Tools
   - ✅ Azure Cosmos DB
   - ✅ Docker
   - ✅ Python
   - ✅ Ruff
   - ✅ GitLens
   - ✅ GitHub Copilot

### 1.4 Verify Port Forwarding
1. Click **Ports** tab (bottom panel or left sidebar)
2. Verify these ports are listed:
   - Port 3000 (Web UI)
   - Port 5000 (API Server)
   - Port 5432 (PostgreSQL)
   - Port 8080 (Dashboard)
   - Port 8443 (HTTPS)

If ports don't appear, right-click the Ports tab → **Forward Port** and add manually.

## Phase 2: Authenticate Services (3-5 minutes)

### 2.1 GitHub Authentication

```powershell
gh auth status
```

If not authenticated:
```powershell
gh auth login
# Follow prompts:
# 1. Choose: github.com
# 2. Choose: SSH (recommended) or HTTPS
# 3. Follow browser authorization
```

### 2.2 Azure Authentication

```powershell
az login
```

This opens browser for login. After login:
```powershell
# Verify login
az account show

# List available subscriptions
az account list --output table

# Set active subscription (if multiple available)
az account set --subscription "<subscription-id>"
```

### 2.3 Docker Authentication (Optional)

```powershell
# Only if pushing to Docker registry
docker login
# Enter Docker Hub credentials when prompted
```

### 2.4 GitHub Copilot Activation

1. In VS Code, press `Ctrl + Shift + P`
2. Search: "Copilot: Sign In"
3. Click and follow browser authorization
4. Return to Codespace - Copilot is now active

## Phase 3: Project Setup (5-10 minutes)

### 3.1 Install Project Dependencies

Dependencies should auto-install in postCreateCommand, but verify:

```powershell
# Node.js dependencies
npm list
# If missing:
npm install

# .NET dependencies
dotnet restore
# Expected: "Restore completed"

# Python dependencies (optional, if needed)
# python -m pip install -r requirements.txt
```

### 3.2 Navigate Project Structure

```powershell
# See directory tree
Get-ChildItem -Recurse -Depth 2 | Select-Object FullName

# Or use simpler view
ls -la
```

Expected structure:
```
helios-platform-repo/
├── src/                 # Source code
│   ├── HELIOS.Platform.csproj
│   └── [C# source files]
├── tests/              # Test projects
├── docs/               # Documentation
├── build/              # Build artifacts
├── scripts/            # Automation scripts
└── .devcontainer/      # Codespace config
```

### 3.3 Verify Project Configuration

```powershell
# Check .NET project
dotnet --list-runtimes
dotnet --list-sdks

# Verify package files
Test-Path "package.json"         # Node.js
Test-Path "HELIOS.Platform.csproj"  # C#
Test-Path "requirements.txt"     # Python (if used)
```

## Phase 4: Build & Test (10-15 minutes)

### 4.1 Build the Project

```powershell
# Build .NET project
dotnet build

# Expected output:
# Build succeeded. X project(s) in X ms.
```

### 4.2 Run Unit Tests

```powershell
# Run all tests
dotnet test

# Run specific test project
dotnet test ./tests/HELIOS.Platform.Tests.csproj

# With verbose output
dotnet test --verbosity normal
```

### 4.3 Check Linting & Code Quality

```powershell
# Python linting (via Ruff extension)
# Will show in VS Code Problems panel

# .NET code analysis
dotnet build /p:EnforceCodeStyleInBuild=true
```

## Phase 5: Start Development Server (5 minutes)

### 5.1 Run the Application

**Option A: Direct .NET Run**
```powershell
dotnet run
# Application starts on http://localhost:5000
```

**Option B: Via npm script (if configured)**
```powershell
npm start
```

**Option C: Using Makefile (if available)**
```powershell
make run
```

### 5.2 Verify Application Started

Open new terminal tab (`Ctrl + Shift + `` or `+` in Terminal panel):
```powershell
# Test API endpoint
curl http://localhost:5000/api/health
# Expected: 200 OK response

# Or test frontend
curl http://localhost:3000
```

### 5.3 Access in Browser

1. Click **Ports** tab
2. Click the open-in-browser icon (🌐) next to port 3000 or 8080
3. Or manually visit: `https://localhost:3000`

## Phase 6: Configuration & Environment (5 minutes)

### 6.1 Verify Environment Variables

```powershell
# Check pre-configured variables
Write-Host "HELIOS_ENV: $env:HELIOS_ENV"
Write-Host "AZURE_SUBSCRIPTION_ID: $env:AZURE_SUBSCRIPTION_ID"
Write-Host "AZURE_TENANT_ID: $env:AZURE_TENANT_ID"
```

### 6.2 Create Local Configuration (if needed)

```powershell
# Create .env file for local settings
@"
HELIOS_ENV=development
DATABASE_URL=postgresql://localhost/helios_dev
API_PORT=5000
"@ | Out-File -Encoding UTF8 ".env"
```

### 6.3 Load Configuration

```powershell
# Load from .env (if using DotEnv)
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\w+\=') {
            $parts = $_ -split '=', 2
            Set-Item "env:$($parts[0])" $parts[1]
        }
    }
    Write-Host "✅ Environment variables loaded"
}
```

## Phase 7: Database Setup (Optional, 5-10 minutes)

If using PostgreSQL:

### 7.1 Start PostgreSQL

```powershell
# If using Docker
docker run -d `
  --name postgres-dev `
  -e POSTGRES_PASSWORD=devpassword `
  -e POSTGRES_DB=helios_dev `
  -p 5432:5432 `
  postgres:latest

# Verify
docker ps | grep postgres
```

### 7.2 Initialize Database

```powershell
# Connect to database
$env:PGPASSWORD = "devpassword"
psql -h localhost -U postgres -d helios_dev

# Or run migrations
dotnet ef database update
```

### 7.3 Verify Database

```powershell
# Test connection
Test-Connection localhost -port 5432 -TcpOnly

# Or from app logs
dotnet run 2>&1 | Select-String "database"
```

## Phase 8: Git Workflow Setup (5 minutes)

### 8.1 Configure Git User

```powershell
# Set local configuration
git config --local user.name "Your Name"
git config --local user.email "your.email@example.com"

# Verify
git config --local --list | Select-String "user"
```

### 8.2 Check Repository Status

```powershell
# Current branch
git branch -v

# Status
git status

# Recent commits
git log --oneline -5
```

### 8.3 Create Feature Branch (when ready)

```powershell
# Create and switch to feature branch
git checkout -b feature/my-feature

# Push to remote
git push -u origin feature/my-feature
```

## Phase 9: VS Code Customization (5 minutes)

### 9.1 Set Editor Preferences

1. Press `Ctrl + ,` to open Settings
2. Search and configure:
   - `editor.fontSize`: 14 (or your preference)
   - `editor.tabSize`: 4
   - `editor.formatOnSave`: true
   - `editor.defaultFormatter`: PowerShell
   - `files.autoSave`: afterDelay

### 9.2 Configure GitLens

Click GitLens icon (left sidebar):
1. Enable "Current Line Blame"
2. Enable "Automatic Line Blame"
3. Set blame format to your preference

### 9.3 Enable Copilot Chat

1. Press `Ctrl + Shift + I` to open Copilot Chat
2. Or click Copilot icon in left sidebar
3. Test: Type a question about your code

## Phase 10: Create Debugging Configuration (Optional, 5 minutes)

### 10.1 Create Launch Configuration

1. Click **Run and Debug** icon (left sidebar)
2. Click **create a launch.json file**
3. Select **.NET 5+ and .NET Core** environment
4. VS Code generates `.vscode/launch.json`

### 10.2 Start Debugging

1. Set breakpoint by clicking line number margin
2. Press `F5` to start debugging
3. Debugger attaches and stops at breakpoint
4. Use Debug Console to inspect variables

## Navigation Commands Summary

```powershell
# Navigation
cd src
cd tests
cd docs

# File operations
dir                    # List files
mkdir newfolder       # Create folder
rm-item file.txt     # Delete file
cp src.txt dst.txt   # Copy file
mv old.txt new.txt   # Rename file

# Useful shortcuts
Ctrl + `              # Toggle terminal
Ctrl + Shift + E      # File explorer
Ctrl + Shift + F      # Find in files
Ctrl + F              # Find in current file
Ctrl + H              # Find & replace
F12                   # Go to definition
Shift + F12           # Find references
```

## Deployment Commands (See CODESPACE_DEPLOYMENT.md for Details)

```powershell
# Build for deployment
dotnet build -c Release

# Create Docker image
docker build -t helios:latest .

# Push to registry
docker push helios:latest

# Deploy to Azure (if configured)
az webapp up --name myapp

# Run GitHub Actions workflow
gh workflow run deploy.yml
```

## Quick Verification Checklist

- [ ] All tools verified (dotnet, node, python, git, gh, az, docker)
- [ ] GitHub authenticated (`gh auth status`)
- [ ] Azure authenticated (`az account show`)
- [ ] Copilot activated (Chat opens)
- [ ] Project dependencies installed
- [ ] Project builds successfully
- [ ] Tests pass
- [ ] Development server starts
- [ ] Can access http://localhost:3000
- [ ] Port forwarding working
- [ ] Git configured
- [ ] Debugger working (F5)

## Troubleshooting First Steps

**Tools not found?**
```powershell
# Rebuild container
# Command Palette: Dev Containers: Rebuild Container
```

**Ports not forwarding?**
```powershell
# Restart port forwarding
# Kill terminal, reopen: Ctrl + Shift + `
```

**Slow performance?**
```powershell
# Check resource usage
top
# Or in terminal: dmesg | tail
```

**Authentication failing?**
```powershell
gh auth logout
gh auth login
```

## Next Steps

1. **Start coding** - Create feature branch, make changes
2. **Commit work** - Commit frequently with meaningful messages
3. **Create PR** - `gh pr create --draft` for feedback
4. **Deploy** - See CODESPACE_DEPLOYMENT.md
5. **Monitor** - See CODESPACE_TROUBLESHOOTING.md for issues

---

**Need Help?**
- 📚 Check extension docs within VS Code
- 🔍 Search GitHub Docs: https://docs.github.com/codespaces
- 💬 Use Copilot Chat: Press `Ctrl + Shift + I`
- 🐛 Report issues: Create GitHub Issue with terminal output

You're all set! Start coding! 🚀
