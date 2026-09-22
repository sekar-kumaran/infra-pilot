# Terraform / OpenTofu Integration

## Purpose
Execute IaC state changes.

## Scope
- `automation/terraform_runner`.

## Contracts
- Run `init`, `plan`, `apply` in isolated workspaces.
- Requires strict policy approval before `apply`.
