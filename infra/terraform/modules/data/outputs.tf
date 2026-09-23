output "s3_bucket_name" {
  value = aws_s3_bucket.corpus.bucket
}

output "s3_bucket_arn" {
  value = aws_s3_bucket.corpus.arn
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.state.name
}

output "dynamodb_table_arn" {
  value = aws_dynamodb_table.state.arn
}

output "opensearch_endpoint" {
  value       = var.enable_opensearch ? aws_opensearch_domain.vectors[0].endpoint : ""
  description = "OpenSearch HTTPS endpoint (empty when disabled)."
}

output "opensearch_arn" {
  value = var.enable_opensearch ? aws_opensearch_domain.vectors[0].arn : ""
}
