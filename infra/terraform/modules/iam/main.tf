# IAM module: least-privilege roles for the ECS task.
# The task role is scoped to the *specific* resource ARNs it needs — no wildcard
# resources except where AWS mandates it (e.g. ECR auth token, log stream fan-out).

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40"
    }
  }
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# --- Execution role: pull image + write logs (AWS-managed policy) ---
resource "aws_iam_role" "execution" {
  name               = "${var.name}-exec-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# --- Task role: least-privilege access to app resources ---
resource "aws_iam_role" "task" {
  name               = "${var.name}-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "task" {
  # S3: read/write only the corpus bucket and its objects.
  statement {
    sid     = "S3Corpus"
    actions = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [
      var.s3_bucket_arn,
      "${var.s3_bucket_arn}/*",
    ]
  }

  # DynamoDB: item-level access only on the state table.
  statement {
    sid = "DynamoState"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query",
    ]
    resources = [var.dynamodb_table_arn]
  }

  # Bedrock: invoke only the specific model ARNs passed in.
  dynamic "statement" {
    for_each = length(var.bedrock_model_arns) > 0 ? [1] : []
    content {
      sid       = "BedrockInvoke"
      actions   = ["bedrock:InvokeModel"]
      resources = var.bedrock_model_arns
    }
  }

  # OpenSearch: HTTP data-plane access only to the specific domain.
  dynamic "statement" {
    for_each = var.opensearch_arn != "" ? [1] : []
    content {
      sid       = "OpenSearchData"
      actions   = ["es:ESHttpGet", "es:ESHttpPost", "es:ESHttpPut"]
      resources = ["${var.opensearch_arn}/*"]
    }
  }

  # SQS: only the specific queue.
  dynamic "statement" {
    for_each = var.sqs_queue_arn != "" ? [1] : []
    content {
      sid       = "SqsAccess"
      actions   = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
      resources = [var.sqs_queue_arn]
    }
  }

  # SNS: publish only to the specific topic.
  dynamic "statement" {
    for_each = var.sns_topic_arn != "" ? [1] : []
    content {
      sid       = "SnsPublish"
      actions   = ["sns:Publish"]
      resources = [var.sns_topic_arn]
    }
  }
}

resource "aws_iam_role_policy" "task" {
  name   = "${var.name}-task-policy"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.task.json
}
