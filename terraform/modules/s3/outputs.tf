output "bucket_name" {
  value       = aws_s3_bucket.bucket.id
  description = "S3 bucket name"
}

output "bucket_arn" {
  value       = aws_s3_bucket.bucket.arn
  description = "S3 bucket ARN"
}

output "bucket_domain_name" {
  value       = aws_s3_bucket.bucket.bucket_domain_name
  description = "S3 bucket domain name"
}

output "bucket_regional_domain_name" {
  value       = aws_s3_bucket.bucket.bucket_regional_domain_name
  description = "S3 bucket regional domain name"
}
