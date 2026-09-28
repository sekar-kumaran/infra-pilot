from app.integrations.exceptions import ProviderError

class AWSProviderError(ProviderError):
    """Base exception for AWS provider."""
    pass

class AWSAuthenticationError(AWSProviderError):
    """Authentication/credential failure."""
    pass

class AWSAuthorizationError(AWSProviderError):
    """AccessDenied or permission failure."""
    pass

class AWSResourceNotFoundError(AWSProviderError):
    """Resource not found (404-equivalent)."""
    pass

class AWSThrottlingError(AWSProviderError):
    """Rate limit or throttling."""
    pass

class AWSNetworkError(AWSProviderError):
    """Network connection failure to AWS."""
    pass

class AWSAPIError(AWSProviderError):
    """Generic AWS API failure."""
    pass

class AWSInvalidParameterError(AWSProviderError):
    """Invalid parameter or bad request."""
    pass
