terraform {
  backend "s3" {
    region = "eu-west-1"
    bucket = "hexrepo-jwn"
    key = "{{project_slug}}-shared.tfstate"
  }
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region  = var.aws_region
}

module "example_ecr" {
  source = "../../../../../../infra/tf/aws/modules/ecr"
  project           = "hexrepo-${var.project}"
}

# Add url domain infra here 
