resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.azure_region
  tags     = var.tags
}

module "vnet" {
  source = "./modules/vnet"

  vnet_name           = var.vnet_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  address_space       = var.vnet_address_space
  subnets             = var.subnets
  tags                = var.tags
}

module "acr" {
  source = "./modules/acr"

  acr_name            = replace(var.acr_name, "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.acr_sku
  admin_enabled       = var.acr_admin_enabled
  repositories        = var.repositories
  tags                = var.tags
}

module "aks" {
  source = "./modules/aks"

  cluster_name        = var.cluster_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  dns_prefix          = var.cluster_name
  subnet_id           = module.vnet.subnet_ids[var.aks_subnet_name]
  acr_id              = module.acr.acr_id
  kubernetes_version  = var.kubernetes_version
  node_pool_name      = var.node_pool_name
  node_count          = var.node_count
  vm_size             = var.vm_size
  os_disk_size_gb     = var.os_disk_size_gb
  enable_auto_scaling = var.enable_auto_scaling
  min_count           = var.min_count
  max_count           = var.max_count
  log_retention_days  = var.log_retention_days
  tags                = var.tags
}

module "argocd" {
  source = "./modules/argocd"

  providers = {
    kubernetes = kubernetes.aks
    helm       = helm.aks
  }
  depends_on = [module.aks]

}
