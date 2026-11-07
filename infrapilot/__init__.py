"""
InfraPilot — Enterprise DevOps & SRE Control Plane Package (v2.2.0)
Unified Tool Orchestration, Container/Pod Exec, Log Multiplexing, Jenkins & GitHub Copilot API Control, SDK, and CLI.
"""

__version__ = "2.2.0"

from .sdk import InfraPilotClient, InfraPilotToolAgent, ToolActionResult
from .store import ControlPlaneStore

# Backward-compatible aliases
InfraTrackClient = InfraPilotClient
InfraTrackToolAgent = InfraPilotToolAgent

__all__ = [
    "__version__",
    "InfraPilotClient",
    "InfraPilotToolAgent",
    "ToolActionResult",
    "ControlPlaneStore",
    "InfraTrackClient",
    "InfraTrackToolAgent",
]
