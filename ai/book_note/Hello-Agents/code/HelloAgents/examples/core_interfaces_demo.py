"""Offline demonstration of Message, Config, and the Agent interface."""

from __future__ import annotations

from typing import Dict, List

from hello_agents import Agent, Config, Message


class DemoLLM:
    """Small deterministic stand-in; it never sends an API request."""

    provider = "mock"

    def invoke(self, messages: List[Dict[str, str]]) -> str:
        return f"已收到：{messages[-1]['content']}"


class EchoAgent(Agent):
    """Minimal concrete Agent used only to verify the 7.3 interfaces."""

    def run(self, input_text: str, **kwargs: object) -> str:
        del kwargs
        self.add_message(Message(role="user", content=input_text))
        payload = [message.to_dict() for message in self.get_history()]
        response = self.llm.invoke(payload)
        self.add_message(Message(role="assistant", content=response))
        return response


def main() -> None:
    """Exercise configuration, message conversion, and history management."""
    config = Config(debug=True, max_history_length=10)
    agent = EchoAgent(
        name="接口演示助手",
        llm=DemoLLM(),  # type: ignore[arg-type]
        system_prompt="你是一个简洁的助手。",
        config=config,
    )

    print(agent)
    print(agent.run("解释 Message 的作用"))
    print("历史消息：")
    for message in agent.get_history():
        print(message)

    history_copy = agent.get_history()
    history_copy.clear()
    print(f"外部清空副本后，内部历史仍有 {len(agent.get_history())} 条")


if __name__ == "__main__":
    main()
