"""Deterministic offline practice for section 16.2."""

from __future__ import annotations

import json
from pathlib import Path

from graduation_project import (
    CriterionRating,
    TopicProposal,
    rank_topic_proposals,
)


DATA_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "graduation_project"
    / "code_review_topic.json"
)


def load_code_review_topic() -> TopicProposal:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return TopicProposal.from_dict(data)


def create_broad_topic() -> TopicProposal:
    return TopicProposal(
        name="UniversalAssistant",
        category="productivity",
        problem="希望用一个助手处理所有日常任务",
        target_users="所有人",
        core_features=(
            "聊天",
            "搜索",
            "写作",
            "编程",
            "日程",
            "数据分析",
        ),
        expected_outcome="实现一个无所不能的助手",
        timebox_weeks=4,
        weekly_hours=6,
        practicality=CriterionRating(
            score=2,
            evidence="用户和问题范围都不清晰",
        ),
        feasibility=CriterionRating(
            score=1,
            evidence="四周内无法稳定完成全部能力",
        ),
        demonstrability=CriterionRating(
            score=2,
            evidence="没有明确任务和可比较的验收结果",
        ),
    )


def main() -> None:
    ranked = rank_topic_proposals(
        [load_code_review_topic(), create_broad_topic()]
    )
    code_review = next(
        evaluation
        for proposal, evaluation in ranked
        if proposal.name == "CodeReviewAgent"
    )
    broad = next(
        evaluation
        for proposal, evaluation in ranked
        if proposal.name == "UniversalAssistant"
    )

    print("=== 16.2 毕业设计选题评估实践 ===")
    print(f"code_review_score: {code_review.total_score:.1f}")
    print(f"code_review_recommendation: {code_review.recommendation}")
    print(f"code_review_feature_count: {code_review.core_feature_count}")
    print(f"broad_idea_score: {broad.total_score:.1f}")
    print(f"broad_idea_recommendation: {broad.recommendation}")
    print(f"broad_idea_risks: {','.join(broad.risks)}")
    print(f"ranking_first: {ranked[0][0].name}")
    print("network_calls: 0")
    print("model_calls: 0")


if __name__ == "__main__":
    main()
