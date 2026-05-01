# AIOps Assistant - Kira

An Azure-focused SRE assistant for the boutique AKS deployment. Kira checks Azure Log Analytics, Prometheus metrics, and AKS workload health, then shows the evidence in a Streamlit chat UI.

## Architecture

```text
Streamlit UI (app.py)
      |
      v
Azure Functions
      |-- fetch-logs    -> Azure Log Analytics
      |-- fetch-metrics -> Prometheus
      `-- fetch-health  -> AKS workload health via Prometheus
```

## Prerequisites

- Azure CLI installed and logged in with `az login`
- AKS cluster from the Terraform Azure stack
- Log Analytics workspace connected to AKS
- Prometheus with kube-state-metrics available to the Azure Functions
- Azure Functions Core Tools if publishing from your machine
- Python 3.10+

## Step 1: Set Up Azure Access

Run the setup script:

```bash
chmod +x setup-iam.sh
./setup-iam.sh
```

Useful overrides:

```bash
RESOURCE_GROUP=boutique-rg \
AKS_CLUSTER_NAME=boutique-aks \
FUNCTION_APP_NAME=<your-function-app-name> \
PROMETHEUS_URL=http://<prometheus-loadbalancer>:9090 \
./setup-iam.sh
```

The script creates or reuses a service principal and grants it `Log Analytics Reader` on the workspace. If `FUNCTION_APP_NAME` is set, it also writes the required Function App settings.

## Step 2: Deploy Azure Functions

The Azure Function code lives in `azure-functions/`:

| Route | Folder | Purpose |
|---|---|---|
| `/api/fetch-logs` | `azure-functions/fetch-logs` | Query Azure Log Analytics |
| `/api/fetch-metrics` | `azure-functions/fetch-metrics` | Query Prometheus metrics |
| `/api/fetch-health` | `azure-functions/fetch-health` | Check AKS workload health |

Publish from the function folder:

```bash
cd azure-functions
func azure functionapp publish <your-function-app-name>
```

Required Function App settings:

```env
LOG_ANALYTICS_WORKSPACE_ID=<workspace-customer-id>
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<service-principal-client-id>
AZURE_CLIENT_SECRET=<service-principal-client-secret>
PROMETHEUS_URL=http://<prometheus-loadbalancer>:9090
```

## Step 3: Run the Streamlit UI

```bash
cp .env.example .env
```

Set these values:

```env
AZURE_FETCH_LOGS_URL=https://<app>.azurewebsites.net/api/fetch-logs
AZURE_FETCH_METRICS_URL=https://<app>.azurewebsites.net/api/fetch-metrics
AZURE_FETCH_HEALTH_URL=https://<app>.azurewebsites.net/api/fetch-health
AZURE_REGION=eastus
AKS_CLUSTER_NAME=boutique-aks
K8S_NAMESPACE=boutique
```

Install dependencies and start the UI:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

## Step 4: Test Function Payloads

Print a sample payload:

```bash
python scripts/generate_sample_data.py --tool logs
```

Call a deployed function:

```bash
python scripts/generate_sample_data.py \
  --tool health \
  --url https://<app>.azurewebsites.net/api/fetch-health
```

## Project Structure

```text
aiops-assistant/
|-- app.py                    # Streamlit chat UI for Azure Functions
|-- setup-iam.sh              # Azure RBAC and Function App settings setup
|-- requirements.txt          # Streamlit UI dependencies
|-- .env.example              # Local UI environment template
|-- azure-functions/
|   |-- fetch-logs/           # Azure Log Analytics query
|   |-- fetch-metrics/        # Prometheus metrics query
|   `-- fetch-health/         # AKS workload health check
|-- schemas/
|   |-- fetch_logs.json       # OpenAPI schema for fetch-logs
|   |-- fetch_metrics.json    # OpenAPI schema for fetch-metrics
|   `-- fetch_health.json     # OpenAPI schema for fetch-health
`-- scripts/
    `-- generate_sample_data.py
```

## Sample Questions

- Why are we seeing 503 errors?
- Is CPU usage high across the boutique services?
- Are all pods healthy?
- What errors happened in the last 2 hours?
- Is there a memory issue?

## Troubleshooting

### Azure Functions cannot query Log Analytics

Check that the Function App has these settings:

```bash
az functionapp config appsettings list \
  --resource-group boutique-rg \
  --name <your-function-app-name>
```

Also confirm the service principal has `Log Analytics Reader` on the workspace.

### Prometheus URL is unreachable

`fetch-metrics` and `fetch-health` call `PROMETHEUS_URL` directly. Make sure the Function App can reach that URL and that Prometheus allows inbound traffic from the Function App networking path.

### Streamlit shows NOT CONFIGURED

The UI needs all three Azure Function URLs in `.env`. Restart Streamlit after editing `.env`.

### No logs are returned

Confirm the table name used by `fetch-logs`. Some AKS setups use `ContainerLogV2` instead of `ContainerLog`.
