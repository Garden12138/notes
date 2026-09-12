"""Absolute LLM-Judge evaluation for generated math problems."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from statistics import fmean
from typing import Any, Iterable


SCORE_DIMENSIONS = (
    "correctness",
    "clarity",
    "difficulty_match",
    "completeness",
)


def call_judge(judge: Any, prompt: str) -> str:
    """Call a SimpleAgent, HelloAgentsLLM, or compatible callable."""
    if hasattr(judge, "run"):
        if hasattr(judge, "clear_history"):
            judge.clear_history()
        response = judge.run(prompt)
    elif hasattr(judge, "invoke"):
        response = judge.invoke(
            [{"role": "user", "content": prompt}],
            temperature=0,
        )
    elif callable(judge):
        response = judge(prompt)
    else:
        raise TypeError("judge must provide run(), invoke(), or be callable")
    if not isinstance(response, str) or not response.strip():
        raise ValueError("Judge returned an empty response")
    return response


def parse_json_object(response: str) -> dict[str, Any]:
    """Extract one JSON object and repair unescaped LaTeX commands."""
    text = response.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fenced:
        text = fenced.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Judge response contains no JSON object")
        text = text[start : end + 1]
    text = _repair_json_escapes(text)
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("Judge response must be a JSON object")
    return value


def _repair_json_escapes(text: str) -> str:
    """Double likely LaTeX backslashes while retaining JSON escapes."""
    result: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char != "\\" or index + 1 >= len(text):
            result.append(char)
            index += 1
            continue
        following = text[index + 1]
        if following in {'"', "\\", "/"}:
            result.extend((char, following))
            index += 2
            continue
        if following == "u" and re.fullmatch(
            r"[0-9a-fA-F]{4}", text[index + 2 : index + 6]
        ):
            result.append(char)
            index += 1
            continue
        after_escape = text[index + 2 : index + 3]
        if following in "bfnrt" and not after_escape.islower():
            result.append(char)
            index += 1
            continue
        result.extend(("\\", "\\"))
        index += 1
    return "".join(result)


class LLMJudgeEvaluator:
    """Score correctness, clarity, difficulty and completeness from 1 to 5."""

    def __init__(
        self,
        judge: Any,
        *,
        pass_threshold: float = 3.5,
        excellent_threshold: float = 4.5,
    ) -> None:
        if not 1 <= pass_threshold <= 5:
            raise ValueError("pass_threshold must be between 1 and 5")
        if not pass_threshold <= excellent_threshold <= 5:
            raise ValueError(
                "excellent_threshold must be between pass_threshold and 5"
            )
        self.judge = judge
        self.pass_threshold = pass_threshold
        self.excellent_threshold = excellent_threshold

    def evaluate(
        self,
        problems: Iterable[dict[str, Any]],
    ) -> dict[str, Any]:
        records = list(problems)
        results = [self._evaluate_one(problem) for problem in records]
        successful = [item for item in results if item["error"] is None]
        metrics = self._metrics(results, successful)
        return {
            "status": "success" if successful else "error",
            "evaluation_type": "llm_judge_absolute",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "thresholds": {
                "pass": self.pass_threshold,
                "excellent": self.excellent_threshold,
            },
            **metrics,
            "results": results,
        }

    def _evaluate_one(self, problem: dict[str, Any]) -> dict[str, Any]:
        problem_id = str(problem.get("problem_id") or "unknown")
        base = {
            "problem_id": problem_id,
            "scores": None,
            "average_score": None,
            "comments": None,
            "raw_response": None,
            "error": None,
        }
        try:
            response = call_judge(self.judge, self._build_prompt(problem))
            value = parse_json_object(response)
            scores_value = value.get("scores", value)
            if not isinstance(scores_value, dict):
                raise ValueError("scores must be an object")
            scores: dict[str, float] = {}
            for dimension in SCORE_DIMENSIONS:
                score = float(scores_value[dimension])
                if not 1 <= score <= 5:
                    raise ValueError(f"{dimension} must be between 1 and 5")
                scores[dimension] = score
            average = fmean(scores.values())
            base.update(
                {
                    "scores": scores,
                    "average_score": round(average, 4),
                    "comments": str(
                        value.get("comments", value.get("reason", ""))
                    ).strip(),
                    "raw_response": response,
                }
            )
        except Exception as exc:
            base["error"] = f"{type(exc).__name__}: {exc}"
        return base

    def _metrics(
        self,
        results: list[dict[str, Any]],
        successful: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not successful:
            return {
                "total_samples": len(results),
                "evaluated_samples": 0,
                "failed_samples": len(results),
                "average_score": None,
                "pass_rate": None,
                "excellent_rate": None,
                "dimension_averages": None,
            }
        averages = [float(item["average_score"]) for item in successful]
        dimension_averages = {
            dimension: round(
                fmean(float(item["scores"][dimension]) for item in successful),
                4,
            )
            for dimension in SCORE_DIMENSIONS
        }
        return {
            "total_samples": len(results),
            "evaluated_samples": len(successful),
            "failed_samples": len(results) - len(successful),
            "average_score": round(fmean(averages), 4),
            "pass_rate": round(
                sum(score >= self.pass_threshold for score in averages)
                / len(averages),
                4,
            ),
            "excellent_rate": round(
                sum(score >= self.excellent_threshold for score in averages)
                / len(averages),
                4,
            ),
            "dimension_averages": dimension_averages,
        }

    @staticmethod
    def _build_prompt(problem: dict[str, Any]) -> str:
        return (
            "你是 AIME 数学题质量评审。请分别从 1 到 5 分评价以下四项：\n"
            "correctness：题目、答案和推导是否正确；\n"
            "clarity：表述是否清楚、无歧义；\n"
            "difficulty_match：是否接近 AIME 第 6–9 题难度；\n"
            "completeness：解答是否完整、可复核。\n\n"
            f"题目：{problem.get('problem', '')}\n"
            f"答案：{problem.get('answer', '')}\n"
            f"解答：{problem.get('solution', '')}\n"
            f"主题：{problem.get('topic', '')}\n\n"
            "仅返回 JSON："
            '{"scores":{"correctness":1,"clarity":1,'
            '"difficulty_match":1,"completeness":1},"comments":"..."}'
        )

    @staticmethod
    def export_results(result: dict[str, Any], path: str | Path) -> Path:
        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(output)
        return output

    @staticmethod
    def generate_report(result: dict[str, Any], path: str | Path) -> Path:
        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        def percentage(value: float | None) -> str:
            return "N/A" if value is None else f"{value:.2%}"

        dimensions = result.get("dimension_averages") or {}
        average_score = result["average_score"]
        lines = [
            "# LLM Judge 评估报告",
            "",
            f"- 样本数：{result['total_samples']}",
            f"- 成功评分：{result['evaluated_samples']}",
            f"- 评分失败：{result['failed_samples']}",
            f"- 平均分：{average_score if average_score is not None else 'N/A'}",
            f"- 通过率：{percentage(result['pass_rate'])}",
            f"- 优秀率：{percentage(result['excellent_rate'])}",
            "",
            "## 维度均分",
            "",
        ]
        lines.extend(
            f"- {dimension}: {score:.2f}"
            for dimension, score in dimensions.items()
        )
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output
