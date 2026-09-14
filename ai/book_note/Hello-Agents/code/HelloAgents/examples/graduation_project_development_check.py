"""CLI for the project-development checklist in section 16.4."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from graduation_project import ManualTestEvidence, ProjectDevelopmentValidator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="检查 README、依赖、Notebook、测试记录和项目大小",
    )
    parser.add_argument("project", type=Path, help="待检查的毕业设计目录")
    parser.add_argument(
        "--github-user",
        help="用于校验 <GitHub用户名>-<项目名称> 命名规则",
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        help="人工测试记录 JSON；未提供时测试证据项不通过",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出适合 CI 保存的 JSON 报告",
    )
    return parser


def load_evidence(path: Path | None) -> ManualTestEvidence | None:
    if path is None:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"无法读取测试记录：{error}") from error
    if not isinstance(data, dict):
        raise ValueError("测试记录的根节点必须是 JSON 对象")
    return ManualTestEvidence.from_dict(data)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        evidence = load_evidence(args.evidence)
    except ValueError as error:
        parser.error(str(error))

    report = ProjectDevelopmentValidator(
        args.project,
        github_username=args.github_user,
        evidence=evidence,
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
            required = "必需" if check.required else "建议"
            print(
                f"[{marker}] [{required}] "
                f"{check.description}：{check.detail}"
            )
        passed, total = report.required_progress
        print(f"必需项：{passed}/{total}")
        print(f"开发检查通过：{'是' if report.ready else '否'}")

    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
