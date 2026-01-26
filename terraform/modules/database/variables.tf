variable "name" {
  type        = string
  description = "Database instance identifier"
}

variable "engine" {
  type        = string
  default     = "postgres"
  description = "Database engine (postgres, mysql, mariadb)"
}

variable "engine_version" {
  type        = string
  default     = "15.4"
  description = "Database engine version"
}

variable "instance_class" {
  type        = string
  default     = "db.t3.micro"
  description = "RDS instance class"
}

variable "allocated_storage" {
  type        = number
  default     = 20
  description = "Initial storage in GB"
}

variable "max_allocated_storage" {
  type        = number
  default     = 100
  description = "Max storage for autoscaling in GB"
}

variable "db_name" {
  type        = string
  default     = "appdb"
  description = "Name of the database to create"
}

variable "username" {
  type        = string
  default     = "admin"
  description = "Master username"
}

variable "password" {
  type        = string
  sensitive   = true
  description = "Master password"
}

variable "security_group_ids" {
  type        = list(string)
  default     = []
  description = "VPC security group IDs"
}

variable "subnet_group_name" {
  type        = string
  default     = ""
  description = "DB subnet group name"
}

variable "publicly_accessible" {
  type        = bool
  default     = false
  description = "Whether the database is publicly accessible"
}

variable "backup_retention_period" {
  type        = number
  default     = 7
  description = "Backup retention period in days"
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