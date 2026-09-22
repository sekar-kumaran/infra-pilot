# Ansible Integration

## Purpose
Execute Ansible playbooks for automated remediation.

## Scope
- `automation/ansible_runner`.

## Contracts
- Accepts playbook path, inventory, and extra vars.
- Streams stdout/stderr.
- Emits execution status events.
