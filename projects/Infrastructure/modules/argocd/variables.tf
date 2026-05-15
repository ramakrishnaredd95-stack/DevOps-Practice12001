variable "aks_cluster" {
  description = "Optional AKS dependency marker. Addons are ordered from the root module with depends_on."
  type        = any
  default     = null
}

# modules/argocd/variables.tf
variable "aks_cluster_id" {
  description = "AKS cluster ID to enforce dependency"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group containing the AKS cluster."
  type        = string
}

variable "cluster_name" {
  description = "AKS cluster name."
  type        = string
}

variable "argocd_chart_version" {
  description = "ArgoCD Helm chart version."
  type        = string
  default     = "6.7.0"
}

variable "monitoring_chart_version" {
  description = "kube-prometheus-stack Helm chart version."
  type        = string
  default     = "56.21.0"
}
