output "cluster_name" {
  value       = azurerm_kubernetes_cluster.aks.name
  description = "Name of the AKS cluster."
}

output "cluster_id" {
  value       = azurerm_kubernetes_cluster.aks.id
  description = "ID of the AKS cluster."
}

output "cluster_endpoint" {
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].host
  description = "AKS API server endpoint."
}

output "cluster_certificate_authority_data" {
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate
  sensitive   = true
  description = "AKS cluster CA certificate data."
}

output "client_certificate" {
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate
  sensitive   = true
  description = "AKS client certificate."
}

output "client_key" {
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].client_key
  sensitive   = true
  description = "AKS client key."
}

output "kube_config_raw" {
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive   = true
  description = "Raw kubeconfig for the AKS cluster."
}

output "log_analytics_workspace_id" {
  value       = azurerm_log_analytics_workspace.main.id
  description = "ID of the AKS Log Analytics workspace."
}
