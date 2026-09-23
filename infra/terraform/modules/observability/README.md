# Observability module

Provisions monitoring for the ECS service:

- A **CloudWatch dashboard** with ECS CPU / memory widgets.
- Alarms for **high CPU** and **ALB 5xx errors**, notifying an **SNS alarm
  topic** (subscribe email/Slack out of band).

## Cost notes

Dashboards, alarms, and SNS are within/near the free tier — effectively **US$0**
for a demo (a few cents/month for many custom metrics/dashboards).
