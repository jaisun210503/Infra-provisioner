terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_s3_bucket" "bucket" {
  bucket = var.name

  tags = merge(var.tags, {
    Name        = var.name
    ManagedBy   = "infrautomater"
    RequestId   = var.request_id
    TeamId      = var.team_id
  })
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.bucket.id

  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "encryption" {
  bucket = aws_s3_bucket.bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "public_access" {
  bucket = aws_s3_bucket.bucket.id

  block_public_acls       = !var.public
  block_public_policy     = !var.public
  ignore_public_acls      = !var.public
  restrict_public_buckets = !var.public
}

resource "aws_s3_bucket_lifecycle_configuration" "lifecycle" {
  count  = var.lifecycle_enabled ? 1 : 0
  bucket = aws_s3_bucket.bucket.id

  rule {
    id     = "cleanup"
    status = "Enabled"

    expiration {
      days = var.lifecycle_expiration_days
    }
  }
}