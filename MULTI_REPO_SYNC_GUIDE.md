# HELIOS Platform - Multi-Repository Synchronization Guide

Complete procedures for cloning, syncing, updating, and troubleshooting all 7 submodules integrated with HELIOS Platform.

---

## 📦 Overview

HELIOS Platform uses **Git submodules** to integrate 7 specialized repositories. This guide covers all operations for managing this multi-repository setup.

### Repository Structure
```
helios-platform/ (main repository)
├── .gitmodules (submodule references)
├── modules/
│   ├── helios-monado-blade/
│   ├── helios-security-setup/
│   ├── helios-ai-hub/
│   ├── helios-dev-ai-hub/
│   ├── helios-build-agents/
│   ├── helios-gui-framework/
│   └── helios-software-stack/
├── src/ (main source)
├── scripts/ (orchestration)
└── docs/ (documentation)
```

---

## 🚀 Initial Clone Operations

### Option 1: Clone with All Submodules (Recommended)

**Best for:** Fresh deployments, complete setup

```bash
# Clone main repo with all submodules
git clone --recurse-submodules https://github.com/M0nado/helios-platform.git
cd helios-platform

# Verify all submodules present
ls -la modules/
# Should show all 7 directories

# Check submodule status
git submodule status
```

**Expected Output:**
```
 hash1 modules/helios-monado-blade (tag: v1.0.0)
 hash2 modules/helios-security-setup (tag: v1.0.0)
 hash3 modules/helios-ai-hub (tag: v1.0.0)
 hash4 modules/helios-dev-ai-hub (tag: v1.0.0)
 hash5 modules/helios-build-agents (tag: v1.0.0)
 hash6 modules/helios-gui-framework (tag: v1.0.0)
 hash7 modules/helios-software-stack (tag: v1.0.0)
```

**Time:** 5-10 minutes (depends on connection)

---

### Option 2: Clone Then Initialize Submodules

**Best for:** Existing clones, partial setups

```bash
# Step 1: Clone main repository without submodules
git clone https://github.com/M0nado/helios-platform.git
cd helios-platform

# Step 2: Initialize all submodules
git submodule update --init

# Step 3: Recursively fetch all nested submodules
git submodule update --init --recursive

# Step 4: Verify initialization
git submodule status
```

**Alternative with foreach:**
```bash
# After Step 1, initialize each submodule individually
git submodule foreach 'git fetch origin'
```

**Time:** 3-8 minutes

---

### Option 3: Clone Specific Submodule Only

**Best for:** Isolated testing, specific component work

```bash
# Example: Clone just Security Setup
mkdir -p modules
git clone --depth 1 https://github.com/M0nado/helios-security-setup.git modules/helios-security-setup

# Or: Add existing submodule from registered URL
git clone --depth 1 https://github.com/M0nado/helios-platform.git
cd helios-platform
git submodule update --init -- modules/helios-security-setup

# Verify
ls -la modules/helios-security-setup
```

**Use shallow clone for faster network:**
```bash
git clone --depth 1 --recurse-submodules https://github.com/M0nado/helios-platform.git
```

**Time:** 30-60 seconds per module

---

## 🔄 Synchronization Commands

### Sync All Submodules to Latest

```bash
# Update all submodules to latest remote version
git pull --recurse-submodules

# Alternative: Sequential update
git pull
git submodule update --remote

# Verbose output
git pull --recurse-submodules -v
```

### Sync Specific Submodule

```bash
# Navigate to submodule and pull
cd modules/helios-security-setup
git pull origin main

# Or from parent:
git submodule update --remote -- modules/helios-security-setup
```

### Sync to Specific Tag/Branch

```bash
# Update all to specific branch
git submodule foreach 'git checkout main'

# Update specific submodule to tag
cd modules/helios-ai-hub
git checkout v2.0.0

# Or with foreach for all
git submodule foreach 'git checkout v1.0.0'
```

### Check What Changed

```bash
# See submodule differences
git diff --submodule

# Show detailed submodule changes
git diff --submodule=diff

# Between branches
git diff main develop -- modules/

# Status of all submodules
git submodule foreach 'git status'
```

---

## 🔧 Update Procedures

### Update All Submodules to Latest

**Full workflow:**
```bash
# 1. Save current state (backup)
git stash
git tag backup-$(date +%Y%m%d-%H%M%S)

# 2. Fetch all updates from remote
git fetch --all

# 3. Update each submodule
git submodule update --init --recursive --remote

# 4. Verify updates
git submodule status
git log --oneline modules/ -10

# 5. Commit changes
git add modules/
git commit -m "Update all submodules to latest versions"
git push
```

### Rolling Update (One at a Time)

**For safer, testable updates:**

```bash
# Update Monado Blade first
cd modules/helios-monado-blade
git pull origin main
cd ../..
git add modules/helios-monado-blade
git commit -m "Update Monado Blade"
git push

# Then: Build Agents
cd modules/helios-build-agents
git pull origin main
# ... repeat pattern

# Then: Other modules in sequence
# Allows testing each update independently
```

### Update from Specific Tag

```bash
# Show available tags
git ls-remote --tags https://github.com/M0nado/helios-security-setup.git | head -20

# Update to specific tag
cd modules/helios-security-setup
git fetch origin tag v2.1.0
git checkout v2.1.0
cd ../..

# Commit
git add modules/helios-security-setup
git commit -m "Update helios-security-setup to v2.1.0"
```

### Merge Updates from Branch

```bash
# Example: Merge develop into main for a module
cd modules/helios-ai-hub
git checkout main
git pull origin main
git merge origin/develop
cd ../..

# Commit
git add modules/helios-ai-hub
git commit -m "Merge helios-ai-hub develop into main"
```

---

## 📊 Monitoring & Status

### Check Submodule Status

```bash
# Quick status
git submodule status

# Detailed foreach
git submodule foreach 'echo "=== $name ===" && git status'

# Show which branches each is on
git submodule foreach 'git branch -vv'

# Check for uncommitted changes
git submodule foreach 'git diff-index --quiet HEAD || echo "$name has changes"'
```

### View Submodule Commits

```bash
# Last commit per module
git submodule foreach 'git log -1 --oneline'

# Show new commits in each
git submodule foreach 'git log origin/main..HEAD'

# Full commit history for one module
git log --all -- modules/helios-build-agents
```

### Compare Versions

```bash
# Between two submodule versions
cd modules/helios-ai-hub
git diff v1.0.0 v2.0.0 --stat

# Check merge-base
git merge-base v1.0.0 v2.0.0

# List commits between versions
git log v1.0.0...v2.0.0 --oneline
```

---

## 🔍 Troubleshooting

### Issue: Submodules Not Cloned

**Problem:** After cloning, `modules/` is empty

**Solution:**
```bash
# Initialize all submodules
git submodule update --init --recursive

# Verify
ls modules/ | wc -l  # Should be 7
```

**Prevention:**
```bash
# Always use --recurse-submodules
git clone --recurse-submodules https://github.com/M0nado/helios-platform.git
```

---

### Issue: Submodule Detached HEAD

**Problem:** Submodule shows detached HEAD state
```
 abc1234 modules/helios-security-setup (detached HEAD)
```

**Solution:**
```bash
# Navigate and checkout branch
cd modules/helios-security-setup
git checkout main

# Or all at once
git submodule foreach 'git checkout main'

# Verify
git submodule status
```

**Prevention:** Submodules track specific commits by design; this is normal.

---

### Issue: Stale Submodule References

**Problem:** Submodule points to old commit

**Solution:**
```bash
# Update to latest remote
git submodule update --remote -- modules/helios-ai-hub

# Or update all
git submodule update --remote

# Verify updates
git diff modules/helios-ai-hub
```

---

### Issue: Conflicts in .gitmodules

**Problem:** Merge conflict in .gitmodules file

**Solution:**
```bash
# View conflict
cat .gitmodules | grep -A 3 -B 3 '<<<<<<<'

# Take version from one side
git checkout --ours .gitmodules   # Use yours
# OR
git checkout --theirs .gitmodules # Use theirs

# Stage resolution
git add .gitmodules
git commit -m "Resolve .gitmodules conflict"
git push
```

---

### Issue: Failed Update in One Submodule

**Problem:** One module fails to update, blocking others

**Solution:**
```bash
# Skip the failing module
git submodule update --init --recursive --filter='--not=helios-security-setup'

# OR: Update individually
cd modules/helios-ai-hub && git pull origin main && cd ../..
# Skip the failing one
cd modules/helios-build-agents && git pull origin main && cd ../..
# etc.

# Check what's wrong with failing module
cd modules/helios-security-setup
git status
git log -3 --oneline

# Debug
git pull origin main -v
git fetch origin -v
```

---

### Issue: Submodule Authentication Failed

**Problem:** Git asks for password/PAT repeatedly

**Solution:**
```bash
# Use SSH instead of HTTPS
cd modules/helios-security-setup
git remote set-url origin git@github.com:M0nado/helios-security-setup.git

# Or set credential caching
git config --global credential.helper store
git config --global credential.helper cache --timeout=3600

# Use GitHub Personal Access Token (if HTTPS required)
# Store in ~/.gitconfig
cat > ~/.gitconfig << 'EOF'
[credential]
    helper = store

[http]
    extraheader = AUTHORIZATION: bearer YOUR_PAT_HERE
EOF
```

---

### Issue: Submodule Out of Sync with Parent

**Problem:** Main repo updated but submodule references not

**Solution:**
```bash
# Check status
git status

# Should show submodule in "Changes not staged for commit"
# Update submodule references
git submodule update --remote
git add modules/
git commit -m "Update submodule references"

# Or force update
git fetch --all
git submodule foreach 'git fetch origin'
git submodule foreach 'git reset --hard origin/main'
```

---

### Issue: Large Clone Size

**Problem:** Clone taking too long or too much space

**Solution:**
```bash
# Use shallow clone (faster, smaller)
git clone --depth 1 --recurse-submodules https://github.com/M0nado/helios-platform.git

# Shallow submodules
git clone --recurse-submodules --depth 1 https://github.com/M0nado/helios-platform.git

# Single branch only
git clone --depth 1 --single-branch -b main --recurse-submodules https://github.com/M0nado/helios-platform.git

# Check size
du -sh helios-platform/
```

---

### Issue: Submodule Branch Tracking

**Problem:** Submodule not tracking latest from remote

**Solution:**
```bash
# Configure to track branch (not just commit)
git config -f .gitmodules submodule.modules/helios-ai-hub.branch main

# Apply to all
git submodule foreach 'git config branch.$(git rev-parse --abbrev-ref HEAD).merge refs/heads/main'

# Update and verify
git submodule update --remote
git submodule status
```

---

## 🛠️ Advanced Operations

### Push All Changes (Including Submodules)

```bash
# Push submodules first, then parent
git push --recurse-submodules=on-demand

# Or specify explicitly
git submodule foreach 'git push'
git push
```

### Delete & Reinitialize Submodule

```bash
# Remove submodule
git submodule deinit modules/helios-ai-hub
git rm modules/helios-ai-hub
git commit -m "Remove helios-ai-hub submodule"

# Re-add it
git submodule add -b main https://github.com/M0nado/helios-ai-hub.git modules/helios-ai-hub
git submodule update --init
git commit -m "Re-add helios-ai-hub submodule"
```

### Clone Specific Branch Only

```bash
# Clone with specific branch for all modules
git clone -b main --recurse-submodules https://github.com/M0nado/helios-platform.git

# Update all to develop branch
git submodule foreach 'git checkout develop'
```

### Verify All Submodule URLs

```bash
# Show all configured URLs
git config --file .gitmodules --get-regexp url

# Verify connectivity
git submodule foreach 'git ls-remote origin | head -3'

# Update URL if changed
git config -f .gitmodules submodule.modules/helios-ai-hub.url https://github.com/M0nado/helios-ai-hub.git
git submodule sync
```

### Backup Before Major Updates

```bash
# Create backup tag
git tag backup-before-update-$(date +%Y%m%d-%H%M%S)
git push --tags

# Or full snapshot
git submodule foreach 'git tag backup-$(date +%Y%m%d-%H%M%S)'

# Restore if needed
git checkout backup-20240101-120000
git submodule update --init --recursive
```

---

## 📋 Pre-Deployment Checklist

### Before Initial Deployment

- [ ] Clone with `--recurse-submodules`
- [ ] Verify all 7 modules present: `ls modules/ | wc -l` = 7
- [ ] Check submodule status: `git submodule status` (no `-` prefix)
- [ ] Verify branches: `git submodule foreach 'git branch -vv'`
- [ ] Check for uncommitted changes: `git status`
- [ ] Test authentication: `git submodule foreach 'git fetch'`

### Before Each Update

- [ ] Create backup tag: `git tag backup-before-$(date +%Y%m%d)`
- [ ] Review changes: `git diff --submodule`
- [ ] Check for conflicts: `git status`
- [ ] Stash local changes: `git stash`
- [ ] Update: `git pull --recurse-submodules`
- [ ] Verify: `git submodule status`

### After Update

- [ ] Run tests: `.scripts/verify-integration.ps1`
- [ ] Check deployment: `git log --oneline modules/ -5`
- [ ] Monitor health: Check dashboards
- [ ] Document changes: `git log --oneline HEAD~3..HEAD`

---

## 🚨 Emergency Procedures

### Rollback All Submodules to Previous Version

```bash
# List recent tags
git tag -l | tail -10

# Checkout backup
git checkout backup-before-20240101-120000

# Restore all submodules
git submodule update --init --recursive

# Verify
git submodule status
git log --oneline HEAD~3..HEAD
```

### Quick Health Check

```bash
# One-liner to verify all
git submodule status | wc -l  # Should be 7
git submodule status | grep -c '^-' # Should be 0 (no detached)
git submodule foreach 'git fetch origin'
echo "✅ All systems ready"
```

### Force Reset All Submodules

```bash
# Reset to HEAD
git submodule foreach 'git reset --hard HEAD'

# Remove all uncommitted changes
git clean -fd
git submodule foreach 'git clean -fd'

# Sync to remote main
git submodule foreach 'git checkout main'
git submodule foreach 'git pull origin main'
```

---

## 📈 Performance Optimization

### Faster Clones
```bash
# Use shallow clone + single branch
git clone --depth 1 --single-branch -b main --recurse-submodules https://github.com/M0nado/helios-platform.git

# Parallel submodule checkout
git clone --recurse-submodules -j 4 https://github.com/M0nado/helios-platform.git

# Disable LFS for speed (if available)
GIT_LFS_SKIP_SMUDGE=1 git clone --recurse-submodules https://github.com/M0nado/helios-platform.git
```

### Faster Updates
```bash
# Fetch all in parallel
git fetch --all -j 8

# Update submodules in parallel
git submodule foreach -P 4 'git pull origin main'

# Combine
git pull -j 8 --recurse-submodules
```

### Optimize Repository Size
```bash
# Garbage collection
git gc --aggressive

# Prune old objects
git prune

# Repack
git repack -ad

# Check size
du -sh .
```

---

## 📚 Reference Commands

### Quick Reference Table

| Task | Command |
|------|---------|
| Clone all | `git clone --recurse-submodules https://...` |
| Init submodules | `git submodule update --init --recursive` |
| Update all | `git pull --recurse-submodules` |
| Check status | `git submodule status` |
| Update one | `cd modules/X && git pull origin main` |
| See changes | `git diff --submodule` |
| Commit updates | `git add modules/ && git commit -m "..."` |
| Push all | `git push --recurse-submodules=on-demand` |
| Troubleshoot | `git submodule foreach 'git status'` |

---

## ✅ Verification Checklist

After any sync/update operation:

```bash
# Verify all submodules present
[ $(ls modules/ | wc -l) -eq 7 ] && echo "✅ All 7 modules present" || echo "❌ Missing modules"

# Verify no detached heads
[ $(git submodule status | grep -c '^-') -eq 0 ] && echo "✅ No detached HEADs" || echo "⚠️ Detached HEAD found"

# Verify latest branch
git submodule foreach 'git branch -v' | grep -c 'main'  # Should be 7

# Verify no uncommitted changes
git submodule status | grep -c ' -' || echo "✅ No uncommitted changes"

# All green
echo "✅ Ready for deployment"
```

---

## 🔗 Related Documentation

- **COMPONENT_INTEGRATION_GUIDE.md** - Detailed component specs
- **COMPONENT_USAGE_MATRIX.md** - Which components in which phases
- **COMPONENT_DEPLOYMENT_GUIDE.md** - Full deployment process
- **RELATED_REPOSITORIES.md** - Repository URLs and details

---

**Last Updated:** 2024  
**Status:** ✅ Complete  
**Tested:** Git 2.40+ with GitHub  
**Supported Platforms:** Windows, macOS, Linux
