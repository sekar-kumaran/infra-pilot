from typing import Dict, Any, List
import logging
import json

from app.models.enums import ProviderType, ResourceType, ResourceStatus
from app.integrations.adapter import ProviderAdapter
from app.integrations.models import IntegrationCapability, DiscoveredResource
from app.integrations.capabilities import ProviderCapabilityRegistryEntry
from app.integrations.providers.exceptions import ProviderExecutionException

from .client import GrafanaClient

logger = logging.getLogger(__name__)

class GrafanaAdapter(ProviderAdapter):
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GRAFANA
        
    def get_capabilities(self) -> IntegrationCapability:
        return IntegrationCapability(
            resource_discovery=True,
            resource_read=True,
            metrics_read=False,
            logs_read=False,
            alerts_read=True,
            health_check=True
        )

    def get_provider_capabilities(self) -> ProviderCapabilityRegistryEntry:
        return ProviderCapabilityRegistryEntry(
            provider=ProviderType.GRAFANA,
            display_name="Grafana",
            version="1.0",
            capabilities=["health_check", "resource_discovery", "resource_read", "dashboard_read", "alert_read", "datasource_read"],
            resources=[
                ResourceType.OBSERVABILITY_DASHBOARD.value, 
                ResourceType.OBSERVABILITY_ALERT_RULE.value, 
                ResourceType.OBSERVABILITY_DATASOURCE.value, 
                ResourceType.OBSERVABILITY_FOLDER.value
            ],
            read_operations=[],
            mutation_operations=[],
            authentication_requirements=["url", "token"]
        )

    def validate_connection(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> bool:
        client = self._get_client(config, secrets)
        return client.health_check()

    def discover_resources(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> List[DiscoveredResource]:
        client = self._get_client(config, secrets)
        resources = []
        
        # 1. Folders
        folders = client.list_folders()
        for folder in folders:
            uid = folder.get("uid")
            if uid:
                resources.append(DiscoveredResource(
                    name=folder.get("title", f"Folder {uid}"),
                    resource_type=ResourceType.OBSERVABILITY_FOLDER,
                    external_id=f"grafana/folder/{uid}",
                    metadata={
                        "uid": uid,
                        "title": folder.get("title"),
                        "url": folder.get("url")
                    },
                    status=ResourceStatus.ACTIVE
                ))
        
        # 2. Dashboards
        dashboards = client.list_dashboards()
        for dash in dashboards:
            uid = dash.get("uid")
            if uid:
                resources.append(DiscoveredResource(
                    name=dash.get("title", f"Dashboard {uid}"),
                    resource_type=ResourceType.OBSERVABILITY_DASHBOARD,
                    external_id=f"grafana/dashboard/{uid}",
                    metadata={
                        "uid": uid,
                        "title": dash.get("title"),
                        "url": dash.get("url"),
                        "folderId": dash.get("folderId"),
                        "folderUid": dash.get("folderUid"),
                        "tags": dash.get("tags", [])
                    },
                    status=ResourceStatus.ACTIVE
                ))
                
        # 3. Alert Rules
        alert_rules = client.list_alert_rules()
        for rule in alert_rules:
            uid = rule.get("uid")
            if uid:
                resources.append(DiscoveredResource(
                    name=rule.get("title", f"Alert {uid}"),
                    resource_type=ResourceType.OBSERVABILITY_ALERT_RULE,
                    external_id=f"grafana/alert-rule/{uid}",
                    metadata={
                        "uid": uid,
                        "title": rule.get("title"),
                        "folderUid": rule.get("folderUID"),
                        "ruleGroup": rule.get("ruleGroup"),
                        "state": rule.get("state")
                    },
                    status=ResourceStatus.ACTIVE
                ))
                
        # 4. Data Sources
        datasources = client.list_datasources()
        for ds in datasources:
            uid = ds.get("uid")
            if uid:
                resources.append(DiscoveredResource(
                    name=ds.get("name", f"Datasource {uid}"),
                    resource_type=ResourceType.OBSERVABILITY_DATASOURCE,
                    external_id=f"grafana/datasource/{uid}",
                    metadata=ds,  # Safe metadata mapped in client
                    status=ResourceStatus.ACTIVE
                ))

        return resources

    def read_resource(self, external_id: str, config: Dict[str, Any], secrets: Dict[str, Any]) -> Dict[str, Any]:
        # Minimal implementation for now; could fetch specific API paths based on external_id
        return {"external_id": external_id}

    def _get_client(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> GrafanaClient:
        # Accept either 'url' or 'base_url' key
        url = config.get("url") or config.get("base_url")
        if not url:
            raise ProviderExecutionException("Grafana URL is required in configuration (url or base_url)")
            
        # Accept 'token', 'api_key', or 'bearer_token' as the auth secret
        token = secrets.get("token") or secrets.get("api_key") or secrets.get("bearer_token")
        if not token:
            raise ProviderExecutionException("Grafana token is required in secrets (token, api_key, or bearer_token)")
            
        verify_tls = config.get("verify_tls", False)  # Default False for local dev
        timeout = config.get("timeout", 15)
        
        return GrafanaClient(url, token, verify_tls, timeout)
