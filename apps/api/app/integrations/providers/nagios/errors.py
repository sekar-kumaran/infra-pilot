from app.integrations.exceptions import ProviderError

class NagiosProviderError(ProviderError):
    """Base exception for Nagios provider errors."""
    pass

class NagiosAuthenticationError(NagiosProviderError):
    """Raised when authentication with Nagios fails."""
    pass

class NagiosConnectionError(NagiosProviderError):
    """Raised when connection to Nagios fails."""
    pass

class NagiosParserError(NagiosProviderError):
    """Raised when parsing Nagios status data fails."""
    pass
