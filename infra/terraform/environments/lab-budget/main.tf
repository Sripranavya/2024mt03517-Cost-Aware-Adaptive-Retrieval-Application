# lab-budget environment: the cheapest defensible architecture.
#
# - Fargate 0.25 vCPU / 0.5 GB, DynamoDB on-demand, S3 (encrypted).
# - NO managed OpenSearch (FAISS runs in-container, persisted to S3).
# - NO SQS/SNS (direct in-process calls).
# - Bedrock is pay-per-use (no idle cost).
# - No NAT gateway: tasks run with public IPs in public subnets to reach AWS
#   APIs, which avoids the ~US$32/month NAT charge that most lab accounts block.

locals {
  name = var.name_prefix
  tags = { Component = "backend" }
}

module "networking" {
  source         = "../../modules/networking"
  name           = local.name
  vpc_cidr       = var.vpc_cidr
  az_count       = 2
  enable_nat     = false
  container_port = var.container_port
  tags           = local.tags
}

module "data" {
  source              = "../../modules/data"
  s3_bucket_name      = var.s3_bucket_name
  dynamodb_table_name = var.dynamodb_table_name
  enable_opensearch   = false
  tags                = local.tags
}

module "auth" {
  source        = "../../modules/auth"
  name          = local.name
  callback_urls = var.frontend_urls
  logout_urls   = var.frontend_urls
  tags          = local.tags
}

module "iam" {
  source             = "../../modules/iam"
  name               = local.name
  s3_bucket_arn      = module.data.s3_bucket_arn
  dynamodb_table_arn = module.data.dynamodb_table_arn
  bedrock_model_arns = var.bedrock_model_arns
  tags               = local.tags
}

module "compute" {
  source                = "../../modules/compute"
  name                  = local.name
  region                = var.region
  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  private_subnet_ids    = module.networking.public_subnet_ids # no NAT: run in public subnets
  alb_security_group_id = module.networking.alb_security_group_id
  ecs_security_group_id = module.networking.ecs_security_group_id
  execution_role_arn    = module.iam.execution_role_arn
  task_role_arn         = module.iam.task_role_arn
  acm_certificate_arn   = var.acm_certificate_arn
  image_tag             = var.image_tag
  container_port        = var.container_port
  task_cpu              = "256"
  task_memory           = "512"
  desired_count         = var.desired_count
  assign_public_ip      = true
  log_retention_days    = 7
  container_environment = {
    USE_LOCAL_MOCKS        = "false"
    APP_ENV                = "lab"
    AWS_REGION             = var.region
    S3_BUCKET_NAME         = module.data.s3_bucket_name
    DYNAMODB_TABLE_NAME    = module.data.dynamodb_table_name
    BEDROCK_MODEL_ID       = var.bedrock_model_id
    BEDROCK_EMBED_MODEL_ID = var.bedrock_embed_model_id
    COGNITO_USER_POOL_ID   = module.auth.user_pool_id
    COGNITO_APP_CLIENT_ID  = module.auth.app_client_id
    COGNITO_REGION         = var.region
    CORS_ALLOW_ORIGINS     = join(",", var.frontend_urls)
  }
  tags = local.tags
}
