"""CLI for checking the graduation-project deliverables in section 16.1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from graduation_project import GraduationProjectValidator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="检查 Hello-Agents 毕业设计的最低交付物",
    )
    parser.add_argument("project", type=Path, help="待检查的项目目录")
    parser.add_argument(
        "--github-user",
        help="用于校验 <GitHub用户名>-<项目名称> 命名规则",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出适合 CI 保存的 JSON 报告",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = GraduationProjectValidator(
        args.project,
        github_username=args.github_user,
    ).validate()

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"项目：{report.project_root}")
        for check in report.checks:
            marker = (
                "PASS"
                if check.passed
                else ("FAIL" if check.required else "INFO")
            )
            required = "必需" if check.required else "可选"
            print(
                f"[{marker}] [{required}] {check.description}：{check.detail}"
            )
        passed, total = report.required_progress
        print(f"必需项：{passed}/{total}")
        print(f"可提交：{'是' if report.ready else '否'}")

    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
