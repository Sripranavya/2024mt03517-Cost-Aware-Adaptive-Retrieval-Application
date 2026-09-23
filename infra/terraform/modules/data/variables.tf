variable "s3_bucket_name" {
  description = "Globally-unique S3 bucket name for corpus artifacts and the index."
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for POMDP episode traces."
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for SSE-KMS. Empty string uses SSE-S3 (AES256)."
  type        = string
  default     = ""
}

variable "enable_opensearch" {
  description = "Provision a managed OpenSearch domain (full env only)."
  type        = bool
  default     = false
}

variable "opensearch_domain_name" {
  description = "OpenSearch domain name."
  type        = string
  default     = "agentic-rag-vectors"
}

variable "opensearch_instance_type" {
  description = "OpenSearch data node instance type."
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch data nodes."
  type        = number
  default     = 1
}

variable "opensearch_volume_size" {
  description = "EBS volume size (GB) per OpenSearch node."
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}
