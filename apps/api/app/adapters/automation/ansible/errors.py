class AnsibleProviderError(Exception):
    """Base exception for Ansible execution errors."""
    pass

class AnsibleValidationError(AnsibleProviderError):
    """Raised when validation of action, playbook, or target fails."""
    pass

class AnsibleExecutionError(AnsibleProviderError):
    """Raised when Ansible subprocess execution fails."""
    pass

class AnsibleTimeoutError(AnsibleProviderError):
    """Raised when Ansible execution times out."""
    pass
