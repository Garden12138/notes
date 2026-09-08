"""Discover and call the calculator through a real A2A HTTP connection."""

from __future__ import annotations

import argparse

from hello_agents import A2AClient


def main() -> None:
    parser = argparse.ArgumentParser(description="调用 A2A 计算器 Agent")
    parser.add_argument("--url", default="http://127.0.0.1:5000")
    args = parser.parse_args()

    client = A2AClient(args.url)
    card = client.get_agent_card()
    print("Agent Card:", card["name"])
    print("Skills:", ", ".join(skill["id"] for skill in card["skills"]))

    response = client.execute_skill("add", "计算 10 + 5")
    print("Status:", response["status"])
    print("Artifact:", response["result"])
    event_labels = []
    for event in response["events"]:
        label = event["type"]
        if event["type"] in {"task", "status"}:
            label += f":{event['status']}"
        elif event["type"] == "artifact":
            label += f":{event['name']}"
        event_labels.append(label)
    print("Events:", " -> ".join(event_labels))

    task = client.get_task(response["task_id"])
    print("tasks/get:", task["status"])


if __name__ == "__main__":
    main()
