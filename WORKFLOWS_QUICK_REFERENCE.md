# HELIOS Platform - Workflows Quick Reference Card

## 🎯 Quick Links

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [WORKFLOWS_COMPLETE_GUIDE.md](WORKFLOWS_COMPLETE_GUIDE.md) | Complete reference | 10 min |
| [WORKFLOW_EXECUTION_GUIDE.md](WORKFLOW_EXECUTION_GUIDE.md) | How to run workflows | 15 min |
| [WORKFLOW_TROUBLESHOOTING.md](WORKFLOW_TROUBLESHOOTING.md) | Problem solving | 5+ min (as needed) |
| [WORKFLOWS_VERIFICATION_REPORT.md](WORKFLOWS_VERIFICATION_REPORT.md) | Verification status | 5 min |

---

## 🚀 Quick Commands

### Setup
```bash
# Authenticate
gh auth login
gh auth status

# Configure secrets (do this first!)
gh secret set AZURE_SUBSCRIPTION_ID
gh secret set AZURE_TENANT_ID
gh secret set AZURE_CLIENT_ID
gh secret set AZURE_CLIENT_SECRET
gh secret set NUGET_API_KEY
```

### List Workflows
```bash
# Show all workflows
gh workflow list

# View specific workflow
gh workflow view deploy.yml
```

### Execute Workflows
```bash
# Full deployment
gh workflow run deploy.yml -f phase=all

# Specific phase
gh workflow run deploy.yml -f phase=preflight
gh workflow run deploy.yml -f phase=infrastructure

# Other workflows
gh workflow run quality.yml
gh workflow run verify.yml
gh workflow run analysis.yml

# NuGet build/publish
gh workflow run nuget.yml
# (Publishes on tag: git tag v1.0.0 && git push origin v1.0.0)
```

### Monitor
```bash
# List runs
gh run list

# Watch real-time
gh run watch RUN_ID --exit-status

# Get logs
gh run view RUN_ID --log

# Get job logs
gh run view RUN_ID --log --name "Job Name"

# Download artifacts
gh run download RUN_ID -n artifact-name

# Get status
gh run view RUN_ID
```

---

## 📋 Workflow Overview

### 1. Deploy Pipeline
- **File**: `.github/workflows/deploy.yml`
- **Trigger**: push, PR, manual
- **Phases**: 7 sequential
- **Duration**: ~35-102 minutes
- **Run**: `gh workflow run deploy.yml -f phase=all`

### 2. NuGet Package
- **File**: `.github/workflows/nuget.yml`
- **Trigger**: push to main, tag v*, manual
- **Jobs**: build → publish
- **Run**: `gh workflow run nuget.yml`
- **Publish**: `git tag v1.0.0 && git push origin v1.0.0`

### 3. Analysis
- **File**: `.github/workflows/analysis.yml`
- **Trigger**: path changes, schedule (weekly)
- **Purpose**: Metrics validation
- **Run**: `gh workflow run analysis.yml`

### 4. Quality
- **File**: `.github/workflows/quality.yml`
- **Trigger**: push, PR
- **Checks**: PowerShell, Markdown, JSON, Security
- **Run**: `gh workflow run quality.yml`

### 5. Verify
- **File**: `.github/workflows/verify.yml`
- **Trigger**: schedule (every 6h), manual
- **Checks**: 42-point verification
- **Run**: `gh workflow run verify.yml`

---

## 🔑 Required Secrets

```
AZURE_SUBSCRIPTION_ID  ← From Azure
AZURE_TENANT_ID        ← From Azure
AZURE_CLIENT_ID        ← From Azure
AZURE_CLIENT_SECRET    ← From Azure
NUGET_API_KEY          ← From nuget.org
```

---

## 🎬 Deploy Phases

| Phase | Name | Status | Duration | Next |
|-------|------|--------|----------|------|
| 0 | Pre-flight | ← Always first | 5 min | Infrastructure |
| 1 | Infrastructure | Depends on Phase 0 | 20 min | Agents |
| 2 | Agents | 6 agents, parallel | 15 min | AI Services |
| 3 | AI Services | Depends on Agents | 10 min | Security |
| 4 | Security | 8-layer framework | 15 min | Monitoring |
| 5 | Monitoring | 7 dashboards | 10 min | Verification |
| 6 | Verification | 42-point check | 15 min | Go-Live ✅ |
| N | Notify | Always (any result) | 1 min | Done |

---

## ⚠️ Common Issues & Quick Fixes

| Issue | Fix |
|-------|-----|
| Workflow not running | `git push` to main/develop, check branch config |
| Secrets not found | `gh secret list`, then `gh secret set NAME` |
| Workflow fails immediately | Check YAML syntax: `python3 -m yaml` |
| Phase skipped | Check previous phase passed in logs |
| Artifact not found | Verify path exists before workflow runs |
| Timeout | Increase `timeout-minutes` in job config |
| Azure auth fails | Check secrets are correct, not expired |
| NuGet publish fails | Ensure tag format `v*`, API key valid |

---

## 📊 Metrics at a Glance

| Metric | Count |
|--------|-------|
| Workflows | 5 |
| Jobs | 13 |
| Deployment Phases | 7 |
| Agents | 6 |
| AI Services | 6 |
| Security Layers | 8 |
| Verification Checks | 42 |
| Required Secrets | 5 |

---

## 🔍 Diagnostic Commands

```bash
# Check syntax locally
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))"

# Validate JSON
python3 -m json.tool COMPONENT_METRICS.json

# List recent runs
gh run list --limit 10

# Get specific run details
gh run view RUN_ID --json status,conclusion,name

# Search for errors
gh run view RUN_ID --log | grep -i error

# Test locally (if Act installed)
act -j preflight
act --dry-run
```

---

## 🎯 Execution Scenarios

### Scenario 1: Full Deployment
```bash
# Step 1: Code ready
git push origin main

# Step 2: (Optional) Verify quality passes
gh run watch $(gh run list --workflow quality.yml --jq '.[] | .id' --limit 1)

# Step 3: Trigger deployment
gh workflow run deploy.yml -f phase=all

# Step 4: Monitor
gh run watch $(gh run list --workflow deploy.yml --jq '.[] | .id' --limit 1) --exit-status

# Step 5: Check results
gh run download $(gh run list --workflow deploy.yml --jq '.[] | .id' --limit 1) -n deployment-report
```

### Scenario 2: Phase-by-Phase Deployment
```bash
# Run each phase individually
gh workflow run deploy.yml -f phase=preflight
# Wait for completion...
gh workflow run deploy.yml -f phase=infrastructure
# Wait for completion...
gh workflow run deploy.yml -f phase=agents
# etc.
```

### Scenario 3: Package Release
```bash
# 1. Prepare code
git add .
git commit -m "Release v1.0.0"

# 2. Tag release
git tag v1.0.0
git push origin v1.0.0

# 3. NuGet workflow runs automatically
gh run list --workflow nuget.yml

# 4. Verify release
gh release list
```

### Scenario 4: Emergency Verification
```bash
# Run immediate health check
gh workflow run verify.yml

# Monitor progress
gh run watch --exit-status $(gh run list --workflow verify.yml --jq '.[] | .id' --limit 1)

# Get results
gh run download $(gh run list --workflow verify.yml --jq '.[] | .id' --limit 1) -n health-report
cat health-report/health-report.md
```

---

## 📞 Support Resources

### Quick Answers
1. "How do I run a workflow?" → Read **WORKFLOW_EXECUTION_GUIDE.md**
2. "Workflow failed, what do I do?" → Check **WORKFLOW_TROUBLESHOOTING.md**
3. "What's in each workflow?" → Read **WORKFLOWS_COMPLETE_GUIDE.md**
4. "Is everything verified?" → Check **WORKFLOWS_VERIFICATION_REPORT.md**

### GitHub CLI Help
```bash
gh workflow --help
gh run --help
gh secret --help
```

### Official Docs
- GitHub Actions: https://docs.github.com/en/actions
- GitHub CLI: https://cli.github.com

---

## ✅ Pre-Deployment Checklist

- [ ] All secrets configured (`gh secret list`)
- [ ] GitHub CLI authenticated (`gh auth status`)
- [ ] Branch is main or develop
- [ ] Code committed and pushed
- [ ] Read WORKFLOWS_COMPLETE_GUIDE.md
- [ ] Quality checks pass
- [ ] Ready to deploy

---

## 🎉 Success Indicators

### Deploy Workflow Success
```
✅ All 7 phases completed
✅ Each phase showed "success"
✅ Artifacts uploaded
✅ Go-Live notification sent
```

### Quality Workflow Success
```
✅ All 4 jobs completed
✅ No errors in linting
✅ All JSON valid
✅ Security scan passed
```

### Verify Workflow Success
```
✅ Health check passed
✅ Metrics validation passed
✅ Status report generated
✅ All critical files present
```

---

## 📝 Notes

- All workflows logged and audited
- Artifacts retained per GitHub retention policy
- Failed jobs don't cascade (unless explicitly dependent)
- Manual phase selection for granular control
- Real-time monitoring available
- Log files for debugging

---

**Last Updated**: January 15, 2024  
**Status**: ✅ Production Ready  
**All Workflows**: Verified & Documented

