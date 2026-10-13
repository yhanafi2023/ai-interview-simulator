# Asks AWS which AZs this account can actually use in this region.
# A "data" block reads existing information; it never creates anything.
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  # Both required for RDS and ElastiCache endpoints to resolve by hostname.
  # Leaving enable_dns_hostnames off causes DNS failures in 14.5 that look
  # like connectivity problems and are miserable to debug.
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

# The VPC's door to the internet. Free, and does nothing until a route
# points traffic at it.
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-igw"
  }
}

resource "aws_subnet" "public" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  # Anything launched here gets a public IP automatically. This is what lets
  # Fargate tasks reach ECR and the Anthropic API without a NAT Gateway.
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name_prefix}-public-${data.aws_availability_zones.available.names[count.index]}"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-public-rt"
  }
}

# THE line that makes these subnets public.
# "Any destination I don't have a specific route for (0.0.0.0/0), send to the IGW."
resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

# A route table does nothing until subnets are attached to it.
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}