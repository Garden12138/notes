"""Switch one HelloAgentsLLM instance between cloud and local providers."""

from __future__ import annotations

import argparse

from hello_agents import HelloAgentsLLM, SUPPORTED_PROVIDERS


def parse_args() -> argparse.Namespace:
    """Parse non-sensitive command-line options."""
    parser = argparse.ArgumentParser(
        description="HelloAgentsLLM 多提供商与本地模型调用示例",
    )
    parser.add_argument(
        "--provider",
        choices=sorted(SUPPORTED_PROVIDERS),
        help="显式选择 provider；省略时读取 LLM_PROVIDER",
    )
    parser.add_argument("--model", help="覆盖 provider 的默认模型 ID")
    parser.add_argument("--base-url", help="覆盖 provider 的默认服务地址")
    parser.add_argument(
        "--prompt",
        default="请用三句话解释什么是 AI Agent。",
        help="发送给模型的问题",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="请求超时秒数",
    )
    return parser.parse_args()


def main() -> None:
    """Create the shared client and make one streaming request."""
    args = parse_args()
    llm = HelloAgentsLLM(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout,
    )
    print("当前连接：" + llm.connection_summary())

    messages = [
        {
            "role": "system",
            "content": "你是一个专业、简洁的中文 AI 助手。",
        },
        {
            "role": "user",
            "content": args.prompt,
        },
    ]
    for _ in llm.think(messages, temperature=0.2):
        pass


if __name__ == "__main__":
    main()
