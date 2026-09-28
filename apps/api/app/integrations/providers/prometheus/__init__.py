from app.integrations.registry import AdapterRegistry
from app.models.enums import ProviderType
from .adapter import PrometheusAdapter

def register():
    """
    Registers the Prometheus adapter with the global AdapterRegistry.
    """
    AdapterRegistry.register(ProviderType.PROMETHEUS, PrometheusAdapter())
