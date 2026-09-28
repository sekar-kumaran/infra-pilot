class DockerExecutorError(Exception):
    """Base error for Docker automation executor failures."""
    pass

class DockerResourceNotFoundError(DockerExecutorError):
    pass

class DockerInvalidActionError(DockerExecutorError):
    pass

class DockerVerificationError(DockerExecutorError):
    pass
