variable "resource_group_name" {
  description = "Resource group that contains the AKS cluster."
  type        = string
}

variable "cluster_name" {
  description = "AKS cluster name."
  type        = string
}

variable "azure_subscription_id" {
  description = "Azure subscription ID. Null uses the active Azure CLI subscription."
  type        = string
  default     = null
}

variable "argocd_chart_version" {
  description = "Argo CD Helm chart version."
  type        = string
  default     = "6.7.0"
}

variable "monitoring_chart_version" {
  description = "kube-prometheus-stack Helm chart version."
  type        = string
  default     = "56.21.0"
}

locals {
  subscription_command = var.azure_subscription_id == null ? "" : "az account set --subscription \"${var.azure_subscription_id}\""
}

resource "terraform_data" "cluster_addons" {
  triggers_replace = {
    cluster_name             = var.cluster_name
    resource_group_name      = var.resource_group_name
    azure_subscription_id    = coalesce(var.azure_subscription_id, "active-cli-subscription")
    argocd_chart_version     = var.argocd_chart_version
    monitoring_chart_version = var.monitoring_chart_version
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"]

    command = <<-EOT
      $ErrorActionPreference = "Stop"

      ${local.subscription_command}

      az aks get-credentials `
        --resource-group "${var.resource_group_name}" `
        --name "${var.cluster_name}" `
        --overwrite-existing

      helm repo add argo https://argoproj.github.io/argo-helm
      helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
      helm repo update

      helm upgrade --install argocd argo/argo-cd `
        --namespace argocd `
        --create-namespace `
        --version "${var.argocd_chart_version}" `
        --set server.service.type=ClusterIP `
        --wait `
        --timeout 10m

      helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack `
        --namespace monitoring `
        --create-namespace `
        --version "${var.monitoring_chart_version}" `
        --set grafana.service.type=ClusterIP `
        --set prometheus.service.type=ClusterIP `
        --set alertmanager.service.type=ClusterIP `
        --wait `
        --timeout 10m
    EOT
  }
}
