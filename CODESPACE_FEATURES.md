# GitHub Codespace Features & Pre-Installed Tools

## Development Environment

### Base Image
- **Container Image**: Microsoft Universal Dev Container (latest)
- **OS**: Ubuntu Linux (latest)
- **Architecture**: Supports both x86_64 and ARM64

### Runtime & SDKs

| Tool | Version | Purpose |
|------|---------|---------|
| .NET SDK | 8 | C# development, ASP.NET Core, project builds |
| Python | 3.x | Python scripts, dependencies management |
| Node.js | Latest LTS | JavaScript/TypeScript tooling |
| npm | Latest | Package management for Node |
| PowerShell | Latest | Cross-platform scripting |

## Pre-Installed VS Code Extensions (11 Total)

### Core Development
1. **PowerShell** (`ms-vscode.powershell`)
   - PowerShell scripting and debugging
   - Integrated terminal support

2. **C# Dev Kit** (`ms-dotnettools.csharp`)
   - C# language support, IntelliSense, debugging
   - .NET framework integration

3. **.NET Runtime Installer** (`ms-dotnettools.vscode-dotnet-runtime`)
   - Automatic .NET runtime detection
   - Version management

### Azure & Cloud
4. **Azure Functions** (`ms-azure-tools.vscode-azurefunctions`)
   - Local Azure Functions debugging
   - Deployment to Azure Functions

5. **Azure Tools** (`ms-azure-tools.vscode-azuretools`)
   - General Azure resource management
   - Storage, VMs, App Service

6. **Azure Cosmos DB** (`ms-azure-tools.vscode-cosmosdb`)
   - Cosmos DB connection and querying
   - Document browser

### DevOps & Containers
7. **Docker** (`ms-azure-tools.vscode-docker`)
   - Docker support and debugging
   - Container image management

### Code Quality & Collaboration
8. **Python** (`ms-python.python`)
   - Python IntelliSense and debugging
   - Virtual environment support

9. **Ruff** (`charliermarsh.ruff`)
   - Python linting and formatting
   - PEP 8 compliance checking

10. **GitLens** (`eamodio.gitlens`)
    - Git blame, history, authorship
    - Repository insights
    - Visual commit history

11. **GitHub Copilot** (`GitHub.Copilot`)
    - AI-powered code completion
    - Intelligent suggestions
    - Chat support (sign in required)

## Features Installed (Dev Container Features)

### 1. Azure CLI
```bash
az --version
```
- Command-line tools for Azure resources
- Authentication with `az login`
- Service management capabilities

### 2. Docker-in-Docker
```bash
docker ps
docker run -it ubuntu bash
```
- Run Docker commands from within container
- Build and test containerized applications
- Access to Docker daemon

### 3. GitHub CLI
```bash
gh --version
gh auth login
```
- Create/manage GitHub repositories
- Create pull requests, issues
- Manage GitHub Actions workflows

### 4. PowerShell
```powershell
$PSVersionTable
```
- Cross-platform PowerShell 7+
- Full scripting capabilities
- Integration with .NET

### 5. .NET SDK 8
```bash
dotnet --version
dotnet new console
```
- Latest .NET features
- C# 12 language support
- ASP.NET Core 8

## Port Forwarding Configuration

### Automatically Forwarded Ports

| Port | Label | Service | Type | Access |
|------|-------|---------|------|--------|
| 3000 | Web UI | Frontend/React | HTTP/HTTPS | Public (notified) |
| 5000 | API Server | ASP.NET Core API | HTTP/HTTPS | Public (notified) |
| 5432 | PostgreSQL | Database | TCP | Private (local) |
| 8080 | Dashboard | Admin/Monitoring | HTTP/HTTPS | Public (notified) |
| 8443 | HTTPS | Secure services | HTTPS | Public (notified) |

### Port Visibility Settings
- Default: **Public** (accessible from internet)
- Change to **Private**: Right-click port → Make Private
- Notification on auto-forward: Enabled for ports 3000, 5000, 8080

### Accessing Forwarded Ports

**From Web Browser:**
```
https://localhost:3000
https://localhost:5000
https://localhost:8080
```

**From within Codespace:**
```bash
curl http://localhost:3000
curl http://localhost:5000
curl http://localhost:8080
```

**From other machines (if Public):**
```
https://<codespace-url>:3000
https://<codespace-url>:5000
https://<codespace-url>:8080
```

## Environment Variables

Pre-configured environment variables available in your Codespace:

| Variable | Value | Source |
|----------|-------|--------|
| `HELIOS_ENV` | development | devcontainer.json |
| `AZURE_SUBSCRIPTION_ID` | *from local machine* | localEnv |
| `AZURE_TENANT_ID` | *from local machine* | localEnv |
| `PATH` | Standard Linux + tools | System |
| `DOTNET_ROOT` | /usr/local/share/dotnet | .NET install |
| `PYTHON_PATH` | /usr/local/bin/python | Python install |
| `SHELL` | /bin/bash | System |

### How Environment Variables Work
- **Local Machine Values**: Copied from your local environment at Codespace creation
- **Secure Secrets**: Use GitHub Settings → Codespaces → Secrets for sensitive data
- **Scope**: Available to all processes in the Codespace

### Setting Custom Variables
```bash
# In terminal
export MY_VAR="value"

# In .devcontainer/devcontainer.json (requires rebuild)
"remoteEnv": {
  "MY_CUSTOM_VAR": "custom-value"
}
```

## File System Mounts

Special folders mounted from your local machine:

| Local Path | Container Path | Purpose | Persistence |
|-----------|---|---------|-------------|
| `~/.ssh` | `/home/vscode/.ssh` | SSH keys for Git/GitHub | From local machine |
| `~/.azure` | `/home/vscode/.azure` | Azure CLI authentication | From local machine |

### Benefits
✅ No need to re-authenticate in Codespace
✅ SSH keys automatically available
✅ Azure credentials preserved

## Terminal & Shell Configuration

### Default Shell
- **Terminal**: PowerShell (configurable)
- **Alternative**: Bash, zsh available

### VS Code Settings Applied
```json
{
  "terminal.defaultProfile": "PowerShell",
  "python.defaultInterpreterPath": "/usr/local/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "[powershell]": {
    "editor.defaultFormatter": "ms-vscode.powershell",
    "editor.formatOnSave": true
  }
}
```

## Resource Allocation

### Machine Types Available

| Type | Cores | RAM | Storage | Price (per hour) |
|------|-------|-----|---------|------------------|
| 2-core | 2 | 4 GB | 32 GB | Free tier credit |
| 4-core | 4 | 8 GB | 32 GB | Higher quota usage |
| 8-core | 8 | 16 GB | 32 GB | Premium |
| 16-core | 16 | 32 GB | 32 GB | Premium |

**Recommended for HELIOS**: 4-core machine

### Storage
- **Total Quota**: 15 GB per user
- **Per Codespace**: Up to 32 GB (but counts toward quota)
- **Cleanup**: Old/deleted Codespaces free up quota

## Git Integration

### Pre-Configured
- ✅ Git 2.x installed and configured
- ✅ SSH keys available for authentication
- ✅ GitHub CLI ready (`gh` command)
- ✅ GitLens extension for enhanced Git features

### Common Git Commands
```bash
git clone <repo>
git checkout -b feature/my-feature
git commit -m "message"
git push origin feature/my-feature
```

## Docker Integration

### Docker Commands Available
```bash
docker ps                      # List running containers
docker build -t myimage .      # Build image
docker run -d myimage          # Run container
docker exec -it container bash # Enter container
```

### Docker-in-Docker Benefits
- ✅ Build and test Docker images
- ✅ Run containers for testing
- ✅ No host machine dependency
- ✅ Isolated environment

## Authentication & Credentials

### Pre-Mounted
- SSH keys from `~/.ssh`
- Azure credentials from `~/.azure`
- GitHub token (via CLI)

### How to Authenticate

**GitHub:**
```bash
gh auth login
# or SSH keys auto-available
```

**Azure:**
```bash
az login
az account set --subscription <subscription-id>
```

**Docker Registry:**
```bash
docker login
```

## Customization Options

### Adding New Extensions
Edit `.devcontainer/devcontainer.json`:
```json
"extensions": [
  "new-extension-publisher.extension-name"
]
```
Then rebuild the Codespace.

### Adding New Features
```json
"features": {
  "ghcr.io/devcontainers/features/npm:1": {}
}
```

### Modifying Settings
```json
"customizations": {
  "vscode": {
    "settings": {
      "editor.fontSize": 14
    }
  }
}
```

## System Tools Available

- **Build Tools**: make, cmake, autotools
- **Compression**: tar, gzip, zip, unzip
- **Version Control**: git, gh
- **Network**: curl, wget, netcat
- **Development**: gcc, clang (if needed)
- **Database**: sqlite3, postgresql-client

## Performance Optimization

### VS Code Settings for Performance
```json
{
  "editor.codeActionsOnSave": false,
  "git.autofetch": false,
  "python.linting.enabled": false
}
```

### Extension Performance
- Disable unused extensions in Remote Containers
- Check Extension Host in About → Performance
- Monitor resource usage with `top` command

## Connection Information

### Network Details
- **Inside Container**: Use `localhost` for local ports
- **From Browser**: Use `https://<codespace-url>` for forwarded ports
- **DNS**: Automatic resolution within container

### Bandwidth Considerations
- ✅ Included in GitHub Codespaces quota
- ✅ No additional charges for transfer
- ⚠️ Large file operations may impact performance

## Security Features

- 🔐 Encrypted SSH connections
- 🔐 HTTPS for web forwarding
- 🔐 Secrets stored in GitHub encrypted
- 🔐 Credentials from local machine (SSH, Azure)
- 🔐 Isolated container environment
- 🔐 Network isolation from host

---

**For more information:**
- 📖 See CODESPACE_LAUNCH_GUIDE.md for launch instructions
- 📋 See CODESPACE_FIRST_STEPS.md for post-launch setup
- ❓ See CODESPACE_TROUBLESHOOTING.md for common issues
- 💰 See CODESPACE_LIMITS.md for pricing and quotas
