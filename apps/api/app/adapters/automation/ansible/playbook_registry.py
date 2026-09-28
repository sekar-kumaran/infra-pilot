import os
from .errors import AnsibleValidationError

_DEFAULT_LOCAL_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../../../../../../ansible/playbooks"
))
PLAYBOOKS_DIR = os.getenv("PLAYBOOKS_DIR", "/app/ansible/playbooks")
if not os.path.exists(PLAYBOOKS_DIR):
    PLAYBOOKS_DIR = _DEFAULT_LOCAL_PATH

# Registry mapping ActionRegistry actions to concrete playbook filenames
ACTION_PLAYBOOK_MAP = {
    "collect_system_information": "collect_system_information.yml",
    "check_service": "check_service.yml",
    "check_disk_usage": "check_disk_usage.yml",
    "check_memory_usage": "check_memory_usage.yml",
    "check_cpu_usage": "check_cpu_usage.yml",
    "restart_service": "restart_service.yml",
    "start_service": "start_service.yml",
    "stop_service": "stop_service.yml",
    "restart_docker_container": "restart_docker_container.yml",
    "start_docker_container": "start_docker_container.yml",
    "stop_docker_container": "stop_docker_container.yml",
    "inspect_docker_container": "inspect_docker_container.yml",
    "validate_configuration": "validate_configuration.yml",
    "deploy_configuration": "deploy_configuration.yml",
    "rollback_configuration": "rollback_configuration.yml",
}

def resolve_playbook_path(action_name: str) -> str:
    """
    Resolves an action name to a physical playbook path.
    Strictly uses the allowlist.
    """
    filename = ACTION_PLAYBOOK_MAP.get(action_name)
    if not filename:
        raise AnsibleValidationError(f"Action {action_name} is not mapped to an Ansible playbook")
        
    path = os.path.join(PLAYBOOKS_DIR, filename)
    
    # In production, we'd verify the file exists on disk
    # but we can just return the resolved path
    return path
