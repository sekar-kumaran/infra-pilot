import os
from app.models.resource import InfrastructureResource
from .errors import AnsibleValidationError

def resolve_inventory_path() -> str:
    """
    Returns the configured ansible inventory path.
    Allows dynamic override via environment (useful for testing/production boundary).
    """
    env_inventory = os.getenv("ANSIBLE_REAL_INVENTORY")
    if env_inventory:
        return env_inventory
        
    default_inventory = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))),
        "ansible", "inventories", "example", "hosts"
    )
    return default_inventory

def resolve_target_host(resource: InfrastructureResource) -> str:
    """
    Maps an InfraPilot resource to a specific Ansible target host.
    """
    if not resource:
        raise AnsibleValidationError("No resource provided for target resolution")
        
    env_target = os.getenv("ANSIBLE_REAL_TARGET")
    if env_target:
        # In real-provider acceptance testing, force this target
        return env_target
        
    # Standard resolution: look for an IP address or hostname in metadata
    meta = resource.metadata_dict if hasattr(resource, "metadata_dict") else (resource.metadata or {})
    
    # Try to extract the host name from the canonical identity if applicable
    # e.g. "nagios/host/web-server-01" -> "web-server-01"
    if resource.resource_type == "host":
        if "hostname" in meta:
            return meta["hostname"]
        elif "ip_address" in meta:
            return meta["ip_address"]
        # Fallback to parsing from external_id
        parts = resource.external_id.split("/")
        if len(parts) >= 3:
            return parts[-1]
            
    elif resource.resource_type == "service":
        # A service runs on a host. 
        # Typically external_id is something like "nagios/service/web-server-01/nginx"
        parts = resource.external_id.split("/")
        if len(parts) >= 4:
            return parts[-2]
            
    raise AnsibleValidationError(f"Could not resolve an Ansible target host for resource {resource.id}")
