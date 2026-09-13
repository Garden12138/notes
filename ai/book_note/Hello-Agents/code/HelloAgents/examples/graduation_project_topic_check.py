"""CLI for applying the section 16.2 topic-selection rubric."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from graduation_project import (
    CATEGORY_LABELS,
    TopicEvaluator,
    TopicProposal,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="按实用性、可行性和展示性评估毕业设计选题",
    )
    parser.add_argument("proposal", type=Path, help="选题方案 JSON 文件")
    parser.add_argument(
        "--json",
        action="store_true",
        help="只输出结构化评估结果",
    )
    return parser


def load_proposal(path: Path) -> TopicProposal:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"无法读取选题文件：{error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"选题文件不是有效 JSON：{error.msg}") from error
    if not isinstance(data, dict):
        raise ValueError("选题文件根节点必须是 JSON 对象")
    return TopicProposal.from_dict(data)


def main() -> int:
    args = build_parser().parse_args()
    try:
        proposal = load_proposal(args.proposal)
        evaluation = TopicEvaluator().evaluate(proposal)
    except ValueError as error:
        print(f"选题方案无效：{error}", file=sys.stderr)
        return 2

    if args.json:
        print(
            json.dumps(
                evaluation.to_dict(),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"项目：{evaluation.topic_name}")
        print(f"类别：{CATEGORY_LABELS[evaluation.category]}")
        print(f"总分：{evaluation.total_score:.1f}/100")
        for name, score in evaluation.criterion_scores.items():
            print(f"  {name}: {score}/5")
        print(f"预计投入：{evaluation.estimated_effort_hours} 小时")
        print(f"建议：{evaluation.recommendation}")
        if evaluation.risks:
            print(f"风险：{', '.join(evaluation.risks)}")

    return 0 if evaluation.ready_for_design else 1


if __name__ == "__main__":
    raise SystemExit(main())
