# AIOPS Implementation Guide - Post GitOps Deployment

## 📋 Prerequisites Checklist

Before implementing AIOPS, verify all services are deployed:

```bash
# 1. Verify AKS Cluster is running
kubectl cluster-info
kubectl get nodes -o wide

# 2. Verify all microservices are deployed
kubectl get deployment -n boutique
kubectl get pods -n boutique

# 3. Verify ArgoCD is installed
kubectl get pods -n argocd
kubectl get applications -n argocd

# 4. Verify storage & databases
kubectl get pvc -n boutique
kubectl get statefulset -n boutique

# 5. Verify monitoring stack
kubectl get pods -n monitoring
```

**Expected Output:**

```
✓ AKS cluster: Active
✓ 7 microservices: Running
✓ ArgoCD: Ready
✓ PostgreSQL: Connected
✓ Prometheus: Scraping metrics
✓ Grafana: Ready
```

---

## 🚀 AIOPS Implementation Steps

### **STEP 1: Set Up Azure Access (IAM & Permissions)**

Run the setup script to create service principal for Azure Functions:

```bash
# Navigate to AIOPS directory
cd projects/aiops-assistant

# Make script executable
chmod +x setup-iam.sh

# Run setup with environment variables
RESOURCE_GROUP=boutique-rg \
AKS_CLUSTER_NAME=boutique-aks \
LOG_ANALYTICS_WORKSPACE_NAME=boutique-aks-logs \
AIOPS_APP_NAME=aiops-functions-reader \
FUNCTION_APP_NAME=aiops-functions-prod \
PROMETHEUS_URL=http://prometheus-service:9090 \
./setup-iam.sh
```

**What this script does:**

```
[1/4] Checking Azure resources
  ✓ Finds Log Analytics workspace ID
  ✓ Locates AKS cluster
  ✓ Identifies resource group

[2/4] Creating service principal
  ✓ Creates Azure AD app (aiops-functions-reader)
  ✓ Generates client credentials
  ✓ Stores client secret securely

[3/4] Assigning RBAC roles
  ✓ Grants "Log Analytics Reader" permission
  ✓ Creates role assignment

[4/4] Configuring Function App
  ✓ Writes credentials to Azure Function App settings
  ✓ Sets environment variables
```

**Output (save these values):**

```
Subscription ID: <your-subscription-id>
Tenant ID: <your-tenant-id>
LOG_ANALYTICS_WORKSPACE_ID: <workspace-guid>
AZURE_CLIENT_ID: <app-id>
AZURE_CLIENT_SECRET: <secret>
PROMETHEUS_URL: http://prometheus-service:9090
```

---

### **STEP 2: Create Azure Function App**

```bash
# Create Function App resource group (if not exists)
az group create --name aiops-functions-rg --location eastus

# Create storage account for Function App
az storage account create \
  --name aiopsstorage \
  --resource-group aiops-functions-rg \
  --location eastus \
  --sku Standard_LRS

# Create Function App
az functionapp create \
  --resource-group aiops-functions-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name aiops-functions-prod \
  --storage-account aiopsstorage
```

**Verify:**

```bash
az functionapp show \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod \
  --query "{Name: name, State: state, Runtime: functionAppConfig.runtime}"
```

---

### **STEP 3: Deploy Azure Functions**

#### **3.1 Deploy fetch-logs Function**

```bash
# Navigate to function directory
cd azure-functions/fetch-logs

# Update requirements
cat > requirements.txt << 'EOF'
azure-functions
azure-identity
azure-monitor-query
requests
EOF

# Deploy to Azure
func azure functionapp publish aiops-functions-prod --build remote

# Verify deployment
az functionapp function list \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod \
  --query "[?name=='fetch-logs']"
```

**Test the function:**

```bash
# Get function URL
FUNCTION_URL=$(az functionapp function show \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod \
  --function-name fetch-logs \
  --query invokeUrlTemplate -o tsv)

# Test with curl
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{
    "messageVersion": "1.0",
    "actionGroup": "aiops-azure-functions",
    "apiPath": "/fetch-logs",
    "httpMethod": "POST",
    "parameters": [
      {"name": "filter_pattern", "value": "ERROR"},
      {"name": "log_table", "value": "ContainerLog"},
      {"name": "hours_back", "value": "1"}
    ]
  }'
```

#### **3.2 Deploy fetch-metrics Function**

```bash
cd ../fetch-metrics

cat > requirements.txt << 'EOF'
azure-functions
requests
EOF

func azure functionapp publish aiops-functions-prod --build remote

# Verify
az functionapp function list \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod \
  --query "[?name=='fetch-metrics']"

# Test the function
FUNCTION_URL=$(az functionapp function show \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod \
  --function-name fetch-metrics \
  --query invokeUrlTemplate -o tsv)

curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{
    "messageVersion": "1.0",
    "apiPath": "/fetch-metrics",
    "parameters": [
      {"name": "metric_name", "value": "pod_cpu_utilization"},
      {"name": "namespace", "value": "boutique"},
      {"name": "hours_back", "value": "1"}
    ]
  }'
```

#### **3.3 Deploy fetch-health Function**

```bash
cd ../fetch-health

cat > requirements.txt << 'EOF'
azure-functions
requests
EOF

func azure functionapp publish aiops-functions-prod --build remote

# Test the function
FUNCTION_URL=$(az functionapp function show \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod \
  --function-name fetch-health \
  --query invokeUrlTemplate -o tsv)

curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{
    "messageVersion": "1.0",
    "apiPath": "/fetch-health",
    "parameters": [
      {"name": "cluster_name", "value": "boutique-aks"},
      {"name": "namespace", "value": "boutique"}
    ]
  }'
```

---

### **STEP 4: Configure Function App Settings**

```bash
# Set environment variables in Function App
az functionapp config appsettings set \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod \
  --settings \
    LOG_ANALYTICS_WORKSPACE_ID="<workspace-id>" \
    AZURE_TENANT_ID="<tenant-id>" \
    AZURE_CLIENT_ID="<client-id>" \
    AZURE_CLIENT_SECRET="<client-secret>" \
    PROMETHEUS_URL="http://prometheus-service:9090"

# Verify settings
az functionapp config appsettings list \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod
```

---

### **STEP 5: Get Function URLs for Streamlit UI**

```bash
# Get all function URLs
az functionapp function list \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod \
  --query "[].{Name: name, URL: invokeUrlTemplate}" -o table

# Save to environment file
cat > .env << 'EOF'
AZURE_FETCH_LOGS_URL=https://aiops-functions-prod.azurewebsites.net/api/fetch-logs
AZURE_FETCH_METRICS_URL=https://aiops-functions-prod.azurewebsites.net/api/fetch-metrics
AZURE_FETCH_HEALTH_URL=https://aiops-functions-prod.azurewebsites.net/api/fetch-health
AZURE_REGION=eastus
AKS_CLUSTER_NAME=boutique-aks
K8S_NAMESPACE=boutique
EOF
```

---

### **STEP 6: Deploy Streamlit UI (3 Options)**

#### **Option A: Local Development**

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with Function URLs from STEP 5

# Run Streamlit
streamlit run app.py

# Access at http://localhost:8501
```

#### **Option B: Azure App Service (Recommended for Production)**

```bash
# Create App Service Plan
az appservice plan create \
  --name aiops-ui-plan \
  --resource-group aiops-functions-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group aiops-functions-rg \
  --plan aiops-ui-plan \
  --name aiops-ui-prod \
  --runtime "PYTHON|3.11"

# Deploy Streamlit app
cd ../..
git push azure main  # If using git deployment

# Or use Azure CLI deployment
az webapp deployment source config-zip \
  --resource-group aiops-functions-rg \
  --name aiops-ui-prod \
  --src app.zip
```

#### **Option C: Docker in AKS (Most Scalable)**

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY .env .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF

# Build and push image
docker build -t boutiqueacr.azurecr.io/aiops-ui:latest .
docker push boutiqueacr.azurecr.io/aiops-ui:latest

# Create Kubernetes deployment
cat > k8s-deployment.yml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aiops-ui
  namespace: boutique
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aiops-ui
  template:
    metadata:
      labels:
        app: aiops-ui
    spec:
      imagePullSecrets:
        - name: azure-acr-secret
      containers:
        - name: aiops-ui
          image: boutiqueacr.azurecr.io/aiops-ui:latest
          ports:
            - containerPort: 8501
          env:
            - name: AZURE_FETCH_LOGS_URL
              valueFrom:
                configMapKeyRef:
                  name: aiops-config
                  key: AZURE_FETCH_LOGS_URL
            - name: AZURE_FETCH_METRICS_URL
              valueFrom:
                configMapKeyRef:
                  name: aiops-config
                  key: AZURE_FETCH_METRICS_URL
            - name: AZURE_FETCH_HEALTH_URL
              valueFrom:
                configMapKeyRef:
                  name: aiops-config
                  key: AZURE_FETCH_HEALTH_URL
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
  name: aiops-ui
  namespace: boutique
spec:
  type: LoadBalancer
  selector:
    app: aiops-ui
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8501
EOF

# Deploy
kubectl apply -f k8s-deployment.yml

# Create ConfigMap for URLs
kubectl create configmap aiops-config \
  -n boutique \
  --from-literal=AZURE_FETCH_LOGS_URL=https://aiops-functions-prod.azurewebsites.net/api/fetch-logs \
  --from-literal=AZURE_FETCH_METRICS_URL=https://aiops-functions-prod.azurewebsites.net/api/fetch-metrics \
  --from-literal=AZURE_FETCH_HEALTH_URL=https://aiops-functions-prod.azurewebsites.net/api/fetch-health
```

---

### **STEP 7: Configure Log Analytics for AKS**

Ensure AKS sends logs to Log Analytics:

```bash
# Check if monitoring agent is enabled
az aks show \
  --resource-group boutique-rg \
  --name boutique-aks \
  --query addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID

# If not enabled, enable it
az aks enable-addons \
  --resource-group boutique-rg \
  --name boutique-aks \
  --addons monitoring \
  --workspace-resource-id /subscriptions/<subscription-id>/resourcegroups/<rg>/providers/microsoft.operationalinsights/workspaces/<workspace-name>
```

---

### **STEP 8: Configure Prometheus to Scrape Metrics**

Create Prometheus scrape configuration:

```yaml
# Create ConfigMap for Prometheus
kubectl create configmap prometheus-config \
  -n monitoring \
  --from-literal=prometheus.yml='global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  - job_name: "kubernetes-pods"
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

  - job_name: "kube-state-metrics"
    static_configs:
      - targets: ["kube-state-metrics:8080"]
'

# Verify
kubectl get configmap -n monitoring
```

---

### **STEP 9: Test AIOPS Functions**

#### **Test 1: Generate Sample Data**

```bash
cd scripts

# Generate sample log query
python generate_sample_data.py --tool logs

# Generate sample metrics query
python generate_sample_data.py --tool metrics

# Generate sample health query
python generate_sample_data.py --tool health
```

#### **Test 2: Call Functions Directly**

```bash
# Test fetch-logs
curl -X POST https://aiops-functions-prod.azurewebsites.net/api/fetch-logs \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "messageVersion": "1.0",
  "actionGroup": "aiops-azure-functions",
  "apiPath": "/fetch-logs",
  "httpMethod": "POST",
  "parameters": [
    {"name": "filter_pattern", "value": "ERROR"},
    {"name": "hours_back", "value": "1"}
  ]
}
EOF

# Test fetch-metrics
curl -X POST https://aiops-functions-prod.azurewebsites.net/api/fetch-metrics \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "messageVersion": "1.0",
  "apiPath": "/fetch-metrics",
  "parameters": [
    {"name": "metric_name", "value": "pod_cpu_utilization"},
    {"name": "namespace", "value": "boutique"},
    {"name": "hours_back", "value": "1"}
  ]
}
EOF

# Test fetch-health
curl -X POST https://aiops-functions-prod.azurewebsites.net/api/fetch-health \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "messageVersion": "1.0",
  "apiPath": "/fetch-health",
  "parameters": [
    {"name": "cluster_name", "value": "boutique-aks"},
    {"name": "namespace", "value": "boutique"}
  ]
}
EOF
```

---

### **STEP 10: Access Streamlit UI and Test AIOPS**

#### **If running locally:**

```bash
# Open browser
http://localhost:8501

# Ask questions in chat:
- "क्या सभी pods healthy हैं?" (Are all pods healthy?)
- "CPU usage क्या है?" (What is CPU usage?)
- "Last hour में कितने errors आए?" (How many errors in last hour?)
```

#### **If running on Azure App Service:**

```bash
# Get URL
az webapp show \
  --resource-group aiops-functions-rg \
  --name aiops-ui-prod \
  --query defaultHostName

# Open in browser
https://<app-name>.azurewebsites.net
```

#### **If running in AKS:**

```bash
# Get LoadBalancer IP
kubectl get svc aiops-ui -n boutique

# Open in browser
http://<external-ip>:80
```

---

## 🧪 Testing Checklist

```bash
# Test 1: Verify all services are running
kubectl get pods -n boutique
# Expected: All pods running

# Test 2: Check function logs
az functionapp logs tail \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod

# Test 3: Verify Prometheus is scraping
kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring
# Open http://localhost:9090
# Go to Targets → Check "kubernetes-pods" is Up

# Test 4: Verify Log Analytics has data
az monitor log-analytics query \
  --resource-group boutique-rg \
  --workspace-name boutique-aks-logs \
  --analytics-query "ContainerLog | limit 10"

# Test 5: Test Streamlit UI
# Navigate to UI and ask questions
# Verify responses appear correctly
```

---

## 🔍 Monitoring AIOPS Performance

### **Monitor Function Execution**

```bash
# View function metrics
az monitor metrics list \
  --resource-group aiops-functions-rg \
  --resource-type "Microsoft.Web/sites" \
  --resource-namespace Microsoft.Web \
  --resource-names aiops-functions-prod \
  --metric "FunctionExecutionCount,FunctionExecutionUnits" \
  --interval PT1H
```

### **Monitor Streamlit UI**

```bash
# If running on Azure App Service
az monitor app-insights component show \
  --resource-group aiops-functions-rg \
  --app aiops-ui-prod

# View application insights
# Portal → App Service → Application Insights
```

### **Monitor Costs**

```bash
# Daily cost for AIOPS
az billing statement show \
  --subscription-id <subscription-id> \
  --query "properties.chargesBilledSeparately[?contains(description, 'Function App')]"
```

---

## 🐛 Troubleshooting

### **Issue: Functions returning 503 errors**

```bash
# Check function app logs
az functionapp logs tail \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod

# Check if environment variables are set
az functionapp config appsettings list \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod

# Verify Prometheus connectivity
kubectl exec -it <prometheus-pod> -n monitoring -- \
  curl http://localhost:9090/api/v1/status/config
```

### **Issue: No logs in Log Analytics**

```bash
# Verify monitoring agent is enabled
az aks show \
  --resource-group boutique-rg \
  --name boutique-aks \
  --query addonProfiles.omsagent.enabled

# Check if pods are sending logs
kubectl logs -n kube-system ds/omsagent --tail=50

# Test query directly
az monitor log-analytics query \
  --resource-group boutique-rg \
  --workspace-name boutique-aks-logs \
  --analytics-query "ContainerLog | count"
```

### **Issue: Streamlit UI not loading**

```bash
# Check pod logs
kubectl logs -f deployment/aiops-ui -n boutique

# Check network connectivity
kubectl exec -it <streamlit-pod> -n boutique -- \
  curl https://aiops-functions-prod.azurewebsites.net/api/fetch-health

# Verify environment variables
kubectl get deployment aiops-ui -n boutique -o yaml | grep -A 20 "env:"
```

---

## 📊 Post-Deployment Verification

Create a comprehensive verification script:

```bash
#!/bin/bash
# verify-aiops.sh

echo "=== AIOPS Verification Report ==="
echo ""

# 1. Check AKS cluster
echo "[1] AKS Cluster Status"
kubectl cluster-info
kubectl get nodes -o wide | awk '{print $1, $2, $3}'
echo ""

# 2. Check microservices
echo "[2] Microservices Status"
kubectl get deployment -n boutique
echo ""

# 3. Check AIOPS functions
echo "[3] Azure Functions Status"
az functionapp function list \
  --resource-group aiops-functions-rg \
  --name aiops-functions-prod \
  --query "[].{Name: name, URL: invokeUrlTemplate}" -o table
echo ""

# 4. Check Streamlit UI
echo "[4] Streamlit UI Status"
kubectl get svc aiops-ui -n boutique
kubectl get pods -l app=aiops-ui -n boutique
echo ""

# 5. Check monitoring
echo "[5] Monitoring Stack Status"
kubectl get pods -n monitoring
echo ""

# 6. Check Prometheus targets
echo "[6] Prometheus Targets"
echo "Prometheus URL: http://localhost:9090 (after port-forward)"
echo ""

echo "=== Verification Complete ==="
```

Run it:

```bash
chmod +x verify-aiops.sh
./verify-aiops.sh
```

---

## ✅ Next Steps After Deployment

1. **Week 1: Monitoring**
   - Set up Grafana dashboards for AIOPS metrics
   - Configure alerts for function failures
   - Monitor cost trends

2. **Week 2: Optimization**
   - Analyze AIOPS function execution times
   - Optimize KQL and PromQL queries
   - Scale Streamlit UI if needed

3. **Week 3: Integration**
   - Integrate AIOPS with Slack/Teams
   - Set up automated daily reports
   - Create runbooks based on AIOPS insights

4. **Week 4: Enhancement**
   - Add custom metrics collection
   - Build predictive alerts
   - Implement anomaly detection

---

## 📞 Support Resources

- **Azure Functions Docs**: https://learn.microsoft.com/en-us/azure/azure-functions/
- **Log Analytics KQL**: https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/
- **Prometheus PromQL**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Streamlit Docs**: https://docs.streamlit.io/

---

## Quick Reference Commands

```bash
# Deploy all AIOPS components
./setup-iam.sh && \
cd azure-functions && \
func azure functionapp publish aiops-functions-prod && \
cd .. && \
kubectl apply -f k8s-deployment.yml

# Check all AIOPS status
echo "=== Functions ===" && \
az functionapp function list --resource-group aiops-functions-rg --name aiops-functions-prod && \
echo "=== Streamlit ===" && \
kubectl get svc aiops-ui -n boutique && \
echo "=== Monitoring ===" && \
kubectl get pods -n monitoring

# Stream logs
kubectl logs -f deployment/aiops-ui -n boutique

# Port forward for UI testing
kubectl port-forward svc/aiops-ui 8501:8501 -n boutique
```
