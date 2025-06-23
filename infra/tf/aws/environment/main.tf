terraform {
  backend "s3" {
    region = "eu-west-1"
    bucket = "hexrepo-jwn"
    key = "{{project_slug}}-environment.tfstate"
  }
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
    account_id = data.aws_caller_identity.current.account_id
    region = data.aws_region.current.name
}

{% if use_db and use_db_logic == "sql" %}
locals {
  db_url = "postgresql+psycopg://postgres:{password}@${module.{{project_slug}}_postgres.db_instance_endpoint}/${var.project}"
}
{% endif %}

provider "aws" {
  region  = var.aws_region
}

data "aws_vpc" "hexrepo" {
  filter {
    name   = "tag:Name"
    values = ["hexrepo-vpc-${terraform.workspace}"]
  }
}

data "aws_ecr_repository" "ecr_repo" {
  name                 = "hexrepo-${var.project}"
}

{% if use_db == "n" or (use_db and use_db_logic == "nosql") %}
data "aws_security_group" "default_sg" {
  tags = {
    Name = "hexrepo-vpc-${terraform.workspace}-default"
  }
}
{% endif %}

{% if use_api and use_api_type == "serverless" %}
module "{{project_slug}}_api" {
  source = "../../../../../../infra/tf/aws/modules/lambda"

  environment       = terraform.workspace
  name              = "${var.project}_api"
  ecr_url           = data.aws_ecr_repository.ecr_repo.repository_url
  docker_tag        = var.docker_tag
  vpc_id            = data.aws_vpc.hexrepo.id
  {% if (cloud_provider == "aws" and use_api ) %}
  lambda_command    = ["src.app.interactor.api.lambda_handler"]
  {% elif cloud_provider == "aws" %}
  lambda_command    = ["src.app.interactor.event.lambda_handler"]
  {% else %}
  lambda_command    = ["uvicorn", "app.interactor.api.fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
  {% endif %}
  {% if use_db and use_db_logic == "sql" %}
  security_group_ids = [module.{{project_slug}}_postgres.db_security_group_id]
  {% else %}
  security_group_ids = [data.aws_security_group.default_sg.id]
  {% endif %}
  {% if use_db and use_db_logic == "nosql" %}
  # This should be modified to be restricted to all tables for this project with project_env prefix
  dynamodb_arn      = "arn:aws:dynamodb:${local.region}:${local.account_id}:table/{{project_slug}}_${terraform.workspace}*"
  {% endif %}
  {% if use_storage %}
  bucket            = module.{{project_slug}}_bucket.bucket_name
  {% endif %}

  environment_variables = {
    ENVIRONMENT                 = terraform.workspace
    CLOUD_PROVIDER              = "{{ cloud_provider|upper }}"
    {% if use_db and use_db_logic == "sql" %}
    DB_URL                      = local.db_url
    DB_RO_URL                   = local.db_ro_url
    READ_REPLICA_ENABLED        = "false"
    DB_PASSWORD_SECRET_NAME     = data.aws_secretsmanager_secret.db_secret.name
    {% endif %}
    {% if use_db and use_db_logic == "nosql" %}
    DB_URL                      = ""
    {% endif %}
    {% if use_task %}
    TASK_QUEUE              = "${var.project}_${terraform.workspace}_tasks"
    {% endif %}
    CLIENT_ID               = module.common_auth.client_id
    USER_POOL_ID            = module.common_auth.user_pool_id
  }
}
{% endif %}

{% if use_api and use_api_type == "container" %}
module "{{project_slug}}_ecs_api" {
  source             = "../../../../../../infra/tf/aws/modules/ecs"
  project            = var.project
  name               = "api"
  environment        = terraform.workspace
  aws_region         = var.aws_region
  vpc_id             = data.aws_vpc.hexrepo.id
  private_subnet_ids = data.aws_subnets.private.ids
  security_group_ids = [module.common_postgres.db_security_group_id]
  target_group_arn   = module.common_alb.target_group_arn
  # This costs money
  container_insights = "disabled"
  min_capacity       = 0

  ecr_url        = data.aws_ecr_repository.ecr_repo.repository_url
  docker_tag     = var.docker_tag_container
  container_port = 8000

  environment_variables = {
    ENVIRONMENT             = terraform.workspace
    PROJECT                 = var.project
    CLOUD_PROVIDER          = "AWS"
    DB_URL                  = local.db_url
    DB_RO_URL               = local.db_ro_url
    READ_REPLICA_ENABLED    = "false"
    DB_PASSWORD_SECRET_NAME = data.aws_secretsmanager_secret.db_secret.name
    TASK_QUEUE              = "${var.project}_${terraform.workspace}_tasks"
    CLIENT_ID               = module.common_auth.client_id
    USER_POOL_ID            = module.common_auth.user_pool_id
    ALLOWED_ORIGINS         = "*"
    LOG_JSON                = "true"
    ORIGIN_URL              = "https://${local.api_subdomain_ecs}.${var.domain}"
    TASK_TABLE_NAME         = module.common_task_nosql.table_name
    LOG_LEVEL               = "INFO"
  }
  secrets = {
    DB_PASSWORD = data.aws_secretsmanager_secret.db_secret.arn
  }

  desired_count = 1
  task_cpu      = 256
  task_memory   = 512
}
{% endif %}


{% if use_task %}
module "queue" {
  source = "../../../../../../infra/tf/aws/modules/sqs"

  project     = var.project
  name        = "${var.project}-${terraform.workspace}"
  environment = terraform.workspace
}

resource "aws_lambda_event_source_mapping" "queue_lambda_mapping" {
  event_source_arn = module.queue.queue_arn
  function_name    = module.{{project_slug}}_tasks.lambda_function_name
}

{% if use_task and use_task_type == "serverless" %}
module "{{project_slug}}_tasks" {
  source = "../../../../../../infra/tf/aws/modules/lambda"

  environment        = terraform.workspace
  name               = "${var.project}_tasks"
  ecr_url            = data.aws_ecr_repository.ecr_repo.repository_url
  docker_tag         = var.docker_tag
  vpc_id             = data.aws_vpc.hexrepo.id
  lambda_command     = ["src.app.interactor.event.lambda_handler"]
  security_group_ids = [module.{{project_slug}}_postgres.db_security_group_id]

  environment_variables = {
    ENVIRONMENT             = terraform.workspace
    CLOUD_PROVIDER          = "AWS"
    DB_URL                  = local.db_url
    DB_RO_URL               = local.db_ro_url
    READ_REPLICA_ENABLED    = "false"
    DB_PASSWORD_SECRET_NAME = data.aws_secretsmanager_secret.db_secret.name
  }
}
{% endif %}

{% if use_task and use_task_type == "container" %}
module "{{project_slug}}_ecs_task" {
  source = "../../../../../../infra/tf/aws/modules/ecs"

  project            = var.project
  name               = "task"
  environment        = terraform.workspace
  aws_region         = var.aws_region
  vpc_id             = data.aws_vpc.hexrepo.id
  private_subnet_ids = data.aws_subnets.private.ids
  security_group_ids = [module.common_postgres.db_security_group_id]
  # This costs money
  container_insights = "disabled"

  ecr_url        = data.aws_ecr_repository.ecr_repo.repository_url
  container_command = ["celery", "-A", "app.interactor.event.celery.celery_app", "worker", "--loglevel=info"]
  docker_tag     = var.docker_tag_container
  container_port = 8000
  min_capacity   = 0

  environment_variables = {
    ENVIRONMENT             = terraform.workspace
    PROJECT                 = var.project
    CLOUD_PROVIDER          = "AWS"
    DB_URL                  = local.db_url
    DB_RO_URL               = local.db_ro_url
    READ_REPLICA_ENABLED    = "false"
    DB_PASSWORD_SECRET_NAME = data.aws_secretsmanager_secret.db_secret.name
    TASK_QUEUE              = "${var.project}_${terraform.workspace}_tasks"
    CLIENT_ID               = module.common_auth.client_id
    USER_POOL_ID            = module.common_auth.user_pool_id
    ALLOWED_ORIGINS         = "*"
    LOG_JSON                = "true"
    ORIGIN_URL              = "https://${local.api_subdomain_ecs}.${var.domain}"
    TASK_TABLE_NAME         = module.common_task_nosql.table_name
    LOG_LEVEL               = "INFO"
  }
  secrets = {
    DB_PASSWORD = data.aws_secretsmanager_secret.db_secret.arn
  }

  desired_count = 1
  task_cpu      = 256
  task_memory   = 512
}
{% endif %}

module "{{project_slug}}_api_gateway" {
  source = "../../../../../../infra/tf/aws/modules/apigateway"

  environment       = terraform.workspace
  lambda_invoke_arn = module.{{project_slug}}_api.lambda_function_invoke_arn
  lambda_name       = module.{{project_slug}}_api.lambda_function_name
  domain            = var.domain
  api_subdomain     = "{{project_slug}}-${terraform.workspace}"
  project           = "{{project_slug}}"
  cognito_user_pool_arn = module.common_auth.user_pool_arn
  # Auth handled in api middleware
  auth_enabled          = false
}

{% if use_db and use_db_logic == "sql" %}
module "{{project_slug}}_postgres" {
  source = "../../../../../../infra/tf/aws/modules/rds"

  environment       = terraform.workspace
  project           = "{{project_slug}}"
  vpc_id            = data.aws_vpc.hexrepo.id
  username          = "postgres"
}

data "aws_secretsmanager_secret" "db_secret" {
  arn = module.{{project_slug}}_postgres.db_password_secret_arn
}
{% elif use_db and use_db_logic == "nosql" %}
module "{{project_slug}}_dynamodb" {
  source = "../../../../../../infra/tf/aws/modules/dynamodb"

  environment   = terraform.workspace
  table_name    = "{{project_slug}}" 
  project       = "{{project_slug}}"
}
{% endif %}

{% if use_storage %}
module "{{project_slug}}_bucket" {
  source = "../../../../../../infra/tf/aws/modules/s3"

  environment = terraform.workspace
  project     = "{{project_slug}}"
  name        = "{{project_slug}}"
}
{% endif %}