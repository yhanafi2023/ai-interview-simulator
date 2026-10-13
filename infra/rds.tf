data "aws_kms_key" "rds" {
  key_id = "alias/aws/rds"
}
# Generated once and stored in state. Never typed, never in a file.
resource "random_password" "db" {
  length  = 32
  special = false # keeps the password safe to embed in a URL unescaped
}

# RDS requires a subnet group spanning 2+ AZs, even for a single-AZ instance.
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db"
  subnet_ids = aws_subnet.public[*].id

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${local.name_prefix}-postgres"

  engine         = "postgres"
  engine_version = "17" # major only; AWS selects the latest minor
  instance_class = "db.t4g.micro"

  allocated_storage = 20 # GB, the minimum for gp3
  storage_type      = "gp3"
  storage_encrypted = true
  kms_key_id        = data.aws_kms_key.rds.arn

  db_name  = "interview"
  username = "interview_app"
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # No public IP and no public DNS. See the note below — this is the
  # setting that keeps the database private despite the public subnet.
  publicly_accessible = false

  # ── Teardown-friendly settings. Deliberately wrong for production. ──
  multi_az                = false # no standby replica
  backup_retention_period = 0     # disables automated backups entirely
  skip_final_snapshot     = true  # destroy doesn't leave a billable snapshot
  deletion_protection     = false # destroy isn't blocked

  performance_insights_enabled = false
  apply_immediately            = true

  tags = {
    Name = "${local.name_prefix}-postgres"
  }
}