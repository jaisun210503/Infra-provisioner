variable "name" {
  type        = string
  description = "Namespace name"
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Additional labels"
}

variable "annotations" {
  type        = map(string)
  default     = {}
  description = "Namespace annotations"
}

variable "quota_enabled" {
  type        = bool
  default     = true
  description = "Enable resource quota"
}

variable "quota_cpu_requests" {
  type        = string
  default     = "2"
  description = "CPU requests quota"
}

variable "quota_memory_requests" {
  type        = string
  default     = "4Gi"
  description = "Memory requests quota"
}

variable "quota_cpu_limits" {
  type        = string
  default     = "4"
  description = "CPU limits quota"
}

variable "quota_memory_limits" {
  type        = string
  default     = "8Gi"
  description = "Memory limits quota"
}

variable "quota_pods" {
  type        = string
  default     = "20"
  description = "Max pods"
}

variable "quota_services" {
  type        = string
  default     = "10"
  description = "Max services"
}

variable "limit_range_enabled" {
  type        = bool
  default     = true
  description = "Enable limit range"
}

variable "default_cpu_limit" {
  type        = string
  default     = "500m"
  description = "Default CPU limit per container"
}

variable "default_memory_limit" {
  type        = string
  default     = "512Mi"
  description = "Default memory limit per container"
}

variable "default_cpu_request" {
  type        = string
  default     = "100m"
  description = "Default CPU request per container"
}

variable "default_memory_request" {
  type        = string
  default     = "128Mi"
  description = "Default memory request per container"
}

variable "network_policy_enabled" {
  type        = bool
  default     = false
  description = "Enable default deny network policy"
}

variable "request_id" {
  type        = string
  description = "Resource request ID from infrautomater"
}

variable "team_id" {
  type        = string
  description = "Team ID from infrautomater"
}