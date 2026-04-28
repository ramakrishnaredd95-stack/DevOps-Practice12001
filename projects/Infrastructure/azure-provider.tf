terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}

provider "kubernetes" {
  alias                  = "aks"
  host                   = module.eks.cluster_endpoint
  client_certificate     = base64decode(module.eks.client_certificate)
  client_key             = base64decode(module.eks.client_key)
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
}

provider "helm" {
  alias = "aks"

  kubernetes {
    host                   = module.eks.cluster_endpoint
    client_certificate     = base64decode(module.eks.client_certificate)
    client_key             = base64decode(module.eks.client_key)
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  }
}
