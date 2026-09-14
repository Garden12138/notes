"""CLI for checking and rendering a section 16.5 pull request."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from graduation_project import (
    ManualTestEvidence,
    PullRequestMetadata,
    PullRequestReadinessChecker,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="检查毕业设计的 Git 状态并生成 PR 描述",
    )
    parser.add_argument("repository", type=Path, help="Hello-Agents 仓库根目录")
    parser.add_argument("metadata", type=Path, help="PR 项目信息 JSON")
    parser.add_argument(
        "--evidence",
        type=Path,
        required=True,
        help="16.4 人工测试记录 JSON",
    )
    parser.add_argument(
        "--write-description",
        type=Path,
        help="检查后将 PR 描述写入指定 Markdown 文件",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出适合 CI 保存的检查报告",
    )
    return parser


def load_json_object(path: Path, label: str) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"无法读取{label}：{error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{label}的根节点必须是 JSON 对象")
    return data


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        metadata = PullRequestMetadata.from_dict(
            load_json_object(args.metadata, "PR 项目信息")
        )
        evidence = ManualTestEvidence.from_dict(
            load_json_object(args.evidence, "人工测试记录")
        )
    except ValueError as error:
        parser.error(str(error))

    report = PullRequestReadinessChecker(
        args.repository,
        metadata,
        evidence=evidence,
    ).check()

    if args.write_description is not None:
        args.write_description.parent.mkdir(parents=True, exist_ok=True)
        args.write_description.write_text(
            metadata.render_markdown(),
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"仓库：{report.repository_root}")
        print(f"项目：{report.project_root}")
        for check in report.checks:
            marker = "PASS" if check.passed else "FAIL"
            print(f"[{marker}] {check.description}：{check.detail}")
        passed, total = report.required_progress
        print(f"必需项：{passed}/{total}")
        print(f"可以创建 PR：{'是' if report.ready else '否'}")

    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
