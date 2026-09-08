"""Lightweight service discovery for the chapter's conceptual ANP example."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ServiceInfo:
    """Describe one discoverable Agent service."""

    service_id: str
    service_type: str
    endpoint: str
    service_name: str | None = None
    capabilities: tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in ("service_id", "service_type", "endpoint"):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} 不能为空")

    @property
    def display_name(self) -> str:
        """Return an explicit service name or fall back to its identifier."""
        return self.service_name or self.service_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a serializable service description."""
        return {
            "service_id": self.service_id,
            "service_type": self.service_type,
            "endpoint": self.endpoint,
            "service_name": self.display_name,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }


class ANPDiscovery:
    """In-memory registry illustrating registration and discovery."""

    def __init__(self) -> None:
        self._services: Dict[str, ServiceInfo] = {}

    def register_service(self, service: ServiceInfo) -> bool:
        """Register or update a service by stable identifier."""
        self._services[service.service_id] = service
        return True

    def unregister_service(self, service_id: str) -> bool:
        """Remove a service and report whether it existed."""
        return self._services.pop(service_id, None) is not None

    def discover_services(
        self,
        service_type: str | None = None,
        filters: Dict[str, Any] | None = None,
    ) -> List[ServiceInfo]:
        """Find services by type and exact metadata matches."""
        services = list(self._services.values())
        if service_type:
            services = [
                service
                for service in services
                if service.service_type == service_type
            ]
        if filters is not None and not isinstance(filters, dict):
            raise TypeError("filters 必须是字典")
        if filters:
            services = [
                service
                for service in services
                if all(
                    service.metadata.get(key) == value
                    for key, value in filters.items()
                )
            ]
        return sorted(services, key=lambda service: service.service_id)

    def get_service(self, service_id: str) -> ServiceInfo | None:
        """Return one service by identifier."""
        return self._services.get(service_id)

    def list_all_services(self) -> List[ServiceInfo]:
        """Return all services in deterministic identifier order."""
        return self.discover_services()
