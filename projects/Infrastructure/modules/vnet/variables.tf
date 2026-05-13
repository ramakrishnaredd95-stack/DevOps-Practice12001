variable "vnet_name" {
  description = "Azure virtual network name."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group where the virtual network is created."
  type        = string
}

variable "location" {
  description = "Azure region for the virtual network."
  type        = string
}

variable "address_space" {
  description = "Address space for the virtual network."
  type        = list(string)
}

variable "subnets" {
  description = "Subnets to create inside the virtual network."
  type = list(object({
    name             = string
    address_prefixes = list(string)
  }))
}

variable "tags" {
  description = "Tags applied to Azure resources."
  type        = map(string)
  default     = {}
}
