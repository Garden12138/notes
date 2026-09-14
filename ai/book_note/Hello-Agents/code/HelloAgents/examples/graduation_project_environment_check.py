"""CLI for checking the development setup described in section 16.3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from graduation_project import DevelopmentEnvironmentChecker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="检查毕业设计的 Python、Git、Jupyter、仓库和项目结构",
    )
    parser.add_argument("repository", type=Path, help="Hello-Agents 仓库根目录")
    parser.add_argument("project", type=Path, help="共创项目目录")
    parser.add_argument("--github-user", help="用于校验项目目录名称")
    parser.add_argument(
        "--entry-mode",
        choices=("script", "notebook"),
        default="script",
        help="项目的主要运行形式",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出适合 CI 保存的 JSON 报告",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = DevelopmentEnvironmentChecker(
        repository_root=args.repository,
        project_root=args.project,
        github_username=args.github_user,
        entry_mode=args.entry_mode,
    ).check()

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"仓库：{report.repository_root}")
        print(f"项目：{report.project_root}")
        for check in report.checks:
            marker = (
                "PASS"
                if check.passed
                else ("FAIL" if check.required else "INFO")
            )
            required = "必需" if check.required else "推荐"
            print(
                f"[{marker}] [{required}] "
                f"{check.description}：{check.detail}"
            )
        passed, total = report.required_progress
        print(f"必需项：{passed}/{total}")
        print(f"环境就绪：{'是' if report.ready else '否'}")

    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
