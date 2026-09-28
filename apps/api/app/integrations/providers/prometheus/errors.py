from app.integrations.exceptions import ProviderError

class PrometheusConnectionError(ProviderError):
    pass

class PrometheusTimeoutError(ProviderError):
    pass

class PrometheusAuthenticationError(ProviderError):
    pass

class PrometheusQueryError(ProviderError):
    pass

class PrometheusInvalidResponseError(ProviderError):
    pass
