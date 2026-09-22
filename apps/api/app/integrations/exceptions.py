class ProviderError(Exception):
    """Base exception for all provider operations."""
    pass

class ProviderConfigurationError(ProviderError):
    pass

class ProviderAuthenticationError(ProviderError):
    pass

class ProviderTimeoutError(ProviderError):
    pass

class ProviderUnavailableError(ProviderError):
    pass

class ProviderValidationError(ProviderError):
    pass

class ProviderDiscoveryError(ProviderError):
    pass

class ProviderUnsupportedOperationError(ProviderError):
    pass

class ProviderNotFoundError(ProviderError):
    pass
