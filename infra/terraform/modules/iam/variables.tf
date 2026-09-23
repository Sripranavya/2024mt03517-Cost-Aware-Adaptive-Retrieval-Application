variable "name" {
  description = "Name prefix for IAM roles."
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the corpus S3 bucket."
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the state DynamoDB table."
  type        = string
}

variable "bedrock_model_arns" {
  description = "Specific Bedrock model ARNs the task may invoke."
  type        = list(string)
  default     = []
}

variable "opensearch_arn" {
  description = "OpenSearch domain ARN (empty to omit access)."
  type        = string
  default     = ""
}

variable "sqs_queue_arn" {
  description = "SQS queue ARN (empty to omit access)."
  type        = string
  default     = ""
}

variable "sns_topic_arn" {
  description = "SNS topic ARN (empty to omit access)."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}
