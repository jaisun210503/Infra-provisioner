terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_db_instance" "database" {
  identifier     = var.name
  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"

  db_name  = var.db_name
  username = var.username
  password = var.password

  vpc_security_group_ids = var.security_group_ids
  db_subnet_group_name   = var.subnet_group_name

  publicly_accessible    = var.publicly_accessible
  skip_final_snapshot    = true
  deletion_protection    = false

  backup_retention_period = var.backup_retention_period

  tags = merge(var.tags, {
    Name        = var.name
    ManagedBy   = "infrautomater"
    RequestId   = var.request_id
    TeamId      = var.team_id
  })
}