from typing import Dict, Any, List
import logging

from app.models.enums import ProviderType, ResourceType, ResourceStatus
from app.integrations.adapter import ProviderAdapter
from app.integrations.models import IntegrationCapability, DiscoveredResource
from app.integrations.capabilities import ProviderCapabilityRegistryEntry
from app.integrations.exceptions import ProviderError

from .client import PrometheusClient
from .schemas import PrometheusIntegrationConfig

logger = logging.getLogger(__name__)

class PrometheusAdapter(ProviderAdapter):
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.PROMETHEUS
        
    def get_capabilities(self) -> IntegrationCapability:
        return IntegrationCapability(
            resource_discovery=True,
            resource_read=True,
            metrics_read=True,
            logs_read=False,
            alerts_read=True,
            health_check=True
        )

    def get_provider_capabilities(self) -> ProviderCapabilityRegistryEntry:
        return ProviderCapabilityRegistryEntry(
            provider=ProviderType.PROMETHEUS,
            display_name="Prometheus",
            version="1.0",
            capabilities=["health_check", "metrics_read", "alerts_read", "resource_discovery"],
            resources=[],
            read_operations=[],
            mutation_operations=[],
            authentication_requirements=["base_url"]
        )

    def validate_connection(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        try:
            client = self._get_client(config, secrets)
            buildinfo = client.get_buildinfo()
            return True
        except ProviderError as e:
            logger.error(f"Prometheus validation failed: {str(e)}")
            raise

    def discover_resources(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[DiscoveredResource]:
        client = self._get_client(config, secrets)
        targets_data = client.get_targets()
        
        active_targets = targets_data.get("activeTargets", [])
        resources = []
        
        for target in active_targets:
            labels = target.get("labels", {})
            job = labels.get("job", "unknown")
            instance = labels.get("instance", "unknown")
            
            external_id = f"{job}/{instance}"
            
            # Map Prometheus health to resource status
            health = target.get("health", "unknown").lower()
            if health == "up":
                status = ResourceStatus.ACTIVE
            elif health == "down":
                status = ResourceStatus.FAILED
            else:
                status = ResourceStatus.UNKNOWN
                
            # Filter metadata to keep sanitized target info
            metadata = {
                "job": job,
                "instance": instance,
                "scrapeUrl": target.get("scrapeUrl"),
                "scrapePool": target.get("scrapePool"),
                "labels": labels,
                "health": health
            }

            resource = DiscoveredResource(
                provider=ProviderType.PROMETHEUS,
                external_id=external_id,
                name=f"{job}-{instance}",
                display_name=instance,
                resource_type=ResourceType.SERVICE, # Map generic targets as SERVICE
                status=status,
                description=f"Prometheus target {job} on {instance}",
                metadata=metadata
            )
            resources.append(resource)
            
        return resources
        
    def _get_client(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> PrometheusClient:
        cfg = PrometheusIntegrationConfig(**config)
        return PrometheusClient(
            base_url=cfg.base_url,
            secrets=secrets,
            timeout=cfg.timeout_seconds,
            tls_verify=cfg.tls_verify
        )

    # Note: metrics read handling will be handled by a specific method in the adapter or directly in endpoint.
    def read_metrics(self, config: Dict[str, Any], secrets: Dict[str, Any], metric_type: str) -> Dict[str, Any]:
        """
        Execute a safe, pre-validated query based on metric_type.
        """
        APPROVED_METRICS = {
            "target_up": "up",
            "cpu_usage": 'rate(node_cpu_seconds_total{mode="idle"}[5m])',
            "memory_usage": '1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)'
        }
        
        if metric_type not in APPROVED_METRICS:
            raise ProviderError(f"Metric type '{metric_type}' is not supported by Prometheus provider.")
            
        query = APPROVED_METRICS[metric_type]
        
        client = self._get_client(config, secrets)
        try:
            result = client.query(query)
            if not result.get("result"):
                return {"status": "unavailable", "message": f"Metric '{metric_type}' is unavailable on this Prometheus server.", "data": []}
            
            return {"status": "success", "data": result.get("result")}
        except Exception as e:
            raise ProviderError(f"Failed to read metric '{metric_type}': {str(e)}")
        
    def get_alerts(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[Dict[str, Any]]:
        client = self._get_client(config, secrets)
        return client.get_alerts().get("alerts", [])
