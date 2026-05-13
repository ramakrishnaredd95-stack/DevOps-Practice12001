variable "cluster_name" {
  description = "Name of the AKS cluster."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group where AKS is created."
  type        = string
}

variable "location" {
  description = "Azure region for AKS."
  type        = string
}

variable "dns_prefix" {
  description = "DNS prefix for the AKS API server."
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID used by the AKS node pool."
  type        = string
}

variable "acr_id" {
  description = "ACR ID to grant AcrPull to the AKS kubelet identity."
  type        = string
}

variable "kubernetes_version" {
  description = "AKS Kubernetes version. Null lets Azure choose the default supported version."
  type        = string
  default     = null
}

variable "node_pool_name" {
  description = "Default AKS node pool name."
  type        = string
  default     = "default"
}

variable "node_count" {
  description = "Desired number of AKS nodes when autoscaling is disabled."
  type        = number
  default     = 3
}

variable "vm_size" {
  description = "VM size for AKS nodes."
  type        = string
  default     = "Standard_D2s_v3"
}

variable "os_disk_size_gb" {
  description = "OS disk size in GB for AKS nodes."
  type        = number
  default     = 128
}

variable "enable_auto_scaling" {
  description = "Enable autoscaling for the default node pool."
  type        = bool
  default     = true
}

variable "min_count" {
  description = "Minimum node count when autoscaling is enabled."
  type        = number
  default     = 2
}

variable "max_count" {
  description = "Maximum node count when autoscaling is enabled."
  type        = number
  default     = 5
}

variable "max_surge" {
  description = "Max surge used during node pool upgrades."
  type        = string
  default     = "1"
}

variable "log_analytics_sku" {
  description = "Log Analytics workspace SKU."
  type        = string
  default     = "PerGB2018"
}

variable "log_retention_days" {
  description = "Log Analytics retention in days."
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags applied to Azure resources."
  type        = map(string)
  default     = {}
}
