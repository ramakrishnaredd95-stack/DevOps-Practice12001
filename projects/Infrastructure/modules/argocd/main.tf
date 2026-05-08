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
