output "namespace_name" {
  value       = kubernetes_namespace.namespace.metadata[0].name
  description = "Namespace name"
}

output "namespace_uid" {
  value       = kubernetes_namespace.namespace.metadata[0].uid
  description = "Namespace UID"
}