# HELIOS Platform - Version Compatibility Guide

Complete version management for all 7 components, compatibility matrix, update strategy, and breaking changes policy.

---

## 📌 Current Versions

### Component Versions

| Component | Current | Release Date | Status | Notes |
|-----------|---------|--------------|--------|-------|
| helios-monado-blade | 1.0.0 | 2024-01-15 | ✅ Stable | Pattern learning engine |
| helios-security-setup | 1.0.0 | 2024-01-15 | ✅ Stable | 8-layer security |
| helios-ai-hub | 1.0.0 | 2024-01-15 | ✅ Stable | AI orchestration |
| helios-dev-ai-hub | 1.0.0 | 2024-01-15 | ✅ Stable | Infrastructure config |
| helios-build-agents | 1.0.0 | 2024-01-15 | ✅ Stable | 11-agent system |
| helios-gui-framework | 1.0.0 | 2024-01-15 | ✅ Stable | 8-tab dashboard |
| helios-software-stack | 1.0.0 | 2024-01-15 | ✅ Stable | 40+ tool installer |
| **helios-platform** | 1.0.0 | 2024-01-15 | ✅ Stable | Main orchestrator |

### Dependency Versions

| Dependency | Min Version | Recommended | Latest | Platform |
|-----------|-------------|-------------|--------|----------|
| .NET | 7.0 | 8.0 | 9.0 | Windows/Linux |
| PowerShell | 7.0 | 7.4 | 7.5 | Windows/Linux |
| Python | 3.9 | 3.11 | 3.12 | Windows/Linux |
| Azure CLI | 2.40 | 2.55 | 2.60 | Windows/Linux |
| Docker | 20.10 | 24.0 | 25.0 | Windows/Linux |
| Git | 2.35 | 2.40 | 2.45 | Windows/Linux |
| Node.js | 14.0 | 18.0 | 20.0 | Windows/Linux |
| Terraform | 1.0 | 1.5 | 1.7 | Windows/Linux |
| Kubernetes | 1.24 | 1.28 | 1.30 | Linux |

---

## 🔀 Compatibility Matrix

### Component Compatibility Table

```
       │ Monado │ Security │ AI Hub │ Dev Hub │ Build │ GUI │ Software
───────┼────────┼──────────┼────────┼─────────┼───────┼─────┼──────────
1.0.0  │   ✅   │    ✅    │   ✅   │    ✅   │  ✅   │  ✅ │    ✅
1.1.0  │   ✅   │    ✅    │   ✅   │    ✅   │  ✅   │  ✅ │    ✅
1.2.0  │   ✅   │    ✅    │   ✅   │    ✅   │  ✅   │  ✅ │    ✅
2.0.0  │   ❌   │    ⚠️    │   ✅   │    ✅   │  ⚠️   │  ⚠️ │    ✅
```

### .NET Version Support

| Component | .NET 7 | .NET 8 | .NET 9 |
|-----------|--------|--------|--------|
| Dev AI Hub | ✅ | ✅ | ✅ |
| Build Agents | ✅ | ✅ | ⏳ |
| AI Hub | ✅ | ✅ | ⏳ |
| GUI Framework | ✅ | ✅ | ⏳ |
| Security Setup | ✅ | ✅ | ✅ |
| Monado Blade | ✅ | ✅ | ⏳ |
| Software Stack | ✅ | ✅ | ✅ |

### PowerShell Version Support

| Component | PS 7.0 | PS 7.4 | PS 7.5 |
|-----------|--------|--------|--------|
| Dev AI Hub | ✅ | ✅ | ✅ |
| Build Agents | ✅ | ✅ | ✅ |
| Security Setup | ✅ | ✅ | ✅ |
| Software Stack | ✅ | ✅ | ✅ |

### Azure Version Support

| Service | v2.40 | v2.50 | v2.55 | v2.60 |
|---------|-------|-------|-------|-------|
| Azure CLI | ✅ | ✅ | ✅ | ✅ |
| Azure PowerShell | ✅ | ✅ | ✅ | ✅ |
| Azure SDK | ✅ | ✅ | ✅ | ✅ |

### Docker Version Support

| Component | 20.10 | 24.0 | 25.0 |
|-----------|-------|------|------|
| Build Agents | ✅ | ✅ | ✅ |
| GUI Framework | ⚠️ | ✅ | ✅ |
| Software Stack | ✅ | ✅ | ✅ |

---

## 🔄 Update Strategy

### Update Policy

**Stability Levels:**
- **Stable (x.y.z)** - Production-ready, breaking changes prohibited
- **Beta (x.y.z-beta.n)** - Pre-release, use in testing only
- **Alpha (x.y.z-alpha.n)** - Development, use with caution
- **RC (x.y.z-rc.n)** - Release candidate, near-ready

### Version Numbering Scheme

```
Version: MAJOR.MINOR.PATCH[-PRERELEASE]

1.0.0
│ │ └─── PATCH: Bug fixes, patches
│ └───── MINOR: New features, backward compatible
└─────── MAJOR: Breaking changes
```

**Examples:**
- 1.0.0 → 1.0.1: Patch (backward compatible)
- 1.0.1 → 1.1.0: Minor (new features, backward compatible)
- 1.1.0 → 2.0.0: Major (breaking changes)

### Update Cadence

| Level | Frequency | Schedule | Notes |
|-------|-----------|----------|-------|
| Patch (z.y.z) | Weekly | Thursdays | Security fixes, bug patches |
| Minor (x.y.0) | Monthly | First Tuesday | New features, enhancements |
| Major (x.0.0) | Quarterly | Q1/Q2/Q3/Q4 | Breaking changes, major overhauls |

### Recommended Update Schedule

```
Phase 1 (Week 1)   → Patch updates only (.z increments)
Phase 2 (Month 1)  → Minor updates (.y increments)
Phase 3 (Quarter)  → Major planning (prepare for x.0.0)
Phase 4 (Q+1)      → Major update (x.0.0 release)
```

---

## 🚀 Update Procedures

### Check Current Versions

```bash
# All submodule versions
git submodule foreach 'echo "=== $name ===" && git describe --tags'

# Specific component
cd modules/helios-ai-hub
git describe --tags

# Show version from file
cat VERSION
cat package.json | grep version
cat .csproj | grep <Version>
```

### List Available Versions

```bash
# GitHub API
curl -s https://api.github.com/repos/M0nado/helios-ai-hub/releases | jq '.[] | .tag_name'

# Git tags
cd modules/helios-ai-hub
git fetch --tags
git tag -l | sort -V

# Show release notes
git show v1.1.0
```

### Update Single Component

**Step-by-step procedure:**

```bash
# 1. Check current version
cd modules/helios-security-setup
git describe --tags

# 2. See what changed
git fetch origin
git log HEAD...origin/main --oneline

# 3. Create branch for testing
git checkout -b update-v1.1.0

# 4. Update to version
git checkout v1.1.0

# 5. Test locally
npm test
dotnet test
pytest tests/

# 6. Return to parent directory
cd ../..

# 7. Verify in git status
git status

# 8. Commit update
git add modules/helios-security-setup
git commit -m "Update helios-security-setup to v1.1.0"

# 9. Push
git push
```

### Update All Components to Latest Patch

```bash
# All to latest patch version (e.g., v1.0.x)
git submodule foreach 'git fetch origin && git checkout $(git describe --tags --abbrev=0)'

# Verify updates
git submodule status

# Commit
git add modules/
git commit -m "Update all components to latest patch versions"
git push
```

### Staged Update (Safe for Production)

```bash
# Week 1: Update & test in dev
git submodule update --remote
git submodule foreach 'git checkout develop'
# Run full test suite here

# Week 2: Stage to staging environment
git checkout -b staging-release
git submodule foreach 'git checkout main'  # Or v1.1.0
git push -u origin staging-release
# Deploy to staging, run integration tests

# Week 3: Merge to production
git checkout main
git merge staging-release
git push
```

---

## ⚠️ Breaking Changes Policy

### Breaking Change Categories

**Level 1: Minor Breaking Changes**
- Deprecated API endpoints removed (warned 1 version prior)
- Configuration format changed (migration script provided)
- Default behavior changed (opt-in period available)
- Minor database schema change (auto-migration included)

**Action:** Update recommended (can skip 1 version)  
**Timeline:** Test before deployment

**Level 2: Major Breaking Changes**
- API incompatibility (requires code changes)
- Major database migration (requires manual action)
- Significant behavior change (operational impact)
- Dependency version bump (requires ecosystem update)

**Action:** Update required (skip not recommended)  
**Timeline:** Plan full deployment cycle

**Level 3: Critical Breaking Changes**
- Security vulnerability fix
- Core protocol change
- System architecture change
- Mandated compliance requirement

**Action:** Immediate update required  
**Timeline:** Emergency deployment procedure

### Breaking Changes in Major Versions

#### Version 2.0.0 Changes (Planned)
- [ ] Migrate from JSON to YAML configuration
- [ ] REST API v2 (v1 deprecated but supported)
- [ ] Python 3.12+ requirement (3.9-3.11 deprecated)
- [ ] Database schema overhaul

**Migration Path:**
1. Run `migrate-v2.ps1` script
2. Validate configuration
3. Test in staging
4. Deploy with 1-hour rollback window
5. Monitor for 24 hours

**Rollback:** `git checkout v1.9.0 && ./rollback.ps1`

---

## 🔐 Security Updates

### Security Update Priority

| Severity | CVSS | Response | Example |
|----------|------|----------|---------|
| Critical | 9.0-10.0 | 24-48 hours | RCE vulnerability |
| High | 7.0-8.9 | 1 week | Authentication bypass |
| Medium | 4.0-6.9 | 2 weeks | Privilege escalation |
| Low | 0.1-3.9 | 1 month | Information disclosure |

### Security Update Procedure

```bash
# 1. Detect vulnerability
# (From GitHub alerts or security advisory)

# 2. Emergency branch
git checkout -b security-fix/CVE-2024-1234

# 3. Apply patch
git submodule update --remote -- modules/helios-security-setup

# 4. Verify fix
npm audit
dotnet list package --vulnerable
pip check

# 5. Test thoroughly
npm test
dotnet test
pytest -v

# 6. Document CVE
echo "Fixes CVE-2024-1234: Remote Code Execution in AI Hub" >> SECURITY.md

# 7. Release patch version
git tag v1.0.1

# 8. Deploy immediately
git push
git push --tags
```

### Vulnerability Disclosure

**Report security issues:**
- Do NOT open public GitHub issues
- Email: security@helios-platform.io
- Include: Description, impact, reproduction steps
- Response time: 48 hours

---

## 📋 Dependency Compatibility

### Critical Dependencies

| Component | Dependency | Min | Max | Notes |
|-----------|-----------|-----|-----|-------|
| Dev AI Hub | .NET | 7.0 | 9.0 | Core runtime |
| Build Agents | Docker | 20.10 | 25.0 | Container engine |
| AI Hub | Node.js | 14.0 | 20.0 | Runtime |
| GUI Framework | React | 16.8 | 18.0 | UI framework |
| Security Setup | PowerShell | 7.0 | 7.5 | Scripting |
| Monado Blade | TensorFlow | 2.8 | 2.15 | ML framework |
| Software Stack | Python | 3.9 | 3.12 | Package management |

### Peer Dependencies

```
helios-platform (main)
├── requires helios-monado-blade@^1.0.0
├── requires helios-security-setup@^1.0.0
├── requires helios-ai-hub@^1.0.0
├── requires helios-dev-ai-hub@^1.0.0
├── requires helios-build-agents@^1.0.0
├── requires helios-gui-framework@^1.0.0
├── requires helios-software-stack@^1.0.0
├── requires .NET@^7.0
├── requires PowerShell@^7.0
├── requires Azure.CLI@^2.40
└── requires Docker@^20.10
```

---

## 🔍 Version Validation

### Pre-Update Checks

```bash
#!/bin/bash

echo "Version Compatibility Check"
echo "=========================="

# Check .NET version
dotnet --version
DOTNET_VER=$(dotnet --version | cut -d. -f1)
if [ "$DOTNET_VER" -lt 7 ]; then
    echo "❌ .NET version too old (require 7.0+)"
    exit 1
fi

# Check PowerShell
pwsh --version
# Check Azure CLI
az version

# Check Docker
docker --version

# Verify submodules
if [ $(ls modules/ | wc -l) -ne 7 ]; then
    echo "❌ Missing submodules"
    exit 1
fi

# Check component versions
echo "Component versions:"
git submodule foreach 'git describe --tags 2>/dev/null || echo "no tag"'

# All checks passed
echo "✅ All version checks passed"
```

### Post-Update Validation

```bash
# 1. Verify each component still accessible
git submodule foreach 'git fetch origin'

# 2. Run tests
npm test
dotnet test
pytest tests/

# 3. Check integrations
./scripts/verify-integration.ps1

# 4. Monitor for 24 hours
# Check logs, metrics, alerts
```

---

## 📊 Version Support Timeline

### Component Support Schedule

```
v1.0.0 (Jan 2024)  ├─ 12 months active support ─┤
v1.1.0 (Apr 2024)  ├─ 12 months active support ─┤
v1.2.0 (Jul 2024)  ├─ 12 months active support ─┤
v2.0.0 (Oct 2024)  ├─ 24 months active support ─┤

Legend:
├─────── Active support (bug fixes + features)
───┤ LTS support (security fixes only)
       EOL (no support)
```

### Supported Versions

| Version | Release | Active Until | EOL | Support Level |
|---------|---------|--------------|-----|---------------|
| 1.0.x | Jan 2024 | Jan 2025 | Jan 2025 | Stable |
| 1.1.x | Apr 2024 | Apr 2025 | Apr 2025 | Stable |
| 1.2.x | Jul 2024 | Jul 2025 | Jul 2025 | Stable |
| 2.0.x | Oct 2024 | Oct 2026 | Oct 2026 | LTS |

### Upgrade Path

```
1.0.0 → 1.0.1 (patch)         ✅ Auto-upgrade
1.0.1 → 1.1.0 (minor)         ✅ Recommended
1.1.0 → 1.2.0 (minor)         ✅ Recommended
1.2.0 → 2.0.0 (major)         ⚠️ Planning required
```

---

## ✅ Version Management Checklist

### Before Update
- [ ] Review changelog for breaking changes
- [ ] Back up current configuration
- [ ] Verify system resources available
- [ ] Schedule maintenance window
- [ ] Notify stakeholders

### During Update
- [ ] Stop all agents gracefully
- [ ] Update components sequentially
- [ ] Run validation tests
- [ ] Monitor dashboards
- [ ] Keep rollback plan ready

### After Update
- [ ] Verify all components running
- [ ] Run full 42-point verification
- [ ] Monitor for 24 hours
- [ ] Document changes made
- [ ] Update documentation

---

## 🔗 Related Documentation

- **COMPONENT_INTEGRATION_GUIDE.md** - Component details
- **COMPONENT_DEPLOYMENT_GUIDE.md** - Deployment procedures
- **MULTI_REPO_SYNC_GUIDE.md** - Git operations
- **COMPONENT_COMMUNICATION_GUIDE.md** - API versions

---

## 📞 Support

**Version Issues?**
- Check this guide first
- Review changelog: `git log --oneline v1.0.0..v1.1.0`
- Open issue with version details
- Contact support with reproduction steps

**Report Compatibility Issues:**
- Component + version affected
- Environment details
- Error messages
- Steps to reproduce

---

**Last Updated:** 2024  
**Status:** ✅ Complete  
**Versions Tracked:** 7 components + platform  
**Support Levels:** 4 (Active, LTS, EOL)  
**Next Major:** v2.0.0 (Oct 2024)
