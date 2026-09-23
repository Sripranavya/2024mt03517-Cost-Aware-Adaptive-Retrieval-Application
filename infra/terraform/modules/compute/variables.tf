variable "name" {
  type        = string
  description = "Name prefix for compute resources."
}

variable "region" {
  type        = string
  description = "AWS region (for the awslogs driver)."
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "ecs_security_group_id" {
  type = string
}

variable "execution_role_arn" {
  type = string
}

variable "task_role_arn" {
  type = string
}

variable "acm_certificate_arn" {
  type        = string
  description = "ACM certificate ARN for the HTTPS listener."
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "task_cpu" {
  type        = string
  description = "Fargate task CPU units (e.g. 256 = 0.25 vCPU)."
  default     = "256"
}

variable "task_memory" {
  type        = string
  description = "Fargate task memory (MiB)."
  default     = "512"
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "assign_public_ip" {
  type        = bool
  description = "Assign public IPs to tasks (true only when there is no NAT)."
  default     = false
}

variable "container_environment" {
  type        = map(string)
  description = "Environment variables passed to the container."
  default     = {}
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "enable_container_insights" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
