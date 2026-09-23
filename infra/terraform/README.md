# Infrastructure as Code (Terraform)

> **The coding agent generates these files; it never runs `terraform apply`.**
> A human applies them manually in a restricted college-lab AWS account, following
> the usage sections below.

## Layout

```
infra/terraform/
├── modules/
│   ├── networking/     # VPC, subnets, NAT (optional), security groups
│   ├── data/           # S3, DynamoDB, optional OpenSearch (encrypted at rest)
│   ├── iam/            # least-privilege task/execution roles (ARN-scoped)
│   ├── compute/        # ECR, ECS Fargate, ALB (HTTPS only)
│   ├── auth/           # Cognito user pool + app client
│   ├── messaging/      # SQS (+ DLQ) and SNS
│   └── observability/  # CloudWatch dashboard + alarms
└── environments/
    ├── lab-budget/     # cheapest defensible architecture (~US$25/mo)
    └── full/           # complete architecture (~US$110/mo)
```

Each module has its own `README.md` describing what it provisions and its
estimated cost.

## Environments

| | lab-budget | full |
|--|-----------|------|
| Fargate | 0.25 vCPU / 0.5 GB | 0.5 vCPU / 1 GB ×2 |
| Vector search | FAISS in-container | managed OpenSearch |
| NAT gateway | ✗ (public subnets) | ✓ |
| SQS / SNS | ✗ | ✓ |
| Cognito | ✓ | ✓ |
| Observability | ✗ | dashboard + alarms |
| Est. monthly cost | ~US$25 | ~US$110 |

## Usage (human-run)

```bash
cd infra/terraform/environments/lab-budget   # or full
cp terraform.tfvars.example terraform.tfvars  # then edit values
terraform init
terraform fmt -check -recursive ../../
terraform validate
terraform plan
# terraform apply    # ONLY in an AWS account you control
```

Both environments pass `terraform validate` (verified in CI). State files,
`.terraform/`, and lock files are git-ignored — never commit them.

## Security properties baked in

- **Least-privilege IAM** — every policy statement is scoped to a specific
  resource ARN; no `Resource: "*"` except inside the AWS-managed execution policy.
- **Encryption at rest** — S3 (SSE-KMS/AES256 + versioning + public access block),
  DynamoDB (SSE + PITR), OpenSearch (at-rest + node-to-node).
- **TLS only** — ALB serves HTTPS (TLS 1.3/1.2); HTTP is redirected to HTTPS.
- **Network isolation** — only the ALB is internet-facing; ECS tasks run in
  private subnets (full env); security groups allow only ALB→ECS→data flows.
- **No static credentials** — the app authenticates via the ECS task IAM role.
