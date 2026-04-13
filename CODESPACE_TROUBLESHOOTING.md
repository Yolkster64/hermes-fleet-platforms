# GitHub Codespace Troubleshooting Guide

## Connection & Access Issues

### Issue: "Cannot connect to Codespace"

**Symptoms:**
- Codespace URL doesn't load
- "Connection timed out" error
- Web editor won't open

**Solutions:**

1. **Check Codespace Status**
   ```powershell
   gh codespace list
   # Look for "Running" status
   ```

2. **Rebuild Connection**
   - Close browser tab
   - Wait 30 seconds
   - Click Codespace name again to reconnect

3. **Restart Codespace**
   - Stop: `gh codespace stop -c <name>`
   - Wait 10 seconds
   - Resume: `gh codespace resume -c <name>`

4. **Check Internet Connection**
   - Test connectivity: Open GitHub.com
   - If GitHub down, GitHub Codespaces unavailable
   - Try different network/VPN

5. **Clear Browser Cache**
   - Press `F12` → **Application** tab
   - Clear cache and cookies for `*.github.dev`
   - Refresh page

### Issue: Desktop VS Code won't connect

**Symptoms:**
- "Remote Connection Failed"
- Codespace not visible in Remote Explorer
- Error: "Extension installation failed"

**Solutions:**

1. **Verify Extension Installed**
   - Open VS Code locally
   - Go to Extensions
   - Search "GitHub Codespaces"
   - Install if missing

2. **Update Codespaces Extension**
   - Check for updates
   - Reload VS Code

3. **Authenticate GitHub**
   ```powershell
   # In local VS Code terminal
   gh auth logout
   gh auth login
   ```

4. **Reload Remote Explorer**
   - Click Codespaces icon in left sidebar
   - Click reload (circular icon)

5. **Clear Remote Connection Cache**
   - On Windows: Delete `C:\Users\<user>\.vscode\`
   - Restart VS Code

---

## Performance Issues

### Issue: "Codespace is very slow"

**Symptoms:**
- Typing lag in editor
- Commands take 30+ seconds
- Extensions slow to load
- Terminal unresponsive

**Solutions:**

1. **Check Network Connection**
   ```bash
   ping github.com
   # Should be < 50ms latency
   ```

2. **Check Resource Usage**
   ```bash
   top
   # Exit with 'q'
   # Look for high CPU or memory usage
   ```

3. **Close Unnecessary Extensions**
   - Press `Ctrl + Shift + P`
   - Search: "Extensions: Disable all extensions"
   - Re-enable only needed ones

4. **Disable Expensive Features**
   - Press `Ctrl + ,` for Settings
   - Search "autosave"
   - Set to "off" or "afterDelay" (not onFocusChange)
   - Disable git autofetch
   - Disable Python linting

5. **Upgrade Machine Type**
   - Stop Codespace: `gh codespace stop -c <name>`
   - GitHub Settings → Codespaces → Machine type
   - Change to 4-core or 8-core
   - Restart Codespace

6. **Use Browser DevTools**
   - In Codespace browser, press F12
   - Check **Network** tab for slow resources
   - Check **Performance** tab for bottlenecks

7. **Reduce File Watching**
   ```bash
   # In terminal
   # Kill any background processes
   pkill -f "node_modules"
   pkill -f "webpack"
   ```

### Issue: "Terminal is slow or unresponsive"

**Solutions:**

1. **Create New Terminal Tab**
   - Old terminal might have hung process
   - Click `+` in terminal panel

2. **Kill Hung Process**
   ```powershell
   # List all processes
   Get-Process | Sort-Object CPU -Descending

   # Kill specific process
   Stop-Process -Id <PID> -Force
   ```

3. **Clear Terminal Scrollback**
   - Right-click terminal → Clear
   - This frees memory

4. **Restart Terminal**
   - Close all terminal tabs
   - Open new one: `Ctrl + Shift + ``

---

## Extension & Tool Issues

### Issue: "Extensions not loading"

**Symptoms:**
- Extensions list is empty
- Specific extension shows error icon
- "Install Failed" message

**Solutions:**

1. **Check Extension Status**
   - Open Extensions panel
   - Look for error messages
   - Click **Show Errors** if available

2. **Reinstall Extension**
   - Right-click extension
   - Choose **Uninstall**
   - Search and reinstall

3. **Rebuild Codespace**
   ```powershell
   # Command Palette (Ctrl + Shift + P)
   # Search: "Dev Containers: Rebuild Container"
   # Wait 3-5 minutes for rebuild
   ```

4. **Clear Extension Cache**
   ```bash
   # In Codespace terminal
   rm -rf ~/.vscode-server/extensions
   # Reload VS Code
   ```

5. **Check devcontainer.json**
   - Verify extension names are correct
   - Check for typos in extension IDs
   - Rebuild if modifications made

### Issue: "Copilot not working"

**Symptoms:**
- Copilot Chat won't open (Ctrl + Shift + I)
- Code completion suggestions don't appear
- "Sign in to Copilot" always shows

**Solutions:**

1. **Sign in to Copilot**
   - Press `Ctrl + Shift + P`
   - Search: "Copilot: Sign In"
   - Follow browser authentication

2. **Check Copilot Settings**
   - Press `Ctrl + ,` for Settings
   - Search: "copilot"
   - Ensure "Copilot: Enable Inline Suggestions" is true

3. **Verify GitHub License**
   - Must have GitHub Copilot subscription
   - Check: https://github.com/settings/copilot
   - Free access for students/maintainers

4. **Restart Copilot**
   - Press `Ctrl + Shift + P`
   - Search: "Developer: Reload Window"
   - Wait 30 seconds

---

## Port Forwarding Issues

### Issue: "Port forwarding not working"

**Symptoms:**
- Can't access http://localhost:3000
- "Cannot GET /" or connection refused
- Port shows in list but can't connect

**Solutions:**

1. **Verify Application Started**
   ```powershell
   # In Codespace terminal
   netstat -ano | Select-String "3000"
   # Should show listening connection
   ```

2. **Check Port Configuration**
   - Click **Ports** tab
   - Verify ports are listed
   - If missing: right-click → **Forward Port**

3. **Verify Application Running**
   ```powershell
   # Start application
   dotnet run
   # or npm start
   # Should see "Server running on port 3000"
   ```

4. **Test Localhost Access**
   ```bash
   curl http://localhost:3000
   # or
   curl http://localhost:5000/api/health
   ```

5. **Change Port Visibility**
   - Right-click port in Ports tab
   - Toggle "Private" ↔ "Public"
   - Sometimes fixes connectivity

6. **Restart Port Forwarding**
   - Close all terminal tabs
   - Open new terminal: `Ctrl + Shift + ``
   - Ports should auto-forward again

### Issue: "Port shows as Private but need Public access"

**Solution:**
1. Click **Ports** tab
2. Right-click port (e.g., 3000)
3. Select **Port Visibility** → **Public**
4. Codespace URL will work: `https://<codespace-url>:3000`

---

## Authentication Issues

### Issue: "GitHub authentication failing"

**Symptoms:**
- `gh` commands fail with auth error
- Cannot create PRs or push to GitHub
- Git operations ask for password repeatedly

**Solutions:**

1. **Check Auth Status**
   ```powershell
   gh auth status
   # Shows: Logged in to github.com
   ```

2. **Re-authenticate**
   ```powershell
   gh auth logout
   gh auth login
   # Choose: github.com
   # Choose: SSH or HTTPS
   # Complete browser auth
   ```

3. **Verify SSH Keys**
   ```bash
   ls -la ~/.ssh
   # Should show: id_rsa, id_rsa.pub, id_ed25519, etc.
   ```

4. **Test SSH Connection**
   ```bash
   ssh -T git@github.com
   # Should respond: Hi <username>! You've successfully authenticated.
   ```

5. **Fix SSH Key Permissions**
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/id_rsa
   chmod 644 ~/.ssh/id_rsa.pub
   ```

### Issue: "Azure CLI not authenticated"

**Symptoms:**
- `az` commands fail
- Cannot access Azure resources
- "Not authenticated with Azure" error

**Solutions:**

1. **Login to Azure**
   ```powershell
   az login
   # Opens browser for authentication
   ```

2. **Check Current Account**
   ```powershell
   az account show
   # Shows current subscription
   ```

3. **List Available Subscriptions**
   ```powershell
   az account list --output table
   ```

4. **Switch Subscription**
   ```powershell
   az account set --subscription "<subscription-id>"
   ```

5. **Refresh Credentials**
   ```powershell
   az login --refresh
   ```

---

## Build & Development Issues

### Issue: "Build fails with errors"

**Symptoms:**
- `dotnet build` fails
- Compilation errors appear
- "Project file not found"

**Solutions:**

1. **Check Project File Exists**
   ```powershell
   Test-Path "HELIOS.Platform.csproj"
   # Should return True
   ```

2. **Clean Build**
   ```powershell
   dotnet clean
   dotnet build
   ```

3. **Restore Dependencies**
   ```powershell
   dotnet restore
   ```

4. **Check .NET Version**
   ```powershell
   dotnet --version
   # Should be 8.x for HELIOS
   ```

5. **Review Build Errors**
   ```powershell
   dotnet build --verbosity diagnostic
   # Shows detailed error info
   ```

6. **Rebuild Container**
   - Codespace might have corrupted .NET
   - Command Palette: "Dev Containers: Rebuild Container"

### Issue: "Tests fail to run"

**Symptoms:**
- `dotnet test` shows errors
- Test explorer is empty
- "No test adapters found"

**Solutions:**

1. **Build Tests First**
   ```powershell
   dotnet test --no-build
   # If fails, run: dotnet build first
   ```

2. **List Tests**
   ```powershell
   dotnet test --list-tests
   ```

3. **Run Specific Test**
   ```powershell
   dotnet test --filter "TestName"
   ```

4. **Enable Test Explorer**
   - Install "Test Explorer UI" extension
   - Or use built-in Test Explorer
   - Press `Ctrl + Shift + P`
   - Search: "Test: Focus on Test Explorer"

---

## Storage & Quota Issues

### Issue: "Out of storage space"

**Symptoms:**
- "Disk full" error
- Cannot clone repositories
- npm install fails

**Solutions:**

1. **Check Disk Usage**
   ```bash
   df -h
   # Shows available space
   ```

2. **Find Large Files**
   ```bash
   du -sh * | sort -rh
   # Lists largest directories
   ```

3. **Clear npm Cache**
   ```powershell
   npm cache clean --force
   ```

4. **Clear Docker Images** (if using Docker)
   ```bash
   docker image prune -a
   ```

5. **Delete Old Codespaces**
   - GitHub.com Settings → Codespaces
   - Delete unused Codespaces to free quota

6. **Cleanup Build Artifacts**
   ```powershell
   dotnet clean
   rm -Recurse bin/
   rm -Recurse obj/
   ```

---

## Database Issues

### Issue: "PostgreSQL won't connect"

**Symptoms:**
- Connection refused on port 5432
- "Cannot connect to database"
- Migrations fail

**Solutions:**

1. **Check PostgreSQL Running**
   ```bash
   docker ps | grep postgres
   # Should see postgres container running
   ```

2. **Start PostgreSQL**
   ```bash
   docker run -d \
     --name postgres-dev \
     -e POSTGRES_PASSWORD=devpass \
     -p 5432:5432 \
     postgres:latest
   ```

3. **Test Connection**
   ```powershell
   $env:PGPASSWORD = "devpass"
   psql -h localhost -U postgres -c "SELECT version();"
   ```

4. **Check Environment Variables**
   ```powershell
   Write-Host "DATABASE_URL: $env:DATABASE_URL"
   # Should have connection string
   ```

---

## File Synchronization Issues

### Issue: "SSH keys not available"

**Symptoms:**
- SSH auth fails in git operations
- "Key not found" error
- `ls ~/.ssh` is empty

**Solutions:**

1. **Verify SSH Mount**
   ```bash
   ls -la ~/.ssh
   # Should show id_rsa, id_ed25519, etc.
   ```

2. **Check devcontainer.json Mount**
   ```json
   "mounts": [
     "source=${localEnv:HOME}${localEnv:USERPROFILE}/.ssh,target=/home/vscode/.ssh"
   ]
   ```

3. **Rebuild Codespace**
   - SSH keys might not have mounted correctly
   - Rebuild: Command Palette → "Dev Containers: Rebuild Container"

4. **Generate New SSH Keys**
   ```bash
   ssh-keygen -t ed25519 -C "your@email.com"
   # Add public key to GitHub
   ```

---

## Workspace Management

### Issue: "Too many Codespaces, can't create new one"

**Symptoms:**
- "You've reached the limit of active Codespaces"
- Can't create new Codespace
- Quota error

**Solutions:**

1. **List All Codespaces**
   ```powershell
   gh codespace list
   ```

2. **Stop Unused Codespaces**
   ```powershell
   gh codespace stop -c <codespace-name>
   ```

3. **Delete Old Codespaces**
   ```powershell
   gh codespace delete -c <codespace-name>
   ```

4. **Check Web Settings**
   - GitHub.com → Settings → Codespaces
   - See all active Codespaces
   - Delete from web interface

---

## Performance Best Practices

### Enable Optimal Performance

1. **Disable Auto-Save** (when unnecessary)
   ```json
   "files.autoSave": "off"
   ```

2. **Disable File Watchers**
   - Search Settings: "files.watcherExclude"
   - Exclude: node_modules, .git, build

3. **Use Workspace Trust**
   - Codespace asks to trust workspace
   - Click "Trust" to enable optimizations

4. **Close Unused Extensions**
   - Keep only active development extensions
   - Disable language packs not needed

5. **Use 4-Core Machine**
   - Better than 2-core (free tier)
   - Costs extra but significant performance

---

## Security Best Practices

### Protect Your Codespace

✅ **Do:**
- Use SSH keys instead of HTTPS passwords
- Keep Codespace URL private
- Change port visibility to Private when possible
- Use environment variables for secrets
- Regularly rotate credentials

❌ **Don't:**
- Commit secrets to repository
- Share Codespace URL with untrusted parties
- Leave Codespace running 24/7
- Store passwords in plain text files
- Disable security features

### Secret Management

```powershell
# Use GitHub Secrets for sensitive data
# GitHub.com → Settings → Codespaces → Secrets
# Example: AZURE_CONNECTION_STRING

# Access in Codespace
$secret = $env:AZURE_CONNECTION_STRING
```

---

## Cost Optimization

### Monitor Usage

```powershell
# Check Codespace details
gh codespace list
# Shows machine type (2-core free, 4-core paid)
```

### Reduce Costs

1. **Use 2-Core Machine**
   - Free tier allocation (if available)
   - Slightly slower, but acceptable
   - Settings → Codespaces → Machine type

2. **Set Auto-Suspend**
   - Default: 30 minutes inactivity
   - Maximum: 60 minutes
   - Prevents runaway charges

3. **Stop When Not Using**
   ```powershell
   gh codespace stop -c <name>
   ```

4. **Delete Unused Codespaces**
   ```powershell
   gh codespace delete -c <name>
   ```

See **CODESPACE_LIMITS.md** for detailed pricing info.

---

## Getting Help

### Before Reporting Issue

1. Check this guide for your symptom
2. Search GitHub Discussions: `github.com/orgs/github-community/discussions`
3. Review VS Code Remote Development docs
4. Check Codespaces status page: `github.com/status`

### Report Issue

1. Collect diagnostic info:
   ```powershell
   gh codespace list -v
   dotnet --info
   gh --version
   ```

2. Create GitHub Issue with:
   - Error message (exact text)
   - Steps to reproduce
   - Codespace configuration
   - Expected vs actual behavior

### Emergency Exit

If Codespace becomes unusable:
1. Delete current Codespace
2. Create new one: `gh codespace create`
3. Recreate from latest branch

---

**For Additional Help:**
- 📚 GitHub Docs: https://docs.github.com/codespaces
- 💬 Copilot Chat: `Ctrl + Shift + I`
- 🔗 VS Code Remote Dev Docs: https://code.visualstudio.com/docs/remote
- 📢 GitHub Discussions: https://github.com/orgs/github-community/discussions
