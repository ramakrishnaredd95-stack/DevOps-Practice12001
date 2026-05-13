output "resource_group_name" {
  value       = azurerm_resource_group.main.name
  description = "Name of the Azure resource group."
}

output "vnet_id" {
  value       = module.vnet.vnet_id
  description = "ID of the Azure virtual network."
}

output "subnet_ids" {
  value       = module.vnet.subnet_ids
  description = "Subnet IDs keyed by subnet name."
}

output "aks_cluster_name" {
  value       = module.aks.cluster_name
  description = "Name of the AKS cluster."
}

output "aks_cluster_id" {
  value       = module.aks.cluster_id
  description = "ID of the AKS cluster."
}

output "aks_cluster_endpoint" {
  value       = nonsensitive(module.aks.cluster_endpoint)
  description = "AKS API server endpoint."
}

output "kube_config" {
  value       = module.aks.kube_config_raw
  sensitive   = true
  description = "Kubernetes config for kubectl."
}

output "acr_login_server" {
  value       = module.acr.login_server
  description = "Azure Container Registry login server."
}

output "acr_repository_urls" {
  value       = module.acr.repository_urls
  description = "Expected image repository URLs inside ACR."
}

output "log_analytics_workspace_id" {
  value       = module.aks.log_analytics_workspace_id
  description = "ID of Log Analytics workspace for monitoring."
}
