# Compute module

Runs the backend container on ECS Fargate behind an internet-facing ALB:

- **ECR repository** (immutable tags, scan-on-push, AES256).
- **CloudWatch log group** for container logs.
- **ECS cluster** + **Fargate task definition** (configurable `task_cpu` /
  `task_memory`, default 0.25 vCPU / 0.5 GB) using the injected execution and
  task roles, with a container health check on `/api/v1/health`.
- **Application Load Balancer**: HTTPS listener (TLS 1.3/1.2) forwarding to the
  tasks; HTTP listener redirecting to HTTPS. Only the ALB is internet-facing.
- **ECS service** running the tasks in **private subnets**.

## Cost notes

- **Fargate** 0.25 vCPU / 0.5 GB, 1 task, 24×7: ~US$9/month.
- **ALB**: ~US$16/month base + LCU usage.
- **ECR / CloudWatch Logs**: a few cents/month at demo volume.

Estimated cost: **~US$25–30/month** for a single always-on task + ALB. For a
lab account you can set `desired_count = 0` when idle to avoid Fargate charges.
