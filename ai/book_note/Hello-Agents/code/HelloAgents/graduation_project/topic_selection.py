"""Topic-selection rubric following section 16.2 of Hello-Agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, Mapping, cast


ProjectCategory = Literal[
    "productivity",
    "learning",
    "creative_entertainment",
    "data_analysis",
    "life_service",
]
Recommendation = Literal["recommended", "narrow_scope", "rework"]

CATEGORY_LABELS: dict[ProjectCategory, str] = {
    "productivity": "生产力工具",
    "learning": "学习辅助",
    "creative_entertainment": "创意娱乐",
    "data_analysis": "数据分析",
    "life_service": "生活服务",
}
CRITERION_WEIGHTS = {
    "practicality": 0.35,
    "feasibility": 0.35,
    "demonstrability": 0.30,
}
MIN_CRITERION_SCORE = 3
RECOMMENDED_TOTAL_SCORE = 80.0


@dataclass(frozen=True)
class CriterionRating:
    """A 1-5 rating that must include reviewable evidence."""

    score: int
    evidence: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.score, bool)
            or not isinstance(self.score, int)
            or not 1 <= self.score <= 5
        ):
            raise ValueError("criterion score must be an integer from 1 to 5")
        if not isinstance(self.evidence, str) or not self.evidence.strip():
            raise ValueError("criterion evidence cannot be empty")


@dataclass(frozen=True)
class TopicProposal:
    """Structured version of section 16.2's topic-description template."""

    name: str
    category: ProjectCategory
    problem: str
    target_users: str
    core_features: tuple[str, ...]
    expected_outcome: str
    timebox_weeks: int
    weekly_hours: int
    practicality: CriterionRating
    feasibility: CriterionRating
    demonstrability: CriterionRating

    def __post_init__(self) -> None:
        text_fields = {
            "name": self.name,
            "problem": self.problem,
            "target_users": self.target_users,
            "expected_outcome": self.expected_outcome,
        }
        for field_name, value in text_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} cannot be empty")
        if self.category not in CATEGORY_LABELS:
            raise ValueError(f"unsupported project category: {self.category}")
        if not self.core_features:
            raise ValueError("at least one core feature is required")
        if any(
            not isinstance(feature, str) or not feature.strip()
            for feature in self.core_features
        ):
            raise ValueError("core features cannot contain empty values")
        if (
            isinstance(self.timebox_weeks, bool)
            or not isinstance(self.timebox_weeks, int)
            or self.timebox_weeks <= 0
        ):
            raise ValueError("timebox_weeks must be a positive integer")
        if (
            isinstance(self.weekly_hours, bool)
            or not isinstance(self.weekly_hours, int)
            or self.weekly_hours <= 0
        ):
            raise ValueError("weekly_hours must be a positive integer")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TopicProposal":
        """Parse a JSON-compatible mapping and reject ambiguous structures."""
        ratings = data.get("ratings")
        if not isinstance(ratings, Mapping):
            raise ValueError("ratings must be an object")
        features = data.get("core_features")
        if not isinstance(features, list) or not all(
            isinstance(feature, str) for feature in features
        ):
            raise ValueError("core_features must be a list of strings")

        def required_text(name: str) -> str:
            value = data.get(name)
            if not isinstance(value, str):
                raise ValueError(f"{name} must be a string")
            return value

        def required_score(name: str) -> CriterionRating:
            value = ratings.get(name)
            if not isinstance(value, Mapping):
                raise ValueError(f"ratings.{name} must be an object")
            score = value.get("score")
            evidence = value.get("evidence")
            if not isinstance(score, int) or not isinstance(evidence, str):
                raise ValueError(
                    f"ratings.{name} requires integer score and string evidence"
                )
            return CriterionRating(score=score, evidence=evidence)

        timebox_weeks = data.get("timebox_weeks")
        weekly_hours = data.get("weekly_hours")
        if not isinstance(timebox_weeks, int):
            raise ValueError("timebox_weeks must be an integer")
        if not isinstance(weekly_hours, int):
            raise ValueError("weekly_hours must be an integer")

        return cls(
            name=required_text("name"),
            category=cast(ProjectCategory, required_text("category")),
            problem=required_text("problem"),
            target_users=required_text("target_users"),
            core_features=tuple(features),
            expected_outcome=required_text("expected_outcome"),
            timebox_weeks=timebox_weeks,
            weekly_hours=weekly_hours,
            practicality=required_score("practicality"),
            feasibility=required_score("feasibility"),
            demonstrability=required_score("demonstrability"),
        )


@dataclass(frozen=True)
class TopicEvaluation:
    """Result of applying the three selection principles to one proposal."""

    topic_name: str
    category: ProjectCategory
    total_score: float
    recommendation: Recommendation
    criterion_scores: dict[str, int]
    risks: tuple[str, ...]
    core_feature_count: int
    estimated_effort_hours: int

    @property
    def ready_for_design(self) -> bool:
        return self.recommendation == "recommended"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category_label"] = CATEGORY_LABELS[self.category]
        result["ready_for_design"] = self.ready_for_design
        return result


class TopicEvaluator:
    """Evaluate practicality, feasibility and demonstrability."""

    def evaluate(self, proposal: TopicProposal) -> TopicEvaluation:
        ratings = {
            "practicality": proposal.practicality,
            "feasibility": proposal.feasibility,
            "demonstrability": proposal.demonstrability,
        }
        total = round(
            sum(
                ratings[name].score * weight
                for name, weight in CRITERION_WEIGHTS.items()
            )
            / 5
            * 100,
            1,
        )
        risks = tuple(
            f"{name}_below_floor"
            for name, rating in ratings.items()
            if rating.score < MIN_CRITERION_SCORE
        )

        if risks:
            recommendation: Recommendation = "rework"
        elif total >= RECOMMENDED_TOTAL_SCORE:
            recommendation = "recommended"
        else:
            recommendation = "narrow_scope"

        return TopicEvaluation(
            topic_name=proposal.name,
            category=proposal.category,
            total_score=total,
            recommendation=recommendation,
            criterion_scores={
                name: rating.score for name, rating in ratings.items()
            },
            risks=risks,
            core_feature_count=len(proposal.core_features),
            estimated_effort_hours=(
                proposal.timebox_weeks * proposal.weekly_hours
            ),
        )


def rank_topic_proposals(
    proposals: list[TopicProposal],
) -> list[tuple[TopicProposal, TopicEvaluation]]:
    """Rank proposals without allowing a high total to hide a weak principle."""
    evaluator = TopicEvaluator()
    recommendation_order = {
        "recommended": 2,
        "narrow_scope": 1,
        "rework": 0,
    }
    evaluated = [(proposal, evaluator.evaluate(proposal)) for proposal in proposals]
    return sorted(
        evaluated,
        key=lambda item: (
            recommendation_order[item[1].recommendation],
            item[1].total_score,
        ),
        reverse=True,
    )
