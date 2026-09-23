# full environment: the complete architecture matching the dissertation's
# tech-stack slide — adds managed OpenSearch, SQS/SNS async orchestration,
# Cognito, and CloudWatch dashboards/alarms on top of the lab-budget core.
#
# Requires an account that permits creating IAM roles, OpenSearch domains, NAT
# gateways, etc. — many student sandboxes block exactly these, so use only where
# the lab account genuinely has the budget and permissions.

locals {
  name = var.name_prefix
  tags = { Component = "backend" }
}

module "networking" {
  source         = "../../modules/networking"
  name           = local.name
  vpc_cidr       = var.vpc_cidr
  az_count       = 2
  enable_nat     = true
  container_port = var.container_port
  tags           = local.tags
}

module "data" {
  source                 = "../../modules/data"
  s3_bucket_name         = var.s3_bucket_name
  dynamodb_table_name    = var.dynamodb_table_name
  kms_key_arn            = var.kms_key_arn
  enable_opensearch      = true
  opensearch_domain_name = var.opensearch_domain_name
  tags                   = local.tags
}

module "messaging" {
  source = "../../modules/messaging"
  name   = local.name
  tags   = local.tags
}

module "auth" {
  source                  = "../../modules/auth"
  name                    = local.name
  callback_urls           = var.frontend_urls
  logout_urls             = var.frontend_urls
  hosted_ui_domain_prefix = var.hosted_ui_domain_prefix
  tags                    = local.tags
}

module "iam" {
  source             = "../../modules/iam"
  name               = local.name
  s3_bucket_arn      = module.data.s3_bucket_arn
  dynamodb_table_arn = module.data.dynamodb_table_arn
  bedrock_model_arns = var.bedrock_model_arns
  opensearch_arn     = module.data.opensearch_arn
  sqs_queue_arn      = module.messaging.queue_arn
  sns_topic_arn      = module.messaging.topic_arn
  tags               = local.tags
}

module "compute" {
  source                    = "../../modules/compute"
  name                      = local.name
  region                    = var.region
  vpc_id                    = module.networking.vpc_id
  public_subnet_ids         = module.networking.public_subnet_ids
  private_subnet_ids        = module.networking.private_subnet_ids
  alb_security_group_id     = module.networking.alb_security_group_id
  ecs_security_group_id     = module.networking.ecs_security_group_id
  execution_role_arn        = module.iam.execution_role_arn
  task_role_arn             = module.iam.task_role_arn
  acm_certificate_arn       = var.acm_certificate_arn
  image_tag                 = var.image_tag
  container_port            = var.container_port
  task_cpu                  = var.task_cpu
  task_memory               = var.task_memory
  desired_count             = var.desired_count
  assign_public_ip          = false
  log_retention_days        = 30
  enable_container_insights = true
  container_environment = {
    USE_LOCAL_MOCKS        = "false"
    APP_ENV                = "production"
    AWS_REGION             = var.region
    S3_BUCKET_NAME         = module.data.s3_bucket_name
    DYNAMODB_TABLE_NAME    = module.data.dynamodb_table_name
    OPENSEARCH_ENDPOINT    = module.data.opensearch_endpoint
    SQS_QUEUE_URL          = module.messaging.queue_url
    SNS_TOPIC_ARN          = module.messaging.topic_arn
    BEDROCK_MODEL_ID       = var.bedrock_model_id
    BEDROCK_EMBED_MODEL_ID = var.bedrock_embed_model_id
    COGNITO_USER_POOL_ID   = module.auth.user_pool_id
    COGNITO_APP_CLIENT_ID  = module.auth.app_client_id
    COGNITO_REGION         = var.region
    CORS_ALLOW_ORIGINS     = join(",", var.frontend_urls)
  }
  tags = local.tags
}

module "observability" {
  source       = "../../modules/observability"
  name         = local.name
  region       = var.region
  cluster_name = module.compute.cluster_name
  service_name = module.compute.service_name
  tags         = local.tags
}
