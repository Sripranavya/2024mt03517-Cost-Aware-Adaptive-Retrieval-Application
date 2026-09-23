variable "region" {
  type    = string
  default = "us-east-1"
}

variable "name_prefix" {
  type    = string
  default = "agentic-rag-lab"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
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

variable "acm_certificate_arn" {
  type        = string
  description = "ACM certificate ARN for the ALB HTTPS listener."
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "desired_count" {
  type    = number
  default = 1
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
  type        = list(string)
  description = "Specific Bedrock model ARNs the task may invoke."
  default     = []
}

variable "frontend_urls" {
  type    = list(string)
  default = ["http://localhost:5173"]
}
