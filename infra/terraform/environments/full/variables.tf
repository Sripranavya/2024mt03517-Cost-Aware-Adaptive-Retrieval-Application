variable "region" {
  type    = string
  default = "us-east-1"
}

variable "name_prefix" {
  type    = string
  default = "agentic-rag"
}

variable "vpc_cidr" {
  type    = string
  default = "10.30.0.0/16"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "s3_bucket_name" {
  type        = string
  description = "Globally-unique S3 bucket name."
}

variable "dynamodb_table_name" {
  type    = string
  default = "agentic-rag-state"
}

variable "kms_key_arn" {
  type        = string
  description = "KMS key ARN for SSE-KMS ('' uses AES256)."
  default     = ""
}

variable "opensearch_domain_name" {
  type    = string
  default = "agentic-rag-vectors"
}

variable "acm_certificate_arn" {
  type        = string
  description = "ACM certificate ARN for the ALB HTTPS listener."
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "task_cpu" {
  type    = string
  default = "512"
}

variable "task_memory" {
  type    = string
  default = "1024"
}

variable "desired_count" {
  type    = number
  default = 2
}

variable "bedrock_model_id" {
  type    = string
  default = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "bedrock_embed_model_id" {
  type    = string
  default = "amazon.titan-embed-text-v2:0"
}

variable "bedrock_model_arns" {
  type    = list(string)
  default = []
}

variable "hosted_ui_domain_prefix" {
  type    = string
  default = ""
}

variable "frontend_urls" {
  type    = list(string)
  default = ["http://localhost:5173"]
}
