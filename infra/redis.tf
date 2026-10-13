resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.name_prefix}-redis"
  subnet_ids = aws_subnet.public[*].id
}

resource "aws_elasticache_cluster" "main" {
  cluster_id = "${local.name_prefix}-redis"

  engine          = "redis"
  engine_version  = "7.1"
  node_type       = "cache.t4g.micro"
  num_cache_nodes = 1
  port            = 6379

  parameter_group_name = "default.redis7"

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  apply_immediately = true

  tags = {
    Name = "${local.name_prefix}-redis"
  }
}