# AWS to Azure Migration Guide

This guide walks through the completed migration from AWS services to Azure services for the Boutique Microservices project.

## Overview of Changes

### 1. CI/CD Pipeline: AWS ECR → Azure Container Registry (ACR)

**File**: `.github/workflows/ci.yml`

**Changes**:

- ✅ Replaced AWS credentials with Azure Container Registry credentials
- ✅ Replaced `aws-actions/configure-aws-credentials` with Docker login to ACR
- ✅ Updated image registry from `<account>.dkr.ecr.<region>.amazonaws.com` to `<registry>.azurecr.io`
- ✅ Simplified manifest updates to use ACR registry

**Required GitHub Secrets**:

```
AZURE_REGISTRY_URL          # e.g., myacr.azurecr.io
AZURE_REGISTRY_USERNAME     # ACR admin username (from Settings > Access keys)
AZURE_REGISTRY_PASSWORD     # ACR admin password
```

### 2. Infrastructure: Terraform AWS → Azure

**New Files**:

- `projects/Infrastructure/azure-provider.tf` - Azure provider configuration
- `projects/Infrastructure/azure-variables.tf` - Azure-specific variables
- `projects/Infrastructure/azure-main.tf` - Main infrastructure resources
- `projects/Infrastructure/azure-outputs.tf` - Output values
- `projects/Infrastructure/azure-terraform.tfvars` - Configuration values

**Resources Deployed**:

- ✅ Azure Resource Group
- ✅ Azure Container Registry (ACR)
- ✅ Azure Kubernetes Service (AKS)
- ✅ Log Analytics Workspace (monitoring)
- ✅ ArgoCD (Helm chart installed in cluster)

**To Deploy**:

```bash
cd projects/Infrastructure

# Update azure-terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

### 3. Serverless Functions: AWS Lambda → Azure Functions

**Migrated Functions**:

#### fetch-logs

- **AWS**: CloudWatch Logs queries
- **Azure**: Log Analytics queries (KQL)
- **Location**: `projects/aiops-assistant/azure-functions/fetch-logs/`
- **Trigger**: HTTP POST

#### fetch-health

- **AWS**: EKS API + Prometheus queries
- **Azure**: AKS health + Prometheus queries (same approach)
- **Location**: `projects/aiops-assistant/azure-functions/fetch-health/`
- **Trigger**: HTTP POST

#### fetch-metrics

- **AWS**: CloudWatch metrics
- **Azure**: Prometheus metrics
- **Location**: `projects/aiops-assistant/azure-functions/fetch-metrics/`
- **Trigger**: HTTP POST

**Azure Functions Setup**:

```bash
cd projects/aiops-assistant/azure-functions

# Install dependencies
pip install -r requirements.txt

# Deploy to Azure
func azure functionapp publish <function-app-name>
```

### 4. Kubernetes Manifests: Update Image References

**Example Conversions**:

- Before: `123456789012.dkr.ecr.us-east-1.amazonaws.com/orders:tag`
- After: `boutiqueacr.azurecr.io/orders:tag`

**Sample Files**:

- `gitops/k8s/backend/orders-azure.yml` - Example backend service
- `gitops/k8s/frontend/deployment-azure.yml` - Example frontend service

**Automation Script**:

```bash
bash gitops/convert-to-acr.sh
```

**Manual Updates**:

1. Add `imagePullSecrets` section to pod specs:

```yaml
spec:
  imagePullSecrets:
    - name: azure-acr-secret
  containers: [...]
```

2. Create the secret in your cluster:

```bash
kubectl create secret docker-registry azure-acr-secret \
  --docker-server=myacr.azurecr.io \
  --docker-username=<username> \
  --docker-password=<password> \
  -n boutique
```

## Deployment Steps

### Step 1: Deploy Infrastructure

```bash
cd projects/Infrastructure
terraform apply -var-file=azure-terraform.tfvars
```

### Step 2: Configure kubectl

```bash
az aks get-credentials \
  --resource-group boutique-rg \
  --name boutique-aks
```

### Step 3: Create Secrets and ConfigMaps

```bash
kubectl apply -f gitops/secrets.yml
kubectl apply -f gitops/namespace.yml
```

### Step 4: Deploy ArgoCD and Applications

```bash
# ArgoCD is deployed by Terraform, configure it via UI or CLI
# Then update GitOps config to point to -azure.yml manifests
```

### Step 5: Deploy Azure Functions

```bash
cd projects/aiops-assistant/azure-functions
func azure functionapp publish <app-name>
```

### Step 6: Update CI/CD Pipeline

- Push changes to `.github/workflows/ci.yml`
- Set GitHub secrets for Azure Container Registry

## Monitoring & Diagnostics

### Azure Monitor

- Log Analytics Workspace: `boutique-aks-logs`
- View logs: Azure Portal > Log Analytics > Query

### Prometheus & Grafana

- Still used for metrics collection
- Configure Prometheus to scrape AKS metrics
- Deploy via Helm in k8s/

### Azure Container Registry

- Monitor images: `az acr repository list --resource-group boutique-rg --name boutiqueacr`
- View image tags: `az acr repository show-tags --resource-group boutique-rg --name boutiqueacr --repository <image-name>`

## Environment Variables for Azure Functions

Set these in Azure Function App Configuration:

```
PROMETHEUS_URL=http://<prometheus-service>:9090
LOG_ANALYTICS_WORKSPACE_ID=<workspace-id>
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<client-id>
AZURE_CLIENT_SECRET=<client-secret>
```

## Rollback Plan

If you need to rollback to AWS:

1. Revert the CI/CD workflow to original version
2. Keep existing manifests in `gitops/k8s/backend/` (non-azure)
3. Redeploy using original Terraform AWS configuration

## Common Issues

### Issue: ImagePullBackOff errors

**Solution**: Verify the image registry credentials and secret creation

```bash
kubectl get secret azure-acr-secret -n boutique -o yaml
```

### Issue: AKS can't pull from ACR

**Solution**: Verify role assignment (RBAC)

```bash
az role assignment list --resource-group boutique-rg
```

### Issue: Azure Functions not responding

**Solution**: Check Application Insights logs

```bash
az functionapp logs streaming --name <function-app-name> --resource-group boutique-rg
```

## Next Steps

1. ✅ Convert CI/CD pipeline
2. ✅ Deploy Azure infrastructure
3. ✅ Migrate Lambda functions
4. ⏳ Update Kubernetes manifests (in progress)
5. ⏳ Test end-to-end deployment
6. ⏳ Configure monitoring and alerts
7. ⏳ Document runbooks and troubleshooting

## Support

For issues or questions:

- Azure Documentation: https://docs.microsoft.com/azure/
- Terraform Azure Provider: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs
- Azure Functions: https://docs.microsoft.com/azure/azure-functions/
