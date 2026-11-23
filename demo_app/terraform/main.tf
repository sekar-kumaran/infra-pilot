terraform {
  required_version = ">= 1.5.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.2"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4.0"
    }
  }
}

provider "docker" {
  host = var.docker_host
}

# Network Bridge for CloudPulse Microservices
resource "docker_network" "cloudpulse_network" {
  name   = "cloudpulse-net"
  driver = "bridge"
  ipam_config {
    subnet  = "172.28.0.0/16"
    gateway = "172.28.0.1"
  }
}

# Volume for Application Persistent State & Logs
resource "docker_volume" "cloudpulse_data" {
  name = "cloudpulse-data"
}

# Main 4-Page Demo Application Container
resource "docker_container" "cloudpulse_app" {
  name  = "cloudpulse-demo-app"
  image = var.app_image

  ports {
    internal = var.internal_port
    external = var.external_port
  }

  networks_advanced {
    name = docker_network.cloudpulse_network.name
  }

  volumes {
    volume_name    = docker_volume.cloudpulse_data.name
    container_path = "/app/data"
  }

  env = [
    "ENV=${var.environment}",
    "APP_PORT=${var.internal_port}",
    "APP_NAME=CloudPulse Demo Application",
    "ENABLE_TELEMETRY=true",
    "NAGIOS_MONITORED=true",
    "INFRAPILOT_MANAGED=true"
  ]

  healthcheck {
    test         = ["CMD", "curl", "-f", "http://localhost:${var.internal_port}/health"]
    interval     = "10s"
    timeout      = "5s"
    retries      = 3
    start_period = "5s"
  }

  restart = "always"
}

# Export environment configuration file for Ansible consumption
resource "local_file" "ansible_env_config" {
  content  = templatefile("${path.module}/templates/app_config.j2", {
    app_host    = "127.0.0.1"
    app_port    = var.external_port
    environment = var.environment
    monitoring  = "nagios"
  })
  filename = "${path.module}/../ansible/generated_env.yml"
}
