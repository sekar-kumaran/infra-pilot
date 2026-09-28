from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.models.enums import ProviderType, ResourceType

class ProviderCapabilityRegistryEntry(BaseModel):
    provider: ProviderType
    display_name: str
    version: str
    status: str = "healthy"
    capabilities: List[str] = Field(default_factory=list)
    resources: List[ResourceType] = Field(default_factory=list)
    read_operations: List[str] = Field(default_factory=list)
    mutation_operations: List[str] = Field(default_factory=list)
    authentication_requirements: List[str] = Field(default_factory=list)

class ProviderCapabilityRegistry:
    _entries: Dict[ProviderType, ProviderCapabilityRegistryEntry] = {}

    @classmethod
    def register(cls, entry: ProviderCapabilityRegistryEntry):
        cls._entries[entry.provider] = entry

    @classmethod
    def get_capabilities(cls, provider: ProviderType) -> Optional[ProviderCapabilityRegistryEntry]:
        return cls._entries.get(provider)

    @classmethod
    def get_all(cls) -> List[ProviderCapabilityRegistryEntry]:
        return list(cls._entries.values())
