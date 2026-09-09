"""Service discovery and network graph used by chapter 10.4's ANP practice.

This module completes the interfaces shown in the chapter. It deliberately
models only the teaching example's in-memory directory and routing metadata;
it does not pretend to implement ANP DID authentication or internet crawling.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field, replace
from numbers import Real
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse


def _required_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{name} 不能为空")
    return normalized


def _http_endpoint(endpoint: str) -> str:
    normalized = _required_text("endpoint", endpoint).rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("endpoint 必须是有效的 HTTP(S) 地址")
    return normalized


@dataclass(frozen=True)
class ServiceInfo:
    """Describe one Agent service in the chapter's discovery directory."""

    service_id: str
    service_type: str
    endpoint: str
    service_name: str | None = None
    capabilities: tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "service_id",
            _required_text("service_id", self.service_id),
        )
        object.__setattr__(
            self,
            "service_type",
            _required_text("service_type", self.service_type),
        )
        object.__setattr__(self, "endpoint", _http_endpoint(self.endpoint))
        if self.service_name is not None:
            object.__setattr__(
                self,
                "service_name",
                _required_text("service_name", self.service_name),
            )

        raw_capabilities = (
            (self.capabilities,)
            if isinstance(self.capabilities, str)
            else self.capabilities
        )
        capabilities = tuple(
            dict.fromkeys(
                _required_text("capability", capability)
                for capability in raw_capabilities
            ),
        )
        metadata = dict(self.metadata)
        try:
            json.dumps(metadata, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("metadata 必须可以序列化为 JSON") from exc
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "metadata", metadata)

    @property
    def display_name(self) -> str:
        """Return an explicit service name or fall back to its identifier."""
        return self.service_name or self.service_id

    def supports(self, required_capabilities: Iterable[str]) -> bool:
        """Report whether all requested capabilities are advertised."""
        return set(required_capabilities).issubset(self.capabilities)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a serializable service description."""
        return {
            "service_id": self.service_id,
            "service_name": self.display_name,
            "service_type": self.service_type,
            "capabilities": list(self.capabilities),
            "endpoint": self.endpoint,
            "metadata": dict(self.metadata),
        }


class ANPDiscovery:
    """In-memory directory illustrating ANP registration and discovery."""

    def __init__(self) -> None:
        self._services: Dict[str, ServiceInfo] = {}

    def register_service(self, service: ServiceInfo) -> bool:
        """Register or update a service by stable identifier."""
        if not isinstance(service, ServiceInfo):
            raise TypeError("service 必须是 ServiceInfo")
        self._services[service.service_id] = service
        return True

    def unregister_service(self, service_id: str) -> bool:
        """Remove a service and report whether it existed."""
        normalized = _required_text("service_id", service_id)
        return self._services.pop(normalized, None) is not None

    def update_metadata(
        self,
        service_id: str,
        updates: Dict[str, Any],
    ) -> ServiceInfo:
        """Replace one service entry with merged routing metadata."""
        if not isinstance(updates, dict):
            raise TypeError("updates 必须是字典")
        service = self.get_service(service_id)
        if service is None:
            raise ValueError(f"服务不存在: {service_id}")
        updated = replace(
            service,
            metadata={**service.metadata, **updates},
        )
        self._services[service.service_id] = updated
        return updated

    def discover_services(
        self,
        service_type: str | None = None,
        filters: Dict[str, Any] | None = None,
        required_capabilities: Iterable[str] | None = None,
    ) -> List[ServiceInfo]:
        """Find services by type, capabilities and exact metadata matches."""
        if filters is not None and not isinstance(filters, dict):
            raise TypeError("filters 必须是字典")
        capabilities = (
            (required_capabilities,)
            if isinstance(required_capabilities, str)
            else tuple(required_capabilities or ())
        )
        services = list(self._services.values())
        if service_type:
            services = [
                service
                for service in services
                if service.service_type == service_type
            ]
        if capabilities:
            services = [
                service
                for service in services
                if service.supports(capabilities)
            ]
        if filters:
            services = [
                service
                for service in services
                if all(
                    key in service.metadata
                    and service.metadata[key] == value
                    for key, value in filters.items()
                )
            ]
        return sorted(services, key=lambda service: service.service_id)

    def select_service(
        self,
        service_type: str,
        *,
        filters: Dict[str, Any] | None = None,
        required_capabilities: Iterable[str] | None = None,
        sort_by: str = "load",
        ascending: bool = True,
    ) -> ServiceInfo | None:
        """Choose one service by a numeric metadata field."""
        service_type = _required_text("service_type", service_type)
        sort_by = _required_text("sort_by", sort_by)
        services = self.discover_services(
            service_type=service_type,
            filters=filters,
            required_capabilities=required_capabilities,
        )
        if not services:
            return None

        candidates: list[tuple[Real, ServiceInfo]] = []
        for service in services:
            value = service.metadata.get(sort_by)
            if isinstance(value, bool) or not isinstance(value, Real):
                continue
            candidates.append((value, service))
        if not candidates:
            raise ValueError(
                f"候选服务缺少数值型 metadata.{sort_by}",
            )
        candidates.sort(
            key=(
                (lambda item: (item[0], item[1].service_id))
                if ascending
                else (lambda item: (-item[0], item[1].service_id))
            ),
        )
        return candidates[0][1]

    def get_service(self, service_id: str) -> ServiceInfo | None:
        """Return one service by identifier."""
        return self._services.get(str(service_id).strip())

    def list_all_services(self) -> List[ServiceInfo]:
        """Return all services in deterministic identifier order."""
        return self.discover_services()

    def __len__(self) -> int:
        return len(self._services)


def register_service(
    discovery: ANPDiscovery,
    service_id: str,
    service_name: str,
    service_type: str,
    capabilities: Iterable[str],
    endpoint: str,
    metadata: Dict[str, Any] | None = None,
) -> ServiceInfo:
    """Create and register the ``ServiceInfo`` shown in the chapter."""
    service = ServiceInfo(
        service_id=service_id,
        service_name=service_name,
        service_type=service_type,
        capabilities=(
            (capabilities,)
            if isinstance(capabilities, str)
            else tuple(capabilities)
        ),
        endpoint=endpoint,
        metadata=dict(metadata or {}),
    )
    discovery.register_service(service)
    return service


def discover_service(
    discovery: ANPDiscovery,
    service_type: str | None = None,
    *,
    capabilities: Iterable[str] | None = None,
    filters: Dict[str, Any] | None = None,
) -> List[ServiceInfo]:
    """Compatibility helper returning all matching services."""
    return discovery.discover_services(
        service_type=service_type,
        filters=filters,
        required_capabilities=capabilities,
    )


class ANPNetwork:
    """Undirected graph of discovered Agent endpoints."""

    def __init__(self, network_id: str) -> None:
        self.network_id = _required_text("network_id", network_id)
        self._nodes: Dict[str, str] = {}
        self._edges: Dict[str, set[str]] = {}

    def add_node(self, service_id: str, endpoint: str) -> None:
        """Add or update one node."""
        node_id = _required_text("service_id", service_id)
        self._nodes[node_id] = _http_endpoint(endpoint)
        self._edges.setdefault(node_id, set())

    def remove_node(self, service_id: str) -> bool:
        """Remove a node and every incident edge."""
        node_id = str(service_id).strip()
        if node_id not in self._nodes:
            return False
        for neighbor in self._edges[node_id]:
            self._edges[neighbor].discard(node_id)
        del self._edges[node_id]
        del self._nodes[node_id]
        return True

    def connect_nodes(self, source_id: str, target_id: str) -> None:
        """Create one bidirectional connection between existing nodes."""
        source = _required_text("source_id", source_id)
        target = _required_text("target_id", target_id)
        if source == target:
            raise ValueError("节点不能连接自身")
        missing = [node for node in (source, target) if node not in self._nodes]
        if missing:
            raise ValueError(f"节点不存在: {', '.join(missing)}")
        self._edges[source].add(target)
        self._edges[target].add(source)

    def disconnect_nodes(self, source_id: str, target_id: str) -> bool:
        """Remove one bidirectional connection."""
        if source_id not in self._edges or target_id not in self._edges:
            return False
        existed = target_id in self._edges[source_id]
        self._edges[source_id].discard(target_id)
        self._edges[target_id].discard(source_id)
        return existed

    def get_neighbors(self, service_id: str) -> List[str]:
        """Return direct neighbors in deterministic order."""
        node_id = _required_text("service_id", service_id)
        if node_id not in self._nodes:
            raise ValueError(f"节点不存在: {node_id}")
        return sorted(self._edges[node_id])

    def find_path(self, source_id: str, target_id: str) -> List[str] | None:
        """Find one shortest unweighted path with breadth-first search."""
        if source_id not in self._nodes or target_id not in self._nodes:
            return None
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        while queue:
            current, path = queue.popleft()
            if current == target_id:
                return path
            for neighbor in sorted(self._edges[current]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, [*path, neighbor]))
        return None

    def get_network_stats(self) -> Dict[str, Any]:
        """Return node and connection counts for the chapter example."""
        total_nodes = len(self._nodes)
        total_connections = sum(map(len, self._edges.values())) // 2
        average_degree = (
            (2 * total_connections / total_nodes) if total_nodes else 0.0
        )
        return {
            "network_id": self.network_id,
            "total_nodes": total_nodes,
            "total_connections": total_connections,
            "isolated_nodes": sum(
                1 for neighbors in self._edges.values() if not neighbors
            ),
            "average_degree": round(average_degree, 2),
        }
