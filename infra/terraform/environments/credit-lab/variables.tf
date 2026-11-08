variable "region" {
  type    = string
  default = "ap-southeast-2"
}

variable "name_prefix" {
  type    = string
  default = "agentic-rag"
}

variable "s3_bucket_name" {
  type        = string
  description = "Globally-unique S3 bucket name."
}

variable "dynamodb_table_name" {
  type    = string
  default = "agentic-rag-state"
}

variable "opensearch_domain_name" {
  type    = string
  default = "agentic-rag-vectors"
}

variable "bedrock_model_arns" {
  type        = list(string)
  default     = []
  description = "Bedrock model / inference-profile ARNs the app may invoke."
}

variable "frontend_urls" {
  type    = list(string)
  default = ["http://localhost:5173"]
}
