class KubernetesProviderError(Exception):
    """Base exception for Kubernetes provider."""
    pass

class KubernetesAuthenticationError(KubernetesProviderError):
    """Raised when authentication fails (HTTP 401)."""
    pass

class KubernetesAuthorizationError(KubernetesProviderError):
    """Raised when authorization fails (HTTP 403)."""
    pass

class KubernetesResourceNotFoundError(KubernetesProviderError):
    """Raised when a resource is not found (HTTP 404)."""
    pass

class KubernetesTimeoutError(KubernetesProviderError):
    """Raised when a request times out (HTTP 408 or connection timeout)."""
    pass

class KubernetesRateLimitError(KubernetesProviderError):
    """Raised when rate limited (HTTP 429)."""
    pass

class KubernetesServerError(KubernetesProviderError):
    """Raised when the server encounters an error (HTTP 5xx)."""
    pass

class KubernetesConnectionError(KubernetesProviderError):
    """Raised when a connection to the server fails."""
    pass

class KubernetesConfigurationError(KubernetesProviderError):
    """Raised when provider configuration is invalid."""
    pass
