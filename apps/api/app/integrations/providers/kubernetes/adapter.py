import logging
from typing import Dict, Any, List, Optional
from app.models.enums import ProviderType, ResourceType, ResourceStatus
from app.integrations.adapter import ProviderAdapter
from app.integrations.models import IntegrationCapability, DiscoveredResource
from app.integrations.capabilities import ProviderCapabilityRegistryEntry
from app.integrations.exceptions import ProviderError

from .client import KubernetesClient
from .errors import KubernetesConfigurationError, KubernetesProviderError
from .schemas import KubernetesConfigSchema
from .resource_mapper import (
    map_node, map_namespace, map_pod, map_deployment, map_service,
    map_replicaset, map_daemonset, map_statefulset, map_job, map_cronjob,
    map_configmap, map_secret, map_ingress
)

logger = logging.getLogger(__name__)

class KubernetesProviderAdapter(ProviderAdapter):
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.KUBERNETES
        
    def get_capabilities(self) -> IntegrationCapability:
        return IntegrationCapability(
            resource_discovery=True,
            resource_read=True,
            metrics_read=False,
            logs_read=False,
            alerts_read=False,
            health_check=True
        )

    def get_provider_capabilities(self) -> ProviderCapabilityRegistryEntry:
        return ProviderCapabilityRegistryEntry(
            provider=ProviderType.KUBERNETES,
            display_name="Kubernetes",
            version="1.30",
            capabilities=[
                "health_check", "resource_discovery", "resource_read",
                "workload_management", "scaling", "deployment_management"
            ],
            resources=[
                ResourceType.KUBERNETES_NODE, ResourceType.KUBERNETES_NAMESPACE,
                ResourceType.KUBERNETES_POD, ResourceType.KUBERNETES_DEPLOYMENT,
                ResourceType.KUBERNETES_SERVICE, ResourceType.KUBERNETES_REPLICA_SET,
                ResourceType.KUBERNETES_DAEMON_SET, ResourceType.KUBERNETES_STATEFUL_SET,
                ResourceType.KUBERNETES_JOB, ResourceType.KUBERNETES_CRON_JOB,
                ResourceType.KUBERNETES_CONFIG_MAP, ResourceType.KUBERNETES_SECRET,
                ResourceType.KUBERNETES_INGRESS
            ],
            read_operations=[
                "kubernetes_collect_pod_information",
                "kubernetes_collect_deployment_information",
                "kubernetes_collect_service_information"
            ],
            mutation_operations=[
                "kubernetes_scale_deployment",
                "kubernetes_restart_pod",
                "kubernetes_restart_deployment",
                "kubernetes_pause_deployment",
                "kubernetes_resume_deployment"
            ],
            authentication_requirements=["base_url", "bearer_token"]
        )

    def _get_client(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> KubernetesClient:
        cfg = KubernetesConfigSchema(**config)
        
        # Real token should be extracted from secrets
        token = secrets.get("bearer_token")
        if not token:
            token = cfg.bearer_token
            
        return KubernetesClient(
            base_url=cfg.base_url,
            token=token,
            verify_tls=cfg.verify_tls,
            ca_cert=cfg.ca_certificate
        )

    def validate_connection(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        try:
            client = self._get_client(config, secrets)
            version = client.get_version()
            logger.info(f"Successfully connected to Kubernetes API: {version.get('gitVersion')}")
            return True
        except KubernetesProviderError as e:
            logger.error(f"Failed to validate Kubernetes connection: {str(e)}")
            raise ProviderError(f"Validation failed: {str(e)}")

    def discover_resources(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[DiscoveredResource]:
        client = self._get_client(config, secrets)
        resources = []
        
        # Nodes
        for node in client.list_nodes():
            mapped = map_node(node)
            resources.append(self._to_discovered(mapped))
            
        # Namespaces
        for namespace in client.list_namespaces():
            mapped = map_namespace(namespace)
            resources.append(self._to_discovered(mapped))
            
        # Pods
        for pod in client.list_pods():
            mapped = map_pod(pod)
            resources.append(self._to_discovered(mapped))
            
        # Deployments
        for deploy in client.list_deployments():
            mapped = map_deployment(deploy)
            resources.append(self._to_discovered(mapped))
            
        # Services
        for svc in client.list_services():
            mapped = map_service(svc)
            resources.append(self._to_discovered(mapped))

        # ReplicaSets
        for rs in client.list_replicasets():
            mapped = map_replicaset(rs)
            resources.append(self._to_discovered(mapped))

        # DaemonSets
        for ds in client.list_daemonsets():
            mapped = map_daemonset(ds)
            resources.append(self._to_discovered(mapped))

        # StatefulSets
        for ss in client.list_statefulsets():
            mapped = map_statefulset(ss)
            resources.append(self._to_discovered(mapped))

        # Jobs
        for job in client.list_jobs():
            mapped = map_job(job)
            resources.append(self._to_discovered(mapped))

        # CronJobs
        for cj in client.list_cronjobs():
            mapped = map_cronjob(cj)
            resources.append(self._to_discovered(mapped))

        # ConfigMaps
        for cm in client.list_configmaps():
            mapped = map_configmap(cm)
            resources.append(self._to_discovered(mapped))

        # Secrets (Metadata Only)
        for secret in client.list_secrets_metadata():
            mapped = map_secret(secret)
            resources.append(self._to_discovered(mapped))

        # Ingress
        for ingress in client.list_ingress():
            mapped = map_ingress(ingress)
            resources.append(self._to_discovered(mapped))
            
        # Optional: hierarchical processing for parent_id based on namespace
        # (Could map things like Pod -> Node or Resource -> Namespace)
        namespace_map = {}
        for r in resources:
            if r.resource_type == ResourceType.KUBERNETES_NAMESPACE:
                namespace_map[r.metadata.get("name")] = r.external_id

        for r in resources:
            if r.resource_type not in (ResourceType.KUBERNETES_NODE, ResourceType.KUBERNETES_NAMESPACE):
                ns = r.metadata.get("namespace")
                if ns and ns in namespace_map:
                    r.parent_external_id = namespace_map[ns]

        return resources

    def read_resource(self, config: Dict[str, Any], secrets: Dict[str, Any], external_id: str) -> Optional[Dict[str, Any]]:
        client = self._get_client(config, secrets)
        parts = external_id.split("/")
        if len(parts) < 3:
            return None
            
        kind = parts[1]
        try:
            if kind == "deployment" and len(parts) == 4:
                namespace, name = parts[2], parts[3]
                deploy = client.get_deployment(namespace, name)
                return map_deployment(deploy)["metadata"]
                
            if kind == "pod" and len(parts) == 4:
                namespace, name = parts[2], parts[3]
                pod = client.get_pod(namespace, name)
                return map_pod(pod)["metadata"]
        except KubernetesProviderError:
            return None
            
        return None

    def _to_discovered(self, mapped: Dict[str, Any], parent_external_id: Optional[str] = None) -> DiscoveredResource:
        return DiscoveredResource(
            provider=ProviderType.KUBERNETES,
            external_id=mapped["external_id"],
            name=mapped["name"],
            display_name=mapped["name"],
            resource_type=mapped["resource_type"],
            status=ResourceStatus.ACTIVE,
            description=f"Kubernetes {mapped['resource_type'].value} - {mapped['name']}",
            metadata=mapped["metadata"],
            parent_external_id=parent_external_id
        )
