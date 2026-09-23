terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "agentic-rag-pomdp"
      Environment = "full"
      ManagedBy   = "terraform"
    }
  }
}
