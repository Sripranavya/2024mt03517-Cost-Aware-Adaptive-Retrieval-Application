# full environment

The **complete architecture** matching the dissertation's tech-stack slide. Use
only where the lab account has budget and permissions (creating IAM roles,
OpenSearch domains, NAT gateways, etc. — many student sandboxes block these).

## What it adds over `lab-budget`

| Module | Resource |
|--------|----------|
| networking | NAT gateway (private-subnet egress) |
| data | managed **OpenSearch** domain (encrypted, HTTPS) |
| messaging | **SQS** queue + DLQ, **SNS** topic |
| observability | CloudWatch **dashboard** + CPU/5xx **alarms** |
| compute | 0.5 vCPU / 1 GB, `desired_count = 2`, private subnets |

## Estimated cost (single-AZ demo sizing)

- Fargate 0.5/1.0 × 2 tasks: **~US$36/month**
- ALB: **~US$16/month**
- OpenSearch `t3.small.search` + 10 GB: **~US$26/month**
- NAT gateway: **~US$32/month**
- S3/DynamoDB/SQS/SNS/Cognito/CloudWatch: **~US$1–3/month**

**Total ≈ US$110–120/month.** Tear down with `terraform destroy` when not in use.

## Usage (human runs this — never the coding agent)

```bash
cd infra/terraform/environments/full
cp terraform.tfvars.example terraform.tfvars   # then edit
terraform init
terraform validate
terraform plan
# terraform apply   # only in an account you control
```
