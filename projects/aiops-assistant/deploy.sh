#!/usr/bin/env bash
# =============================================================================
# AIOps Assistant - Azure Functions deployment script
#
# Publishes the three HTTP-triggered Azure Functions and prints the URLs needed
# by the Streamlit UI.
#
# Usage:
#   az login
#   FUNCTION_APP_NAME=<your-function-app-name> ./deploy.sh
#
# Optional environment overrides:
#   RESOURCE_GROUP=boutique-rg
#   PROMETHEUS_URL=http://<prometheus-loadbalancer>:9090
# =============================================================================

set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-boutique-rg}"
FUNCTION_APP_NAME="${FUNCTION_APP_NAME:-}"
PROMETHEUS_URL="${PROMETHEUS_URL:-}"

if [ -z "$FUNCTION_APP_NAME" ]; then
  echo "FUNCTION_APP_NAME is required."
  echo "Example: FUNCTION_APP_NAME=aiops-functions ./deploy.sh"
  exit 1
fi

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI is required."
  exit 1
fi

if ! command -v func >/dev/null 2>&1; then
  echo "Azure Functions Core Tools is required."
  exit 1
fi

if ! az account show >/dev/null 2>&1; then
  echo "Azure CLI is not logged in. Run: az login"
  exit 1
fi

echo ""
echo "============================================="
echo " AIOps - Azure Functions Deployment"
echo " Resource Group : $RESOURCE_GROUP"
echo " Function App   : $FUNCTION_APP_NAME"
echo "============================================="
echo ""

if [ -n "$PROMETHEUS_URL" ]; then
  echo "Updating PROMETHEUS_URL app setting..."
  az functionapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$FUNCTION_APP_NAME" \
    --settings "PROMETHEUS_URL=$PROMETHEUS_URL" >/dev/null
fi

echo "Publishing Azure Functions..."
(
  cd azure-functions
  func azure functionapp publish "$FUNCTION_APP_NAME"
)

BASE_URL="https://${FUNCTION_APP_NAME}.azurewebsites.net/api"

echo ""
echo "Done."
echo ""
echo "Add these values to .env for the Streamlit UI:"
echo "AZURE_FETCH_LOGS_URL=${BASE_URL}/fetch-logs"
echo "AZURE_FETCH_METRICS_URL=${BASE_URL}/fetch-metrics"
echo "AZURE_FETCH_HEALTH_URL=${BASE_URL}/fetch-health"
echo ""
