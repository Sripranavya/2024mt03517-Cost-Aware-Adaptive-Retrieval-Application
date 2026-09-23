# lab-budget environment

The **cheapest defensible architecture** — what a restricted college lab account
(AWS Academy Learner Lab, sandbox) can actually create and afford.

## What it provisions

| Module | Resource | Notes |
|--------|----------|-------|
| networking | VPC, public subnets, SGs | **No NAT gateway** (tasks use public IPs) |
| data | S3 (encrypted), DynamoDB on-demand | **No OpenSearch** — FAISS in-container |
| auth | Cognito user pool + app client | free tier |
| iam | least-privilege task role | scoped to specific ARNs |
| compute | ECR, ECS Fargate (0.25 vCPU/0.5 GB), ALB | single task |

No SQS/SNS, no OpenSearch, no observability dashboards — those live in the `full`
environment.

## Estimated cost

- Fargate 0.25/0.5 (1 task, 24×7): **~US$9/month**
- ALB: **~US$16/month**
- S3 + DynamoDB + Cognito + Bedrock: **~US$0–1/month** at demo volume

**Total ≈ US$25/month**, or near **US$0** if you set `desired_count = 0` when idle.

## Usage (human runs this — never the coding agent)

```bash
cd infra/terraform/environments/lab-budget
cp terraform.tfvars.example terraform.tfvars   # then edit
terraform init
terraform validate
terraform plan
# terraform apply   # only in your own restricted lab account
```
