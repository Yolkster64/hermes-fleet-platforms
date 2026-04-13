# GitHub Codespace Launch Guide for HELIOS Platform

## Quick Launch

### Direct URL Launch (Fastest)
Click the button below to create and launch a new Codespace:

```
https://codespaces.new/helios-platform/helios-platform-repo
```

### From GitHub Repository
1. Navigate to: https://github.com/helios-platform/helios-platform-repo
2. Click the **Code** button (green button)
3. Select the **Codespaces** tab
4. Click **Create codespace on main** or choose a specific branch
5. Wait 2-3 minutes for the environment to initialize

### Manual Steps in GitHub UI
1. Go to your repository on GitHub.com
2. Click **Code** → **Codespaces** tab
3. Click **"..." (three dots)** → **New with options**
4. Choose settings:
   - **Branch**: main (or your preferred branch)
   - **Region**: Select closest to you for better performance
   - **Machine type**: 4-core (default, recommended for HELIOS)
5. Click **Create codespace**

## What to Expect on First Launch

### Initialization Timeline
| Phase | Time | What's Happening |
|-------|------|-----------------|
| Container Setup | 30-60s | GitHub building the dev container image |
| Feature Installation | 30-45s | Installing Azure CLI, Docker, GitHub CLI, PowerShell, .NET 8 |
| Extension Loading | 15-30s | Loading VS Code extensions (Copilot, GitLens, C#, Python, etc.) |
| Post-Create Command | 60-120s | `npm install`, `dotnet restore`, `pip install` running in parallel |
| Ready for Development | Total: 2-4 min | 🎉 Codespace fully initialized and ready |

### Initial Setup Progress
Watch the terminal for these indicators:
```
🚀 HELIOS DevContainer Ready
📦 Installing dependencies...
[npm install completing...]
[dotnet restore completing...]
[pip install completing...]
✅ Setup complete
```

### First-Time Features Auto-Loaded
- ✅ 11 VS Code extensions pre-installed
- ✅ .NET 8 SDK and runtime
- ✅ Python 3 environment
- ✅ Docker-in-Docker enabled
- ✅ Azure CLI authenticated (if credentials available)
- ✅ GitHub CLI ready
- ✅ Port forwarding configured (3000, 5000, 5432, 8080, 8443)
- ✅ SSH keys and Azure credentials mounted

## Accessing Your Codespace

### Via Web Browser
- GitHub creates a unique URL: `https://<your-username>-<random-id>.github.dev`
- Automatically opens after creation
- Full VS Code experience in browser

### Via Desktop VS Code
1. Open desktop VS Code
2. Install "GitHub Codespaces" extension
3. Click **Remote Explorer** in left sidebar
4. Select your Codespace from the list
5. Click **Connect**

### Via Command Line
```powershell
gh codespace list
gh codespace code -c <codespace-name>
```

## First Steps After Launch

```powershell
# Verify development environment
npm --version
dotnet --version
python --version

# Verify project structure
ls -la
cd src

# Run the application
npm start         # or your project's start script
# OR
dotnet run

# Run tests
npm test
# OR
dotnet test
```

## Connecting Tools to Your Codespace

### GitHub CLI
```powershell
gh auth status
```

### Azure CLI
```powershell
az login
az account show
```

### Docker
```powershell
docker ps
docker run hello-world
```

## Port Forwarding

These ports are automatically forwarded and accessible:

| Port | Service | Access URL |
|------|---------|------------|
| 3000 | Web UI | https://github.dev:3000 |
| 5000 | API Server | https://github.dev:5000 |
| 5432 | PostgreSQL | localhost:5432 |
| 8080 | Dashboard | https://github.dev:8080 |
| 8443 | HTTPS | https://github.dev:8443 |

## Performance Tips

✅ **Best Practices:**
- Use the browser-based editor for lower latency
- 4-core machine type is sufficient for HELIOS
- Choose a region close to your location
- Limit background processes to save resources

⚠️ **Avoid:**
- Running multiple resource-intensive services simultaneously
- Large file uploads/downloads over weak connections
- Long-running background tasks without need

## Stopping Your Codespace

### Automatic Stop
- **Default**: Stops after 30 minutes of inactivity
- **Max Duration**: 60 minutes maximum continuous use (adjustable in settings)

### Manual Stop
1. In the browser tab, click your avatar (top-right)
2. Select **Stop current codespace**
3. Or: `gh codespace stop -c <codespace-name>`

## Deleting Your Codespace

### After You're Done
1. GitHub stops unused Codespaces automatically
2. To free up storage quota: Delete the Codespace
3. In Settings → Codespaces → Delete old Codespaces
4. Or: `gh codespace delete -c <codespace-name>`

## Cost Awareness

See **CODESPACE_LIMITS.md** for:
- Free tier hours (120 hours/month for 2-core, 60 hours for 4-core)
- Storage quota (15 GB)
- Auto-suspend behavior
- Cost prevention strategies

## Troubleshooting

See **CODESPACE_TROUBLESHOOTING.md** for solutions to:
- Connection issues
- Slow performance
- Extension not loading
- Port forwarding not working
- Authentication failures

## Environment Configuration

The Codespace includes pre-configured environment variables:
- `HELIOS_ENV=development`
- `AZURE_SUBSCRIPTION_ID` (from local machine)
- `AZURE_TENANT_ID` (from local machine)

For sensitive data, add secrets in:
Settings → Codespaces → Secrets (for Codespaces)

## Need Help?

- 📖 Read **CODESPACE_FIRST_STEPS.md** for commands to run after launch
- 🚀 Check **CODESPACE_DEPLOYMENT.md** for deployment from Codespace
- 📋 See **CODESPACE_FEATURES.md** for full environment details
- ❓ Review **CODESPACE_TROUBLESHOOTING.md** for common issues
