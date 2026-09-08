"""A2A calculator server backed by the official SDK."""

from __future__ import annotations

import argparse

from hello_agents import A2A_AVAILABLE, A2AServer


def create_server() -> A2AServer:
    calculator = A2AServer(
        name="calculator-agent",
        description="提供加法和乘法计算的 Agent",
        capabilities={"math": ["addition", "multiplication"]},
    )

    @calculator.skill("add", examples=["计算 10 + 5"])
    def add_numbers(query: str) -> str:
        """计算由加号分隔的一组数字。"""
        expression = query.replace("计算", "").replace("加上", "+")
        numbers = [float(value.strip()) for value in expression.split("+")]
        return f"计算结果: {' + '.join(map(str, numbers))} = {sum(numbers)}"

    @calculator.skill("multiply", examples=["计算 6 * 7"])
    def multiply_numbers(query: str) -> str:
        """计算由乘号分隔的一组数字。"""
        expression = query.replace("计算", "").replace("×", "*")
        numbers = [float(value.strip()) for value in expression.split("*")]
        result = 1.0
        for number in numbers:
            result *= number
        return f"计算结果: {' × '.join(map(str, numbers))} = {result}"

    return calculator


def main() -> None:
    parser = argparse.ArgumentParser(description="运行 A2A 计算器 Agent")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    if not A2A_AVAILABLE:
        raise SystemExit('请先安装: pip install "a2a-sdk[http-server]"')
    print(f"A2A calculator: http://{args.host}:{args.port}", flush=True)
    create_server().run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
