variable "azure_subscription_id" {
  description = "Azure subscription ID. Leave null to use the active Azure CLI subscription."
  type        = string
  default     = null
}

variable "azure_region" {
  description = "Azure region for resources."
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the Azure resource group."
  type        = string
}

variable "vnet_name" {
  description = "Name of the Azure virtual network."
  type        = string
}

variable "vnet_address_space" {
  description = "Address space for the Azure virtual network."
  type        = list(string)
}

variable "subnets" {
  description = "Subnets created inside the virtual network."
  type = list(object({
    name             = string
    address_prefixes = list(string)
  }))
}

variable "aks_subnet_name" {
  description = "Name of the subnet used by AKS."
  type        = string
}

variable "cluster_name" {
  description = "Name of the AKS cluster."
  type        = string
}

variable "kubernetes_version" {
  description = "AKS Kubernetes version. Null lets Azure choose the current supported default."
  type        = string
  default     = null
}

variable "node_pool_name" {
  description = "Name of the default AKS node pool."
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
  description = "Enable autoscaling for the default AKS node pool."
  type        = bool
  default     = true
}

variable "min_count" {
  description = "Minimum AKS node count when autoscaling is enabled."
  type        = number
  default     = 2
}

variable "max_count" {
  description = "Maximum AKS node count when autoscaling is enabled."
  type        = number
  default     = 5
}

variable "acr_name" {
  description = "Name of Azure Container Registry. Use only letters and numbers."
  type        = string
}

variable "acr_sku" {
  description = "SKU for Azure Container Registry."
  type        = string
  default     = "Standard"
}

variable "acr_admin_enabled" {
  description = "Enable ACR admin credentials. Keep false unless a legacy CI flow requires it."
  type        = bool
  default     = false
}

variable "deploy_cluster_addons" {
  description = "Deploy Kubernetes and Helm resources after the AKS cluster exists."
  type        = bool
  default     = false
}

variable "repositories" {
  description = "Logical container repositories expected to be pushed into ACR."
  type        = list(string)
  default = [
    "frontend",
    "gateway",
    "auth",
    "order-service",
    "orders",
    "product-service",
    "user-service"
  ]
}

variable "log_retention_days" {
  description = "Log Analytics retention in days."
  type        = number
  default     = 30
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Tags for all resources."
  type        = map(string)
  default = {
    Environment = "dev"
    ManagedBy   = "terraform"
    Project     = "boutique"
  }
}
