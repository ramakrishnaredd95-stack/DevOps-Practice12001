azure_subscription_id = null
azure_region          = "eastus"
resource_group_name   = "boutique-rg"

vnet_name          = "boutique-vnet"
vnet_address_space = ["10.0.0.0/16"]
aks_subnet_name    = "aks"

subnets = [
  {
    name             = "aks"
    address_prefixes = ["10.0.1.0/24"]
  },
  {
    name             = "private"
    address_prefixes = ["10.0.2.0/24"]
  }
]

cluster_name        = "boutique-aks"
kubernetes_version  = null
node_pool_name      = "default"
node_count          = 3
vm_size             = "Standard_D2s_v3"
os_disk_size_gb     = 128
enable_auto_scaling = true
min_count           = 2
max_count           = 5

acr_name          = "boutiqueacr"
acr_sku           = "Standard"
acr_admin_enabled = false

repositories = [
  "frontend",
  "gateway",
  "auth",
  "order-service",
  "orders",
  "product-service",
  "user-service"
]

environment        = "dev"
log_retention_days = 30

tags = {
  Environment = "dev"
  ManagedBy   = "terraform"
  Project     = "boutique"
  Owner       = "devops-team"
}
