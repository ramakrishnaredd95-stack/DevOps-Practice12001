variable "resource_group_name" {
  description = "Azure resource group that contains the AKS cluster."
  type        = string
}

variable "cluster_name" {
  description = "AKS cluster name used for az aks get-credentials."
  type        = string
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
