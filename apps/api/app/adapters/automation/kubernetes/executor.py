import logging
from typing import Dict, Any, Tuple
import time

from sqlalchemy.orm import Session
from app.adapters.automation.base import AutomationExecutor
from app.services.action_registry import ActionRegistry
from app.models.resource import InfrastructureResource
from app.models.integration import Integration
from app.models.enums import ProviderType, ResourceType

from app.integrations.providers.kubernetes.client import KubernetesClient
from app.integrations.providers.kubernetes.schemas import KubernetesConfigSchema
from app.core.encryption import decrypt_secret_payload

from .errors import KubernetesValidationError, KubernetesExecutionError
from .models import ScaleDeploymentParams

logger = logging.getLogger(__name__)

class KubernetesAutomationExecutor(AutomationExecutor):
    """
    Real execution provider for Kubernetes operations.
    Complies with AutomationExecutor interface, strictly preventing arbitrary API path execution.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.client = None

    def _get_client_for_resource(self, resource: InfrastructureResource) -> KubernetesClient:
        if resource.provider != ProviderType.KUBERNETES.value:
            raise KubernetesValidationError(f"Target resource must belong to KUBERNETES provider, got {resource.provider}")
            
        integration = self.session.query(Integration).filter(
            Integration.provider == ProviderType.KUBERNETES,
            Integration.environment_id == resource.environment_id
        ).first()
        
        if not integration:
            raise KubernetesValidationError("No active Kubernetes integration found for the environment")
            
        cfg = KubernetesConfigSchema(**(integration.config or {}))
        
        decrypted_token = None
        if integration.secrets:
            secrets = decrypt_secret_payload(integration.secrets)
            decrypted_token = secrets.get("bearer_token")
            
        if not decrypted_token and cfg.bearer_token:
            decrypted_token = cfg.bearer_token
            
        return KubernetesClient(
            base_url=cfg.base_url,
            token=decrypted_token,
            verify_tls=cfg.verify_tls,
            ca_cert=cfg.ca_certificate
        )

    def validate(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        action_def = ActionRegistry.get_action(action_name)
        if not action_def:
            logger.error(f"Action '{action_name}' is not registered.")
            return False
            
        if action_def.executor_name != "kubernetes":
            logger.error(f"Action '{action_name}' is not a kubernetes action.")
            return False
            
        if not ActionRegistry.validate_parameters(action_name, parameters):
            logger.error(f"Action '{action_name}' failed parameter schema validation.")
            return False
            
        resource = parameters.get("resource")
        if not resource or not isinstance(resource, InfrastructureResource):
            logger.error("Target resource is missing or invalid.")
            return False
            
        # Target validation
        if action_name in ["kubernetes_scale_deployment", "kubernetes_collect_deployment_information", "kubernetes_verify_deployment"]:
            if resource.resource_type != ResourceType.KUBERNETES_DEPLOYMENT.value:
                logger.error(f"Action {action_name} requires a DEPLOYMENT resource.")
                return False
                
        if action_name in ["kubernetes_restart_pod", "kubernetes_collect_pod_information"]:
            if resource.resource_type != ResourceType.KUBERNETES_POD.value:
                logger.error(f"Action {action_name} requires a POD resource.")
                return False
                
        # Value bounds validation
        if action_name == "kubernetes_scale_deployment":
            try:
                ScaleDeploymentParams(desired_replicas=parameters.get("desired_replicas"))
            except Exception as e:
                logger.error(f"Scale parameter validation failed: {str(e)}")
                return False
                
        return True

    def execute(self, action_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        if not self.validate(action_name, parameters):
            return False, {}, "Validation failed for Kubernetes execution"
            
        resource = parameters.get("resource")
        
        try:
            client = self._get_client_for_resource(resource)
            
            # The resource external_id format is kubernetes/kind/namespace/name
            parts = resource.external_id.split("/")
            if len(parts) < 4:
                return False, {}, "Invalid external_id format for Kubernetes resource"
            namespace = parts[2]
            name = parts[3]
            
            if action_name == "kubernetes_scale_deployment":
                desired = int(parameters.get("desired_replicas"))
                res = client.scale_deployment(namespace, name, desired)
                return True, {"deployment": res.get("metadata", {}).get("name"), "desired_replicas": desired}, ""
                
            elif action_name == "kubernetes_restart_pod":
                client.restart_pod(namespace, name)
                return True, {"pod": name, "namespace": namespace, "status": "delete_issued"}, ""
                
            elif action_name == "kubernetes_collect_deployment_information":
                res = client.get_deployment(namespace, name)
                return True, res, ""
                
            elif action_name == "kubernetes_collect_pod_information":
                res = client.get_pod(namespace, name)
                return True, res, ""
                
            elif action_name == "kubernetes_verify_deployment":
                res = client.get_deployment(namespace, name)
                return True, res.get("status", {}), ""
                
            else:
                return False, {}, f"Unsupported action {action_name}"
                
        except Exception as e:
            logger.error(f"Kubernetes execution failed: {str(e)}")
            return False, {}, str(e)

    def cancel(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        return False

    def verify(self, action_name: str, expected_state: Any, parameters: Dict[str, Any]) -> Tuple[bool, Any, str]:
        resource = parameters.get("resource")
        if not resource:
            return False, {}, "No resource provided for verification"
            
        parts = resource.external_id.split("/")
        if len(parts) < 4:
            return False, {}, "Invalid resource external ID"
        namespace = parts[2]
        name = parts[3]
        
        try:
            client = self._get_client_for_resource(resource)
            
            if action_name == "kubernetes_scale_deployment":
                desired = int(parameters.get("desired_replicas"))
                
                # Bounded polling
                max_attempts = 10
                for attempt in range(max_attempts):
                    deploy = client.get_deployment(namespace, name)
                    status = deploy.get("status", {})
                    spec = deploy.get("spec", {})
                    
                    req_replicas = spec.get("replicas", 0)
                    available = status.get("availableReplicas", 0)
                    ready = status.get("readyReplicas", 0)
                    
                    if req_replicas == desired and available >= desired and ready >= desired:
                        return True, status, "Deployment successfully scaled and ready"
                        
                    time.sleep(2)
                    
                return False, status, f"Timeout verifying deployment scaling to {desired} replicas"
                
            elif action_name == "kubernetes_restart_pod":
                # We wait for the old pod to disappear and potentially a new one to show up if managed by deployment.
                # Strictly speaking, restarting a pod means deleting it. If it's a bare pod, it won't be replaced.
                # If managed, another will be replaced. We just verify the original is gone.
                
                max_attempts = 10
                for attempt in range(max_attempts):
                    try:
                        pod = client.get_pod(namespace, name)
                        phase = pod.get("status", {}).get("phase", "Unknown")
                        # If we can still get it, it must be terminating or running. 
                        # Wait for it to not be found.
                    except Exception as e:
                        if "Not Found" in str(e):
                            return True, {"status": "deleted"}, "Pod successfully terminated"
                    time.sleep(2)
                    
                return False, {}, "Timeout verifying pod termination"

            return True, {}, "Verification not strictly required for this action"
            
        except Exception as e:
            return False, {}, f"Verification error: {str(e)}"
