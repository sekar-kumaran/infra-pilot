variable "environment" {
  description = "Target deployment environment (development, staging, production)"
  type        = string
  default     = "production"
}

variable "app_image" {
  description = "Docker image for the CloudPulse 4-page demo application"
  type        = string
  default     = "python:3.12-slim"
}

variable "internal_port" {
  description = "Internal port exposed by the FastAPI container"
  type        = number
  default     = 5050
}

variable "external_port" {
  description = "External port published to the host"
  type        = number
  default     = 5050
}

variable "docker_host" {
  description = "Docker daemon connection string"
  type        = string
  default     = "npipe:////./pipe/docker_engine"
}
