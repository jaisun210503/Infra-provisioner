terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

resource "kubernetes_namespace" "namespace" {
  metadata {
    name = var.name

    labels = merge(var.labels, {
      "managed-by" = "infrautomater"
      "request-id" = var.request_id
      "team-id"    = var.team_id
    })

    annotations = var.annotations
  }
}

resource "kubernetes_resource_quota" "quota" {
  count = var.quota_enabled ? 1 : 0

  metadata {
    name      = "${var.name}-quota"
    namespace = kubernetes_namespace.namespace.metadata[0].name
  }

  spec {
    hard = {
      "requests.cpu"    = var.quota_cpu_requests
      "requests.memory" = var.quota_memory_requests
      "limits.cpu"      = var.quota_cpu_limits
      "limits.memory"   = var.quota_memory_limits
      "pods"            = var.quota_pods
      "services"        = var.quota_services
    }
  }
}

resource "kubernetes_limit_range" "limits" {
  count = var.limit_range_enabled ? 1 : 0

  metadata {
    name      = "${var.name}-limits"
    namespace = kubernetes_namespace.namespace.metadata[0].name
  }

  spec {
    limit {
      type = "Container"

      default = {
        cpu    = var.default_cpu_limit
        memory = var.default_memory_limit
      }

      default_request = {
        cpu    = var.default_cpu_request
        memory = var.default_memory_request
      }
    }
  }
}

resource "kubernetes_network_policy" "deny_all" {
  count = var.network_policy_enabled ? 1 : 0

  metadata {
    name      = "${var.name}-deny-all"
    namespace = kubernetes_namespace.namespace.metadata[0].name
  }

  spec {
    pod_selector {}
    policy_types = ["Ingress", "Egress"]
  }
}