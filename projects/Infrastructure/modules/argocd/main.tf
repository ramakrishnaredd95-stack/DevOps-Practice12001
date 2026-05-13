<<<<<<< HEAD
resource "kubernetes_namespace_v1" "argocd" {

  metadata {
    name = "argocd"
  }
}

resource "kubernetes_namespace_v1" "monitoring" {

  metadata {
    name = "monitoring"
  }
}

terraform {
  required_providers {
    kubernetes = {
      source = "hashicorp/kubernetes"
    }
    helm = {
      source = "hashicorp/helm"
    }
  }
}

resource "helm_release" "argocd" {
  name       = "argocd"
  namespace  = kubernetes_namespace_v1.argocd.metadata[0].name
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = "6.7.0"

  create_namespace = false

  values = [
    yamlencode({
      server = {
        service = {
          type = "ClusterIP"
        }
      }
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.argocd
  ]
}

resource "helm_release" "monitoring" {
  name      = "kube-prometheus-stack"
  namespace = kubernetes_namespace_v1.monitoring.metadata[0].name

  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "56.21.0"

  timeout           = 1800
  wait              = true
  atomic            = true
  cleanup_on_fail   = true
  dependency_update = true
  create_namespace  = false

  values = [
    yamlencode({
      grafana = {
        service = {
          type = "ClusterIP"
        }
      }

      prometheus = {
        service = {
          type = "ClusterIP"
        }
      }

      alertmanager = {
        service = {
          type = "ClusterIP"
        }
      }
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.monitoring,
    helm_release.argocd
  ]
}
=======
resource "terraform_data" "cluster_addons" {
  triggers_replace = {
    cluster_name        = var.cluster_name
    resource_group_name = var.resource_group_name
    argocd_version      = var.argocd_chart_version
    monitoring_version  = var.monitoring_chart_version
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"]
    command     = <<-EOT
      $ErrorActionPreference = "Stop"

      az aks get-credentials --resource-group "${var.resource_group_name}" --name "${var.cluster_name}" --admin --overwrite-existing

      helm repo add argo https://argoproj.github.io/argo-helm --force-update
      helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update
      helm repo update

      kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
      kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

      helm upgrade --install argocd argo/argo-cd `
        --namespace argocd `
        --version "${var.argocd_chart_version}" `
        --set server.service.type=ClusterIP `
        --wait `
        --timeout 15m

      helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack `
        --namespace monitoring `
        --version "${var.monitoring_chart_version}" `
        --set grafana.service.type=ClusterIP `
        --set prometheus.service.type=ClusterIP `
        --set alertmanager.service.type=ClusterIP `
        --wait `
        --timeout 30m
    EOT
  }
}
>>>>>>> 1f105379fa083ff7352a1e8dbd180cf5024b433d
