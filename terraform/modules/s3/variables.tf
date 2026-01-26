variable "name" {
  type        = string
  description = "S3 bucket name (must be globally unique)"
}

variable "public" {
  type        = bool
  default     = false
  description = "Whether the bucket allows public access"
}

variable "versioning_enabled" {
  type        = bool
  default     = true
  description = "Enable versioning"
}

variable "lifecycle_enabled" {
  type        = bool
  default     = false
  description = "Enable lifecycle rules"
}

variable "lifecycle_expiration_days" {
  type        = number
  default     = 90
  description = "Days until objects expire"
}

variable "request_id" {
  type        = string
  description = "Resource request ID from infrautomater"
}

variable "team_id" {
  type        = string
  description = "Team ID from infrautomater"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Additional tags"
}