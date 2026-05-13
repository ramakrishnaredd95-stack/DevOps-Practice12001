<<<<<<< HEAD
variable "aks_cluster" {
  description = "Optional AKS dependency marker. Addons are ordered from the root module with depends_on."
  type        = any
  default     = null
=======
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
>>>>>>> 1f105379fa083ff7352a1e8dbd180cf5024b433d
}
