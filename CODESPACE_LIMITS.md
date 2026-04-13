# GitHub Codespace Limits and Pricing

## Free Tier (Individual Users)

### Monthly Usage Allowance

| Item | Free Tier | With Subscription |
|------|-----------|------------------|
| **Core-Hours** | 120 hours/month | Unlimited or higher quota |
| **Storage** | 15 GB total | Up to 100 GB |
| **Concurrent Codespaces** | 1 active | 4 active (pro tier) |
| **Cost** | Free (limited) | $15/month (Pro) |

### Machine Type Allocation

| Machine Type | Cores/RAM | Monthly Hours (Free) | Quota Usage |
|---|---|---|---|
| 2-core (4 GB) | 2/4 GB | 120 hours | 1x quota |
| 4-core (8 GB) | 4/8 GB | 60 hours | 2x quota |
| 8-core (16 GB) | 8/16 GB | 30 hours | 4x quota |
| 16-core (32 GB) | 16/32 GB | 15 hours | 8x quota |

**Example Calculations:**
- 60 hours on 2-core = 60 core-hours (within 120 limit) ✅
- 30 hours on 4-core = 60 core-hours (within 120 limit) ✅
- 40 hours on 4-core = 80 core-hours (within 120 limit) ✅
- 50 hours on 4-core = 100 core-hours (within 120 limit) ✅
- 61 hours on 2-core + 30 hours on 4-core = 61 + 60 = 121 core-hours (OVER) ❌

### Storage Limits

| Resource | Limit |
|----------|-------|
| **Total user storage** | 15 GB |
| **Per Codespace** | Up to 32 GB (but counts toward 15 GB quota) |
| **Backup storage** | Included in 15 GB quota |
| **Unused Codespace cleanup** | After 30 days of inactivity |

### Connection Limits

| Limit | Value |
|-------|-------|
| **Idle timeout** | 30 minutes of inactivity → auto-suspend |
| **Maximum session** | 60 minutes continuous (if not idle) |
| **Connection timeout** | Browser tab must reconnect periodically |
| **Rebuild timeout** | 60 minutes (codespace rebuilds can't exceed this) |

## Team Plans (Organizations)

### GitHub Team & Enterprise Plans

| Feature | Team | Enterprise |
|---------|------|-----------|
| Core-hours per user | 120 hours | 180 hours |
| Storage per user | 15 GB | 50 GB |
| Concurrent Codespaces | 2 | 5 |
| Retention (old codespaces) | 14 days | 30 days |
| Cost | Included in plan | Included in plan |

### Organization-Level Management

- Restrict base image selection
- Limit machine types available
- Set spending limits
- Manage team quotas
- Configure retention policies

## How Usage is Calculated

### Core-Hour Calculation

```
Total Core-Hours = Σ(Machine Cores × Running Hours)

Example:
- 4-core machine running 2 hours = 4 cores × 2 hours = 8 core-hours
- 2-core machine running 3 hours = 2 cores × 3 hours = 6 core-hours
- Total = 14 core-hours used
```

### Storage Calculation

```
Total Storage Used = Σ(All Codespaces + All Backups)

Example:
- Codespace 1: 8 GB
- Codespace 2: 5 GB
- Codespace 3: 2 GB
- Total = 15 GB (at limit)
```

### When Does Usage Count?

| Activity | Counts? |
|----------|---------|
| Codespace Running | ✅ Yes |
| Codespace Suspended (idle) | ❌ No |
| Codespace Stopped | ❌ No |
| Codespace Rebuilding | ✅ Yes (rebuilding counts as running) |
| Terminal/Editor Active | ✅ Yes |
| Sleeping (awaiting activity) | ❌ No |

## Auto-Suspend Behavior

### Default Behavior

- **Timer**: Starts after 30 minutes of inactivity
- **Action**: Codespace automatically suspends
- **Resume Time**: 5-20 seconds to wake up
- **Usage Impact**: Suspended time = 0 core-hours

### Inactivity Definition

Codespace is **active** when:
- ✅ Typing in editor
- ✅ Terminal command running
- ✅ File being edited
- ✅ Browser tab focused

Codespace is **idle** when:
- ❌ No keyboard input for 30 minutes
- ❌ No mouse clicks
- ❌ No active processes
- ❌ Browser tab not focused

### Custom Idle Timeout

```powershell
# In VS Code: Settings → Codespaces → Idle Timeout
# Options: 10, 30, 60, 120 minutes

# Or via settings.json:
"github.codespaces.idleTimeoutDuration": 60
```

### Maximum Session Duration

- **Hard Limit**: 60 minutes of continuous usage (no idle suspension)
- **Why**: Prevents runaway costs
- **Workaround**: Activity between sessions resets timer
- **Better Practice**: Use auto-suspend instead of long sessions

## Resource Allocation Details

### Memory Allocation

| Machine Type | Total RAM | Available to App | Reserved |
|---|---|---|---|
| 2-core | 4 GB | 2.5 GB | 1.5 GB |
| 4-core | 8 GB | 5 GB | 3 GB |
| 8-core | 16 GB | 12 GB | 4 GB |
| 16-core | 32 GB | 24 GB | 8 GB |

### Storage Allocation

| Type | Amount | Notes |
|------|--------|-------|
| Root filesystem | 32 GB | OS, tools, extensions |
| User home | 10 GB | Code, configs, cache |
| Workspace | 20 GB | Project files |
| **Total per Codespace** | **32 GB** | Shared across all three |

### CPU Allocation

- **2-core**: 2 vCPU (burstable to higher temporarily)
- **4-core**: 4 vCPU
- **8-core**: 8 vCPU
- **16-core**: 16 vCPU

All CPUs are shared infrastructure (not guaranteed exclusive).

## Bandwidth Limits

### Data Transfer

| Direction | Limit | Cost |
|-----------|-------|------|
| **Inbound** | Unlimited | Free (included) |
| **Outbound** | Unlimited | Free (included) |
| **Large file uploads** | No hard limit | May impact performance |
| **Large file downloads** | No hard limit | May impact performance |

### Connection Limits

- Maximum concurrent connections: 1024 (typical OS limit)
- TCP connection timeout: Standard (typically 10 minutes inactive)
- WebSocket connections: Unlimited (for Live Share, etc.)

## Pricing Breakdown

### Per-Month Costs (If purchased separately)

| Machine | Hours/Month | Cost/Hour | Total Cost |
|---------|------------|-----------|------------|
| 2-core | Unlimited | $0.018 | ~$13/month |
| 4-core | Unlimited | $0.036 | ~$26/month |
| 8-core | Unlimited | $0.072 | ~$52/month |
| 16-core | Unlimited | $0.144 | ~$104/month |

**Note:** Pricing is per **core-hour** after free tier is exceeded.

### Bundle Plans

| Plan | Price | Includes |
|------|-------|----------|
| **Free** | $0 | 120 core-hours/month, 15 GB storage |
| **Copilot Pro** | $20 | 500 core-hours/month, 50 GB storage, Copilot chat |
| **GitHub Pro** | $7 | 120 core-hours/month, 15 GB storage |
| **GitHub Team** | $21/user | Varies (see organization plans) |

## Cost Prevention Tips

### ✅ Best Practices

1. **Use 2-Core Machines by Default**
   - Sufficient for most development
   - Free tier compatible
   - Upgrade only when needed

2. **Stop Codespaces When Done**
   ```powershell
   gh codespace stop -c <name>
   # OR
   Click stop in Codespaces settings
   ```

3. **Set Aggressive Idle Timeout**
   - Set to 10 or 30 minutes (vs. default 60)
   - Most activity has natural breaks
   - Still leaves time for thinking

4. **Delete Old Codespaces**
   ```powershell
   gh codespace delete -c <name>
   # Frees storage quota
   ```

5. **Monitor Usage Regularly**
   - GitHub.com → Settings → Codespaces
   - See current month usage
   - Adjust strategy if exceeding quota

6. **Batch Development Sessions**
   - Work in longer focused sessions
   - Reduce number of suspend/resume cycles
   - Minimize idle time between tasks

### ❌ Cost Traps to Avoid

- ❌ Leaving Codespace running (mitigated by auto-suspend, but verify it works)
- ❌ Using 4-core when 2-core sufficient
- ❌ Creating multiple Codespaces for same project
- ❌ Large docker images stored in Codespace
- ❌ Development servers that never idle (kill them when done)
- ❌ Keeping old, unused Codespaces around

## Quota Management

### Check Current Usage

```powershell
# Web interface: GitHub.com → Settings → Codespaces → Usage
# Shows: Current month usage, % of quota used

# Via CLI
gh codespace list -v
# Shows: Machine type, region, idle timeout
```

### When Quota is Exceeded

| Scenario | What Happens | Solution |
|----------|---|---|
| Run out of core-hours | Can't create new Codespaces | Delete unused or wait for reset |
| Run out of storage | Can't commit/backup Codespaces | Delete old Codespaces |
| Hit concurrent limit | Can't create another active | Stop existing one first |
| Hard timeout (60 min) | Codespace forcibly suspends | Resume or switch machines |

### Quota Reset Schedule

- **Free Tier**: Resets monthly on billing date
- **Paid Plans**: Resets monthly on billing date
- **Pro/Team**: Different allocation based on plan
- **Enterprise**: Custom allocations per organization

## Performance Considerations

### Machine Type Impact on Cost

Running same project on different machines:

**Scenario: 1 hour of development**

| Machine | Cost | Duration | Reason |
|---------|------|----------|--------|
| 2-core | $0.018 | 60 min | Slower, take longer |
| 4-core | $0.036 | 30 min | 2x faster, takes 30 min |
| **Total to complete task** | **$0.018** | **30 min** | Faster finish = less idle time |

**Key Insight:** Faster machine may be MORE cost-effective if it reduces idle time!

### Optimization Strategy

- Use 2-core for: Reading docs, writing code, git operations
- Use 4-core for: Building, testing, debugging (often needed)
- Use 8-core+ for: Large project builds, heavy compute tasks

## Storage Management

### Cleanup Old Codespaces

```powershell
# List all Codespaces with size
gh codespace list

# Delete specific Codespace
gh codespace delete -c <codespace-name>

# GitHub auto-deletes after 30 days (free tier)
# Faster cleanup recommended if running low on quota
```

### Manage Build Artifacts

```powershell
# In Codespace, clean build output
dotnet clean
rm -Recurse bin/
rm -Recurse obj/

# Clear npm cache
npm cache clean --force

# Clear pip cache
pip cache purge
```

### .gitignore Optimization

Ensure `.gitignore` excludes:
- `node_modules/` (can be 500+ MB)
- `bin/` and `obj/` (.NET build outputs)
- `__pycache__/` (Python cache)
- `.vs/` and `.vscode/` (editor cache)
- `dist/` and `build/` (build outputs)

## Estimation Calculator

### Plan Your Monthly Usage

```
1. Estimate daily development hours: ___ hours
2. Multiply by 22 working days: ___ core-hours (2-core equivalent)
3. Add extra for building (2x time): ___ core-hours
4. Total estimated: ___ core-hours

Quota available: 120 core-hours (free tier)
Your estimate vs. quota: _____ (surplus or deficit)
```

**Example:**
```
- 4 hours/day coding on 2-core = 4 core-hours/day
- 4 hours × 22 days = 88 core-hours
- Plus 2 hours/week building = 88 + 8 = 96 core-hours
- 96 < 120 ✅ (fits in free tier!)
```

## Monitoring and Alerts

### Set Budget Alert

1. Go to GitHub.com → Settings → Billing and plans
2. Set spending limit for Codespaces
3. GitHub notifies when approaching limit
4. Prevents unexpected charges

### Export Usage Data

```powershell
# Usage is visible in Settings → Codespaces
# Export/track manually or:

# Via GitHub API
gh api -H "Accept: application/vnd.github+json" \
  /user/codespaces \
  --paginate > codespaces.json
```

## Regional Pricing

### No Regional Price Variation

- **All regions**: Same core-hour rate
- **Region choice**: Affects latency, not cost
- **Recommendation**: Choose closest region for speed

### Region Selection

1. Codespace creation → "New with options"
2. Choose region with lowest latency
3. Closer region = faster response = shorter sessions = lower cost

## Conclusion: Cost-Optimized Strategy

1. **Default 2-core machine** for daily development
2. **Upgrade to 4-core** only for long build sessions
3. **Set idle timeout to 30 min** (or even 10 min)
4. **Stop when done**: `gh codespace stop`
5. **Delete monthly**: Clean up old Codespaces
6. **Monitor**: Check Settings → Codespaces monthly
7. **Estimate**: Use calculator above to plan usage

---

**Quick Reference:**
- 💰 Free: 120 core-hours/month = ~60 hours at 2-core
- 💾 Storage: 15 GB total across all Codespaces
- ⏱️ Idle timeout: Default 30 min (customizable)
- 🎯 Max session: 60 min continuous
- 📊 Pricing: Included in plan (or $0.018/core-hour if overages)

**See Also:**
- 📖 CODESPACE_LAUNCH_GUIDE.md - How to create Codespaces
- 💬 CODESPACE_FIRST_STEPS.md - Setup after launch
- 🆘 CODESPACE_TROUBLESHOOTING.md - Solve issues
