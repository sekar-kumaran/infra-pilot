class DockerProviderError(Exception):
    """Base exception for Docker provider errors."""
    pass

class DockerConnectionError(DockerProviderError):
    """Raised when unable to connect to the Docker Engine API."""
    pass

class DockerAuthenticationError(DockerProviderError):
    """Raised when authentication with Docker Engine fails."""
    pass

class DockerNotFoundError(DockerProviderError):
    """Raised when a Docker resource (container, image, etc.) is not found."""
    pass

class DockerAPIError(DockerProviderError):
    """Raised when the Docker API returns an unexpected error."""
    pass

class DockerTimeoutError(DockerProviderError):
    """Raised when a request to the Docker API times out."""
    pass
