# Auth module: Amazon Cognito user pool + app client for JWT auth.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40"
    }
  }
}

resource "aws_cognito_user_pool" "this" {
  name = "${var.name}-users"

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = var.admin_only_signup
  }

  auto_verified_attributes = ["email"]
  tags                     = var.tags
}

resource "aws_cognito_user_pool_client" "this" {
  name         = "${var.name}-app-client"
  user_pool_id = aws_cognito_user_pool.this.id

  generate_secret = false
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  allowed_oauth_flows_user_pool_client = true
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = var.callback_urls
  logout_urls                          = var.logout_urls
}

resource "aws_cognito_user_pool_domain" "this" {
  count        = var.hosted_ui_domain_prefix == "" ? 0 : 1
  domain       = var.hosted_ui_domain_prefix
  user_pool_id = aws_cognito_user_pool.this.id
}
