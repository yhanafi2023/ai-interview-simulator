resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

# ─── database URL ───
resource "aws_secretsmanager_secret" "database_url" {
  name        = "${local.name_prefix}/database-url"
  description = "SQLAlchemy connection URL for the application database."

  # 0 = delete immediately on destroy. See the warning below.
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id = aws_secretsmanager_secret.database_url.id
  secret_string = format(
    "postgresql+psycopg://%s:%s@%s/%s",
    aws_db_instance.main.username,
    random_password.db.result,
    aws_db_instance.main.endpoint,
    aws_db_instance.main.db_name,
  )
}

# ─── JWT signing secret ───
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${local.name_prefix}/jwt-secret"
  description             = "HMAC key for signing access and refresh tokens."
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}

# ─── Anthropic API key ───
resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name                    = "${local.name_prefix}/anthropic-api-key"
  description             = "Anthropic API key used by the grading service."
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "anthropic_api_key" {
  secret_id     = aws_secretsmanager_secret.anthropic_api_key.id
  secret_string = var.anthropic_api_key
}