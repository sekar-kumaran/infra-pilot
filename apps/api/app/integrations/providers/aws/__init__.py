from app.models.enums import ProviderType
from app.integrations.registry import AdapterRegistry
from app.integrations.providers.aws.adapter import AWSAdapter
from app.integrations.providers.aws.capabilities import AWS_CAPABILITIES

def register_provider():
    AdapterRegistry.register(ProviderType.AWS, AWSAdapter())

# Export for capability registry
capabilities = AWS_CAPABILITIES
