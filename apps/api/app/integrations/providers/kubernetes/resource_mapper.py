from typing import Dict, Any, List
from app.models.enums import ResourceType

def map_node(node: Dict[str, Any]) -> Dict[str, Any]:
    metadata = node.get("metadata", {})
    status = node.get("status", {})
    
    name = metadata.get("name", "unknown")
    
    conditions = status.get("conditions", [])
    ready_status = "Unknown"
    for condition in conditions:
        if condition.get("type") == "Ready":
            ready_status = condition.get("status")
            break
            
    node_info = status.get("nodeInfo", {})
    kubelet_version = node_info.get("kubeletVersion", "unknown")
            
    return {
        "name": name,
        "external_id": f"kubernetes/node/{name}",
        "resource_type": ResourceType.KUBERNETES_NODE,
        "metadata": {
            "name": name,
            "ready_status": ready_status,
            "kubernetes_version": kubelet_version
        }
    }

def map_namespace(namespace: Dict[str, Any]) -> Dict[str, Any]:
    metadata = namespace.get("metadata", {})
    status = namespace.get("status", {})
    
    name = metadata.get("name", "unknown")
    phase = status.get("phase", "Unknown")
    
    return {
        "name": name,
        "external_id": f"kubernetes/namespace/{name}",
        "resource_type": ResourceType.KUBERNETES_NAMESPACE,
        "metadata": {
            "name": name,
            "phase": phase
        }
    }

def map_pod(pod: Dict[str, Any]) -> Dict[str, Any]:
    metadata = pod.get("metadata", {})
    status = pod.get("status", {})
    spec = pod.get("spec", {})
    
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    phase = status.get("phase", "Unknown")
    node_name = spec.get("nodeName", "unknown")
    
    container_statuses = status.get("containerStatuses", [])
    restart_count = sum(c.get("restartCount", 0) for c in container_statuses)
    
    conditions = status.get("conditions", [])
    ready_state = "False"
    for condition in conditions:
        if condition.get("type") == "Ready":
            ready_state = condition.get("status")
            break
            
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/pod/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_POD,
        "metadata": {
            "name": name,
            "namespace": namespace,
            "phase": phase,
            "ready_state": ready_state,
            "node_name": node_name,
            "restart_count": restart_count
        }
    }

def map_deployment(deployment: Dict[str, Any]) -> Dict[str, Any]:
    metadata = deployment.get("metadata", {})
    status = deployment.get("status", {})
    spec = deployment.get("spec", {})
    
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    
    replicas = spec.get("replicas", 0)
    ready_replicas = status.get("readyReplicas", 0)
    available_replicas = status.get("availableReplicas", 0)
    updated_replicas = status.get("updatedReplicas", 0)
    
    strategy = spec.get("strategy", {}).get("type", "Unknown")
    
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/deployment/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_DEPLOYMENT,
        "metadata": {
            "name": name,
            "namespace": namespace,
            "replicas": replicas,
            "ready_replicas": ready_replicas,
            "available_replicas": available_replicas,
            "updated_replicas": updated_replicas,
            "strategy": strategy
        }
    }

def map_service(service: Dict[str, Any]) -> Dict[str, Any]:
    metadata = service.get("metadata", {})
    spec = service.get("spec", {})
    
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    
    service_type = spec.get("type", "Unknown")
    cluster_ip = spec.get("clusterIP", "None")
    
    ports = []
    for port in spec.get("ports", []):
        ports.append({
            "port": port.get("port"),
            "protocol": port.get("protocol"),
            "targetPort": port.get("targetPort")
        })
        
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/service/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_SERVICE,
        "metadata": {
            "name": name,
            "namespace": namespace,
            "type": service_type,
            "cluster_ip": cluster_ip,
            "ports": ports
        }
    }

def map_replicaset(rs: Dict[str, Any]) -> Dict[str, Any]:
    metadata = rs.get("metadata", {})
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/replicaset/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_REPLICA_SET,
        "metadata": {"name": name, "namespace": namespace}
    }

def map_daemonset(ds: Dict[str, Any]) -> Dict[str, Any]:
    metadata = ds.get("metadata", {})
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/daemonset/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_DAEMON_SET,
        "metadata": {"name": name, "namespace": namespace}
    }

def map_statefulset(ss: Dict[str, Any]) -> Dict[str, Any]:
    metadata = ss.get("metadata", {})
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/statefulset/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_STATEFUL_SET,
        "metadata": {"name": name, "namespace": namespace}
    }

def map_job(job: Dict[str, Any]) -> Dict[str, Any]:
    metadata = job.get("metadata", {})
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/job/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_JOB,
        "metadata": {"name": name, "namespace": namespace}
    }

def map_cronjob(cj: Dict[str, Any]) -> Dict[str, Any]:
    metadata = cj.get("metadata", {})
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/cronjob/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_CRON_JOB,
        "metadata": {"name": name, "namespace": namespace}
    }

def map_configmap(cm: Dict[str, Any]) -> Dict[str, Any]:
    metadata = cm.get("metadata", {})
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/configmap/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_CONFIG_MAP,
        "metadata": {"name": name, "namespace": namespace}
    }

def map_secret(secret: Dict[str, Any]) -> Dict[str, Any]:
    metadata = secret.get("metadata", {})
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    secret_type = secret.get("type", "Opaque")
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/secret/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_SECRET,
        "metadata": {"name": name, "namespace": namespace, "type": secret_type}
    }

def map_ingress(ingress: Dict[str, Any]) -> Dict[str, Any]:
    metadata = ingress.get("metadata", {})
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "default")
    return {
        "name": f"{namespace}/{name}",
        "external_id": f"kubernetes/ingress/{namespace}/{name}",
        "resource_type": ResourceType.KUBERNETES_INGRESS,
        "metadata": {"name": name, "namespace": namespace}
    }
