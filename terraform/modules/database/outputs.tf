output "endpoint" {
  value       = aws_db_instance.database.endpoint
  description = "Database endpoint"
}

output "address" {
  value       = aws_db_instance.database.address
  description = "Database hostname"
}

output "port" {
  value       = aws_db_instance.database.port
  description = "Database port"
}

output "db_name" {
  value       = aws_db_instance.database.db_name
  description = "Database name"
}

output "arn" {
  value       = aws_db_instance.database.arn
  description = "Database ARN"
}

output "id" {
  value       = aws_db_instance.database.id
  description = "Database instance ID"
}
