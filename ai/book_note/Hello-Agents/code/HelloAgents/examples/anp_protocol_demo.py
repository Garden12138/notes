"""Deterministic ANP discovery, network and load-balancing practice."""

from __future__ import annotations

from hello_agents import (
    ANPDiscovery,
    ANPNetwork,
    discover_service,
    register_service,
)


def build_nlp_directory() -> ANPDiscovery:
    discovery = ANPDiscovery()
    register_service(
        discovery=discovery,
        service_id="nlp_agent_1",
        service_name="NLP处理专家A",
        service_type="nlp",
        capabilities=["text_analysis", "sentiment_analysis", "ner"],
        endpoint="http://localhost:8001",
        metadata={"load": 0.3, "price": 0.01, "version": "1.0.0"},
    )
    register_service(
        discovery=discovery,
        service_id="nlp_agent_2",
        service_name="NLP处理专家B",
        service_type="nlp",
        capabilities=["text_analysis", "translation"],
        endpoint="http://localhost:8002",
        metadata={"load": 0.7, "price": 0.02, "version": "1.1.0"},
    )
    return discovery


def run_discovery_and_network() -> None:
    discovery = build_nlp_directory()
    services = discover_service(discovery, service_type="nlp")
    best = discovery.select_service("nlp", sort_by="load")
    assert best is not None

    print("=== 服务注册、发现与选择 ===")
    print("已注册:", len(discovery))
    print("NLP 服务:", ", ".join(item.display_name for item in services))
    print(f"最低负载: {best.display_name} ({best.metadata['load']:.2f})")

    network = ANPNetwork(network_id="ai_cluster")
    for service in discovery.list_all_services():
        network.add_node(service.service_id, service.endpoint)
    network.connect_nodes("nlp_agent_1", "nlp_agent_2")
    stats = network.get_network_stats()
    print(
        "网络:",
        f"nodes={stats['total_nodes']}, edges={stats['total_connections']}",
    )
    print(
        "路径:",
        " -> ".join(network.find_path("nlp_agent_1", "nlp_agent_2") or []),
    )


def run_load_balancing() -> None:
    discovery = ANPDiscovery()
    initial_loads = [0.15, 0.25, 0.35, 0.45, 0.55]
    for index, load in enumerate(initial_loads):
        register_service(
            discovery=discovery,
            service_id=f"api_server_{index}",
            service_name=f"API服务器{index}",
            service_type="api",
            capabilities=["rest_api"],
            endpoint=f"http://api{index}:8000",
            metadata={"load": load},
        )

    print("\n=== 基于负载元数据的请求分配 ===")
    for request_number in range(1, 11):
        server = discovery.select_service("api", sort_by="load")
        assert server is not None
        load = float(server.metadata["load"])
        print(
            f"请求 {request_number:02d} -> {server.display_name} "
            f"(分配前负载 {load:.2f})",
        )
        discovery.update_metadata(
            server.service_id,
            {"load": round(load + 0.1, 2)},
        )


def main() -> None:
    run_discovery_and_network()
    run_load_balancing()


if __name__ == "__main__":
    main()
