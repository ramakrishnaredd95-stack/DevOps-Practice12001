output "vnet_id" {
  value       = azurerm_virtual_network.main.id
  description = "ID of the Azure virtual network."
}

output "subnet_ids" {
  value       = { for name, subnet in azurerm_subnet.subnets : name => subnet.id }
  description = "Subnet IDs keyed by subnet name."
}
