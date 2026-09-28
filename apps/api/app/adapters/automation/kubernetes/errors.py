class KubernetesAutomationError(Exception):
    """Base exception for Kubernetes automation."""
    pass

class KubernetesExecutionError(KubernetesAutomationError):
    """Raised when an execution operation fails."""
    pass

class KubernetesVerificationTimeout(KubernetesAutomationError):
    """Raised when a verification polling loop times out."""
    pass

class KubernetesValidationError(KubernetesAutomationError):
    """Raised when validation of target or parameters fails."""
    pass
