variable "aks_cluster" {
  description = "Optional AKS dependency marker. Addons are ordered from the root module with depends_on."
  type        = any
  default     = null
}
