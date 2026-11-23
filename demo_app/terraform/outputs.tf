output "app_url" {
  description = "Direct URL to access the 4-page demo application"
  value       = "http://localhost:${var.external_port}"
}

output "health_endpoint" {
  description = "Health check endpoint for Nagios and InfraPilot"
  value       = "http://localhost:${var.external_port}/health"
}

output "metrics_endpoint" {
  description = "Observability metrics endpoint"
  value       = "http://localhost:${var.external_port}/api/metrics"
}

output "container_id" {
  description = "Identifier of the provisioned container"
  value       = docker_container.cloudpulse_app.id
}

output "network_name" {
  description = "Docker network name"
  value       = docker_network.cloudpulse_network.name
}
