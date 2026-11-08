# credit-lab: laptop-run controller against managed AWS data services only.
# S3 + DynamoDB (on-demand) + one t3.small OpenSearch node + Cognito + IAM.
# No ECS/Fargate, ALB, NAT, SQS or SNS (they bill continuously).

locals {
  tags = { Component = "backend" }
}

module "data" {
  source                 = "../../modules/data"
  s3_bucket_name         = var.s3_bucket_name
  dynamodb_table_name    = var.dynamodb_table_name
  kms_key_arn            = ""
  enable_opensearch      = true
  opensearch_domain_name = var.opensearch_domain_name
  tags                   = local.tags
}

module "auth" {
  source                  = "../../modules/auth"
  name                    = var.name_prefix
  callback_urls           = var.frontend_urls
  logout_urls             = var.frontend_urls
  hosted_ui_domain_prefix = ""
  tags                    = local.tags
}

module "iam" {
  source             = "../../modules/iam"
  name               = var.name_prefix
  s3_bucket_arn      = module.data.s3_bucket_arn
  dynamodb_table_arn = module.data.dynamodb_table_arn
  bedrock_model_arns = var.bedrock_model_arns
  opensearch_arn     = module.data.opensearch_arn
  tags               = local.tags
}

output "opensearch_endpoint" {
  value = module.data.opensearch_endpoint
}

output "s3_bucket_name" {
  value = module.data.s3_bucket_name
}

output "dynamodb_table_name" {
  value = module.data.dynamodb_table_name
}
