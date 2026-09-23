# Networking module

Provisions the network foundation:

- A VPC (`var.vpc_cidr`, default `10.20.0.0/16`).
- `var.az_count` public + private subnet pairs across availability zones.
- An internet gateway (public egress) and, when `enable_nat = true`, a single NAT
  gateway for private-subnet egress.
- Security groups implementing least-privilege flows:
  - ALB SG: inbound `443` from the internet only.
  - ECS SG: inbound `container_port` from the ALB SG only.

## Cost notes

- VPC, subnets, route tables, IGW, security groups: **no hourly charge**.
- **NAT gateway** (`enable_nat = true`): ~US$0.045/hour (~US$32/month) plus data
  processing. The `lab-budget` environment sets `enable_nat = false` to avoid
  this; the container reaches AWS APIs via public subnets / VPC endpoints instead.

Estimated cost: **~US$0/month** with `enable_nat = false`, **~US$32+/month** with
a NAT gateway.
