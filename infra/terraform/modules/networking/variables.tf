variable "name" {
  description = "Name prefix for networking resources."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones (and subnet pairs) to create."
  type        = number
  default     = 2
}

variable "enable_nat" {
  description = "Provision a NAT gateway for private-subnet egress (adds cost)."
  type        = bool
  default     = true
}

variable "container_port" {
  description = "Container/app port the ECS service listens on."
  type        = number
  default     = 8000
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}
