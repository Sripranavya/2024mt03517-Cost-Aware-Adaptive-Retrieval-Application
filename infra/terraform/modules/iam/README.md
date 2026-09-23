# IAM module

Least-privilege roles for the ECS/Fargate task:

- **Execution role** — pulls the image from ECR and writes container logs
  (AWS-managed `AmazonECSTaskExecutionRolePolicy`).
- **Task role** — the application's own permissions, each statement scoped to a
  *specific resource ARN*:
  - S3: the corpus bucket and its objects only;
  - DynamoDB: item operations on the state table only;
  - Bedrock: `InvokeModel` on the specific model ARNs only;
  - OpenSearch / SQS / SNS: only the specific domain / queue / topic, and only
    when their ARNs are provided.

There are no `Resource: "*"` grants except those AWS mandates inside the managed
execution policy. The task uses this role via the ECS task-role credential
provider — **no static AWS keys anywhere**.

## Cost notes

IAM roles and policies are **free**.
