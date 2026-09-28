from app.models.enums import ProviderErrorClassification

class ProviderExecutionException(Exception):
    def __init__(self, message: str, classification: ProviderErrorClassification = ProviderErrorClassification.UNKNOWN_FAILURE):
        super().__init__(message)
        self.classification = classification
        self.message = message

class ProviderAuthenticationError(ProviderExecutionException):
    def __init__(self, message: str):
        super().__init__(message, ProviderErrorClassification.AUTHENTICATION_FAILURE)

class ProviderTimeoutError(ProviderExecutionException):
    def __init__(self, message: str):
        super().__init__(message, ProviderErrorClassification.TIMEOUT)

class ProviderResourceNotFoundError(ProviderExecutionException):
    def __init__(self, message: str):
        super().__init__(message, ProviderErrorClassification.RESOURCE_NOT_FOUND)

class ProviderUnavailableError(ProviderExecutionException):
    def __init__(self, message: str):
        super().__init__(message, ProviderErrorClassification.PROVIDER_UNAVAILABLE)
