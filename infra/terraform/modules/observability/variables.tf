variable "name" {
  type        = string
  description = "Name prefix for observability resources."
}

variable "region" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "service_name" {
  type = string
}

variable "cpu_threshold" {
  type    = number
  default = 80
}

variable "error_threshold" {
  type    = number
  default = 5
}

variable "tags" {
  type    = map(string)
  default = {}
}
