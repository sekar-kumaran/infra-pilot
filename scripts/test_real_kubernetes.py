#!/usr/bin/env python3
import os
import sys
import logging

# Add the apps/api directory to sys.path so we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__), "../apps/api"))

from app.integrations.providers.kubernetes.client import KubernetesClient
from app.integrations.providers.kubernetes.errors import KubernetesProviderError
from app.integrations.providers.kubernetes.resource_mapper import (
    map_node, map_namespace, map_pod, map_deployment, map_service
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    base_url = os.environ.get("KUBERNETES_REAL_URL")
    token = os.environ.get("KUBERNETES_REAL_TOKEN")
    verify_tls_str = os.environ.get("KUBERNETES_REAL_VERIFY_TLS", "true").lower()
    verify_tls = verify_tls_str in ["true", "1", "yes"]
    allow_mutation = os.environ.get("KUBERNETES_ALLOW_REAL_MUTATION", "false").lower() == "true"
    
    if not base_url or not token:
        logger.error("KUBERNETES_REAL_URL and KUBERNETES_REAL_TOKEN environment variables must be set.")
        sys.exit(1)
        
    client = KubernetesClient(base_url=base_url, token=token, verify_tls=verify_tls)
    
    results = {
        "Connection": "FAIL",
        "Authentication": "FAIL",
        "Version": "FAIL",
        "Namespaces": "FAIL",
        "Nodes": "FAIL",
        "Pods": "FAIL",
        "Deployments": "FAIL",
        "Services": "FAIL",
        "Resource Mapping": "FAIL"
    }
    
    try:
        # Connection, Auth, Version
        version = client.get_version()
        results["Connection"] = "PASS"
        results["Authentication"] = "PASS"
        results["Version"] = "PASS"
        logger.info(f"Connected to Kubernetes version: {version.get('gitVersion')}")
        
        # Namespaces
        namespaces = client.list_namespaces()
        results["Namespaces"] = "PASS"
        logger.info(f"Discovered {len(namespaces)} namespaces.")
        
        # Nodes
        nodes = client.list_nodes()
        results["Nodes"] = "PASS"
        logger.info(f"Discovered {len(nodes)} nodes.")
        
        # Pods
        pods = client.list_pods()
        results["Pods"] = "PASS"
        logger.info(f"Discovered {len(pods)} pods.")
        
        # Deployments
        deployments = client.list_deployments()
        results["Deployments"] = "PASS"
        logger.info(f"Discovered {len(deployments)} deployments.")
        
        # Services
        services = client.list_services()
        results["Services"] = "PASS"
        logger.info(f"Discovered {len(services)} services.")
        
        # Resource Mapping
        if nodes:
            map_node(nodes[0])
        if namespaces:
            map_namespace(namespaces[0])
        if pods:
            map_pod(pods[0])
        if deployments:
            map_deployment(deployments[0])
        if services:
            map_service(services[0])
        results["Resource Mapping"] = "PASS"
        logger.info("Resource mapping completed successfully.")
        
        if allow_mutation:
            target_ns = os.environ.get("KUBERNETES_MUTATION_NAMESPACE")
            target_deploy = os.environ.get("KUBERNETES_MUTATION_DEPLOYMENT")
            target_replicas = os.environ.get("KUBERNETES_MUTATION_REPLICAS")
            if target_ns and target_deploy and target_replicas:
                logger.warning(f"Performing mutation: Scaling {target_deploy} in {target_ns} to {target_replicas}")
                client.scale_deployment(target_ns, target_deploy, int(target_replicas))
                logger.info("Mutation issued successfully.")
            else:
                logger.info("Mutation allowed, but target namespace/deployment/replicas not provided.")
        
    except KubernetesProviderError as e:
        logger.error(f"Kubernetes Provider Error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        
    print("\n--- Final Acceptance Results ---")
    for k, v in results.items():
        print(f"{k}: {v}")
        
    if all(v == "PASS" for v in results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
