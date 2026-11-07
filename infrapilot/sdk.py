"""
InfraPilot SDK — Package interface for connecting any application or microservice
to the InfraPilot Control Plane as a monitored Application & controllable DevOps Tool.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
import requests
from .store import ControlPlaneStore, DEFAULT_DB_PATH


@dataclass
class ToolActionResult:
    success: bool
    action: str
    message: str
    output: Dict[str, Any] = field(default_factory=dict)


class InfraPilotClient:
    """
    Unified client for interacting with the InfraPilot Control Plane via HTTP REST API
    with automatic fallback to the local ControlPlaneStore.
    """

    def __init__(
        self,
        api_url: str = "http://127.0.0.1:8000/api/v1",
        token: Optional[str] = None,
        db_path: str = DEFAULT_DB_PATH,
        prefer_http: bool = False,
    ):
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.store = ControlPlaneStore(db_path=db_path)
        self.prefer_http = prefer_http

    def get_metrics_summary(self) -> Dict[str, Any]:
        return self.store.get_metrics_summary()

    def register_application(
        self,
        name: str,
        description: str = "",
        endpoint_url: str = "",
        owner_team: str = "Platform Engineering",
        app_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.store.create_application(
            name=name,
            description=description,
            endpoint_url=endpoint_url,
            owner_team=owner_team,
            sdk_connected=True,
            app_id=app_id,
        )

    def register_tool(
        self,
        name: str,
        provider: str = "custom_tool",
        description: str = "",
        configuration: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.store.create_integration(
            name=name,
            provider=provider,
            description=description,
            configuration=configuration or {},
        )

    def register_resource(
        self,
        name: str,
        provider: str,
        resource_type: str,
        external_id: str,
        display_name: Optional[str] = None,
        application_id: Optional[str] = None,
        integration_id: Optional[str] = None,
        status: str = "ACTIVE",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.store.register_resource(
            name=name,
            provider=provider,
            resource_type=resource_type,
            external_id=external_id,
            display_name=display_name,
            application_id=application_id,
            integration_id=integration_id,
            status=status,
            description=description,
            metadata=metadata,
        )

    def get_logs(self, target: str, level: Optional[str] = None, query: Optional[str] = None, tail: int = 100) -> Dict[str, Any]:
        return self.store.get_target_logs(target=target, level=level, query=query, tail=tail)

    def exec_command(self, target: str, command: str, shell: str = "bash") -> Dict[str, Any]:
        return self.store.exec_in_target(target=target, command=command, shell=shell)

    def send_prometheus_alert(
        self,
        alertname: str,
        severity: str,
        instance: str,
        job: str,
        summary: str,
        description: str,
        resource_external_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.store.ingest_event(
            provider="prometheus",
            event_type="prometheus_firing",
            payload={
                "title": f"[{alertname}] {summary}",
                "description": description,
                "severity": severity.upper(),
                "labels": {"alertname": alertname, "instance": instance, "job": job},
                "resource": resource_external_id,
            },
            resource_external_id=resource_external_id,
        )

    def trigger_playbook(
        self,
        playbook_id: str,
        incident_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        force_auto_approve: bool = False,
    ) -> Dict[str, Any]:
        return self.store.trigger_execution(
            playbook_id=playbook_id,
            trigger_type="SDK_AUTO",
            trigger_source="infrapilot_sdk",
            incident_id=incident_id,
            resource_id=resource_id,
            force_auto_approve=force_auto_approve,
        )


class InfraPilotToolAgent:
    """
    Embeddable DevOps Tool Agent that turns any application or microservice into
    a first-class controllable tool in the InfraPilot Control Plane.
    """

    def __init__(
        self,
        app_name: str,
        tool_name: str,
        endpoint_url: str,
        description: str = "",
        owner_team: str = "Platform Engineering",
        control_plane_url: str = "http://127.0.0.1:8000/api/v1",
        db_path: str = DEFAULT_DB_PATH,
    ):
        self.app_name = app_name
        self.tool_name = tool_name
        self.endpoint_url = endpoint_url
        self.description = description
        self.owner_team = owner_team
        self.client = InfraPilotClient(api_url=control_plane_url, db_path=db_path)
        self.actions: Dict[str, Dict[str, Any]] = {}
        self.app_record: Optional[Dict[str, Any]] = None
        self.tool_record: Optional[Dict[str, Any]] = None

    def action(self, name: str, risk: str = "LOW", description: str = "", requires_approval: bool = False):
        def decorator(fn: Callable):
            self.actions[name] = {
                "name": name,
                "risk": risk.upper(),
                "description": description or fn.__doc__ or name,
                "requires_approval": requires_approval,
                "handler": fn,
            }
            return fn
        return decorator

    def execute_action(self, action_name: str, parameters: Optional[Dict[str, Any]] = None) -> ToolActionResult:
        if action_name not in self.actions:
            return ToolActionResult(
                success=False,
                action=action_name,
                message=f"Unknown tool action: {action_name}",
                output={"available_actions": list(self.actions.keys())},
            )
        entry = self.actions[action_name]
        result = entry["handler"](**(parameters or {}))
        if isinstance(result, ToolActionResult):
            return result
        return ToolActionResult(
            success=True,
            action=action_name,
            message=f"Executed {action_name} successfully",
            output=result if isinstance(result, dict) else {"result": result},
        )

    def connect_to_control_plane(self, resources: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        self.app_record = self.client.register_application(
            name=self.app_name,
            description=self.description,
            endpoint_url=self.endpoint_url,
            owner_team=self.owner_team,
        )
        self.tool_record = self.client.register_tool(
            name=self.tool_name,
            provider="custom_tool",
            description=f"SDK Tool Agent for {self.app_name}",
            configuration={
                "base_url": self.endpoint_url,
                "app_id": self.app_record["id"],
                "registered_actions": [
                    {"name": k, "risk": v["risk"], "description": v["description"]}
                    for k, v in self.actions.items()
                ],
            },
        )
        registered_resources = []
        for res in (resources or []):
            r = self.client.register_resource(
                name=res["name"],
                provider=res.get("provider", "docker"),
                resource_type=res.get("resource_type", "CONTAINER"),
                external_id=res.get("external_id", f"sdk/{res['name']}"),
                display_name=res.get("display_name", res["name"]),
                application_id=self.app_record["id"],
                integration_id=self.tool_record["id"],
                status=res.get("status", "ACTIVE"),
                description=res.get("description", ""),
                metadata=res.get("metadata", {}),
            )
            registered_resources.append(r)

        return {
            "application": self.app_record,
            "tool_integration": self.tool_record,
            "resources": registered_resources,
            "actions_registered": list(self.actions.keys()),
        }
