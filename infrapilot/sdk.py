"""InfraPilot v2.6.0 Python SDK (`InfraPilotClient` & `InfraPilotToolAgent`)."""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from .store import ControlPlaneStore, DEFAULT_DB_PATH


@dataclass
class ToolActionResult:
    success: bool
    action: str
    message: str
    output: Dict[str, Any] = field(default_factory=dict)


class InfraPilotClient:
    def __init__(self, api_url: str = "http://127.0.0.1:8000/api/v1", db_path: str = DEFAULT_DB_PATH):
        self.api_url = api_url
        self.store = ControlPlaneStore(db_path=db_path)


class InfraPilotToolAgent:
    def __init__(
        self,
        app_name: str,
        endpoint_url: str,
        tool_name: Optional[str] = None,
        description: str = "",
        owner_team: str = "Platform Engineering",
        control_plane_url: str = "http://127.0.0.1:8000/api/v1",
    ):
        self.app_name = app_name
        self.tool_name = tool_name or f"{app_name} SDK Agent"
        self.endpoint_url = endpoint_url
        self.description = description
        self.owner_team = owner_team
        self.client = InfraPilotClient(api_url=control_plane_url)
        self.actions: Dict[str, Callable[..., ToolActionResult]] = {}

    def action(self, name: str, risk: str = "LOW", requires_approval: bool = False, description: str = ""):
        def decorator(fn: Callable[..., ToolActionResult]):
            self.actions[name] = fn
            return fn
        return decorator

    def connect_to_control_plane(self, resources: Optional[List[Dict[str, Any]]] = None):
        integration = self.client.store.create_integration(
            name=self.tool_name,
            provider="CUSTOM_TOOL",
            endpoint=self.endpoint_url,
            description=self.description or f"SDK Agent for {self.app_name}",
        )
        for r in (resources or []):
            self.client.store.register_resource(
                name=r.get("name", "service-container"),
                provider=r.get("provider", "docker"),
                resource_type=r.get("resource_type", "CONTAINER"),
                metadata=r.get("metadata", {}),
            )
        return integration

    def execute_action(self, name: str, parameters: Optional[Dict[str, Any]] = None) -> ToolActionResult:
        fn = self.actions.get(name)
        if not fn:
            return ToolActionResult(success=False, action=name, message=f"Action {name} not registered")
        return fn(**(parameters or {}))
