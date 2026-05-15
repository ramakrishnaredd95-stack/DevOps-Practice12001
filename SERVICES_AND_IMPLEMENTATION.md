# AIOPS Services Architecture & Implementation Guide

## 📋 Complete Services List

### **Tier 1: Infrastructure Services (Azure)**

| Service                            | Type       | Purpose                    | Port | Cost (Daily) |
| ---------------------------------- | ---------- | -------------------------- | ---- | ------------ |
| **Azure Kubernetes Service (AKS)** | Compute    | Container orchestration    | -    | $10.50       |
| **Azure Container Registry (ACR)** | Storage    | Docker image registry      | -    | $0.50        |
| **Log Analytics Workspace**        | Monitoring | Log aggregation & querying | -    | $1.50        |
| **Virtual Network (VNet)**         | Networking | Network isolation          | -    | $0.20        |
| **Application Insights**           | Monitoring | App performance tracking   | -    | $0.15        |

---

### **Tier 2: Microservices (Running in AKS Pods)**

| Service             | Framework        | Purpose             | Port | Database   |
| ------------------- | ---------------- | ------------------- | ---- | ---------- |
| **Frontend**        | React/TypeScript | Web UI              | 3000 | -          |
| **API Gateway**     | Node.js/Express  | Request routing     | 3001 | -          |
| **Auth Service**    | Node.js/Express  | User authentication | 3002 | PostgreSQL |
| **Product Service** | Node.js/Express  | Product catalog     | 3003 | PostgreSQL |
| **Order Service**   | Node.js/Express  | Order processing    | 3004 | PostgreSQL |
| **Orders Service**  | Node.js/Express  | Order management    | 3005 | PostgreSQL |
| **User Service**    | Node.js/Express  | User management     | 3006 | PostgreSQL |

---

### **Tier 3: Data & Observability Services**

| Service        | Purpose                 | Port      | Type           |
| -------------- | ----------------------- | --------- | -------------- |
| **PostgreSQL** | Primary database        | 5432      | Data Store     |
| **Prometheus** | Metrics collection      | 9090      | Time-series DB |
| **Grafana**    | Dashboard visualization | 3007      | Visualization  |
| **ArgoCD**     | GitOps controller       | 8080/8443 | Deployment     |

---

### **Tier 4: AIOps Assistant Services (Azure Functions)**

| Function          | Purpose                   | Language | Trigger   |
| ----------------- | ------------------------- | -------- | --------- |
| **fetch-logs**    | Query Azure Log Analytics | Python   | HTTP POST |
| **fetch-metrics** | Query Prometheus metrics  | Python   | HTTP POST |
| **fetch-health**  | Check AKS cluster health  | Python   | HTTP POST |
| **Streamlit UI**  | Chat interface            | Python   | Web App   |

---

## 💰 Cost Analysis

### **Daily Cost Breakdown (USD)**

```
┌─────────────────────────────────────────┐
│ SERVICE COST ANALYSIS                   │
├─────────────────────────────────────────┤
│ AKS (3x Standard_D2s_v3)    $10.50     │
│ Log Analytics (100GB ingest) $1.50     │
│ ACR Standard (1 repository)  $0.50     │
│ Azure Functions (execution)  $0.30     │
│ Bandwidth/Data Transfer      $1.20     │
│ Application Insights         $0.10     │
├─────────────────────────────────────────┤
│ TOTAL DAILY:                 $14.10    │
│ TOTAL WEEKLY:                $98.70    │
│ TOTAL MONTHLY:              ~$423.00   │
└─────────────────────────────────────────┘
```

### **Cost Optimization Tips**

1. **Reduce AKS nodes** from 3 to 2: Saves $3.50/day
2. **Use B-series VMs** instead of D-series: Saves $5/day
3. **Enable auto-scaling**: Scales down during off-peak, saves 20-30%
4. **Spot instances for non-critical pods**: 70% discount
5. **Reserved instances (1-year)**: 20-30% discount on compute

**Optimized Monthly Cost: $250-300**

---

## 🚀 GitOps Implementation (ArgoCD)

### **Architecture Overview**

```
GitHub Repository (Source of Truth)
        ↓
        └─→ ArgoCD (Reconciliation)
            ├─→ Fetches manifests
            ├─→ Compares desired vs actual state
            └─→ Automatically syncs
                ├─→ AKS Cluster
                ├─→ Microservices
                └─→ Config/Secrets
```

### **Setup Steps**

#### **1. Install ArgoCD in Cluster**

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

#### **2. Configure Git Repository**

```yaml
# ArgoCD Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: boutique-apps
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/ai-devops
    targetRevision: main
    path: gitops/k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: boutique
  syncPolicy:
    automated:
      prune: true # Delete resources removed from git
      selfHeal: true # Auto-sync on cluster drift
    syncOptions:
      - CreateNamespace=true
```

#### **3. Repository Structure**

```
gitops/
├── namespace.yml              # Create boutique namespace
├── secrets.yml                # Database credentials
├── kustomization.yml          # Overlay management
└── k8s/
    ├── backend/
    │   ├── gateway-deployment.yml
    │   ├── auth-deployment.yml
    │   ├── product-deployment.yml
    │   ├── order-deployment.yml
    │   └── kustomization.yml
    ├── frontend/
    │   ├── deployment.yml
    │   └── service.yml
    ├── database/
    │   ├── postgresql-statefulset.yml
    │   └── pvc.yml
    └── monitoring/
        ├── prometheus-configmap.yml
        ├── grafana-deployment.yml
        └── argocd-dashboard.yml
```

#### **4. Deployment Workflow**

```bash
# 1. Developer commits to main branch
git commit -am "Update product service image to v2.1"
git push origin main

# 2. ArgoCD detects change (within 3 minutes or trigger webhook)
# 3. ArgoCD applies new manifests
kubectl get applications -n argocd
kubectl get pods -n boutique

# 4. Monitor deployment
argocd app get boutique-apps
```

#### **5. Rollback Strategy**

```bash
# Revert to previous version
argocd app rollback boutique-apps 1

# Or revert in git
git revert HEAD
git push origin main
```

---

## 🔄 DevOps Implementation (Azure Pipelines)

### **CI/CD Pipeline Flow**

```
┌──────────────┐
│ Git Commit   │
└──────┬───────┘
       ↓
┌──────────────────────────────────────┐
│ Azure Pipelines Triggered            │
└──────┬───────────────────────────────┘
       ├→ [BUILD] Build Docker images
       ├→ [TEST] Run unit tests
       ├→ [PUSH] Push to ACR
       ├→ [DEPLOY] Deploy to AKS
       └→ [MONITOR] Health checks
```

### **Azure Pipelines YAML Configuration**

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - "projects/boutique-microservices/**"
      - "gitops/**"

pr:
  - main

pool:
  vmImage: "ubuntu-latest"

variables:
  REGISTRY_URL: myacr.azurecr.io
  IMAGE_REPO: boutique
  KUBERNETES_NAMESPACE: boutique
  AKS_CLUSTER: boutique-aks
  RESOURCE_GROUP: boutique-rg

stages:
  - stage: Build
    displayName: Build and Test
    jobs:
      - job: BuildImages
        displayName: Build Docker Images
        steps:
          - task: Docker@2
            displayName: Build Frontend
            inputs:
              command: build
              Dockerfile: "projects/boutique-microservices/frontend/Dockerfile"
              tags: |
                $(REGISTRY_URL)/$(IMAGE_REPO)-frontend:$(Build.BuildId)
                $(REGISTRY_URL)/$(IMAGE_REPO)-frontend:latest
              arguments: --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

          - task: Docker@2
            displayName: Build Gateway
            inputs:
              command: build
              Dockerfile: "projects/boutique-microservices/backend/services/gateway/Dockerfile"
              tags: |
                $(REGISTRY_URL)/$(IMAGE_REPO)-gateway:$(Build.BuildId)
                $(REGISTRY_URL)/$(IMAGE_REPO)-gateway:latest

          - task: Docker@2
            displayName: Build Auth Service
            inputs:
              command: build
              Dockerfile: "projects/boutique-microservices/backend/services/auth/Dockerfile"
              tags: |
                $(REGISTRY_URL)/$(IMAGE_REPO)-auth:$(Build.BuildId)

          - task: Docker@2
            displayName: Build Product Service
            inputs:
              command: build
              Dockerfile: "projects/boutique-microservices/backend/services/product-service/Dockerfile"
              tags: |
                $(REGISTRY_URL)/$(IMAGE_REPO)-product:$(Build.BuildId)

          - task: Docker@2
            displayName: Build Order Service
            inputs:
              command: build
              Dockerfile: "projects/boutique-microservices/backend/services/order-service/Dockerfile"
              tags: |
                $(REGISTRY_URL)/$(IMAGE_REPO)-order:$(Build.BuildId)

      - job: RunTests
        displayName: Run Unit Tests
        steps:
          - task: NodeTool@0
            inputs:
              versionSpec: "18.x"

          - script: |
              cd projects/boutique-microservices
              npm install
            displayName: Install Dependencies

          - script: |
              npm run test
            displayName: Run Tests
            continueOnError: true

  - stage: Push
    displayName: Push to ACR
    dependsOn: Build
    condition: succeeded()
    jobs:
      - job: PushImages
        steps:
          - task: AzureCLI@2
            displayName: Login to ACR
            inputs:
              azureSubscription: "Azure Connection"
              scriptType: "bash"
              scriptLocation: "inlineScript"
              inlineScript: |
                az acr login --name $(REGISTRY_URL)

          - task: Docker@2
            displayName: Push Frontend Image
            inputs:
              command: push
              repository: "$(IMAGE_REPO)-frontend"
              tags: |
                $(Build.BuildId)
                latest
              containerRegistry: "ACR Connection"

          - task: Docker@2
            displayName: Push Gateway Image
            inputs:
              command: push
              repository: "$(IMAGE_REPO)-gateway"
              tags: |
                $(Build.BuildId)
                latest
              containerRegistry: "ACR Connection"

          # Similar for other services...

  - stage: Deploy
    displayName: Deploy to AKS
    dependsOn: Push
    condition: succeeded()
    jobs:
      - job: DeployToAKS
        steps:
          - task: AzureCLI@2
            displayName: Get AKS Credentials
            inputs:
              azureSubscription: "Azure Connection"
              scriptType: "bash"
              scriptLocation: "inlineScript"
              inlineScript: |
                az aks get-credentials \
                  --resource-group $(RESOURCE_GROUP) \
                  --name $(AKS_CLUSTER)
                  --overwrite-existing

          - task: KubernetesManifest@0
            displayName: Deploy Microservices
            inputs:
              action: "deploy"
              kubernetesServiceConnection: "AKS Connection"
              namespace: "$(KUBERNETES_NAMESPACE)"
              manifests: |
                gitops/k8s/backend/gateway-deployment.yml
                gitops/k8s/backend/auth-deployment.yml
                gitops/k8s/backend/product-deployment.yml
              imagePullSecrets: "azure-acr-secret"

          - task: KubernetesManifest@0
            displayName: Deploy Frontend
            inputs:
              action: "deploy"
              kubernetesServiceConnection: "AKS Connection"
              namespace: "$(KUBERNETES_NAMESPACE)"
              manifests: |
                gitops/k8s/frontend/deployment.yml

          - script: |
              kubectl rollout status deployment/gateway -n $(KUBERNETES_NAMESPACE)
              kubectl rollout status deployment/frontend -n $(KUBERNETES_NAMESPACE)
            displayName: Wait for Rollout

  - stage: HealthCheck
    displayName: Health Checks
    dependsOn: Deploy
    condition: succeeded()
    jobs:
      - job: VerifyDeployment
        steps:
          - script: |
              kubectl get pods -n $(KUBERNETES_NAMESPACE)
              kubectl get svc -n $(KUBERNETES_NAMESPACE)
            displayName: Check Pods and Services

          - task: AzureCLI@2
            displayName: Run Health Check Function
            inputs:
              azureSubscription: "Azure Connection"
              scriptType: "bash"
              scriptLocation: "inlineScript"
              inlineScript: |
                curl -X POST https://$(FUNCTION_APP).azurewebsites.net/api/fetch-health \
                  -H "Content-Type: application/json" \
                  -d '{"parameters":[
                    {"name":"cluster_name","value":"$(AKS_CLUSTER)"},
                    {"name":"namespace","value":"$(KUBERNETES_NAMESPACE)"}
                  ]}'

  - stage: Notify
    displayName: Send Notifications
    dependsOn: HealthCheck
    condition: always()
    jobs:
      - job: NotifySlack
        steps:
          - task: SlackNotification@0
            inputs:
              SlackWebhook: "$(SLACK_WEBHOOK)"
              message: "Deployment completed"
```

### **Pipeline Configuration Steps**

```bash
# 1. Create Azure Pipeline
az pipelines create \
  --repository https://github.com/your-org/ai-devops \
  --branch main

# 2. Set GitHub secrets in Azure DevOps
# Variable Group: ACR Credentials
#   - REGISTRY_URL
#   - REGISTRY_USERNAME
#   - REGISTRY_PASSWORD

# 3. Set up Service Connections
# - Azure Subscription
# - Kubernetes
# - Container Registry

# 4. Run pipeline
az pipelines run --id <pipeline-id>
```

---

## 🔗 Integration: GitOps + DevOps Workflow

```
Developer Push
      ↓
GitHub Webhooks
      ↓
Azure Pipelines (CI/CD)
      ├→ Build & Test
      ├→ Push to ACR
      └→ Update image tag in Git
            ↓
    Commit to gitops branch
            ↓
      ArgoCD Detects Change
            ↓
      Compare Desired State
            ↓
    Sync to AKS Cluster
            ↓
  Deployment Complete ✓
```

---

## 📊 Monitoring & Cost Tracking

### **Azure Cost Management**

```bash
# View current costs
az costmanagement query create \
  --scope "/subscriptions/{subscriptionId}" \
  --timeframe MonthToDate \
  --granularity Daily

# Set budget alerts
az consumption budget create \
  --resource-group boutique-rg \
  --budget-name monthly-limit \
  --amount 500 \
  --category Cost \
  --time-grain Monthly
```

### **Daily Cost Report Script**

```bash
#!/bin/bash
# daily-cost-report.sh

RESOURCE_GROUP="boutique-rg"
TODAY=$(date +%Y-%m-%d)

echo "=== Cost Report for $TODAY ==="

# AKS Costs
AKS_COST=$(az billing statement show --query "properties.chargesBilledSeparately[?contains(properties.description, 'AKS')] | [0].amount" -o tsv)
echo "AKS: $AKS_COST"

# ACR Costs
ACR_COST=$(az billing statement show --query "properties.chargesBilledSeparately[?contains(properties.description, 'Container Registry')] | [0].amount" -o tsv)
echo "ACR: $ACR_COST"

# Log Analytics
LA_COST=$(az billing statement show --query "properties.chargesBilledSeparately[?contains(properties.description, 'Log Analytics')] | [0].amount" -o tsv)
echo "Log Analytics: $LA_COST"

echo "Total Daily Estimate: ~$14.10"
echo "Weekly Estimate: ~$98.70"
```

---

## ✅ Deployment Checklist

- [ ] Create Azure Resource Group
- [ ] Deploy Terraform infrastructure (AKS, ACR, VNet)
- [ ] Create Log Analytics Workspace
- [ ] Install ArgoCD in AKS cluster
- [ ] Create GitHub repository with gitops structure
- [ ] Set up Azure Pipelines with CI/CD
- [ ] Configure GitHub Secrets (ACR credentials)
- [ ] Deploy microservices via ArgoCD
- [ ] Deploy Azure Functions (fetch-logs, fetch-metrics, fetch-health)
- [ ] Set up cost budgets and alerts
- [ ] Configure monitoring (Prometheus, Grafana, Application Insights)
- [ ] Run health check tests
- [ ] Document runbooks

---

## 📚 Useful Commands

```bash
# Deploy infrastructure
terraform -chdir=projects/Infrastructure apply

# Check AKS cluster
kubectl cluster-info
kubectl get nodes

# Check ArgoCD applications
argocd app list
argocd app sync boutique-apps

# Check microservices
kubectl get deployment -n boutique
kubectl get pods -n boutique

# View logs
kubectl logs -f deployment/gateway -n boutique

# Deploy Azure Functions
FUNCTION_APP_NAME=aiops-functions ./deploy.sh

# Check daily costs
az billing statement show --query "properties.chargesBilledSeparately" --output table
```

---

## 🎯 Next Steps

1. **Week 1**: Infrastructure setup (Terraform + AKS)
2. **Week 2**: CI/CD pipeline (Azure Pipelines)
3. **Week 3**: GitOps (ArgoCD) setup
4. **Week 4**: Monitoring & cost optimization
5. **Week 5**: Production deployment & validation
