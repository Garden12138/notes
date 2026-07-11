#!/usr/bin/env python3
"""
plan_and_solve_agent_main.py

Plan-and-Solve Agent 的命令行启动入口。

依赖文件：
- llm.py
- plan.py
- plan_executor.py
- plan_and_solve_agent.py

使用示例：
    python plan_and_solve_agent_main.py "请分析人工智能 Agent 的基本工作流程"

也可以直接赋予执行权限后运行：
    chmod +x plan_and_solve_agent_main.py
    ./plan_and_solve_agent_main.py "请制定一个学习 LangGraph 的计划"

模型配置默认从 .env 文件读取：
    LLM_MODEL_ID=你的模型名称
    LLM_API_KEY=你的API密钥
    LLM_BASE_URL=模型服务地址
    LLM_TIMEOUT=60
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


# 确保无论从哪个工作目录启动，都可以导入脚本同目录下的模块。
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from llm import HelloAgentsLLM
from plan_and_solve_agent import PlanAndSolveAgent


def build_argument_parser() -> argparse.ArgumentParser:
    """创建并返回命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="先生成行动计划，再按照计划逐步执行并回答问题。"
    )

    parser.add_argument(
        "question",
        nargs="+",
        help="需要交给 Plan-and-Solve Agent 处理的问题。",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="可选：覆盖 .env 中的 LLM_MODEL_ID。",
    )

    parser.add_argument(
        "--api-key",
        default=None,
        help="可选：覆盖 .env 中的 LLM_API_KEY；更推荐在 .env 中配置。",
    )

    parser.add_argument(
        "--base-url",
        default=None,
        help="可选：覆盖 .env 中的 LLM_BASE_URL。",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="可选：覆盖 .env 中的 LLM_TIMEOUT，单位为秒。",
    )

    return parser


def create_agent(args: argparse.Namespace):
    """根据命令行参数创建 PlanAndSolveAgent。"""
    llm_client = HelloAgentsLLM(
        model=args.model,
        apiKey=args.api_key,
        baseUrl=args.base_url,
        timeout=args.timeout,
    )

    return PlanAndSolveAgent(llm_client=llm_client)


def main(argv: Sequence[str] | None = None) -> int:
    """程序主入口，返回进程退出码。"""
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    question = " ".join(args.question).strip()
    if not question:
        parser.error("问题不能为空。")

    try:
        agent = create_agent(args)
        agent.run(question)
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断了任务。", file=sys.stderr)
        return 130

    except ValueError as exc:
        print(f"\n❌ 配置错误：{exc}", file=sys.stderr)
        print(
            "请检查 .env 中的 LLM_MODEL_ID、LLM_API_KEY 和 LLM_BASE_URL。",
            file=sys.stderr,
        )
        return 2

    except ModuleNotFoundError as exc:
        print(f"\n❌ 缺少模块或依赖：{exc}", file=sys.stderr)
        print(
            "请确认 llm.py、plan.py、plan_executor.py 和 "
            "plan_and_solve_agent.py 与本文件位于同一目录。",
            file=sys.stderr,
        )
        return 3

    except Exception as exc:
        print(f"\n❌ Plan-and-Solve Agent 运行失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
