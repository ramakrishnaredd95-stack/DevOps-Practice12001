#!/usr/bin/env bash
# =============================================================================
# AIOps Assistant - Azure setup script
#
# This prepares Azure access for the
# AIOps Azure Functions that read Log Analytics and query Prometheus.
#
# What it does:
#   1. Reads the current Azure subscription and tenant.
#   2. Finds the Log Analytics workspace used by AKS.
#   3. Creates or reuses an Azure AD application/service principal.
#   4. Grants the service principal Log Analytics Reader on the workspace.
#   5. Optionally writes app settings to an Azure Function App.
#
# Usage:
#   az login
#   chmod +x setup-iam.sh
#   ./setup-iam.sh
#
# Optional environment overrides:
#   RESOURCE_GROUP=boutique-rg
#   AKS_CLUSTER_NAME=boutique-aks
#   LOG_ANALYTICS_WORKSPACE_NAME=boutique-aks-logs
#   AIOPS_APP_NAME=aiops-functions-reader
#   FUNCTION_APP_NAME=<your-function-app-name>
#   PROMETHEUS_URL=http://<prometheus-loadbalancer>:9090
# =============================================================================

set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-boutique-rg}"
AKS_CLUSTER_NAME="${AKS_CLUSTER_NAME:-boutique-aks}"
LOG_ANALYTICS_WORKSPACE_NAME="${LOG_ANALYTICS_WORKSPACE_NAME:-${AKS_CLUSTER_NAME}-logs}"
AIOPS_APP_NAME="${AIOPS_APP_NAME:-aiops-functions-reader}"
FUNCTION_APP_NAME="${FUNCTION_APP_NAME:-}"
PROMETHEUS_URL="${PROMETHEUS_URL:-}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

require_command az

if ! az account show >/dev/null 2>&1; then
  echo "Azure CLI is not logged in. Run: az login"
  exit 1
fi

SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
TENANT_ID="$(az account show --query tenantId -o tsv)"

echo ""
echo "============================================="
echo " AIOps - Azure Setup"
echo " Subscription : $SUBSCRIPTION_ID"
echo " Tenant       : $TENANT_ID"
echo " Resource RG  : $RESOURCE_GROUP"
echo " AKS Cluster  : $AKS_CLUSTER_NAME"
echo " Log Workspace: $LOG_ANALYTICS_WORKSPACE_NAME"
echo "============================================="
echo ""

echo "[1/4] Checking Azure resources..."
WORKSPACE_ID="$(az monitor log-analytics workspace show \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$LOG_ANALYTICS_WORKSPACE_NAME" \
  --query customerId -o tsv)"

WORKSPACE_RESOURCE_ID="$(az monitor log-analytics workspace show \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$LOG_ANALYTICS_WORKSPACE_NAME" \
  --query id -o tsv)"

AKS_ID="$(az aks show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$AKS_CLUSTER_NAME" \
  --query id -o tsv)"

echo "  Found Log Analytics workspace: $WORKSPACE_ID"
echo "  Found AKS cluster: $AKS_ID"

echo ""
echo "[2/4] Creating or reusing service principal: $AIOPS_APP_NAME"
APP_ID="$(az ad app list --display-name "$AIOPS_APP_NAME" --query '[0].appId' -o tsv)"

if [ -z "$APP_ID" ]; then
  SP_OUTPUT="$(az ad sp create-for-rbac \
    --name "$AIOPS_APP_NAME" \
    --role "Log Analytics Reader" \
    --scopes "$WORKSPACE_RESOURCE_ID" \
    -o json)"
  CLIENT_ID="$(echo "$SP_OUTPUT" | tr -d '\r' | sed -n 's/.*"appId": "\([^"]*\)".*/\1/p')"
  CLIENT_SECRET="$(echo "$SP_OUTPUT" | tr -d '\r' | sed -n 's/.*"password": "\([^"]*\)".*/\1/p')"
  echo "  Created service principal: $CLIENT_ID"
else
  CLIENT_ID="$APP_ID"
  CLIENT_SECRET=""
  echo "  Reusing existing service principal: $CLIENT_ID"
fi

echo ""
echo "[3/4] Ensuring Log Analytics Reader role assignment..."
SP_OBJECT_ID="$(az ad sp show --id "$CLIENT_ID" --query id -o tsv)"

if az role assignment list \
  --assignee "$SP_OBJECT_ID" \
  --scope "$WORKSPACE_RESOURCE_ID" \
  --query "[?roleDefinitionName=='Log Analytics Reader']" -o tsv | grep -q .; then
  echo "  Role already assigned."
else
  az role assignment create \
    --assignee "$SP_OBJECT_ID" \
    --role "Log Analytics Reader" \
    --scope "$WORKSPACE_RESOURCE_ID" >/dev/null
  echo "  Assigned Log Analytics Reader."
fi

echo ""
echo "[4/4] Function App settings..."
if [ -n "$FUNCTION_APP_NAME" ]; then
  if [ -z "$CLIENT_SECRET" ]; then
    echo "  Existing service principal found, but no client secret is available."
    echo "  Create a new secret and set AZURE_CLIENT_SECRET manually:"
    echo "    az ad app credential reset --id $CLIENT_ID"
  else
    SETTINGS=(
      "LOG_ANALYTICS_WORKSPACE_ID=$WORKSPACE_ID"
      "AZURE_TENANT_ID=$TENANT_ID"
      "AZURE_CLIENT_ID=$CLIENT_ID"
      "AZURE_CLIENT_SECRET=$CLIENT_SECRET"
    )

    if [ -n "$PROMETHEUS_URL" ]; then
      SETTINGS+=("PROMETHEUS_URL=$PROMETHEUS_URL")
    fi

    az functionapp config appsettings set \
      --resource-group "$RESOURCE_GROUP" \
      --name "$FUNCTION_APP_NAME" \
      --settings "${SETTINGS[@]}" >/dev/null
    echo "  Updated app settings on Function App: $FUNCTION_APP_NAME"
  fi
else
  echo "  FUNCTION_APP_NAME is not set, so no app settings were written."
fi

echo ""
echo "============================================="
echo " Done"
echo "============================================="
echo ""
echo "Use these values in your Azure Function App settings:"
echo "  LOG_ANALYTICS_WORKSPACE_ID=$WORKSPACE_ID"
echo "  AZURE_TENANT_ID=$TENANT_ID"
echo "  AZURE_CLIENT_ID=$CLIENT_ID"
if [ -n "$CLIENT_SECRET" ]; then
  echo "  AZURE_CLIENT_SECRET=$CLIENT_SECRET"
else
  echo "  AZURE_CLIENT_SECRET=<create/reset a client secret for this app>"
fi
echo "  PROMETHEUS_URL=${PROMETHEUS_URL:-http://<prometheus-loadbalancer>:9090}"
echo ""
