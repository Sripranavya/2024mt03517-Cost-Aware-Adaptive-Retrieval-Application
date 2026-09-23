variable "name" {
  type        = string
  description = "Name prefix for Cognito resources."
}

variable "admin_only_signup" {
  type        = bool
  description = "Restrict user creation to administrators."
  default     = true
}

variable "callback_urls" {
  type    = list(string)
  default = ["http://localhost:5173"]
}

variable "logout_urls" {
  type    = list(string)
  default = ["http://localhost:5173"]
}

variable "hosted_ui_domain_prefix" {
  type        = string
  description = "Prefix for the Cognito Hosted UI domain (empty to skip)."
  default     = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
