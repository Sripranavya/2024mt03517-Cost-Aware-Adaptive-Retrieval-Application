output "alb_dns_name" {
  value = module.compute.alb_dns_name
}

output "ecr_repository_url" {
  value = module.compute.ecr_repository_url
}

output "s3_bucket_name" {
  value = module.data.s3_bucket_name
}

output "dynamodb_table_name" {
  value = module.data.dynamodb_table_name
}

output "cognito_user_pool_id" {
  value = module.auth.user_pool_id
}

output "cognito_app_client_id" {
  value = module.auth.app_client_id
}
