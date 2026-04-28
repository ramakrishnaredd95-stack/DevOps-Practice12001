#!/bin/bash
# Script to convert AWS ECR image references to Azure Container Registry (ACR)

# Configuration
AZURE_REGISTRY="myacr.azurecr.io"  # Change to your ACR login server
AWS_ACCOUNT_ID="123456789012"       # Your AWS account ID
AWS_REGION="us-east-1"

# Find all k8s manifests and update image references
echo "Converting ECR references to ACR..."

for manifest in gitops/k8s/backend/*.yml gitops/k8s/frontend/*.yml gitops/k8s/database/*.yml; do
  if [ -f "$manifest" ]; then
    echo "Processing $manifest..."
    # Replace AWS ECR references with ACR references
    sed -i "s|${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/|${AZURE_REGISTRY}/|g" "$manifest"
  fi
done

# Create Azure imagePullSecret for ACR authentication
echo "Creating Azure Container Registry pull secret..."
kubectl create secret docker-registry azure-acr-secret \
  --docker-server="${AZURE_REGISTRY}" \
  --docker-username="<acr-username>" \
  --docker-password="<acr-password>" \
  --docker-email="your-email@example.com" \
  -n boutique

# Update all deployments to use the imagePullSecrets
echo "Adding imagePullSecret to manifests..."
for manifest in gitops/k8s/backend/*.yml gitops/k8s/frontend/*.yml; do
  if [ -f "$manifest" ]; then
    # Add imagePullSecrets section after spec
    sed -i '/spec:/a\      imagePullSecrets:\n        - name: azure-acr-secret' "$manifest"
  fi
done

echo "Conversion complete! Verify the manifests and push to GitOps repo."
