output "acr_id" {
  value       = azurerm_container_registry.acr.id
  description = "ID of the Azure Container Registry."
}

output "login_server" {
  value       = azurerm_container_registry.acr.login_server
  description = "Azure Container Registry login server."
}

output "repository_urls" {
  value       = { for repo in var.repositories : repo => "${azurerm_container_registry.acr.login_server}/${repo}" }
  description = "Expected image repository URLs inside ACR."
}
