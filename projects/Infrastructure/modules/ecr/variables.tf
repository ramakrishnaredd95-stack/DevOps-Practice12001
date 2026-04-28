variable "acr_name" {
  description = "Globally unique Azure Container Registry name. Use only letters and numbers."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group where ACR is created."
  type        = string
}

variable "location" {
  description = "Azure region for ACR."
  type        = string
}

variable "sku" {
  description = "ACR SKU."
  type        = string
  default     = "Standard"
}

variable "admin_enabled" {
  description = "Whether to enable ACR admin credentials."
  type        = bool
  default     = false
}

variable "repositories" {
  description = "Logical container repositories expected to be pushed into ACR."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags applied to Azure resources."
  type        = map(string)
  default     = {}
}
