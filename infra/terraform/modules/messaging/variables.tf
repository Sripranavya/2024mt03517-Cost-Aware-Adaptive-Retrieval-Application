variable "name" {
  type        = string
  description = "Name prefix for messaging resources."
}

variable "visibility_timeout_seconds" {
  type    = number
  default = 60
}

variable "max_receive_count" {
  type    = number
  default = 5
}

variable "kms_key_id" {
  type        = string
  description = "KMS key id for SNS encryption ('' uses the AWS-managed key)."
  default     = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
