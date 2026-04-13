# GitHub Codespace Deployment Guide

Deploy your HELIOS Platform application directly from your GitHub Codespace environment.

## Prerequisites

Before deploying from Codespace:
- ✅ Codespace fully initialized (see CODESPACE_FIRST_STEPS.md)
- ✅ GitHub authenticated: `gh auth status`
- ✅ Azure authenticated: `az account show`
- ✅ Project builds successfully: `dotnet build`
- ✅ All tests pass: `dotnet test`

## Deployment Options

### Option 1: Deploy to Azure App Service

#### Step 1: Prepare Application

```powershell
# Build for production
dotnet publish -c Release -o release

# Verify build
Test-Path "release/"
```

#### Step 2: Create Azure Resources (if not existing)

```powershell
# Set variables
$resourceGroup = "helios-rg"
$appName = "helios-platform-app"
$region = "eastus"
$appServicePlan = "helios-app-plan"

# Create resource group
az group create `
  --name $resourceGroup `
  --location $region

# Create App Service plan
az appservice plan create `
  --name $appServicePlan `
  --resource-group $resourceGroup `
  --sku B2

# Create web app
az webapp create `
  --resource-group $resourceGroup `
  --plan $appServicePlan `
  --name $appName `
  --runtime "DOTNET|8.0"
```

#### Step 3: Deploy Application

**Method A: Using Azure CLI**
```powershell
az webapp up `
  --resource-group helios-rg `
  --name helios-platform-app `
  --plan helios-app-plan
```

**Method B: Using Zip Deploy**
```powershell
# Create deployment package
cd release
Compress-Archive -Path * -DestinationPath ../app.zip

# Deploy
az webapp deployment source config-zip `
  --resource-group helios-rg `
  --name helios-platform-app `
  --src ../app.zip
```

**Method C: Using GitHub Actions**
```powershell
# Check if workflow exists
gh workflow list

# Trigger deploy workflow manually
gh workflow run deploy.yml -f environment=production
```

#### Step 4: Verify Deployment

```powershell
# Get app URL
az webapp list `
  --resource-group helios-rg `
  --query "[].defaultHostName" `
  --output tsv

# Test endpoint
$appUrl = "https://helios-platform-app.azurewebsites.net"
Invoke-RestMethod "$appUrl/api/health" -Method Get
```

---

### Option 2: Deploy Docker Image to Azure Container Registry

#### Step 1: Build Docker Image

```powershell
# In Codespace terminal
docker build -t helios:latest .

# Verify image
docker images | Select-String "helios"
```

#### Step 2: Create Azure Container Registry (if needed)

```powershell
$registryName = "heliosregistry"
$resourceGroup = "helios-rg"

# Create registry
az acr create `
  --resource-group $resourceGroup `
  --name $registryName `
  --sku Basic
```

#### Step 3: Push to Registry

```powershell
# Login to registry
az acr login --name $registryName

# Tag image
$loginServer = "heliosregistry.azurecr.io"
docker tag helios:latest "$loginServer/helios:latest"
docker tag helios:latest "$loginServer/helios:$((Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmm'))"

# Push image
docker push "$loginServer/helios:latest"

# Verify
az acr repository list --name $registryName
```

#### Step 4: Deploy to Azure Container Instances

```powershell
# Deploy from registry
az container create `
  --resource-group helios-rg `
  --name helios-container `
  --image heliosregistry.azurecr.io/helios:latest `
  --cpu 2 `
  --memory 4 `
  --environment-variables HELIOS_ENV=production `
  --ports 80 443 `
  --registry-login-server heliosregistry.azurecr.io `
  --registry-username <username> `
  --registry-password <password>

# Get container IP
az container show `
  --resource-group helios-rg `
  --name helios-container `
  --query ipAddress.ip
```

---

### Option 3: Deploy to Kubernetes (AKS)

#### Step 1: Create AKS Cluster (if needed)

```powershell
$clusterName = "helios-aks"
$resourceGroup = "helios-rg"

az aks create `
  --resource-group $resourceGroup `
  --name $clusterName `
  --node-count 2 `
  --enable-managed-identity `
  --enable-addons monitoring
```

#### Step 2: Get Kubernetes Credentials

```powershell
az aks get-credentials `
  --resource-group helios-rg `
  --name helios-aks

# Verify connection
kubectl cluster-info
```

#### Step 3: Create Kubernetes Manifest

Create `k8s-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helios-platform
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: helios
  template:
    metadata:
      labels:
        app: helios
    spec:
      containers:
      - name: helios
        image: heliosregistry.azurecr.io/helios:latest
        ports:
        - containerPort: 5000
        env:
        - name: HELIOS_ENV
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: helios-service
spec:
  type: LoadBalancer
  selector:
    app: helios
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
```

#### Step 4: Deploy to AKS

```powershell
# Deploy
kubectl apply -f k8s-deployment.yaml

# Verify deployment
kubectl get deployments
kubectl get pods
kubectl get services

# Watch pods
kubectl logs deployment/helios-platform --follow
```

---

### Option 4: Deploy Using GitHub Actions Workflow

#### Step 1: Check Existing Workflow

```powershell
# List workflows
gh workflow list

# View workflow file
gh workflow list --limit 1
# Then: gh workflow view <workflow-id>
```

#### Step 2: Trigger Workflow from Codespace

```powershell
# Run workflow with inputs
gh workflow run deploy.yml `
  -f environment=production `
  -f region=eastus

# Monitor execution
gh run list --workflow=deploy.yml

# View logs
$runId = (gh run list --workflow=deploy.yml --limit 1 --json databaseId -q ".[0].databaseId")
gh run view $runId --log
```

#### Step 3: Wait for Completion

```powershell
# Poll status
do {
    $status = gh run list --workflow=deploy.yml --limit 1 --json status -q ".[0].status"
    Write-Host "Status: $status"
    if ($status -eq "completed") { break }
    Start-Sleep -Seconds 10
} while ($true)
```

#### Step 4: Check Deployment Result

```powershell
# Get final result
gh run view $runId --json conclusion
```

---

## Monitoring Deployment

### Check Deployment Status

#### Azure App Service
```powershell
# View deployment slots
az webapp deployment slot list `
  --resource-group helios-rg `
  --name helios-platform-app

# Check application settings
az webapp config appsettings list `
  --resource-group helios-rg `
  --name helios-platform-app
```

#### Azure Container Instances
```powershell
# View container status
az container show `
  --resource-group helios-rg `
  --name helios-container `
  --query "containers[0].instanceView.currentState"

# Stream logs
az container logs `
  --resource-group helios-rg `
  --name helios-container `
  --follow
```

#### Kubernetes
```powershell
# Get pod status
kubectl get pods

# Get pod logs
kubectl logs <pod-name>

# Describe pod (detailed info)
kubectl describe pod <pod-name>

# Watch pods in real-time
kubectl get pods --watch
```

### Monitor Application Health

```powershell
# Test API endpoint
$apiUrl = "https://helios-platform-app.azurewebsites.net"

# Health check
Invoke-RestMethod "$apiUrl/api/health" -Method Get

# Get metrics
Invoke-RestMethod "$apiUrl/api/metrics" -Method Get

# Check logs
$startTime = (Get-Date).AddHours(-1)
az monitor metrics list `
  --resource /subscriptions/<id>/resourceGroups/helios-rg/providers/Microsoft.Web/sites/helios-platform-app `
  --start-time $startTime
```

---

## Handling Deployment Failures

### Common Failure Scenarios

#### 1. Build Failures

```powershell
# Rebuild locally to test
dotnet clean
dotnet build -c Release

# If fails, view detailed errors
dotnet build -c Release --verbosity diagnostic

# Commit fix and retry deployment
git add .
git commit -m "Fix build issue"
git push
```

#### 2. Deployment Timeouts

```powershell
# Increase timeout (in workflow) or manually retry
gh workflow run deploy.yml \
  -f timeout=30  # minutes

# Or re-run failed deployment
$runId = (gh run list --limit 1 --json databaseId -q ".[0].databaseId")
gh run rerun $runId
```

#### 3. Insufficient Resources

**Azure App Service:**
```powershell
# Scale up app service plan
az appservice plan update `
  --resource-group helios-rg `
  --name helios-app-plan `
  --sku P1
```

**Kubernetes:**
```powershell
# Scale deployment
kubectl scale deployment helios-platform --replicas=3

# Or update resource requests
kubectl edit deployment helios-platform
# Increase memory/CPU limits
```

#### 4. Authentication/Permission Errors

```powershell
# Verify credentials
az account show

# Re-authenticate if needed
az logout
az login

# Check RBAC permissions
az role assignment list --assignee <user-object-id>
```

### Rollback Failed Deployment

#### Azure App Service
```powershell
# Swap with staging slot
az webapp deployment slot swap `
  --resource-group helios-rg `
  --name helios-platform-app `
  --slot staging
```

#### Kubernetes
```powershell
# Rollback to previous deployment
kubectl rollout undo deployment/helios-platform

# View rollout history
kubectl rollout history deployment/helios-platform
```

#### GitHub Actions
```powershell
# Re-deploy previous commit
git revert HEAD
git push

# Trigger deploy workflow
gh workflow run deploy.yml
```

---

## Deployment Best Practices

### Pre-Deployment Checklist
- [ ] All tests pass locally: `dotnet test`
- [ ] Code reviewed and approved
- [ ] CHANGELOG updated with version/changes
- [ ] Environment variables configured
- [ ] Database migrations ready (if applicable)
- [ ] Secrets stored in GitHub Settings → Secrets
- [ ] No hardcoded credentials in code

### During Deployment
- ✅ Monitor logs in real-time
- ✅ Check application health endpoints
- ✅ Verify database connectivity
- ✅ Test critical user flows
- ✅ Monitor error rates

### Post-Deployment
- [ ] Verify application is responding
- [ ] Check error logs for exceptions
- [ ] Confirm all services are communicating
- [ ] Test API endpoints manually
- [ ] Monitor application metrics
- [ ] Notify team of deployment

### Performance & Reliability

```powershell
# Enable autoscaling (Kubernetes)
kubectl autoscale deployment helios-platform `
  --min=2 --max=5 --cpu-percent=80

# Set resource limits
kubectl set resources deployment helios-platform `
  --requests=cpu=250m,memory=256Mi `
  --limits=cpu=500m,memory=512Mi

# Configure health checks
kubectl set probe deployment/helios-platform `
  --liveness --initial-delay-seconds=30 `
  --failure-threshold=3
```

---

## Environment-Specific Deployments

### Development Environment
```powershell
# Use 2-core Azure App Service
# Enable remote debugging
# Don't configure auto-scaling
```

### Staging Environment
```powershell
# Mirror production configuration
# Use same machine types
# Test deployment process
# Enable monitoring
```

### Production Environment
```powershell
# Use 4+ core machines
# Enable redundancy (multiple replicas)
# Configure auto-scaling based on metrics
# Enable comprehensive logging and alerts
# Use managed databases
```

---

## Continuous Deployment Setup

### Automatic Deployment on Push

**1. Create Workflow File** (`.github/workflows/deploy-on-push.yml`):
```yaml
name: Deploy on Push
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and Deploy
        run: |
          dotnet build -c Release
          dotnet test
          # Add deployment commands
```

**2. Enable Workflow**:
```powershell
gh workflow enable
```

**3. Verify Workflow**:
```powershell
gh workflow list
gh run list
```

---

## Cost Management

### Monitor Deployment Costs

```powershell
# Get resource costs
az cost management query --query-type "Usage" `
  --timeframe "MonthToDate" `
  --granularity "Daily"
```

### Optimize Costs

- Use B-series App Service plans (burstable, cheaper)
- Delete unused resources regularly
- Use spot instances for non-critical workloads
- Enable auto-shutdown for dev environments
- Use container instances only when needed

---

## Troubleshooting Deployments

### Can't Push to Registry

```powershell
# Verify login
az acr login --name $registryName

# Check credentials
az acr credential show --name $registryName

# Retry push
docker push $image
```

### Deployment Not Updating

```powershell
# Clear image cache
docker image prune -a

# Force pull latest
kubectl set image deployment/helios-platform \
  helios=heliosregistry.azurecr.io/helios:latest --record
```

### Application Crashes After Deployment

```powershell
# Check logs
kubectl logs <pod-name>

# Or for App Service
az webapp log tail --name helios-platform-app

# Rollback if necessary
kubectl rollout undo deployment/helios-platform
```

---

## Next Steps

1. **Monitor Application** - Check logs and metrics regularly
2. **Implement Alerts** - Set up notifications for failures
3. **Document Procedures** - Create runbooks for your team
4. **Automate More** - Add more workflows for testing/staging
5. **Plan Scaling** - Prepare for production growth

---

**For More Help:**
- 📖 See CODESPACE_FIRST_STEPS.md for pre-deployment setup
- 🆘 See CODESPACE_TROUBLESHOOTING.md for common issues
- 💰 See CODESPACE_LIMITS.md for cost considerations
- 📚 GitHub Actions Docs: https://docs.github.com/actions
