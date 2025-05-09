/* general */

variable "aws_region" {
  default = "eu-west-1"
}

variable "aws_access_key" {
}

variable "aws_secret_key" {
}

variable "project" {
  default = "{{project_slug}}"
}

variable "docker_tag" {
  default = "latest"
}

variable "domain" {
  default = "{{api_domain}}"
}

variable "api_subdomain" {
  default = "{{project_slug}}"
}

variable "api_repo" {
  description = "Name of container image repository"
  default     = "{{project_slug}}_api"
}