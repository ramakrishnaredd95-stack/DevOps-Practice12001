output "argocd_namespace" {
  value       = kubernetes_namespace_v1.argocd.metadata[0].name
  description = "Kubernetes namespace where ArgoCD is installed."
}

output "argocd_release_name" {
  value       = helm_release.argocd.name
  description = "Helm release name for ArgoCD."
}

output "argocd_release_status" {
  value       = helm_release.argocd.status
  description = "Current Terraform-known Helm release status for ArgoCD."
}

output "argocd_chart_version" {
  value       = helm_release.argocd.version
  description = "ArgoCD Helm chart version installed by this module."
}

output "argocd_server_service_name" {
  value       = "argocd-server"
  description = "ArgoCD server Kubernetes service name."
}

output "argocd_port_forward_command" {
  value       = "kubectl -n ${kubernetes_namespace_v1.argocd.metadata[0].name} port-forward svc/argocd-server 8080:443"
  description = "Command to open local access to the ArgoCD UI at https://localhost:8080."
}

output "monitoring_namespace" {
  value       = kubernetes_namespace_v1.monitoring.metadata[0].name
  description = "Kubernetes namespace where monitoring tools are installed."
}

output "monitoring_release_name" {
  value       = helm_release.monitoring.name
  description = "Helm release name for kube-prometheus-stack."
}

output "monitoring_release_status" {
  value       = helm_release.monitoring.status
  description = "Current Terraform-known Helm release status for kube-prometheus-stack."
}

output "monitoring_chart_version" {
  value       = helm_release.monitoring.version
  description = "kube-prometheus-stack Helm chart version installed by this module."
}

output "grafana_service_name" {
  value       = "kube-prometheus-stack-grafana"
  description = "Grafana Kubernetes service name created by kube-prometheus-stack."
}

output "grafana_port_forward_command" {
  value       = "kubectl -n ${kubernetes_namespace_v1.monitoring.metadata[0].name} port-forward svc/kube-prometheus-stack-grafana 3000:80"
  description = "Command to open local access to Grafana at http://localhost:3000."
}

output "grafana_admin_user" {
  value       = "admin"
  description = "Default Grafana admin username."
}

output "grafana_admin_password_command" {
  value       = "$encoded = kubectl -n ${kubernetes_namespace_v1.monitoring.metadata[0].name} get secret kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}'; [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded))"
  description = "PowerShell command to read the Grafana admin password from the Kubernetes secret after deployment."
}
