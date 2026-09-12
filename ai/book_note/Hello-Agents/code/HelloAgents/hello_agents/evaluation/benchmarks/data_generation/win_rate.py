"""Pairwise Win Rate evaluation for generated math problems."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import random
from typing import Any, Iterable

from .llm_judge import call_judge, parse_json_object


class WinRateEvaluator:
    """Compare generated problem A with real reference problem B."""

    def __init__(self, judge: Any, *, seed: int = 42) -> None:
        self.judge = judge
        self.random = random.Random(seed)

    def evaluate(
        self,
        generated_problems: Iterable[dict[str, Any]],
        reference_problems: Iterable[dict[str, Any]],
        *,
        max_pairs: int = 0,
    ) -> dict[str, Any]:
        if max_pairs < 0:
            raise ValueError("max_pairs cannot be negative")
        generated = list(generated_problems)
        references = list(reference_problems)
        if not generated or not references:
            raise ValueError("Both generated and reference data are required")
        self.random.shuffle(references)
        pair_count = min(len(generated), len(references))
        if max_pairs:
            pair_count = min(pair_count, max_pairs)
        results = [
            self._compare(index + 1, generated[index], references[index])
            for index in range(pair_count)
        ]
        successful = [item for item in results if item["error"] is None]
        counts = {
            "wins": sum(item["winner"] == "A" for item in successful),
            "losses": sum(item["winner"] == "B" for item in successful),
            "ties": sum(item["winner"] == "Tie" for item in successful),
        }
        evaluated = len(successful)
        rates = {
            "win_rate": round(counts["wins"] / evaluated, 4),
            "loss_rate": round(counts["losses"] / evaluated, 4),
            "tie_rate": round(counts["ties"] / evaluated, 4),
        } if evaluated else {
            "win_rate": None,
            "loss_rate": None,
            "tie_rate": None,
        }
        return {
            "status": "success" if successful else "error",
            "evaluation_type": "pairwise_win_rate",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "position_policy": "generated_is_A_reference_is_B",
            "total_pairs": len(results),
            "evaluated_pairs": evaluated,
            "failed_pairs": len(results) - evaluated,
            **counts,
            **rates,
            "results": results,
        }

    def _compare(
        self,
        pair_id: int,
        generated: dict[str, Any],
        reference: dict[str, Any],
    ) -> dict[str, Any]:
        base = {
            "pair_id": pair_id,
            "generated_problem_id": generated.get("problem_id"),
            "reference_problem_id": reference.get("problem_id"),
            "winner": None,
            "reason": None,
            "raw_response": None,
            "error": None,
        }
        try:
            response = call_judge(
                self.judge,
                self._build_prompt(generated, reference),
            )
            value = parse_json_object(response)
            winner_raw = str(value.get("winner", "")).strip().lower()
            aliases = {"a": "A", "b": "B", "tie": "Tie", "平局": "Tie"}
            if winner_raw not in aliases:
                raise ValueError("winner must be A, B, or Tie")
            base.update(
                {
                    "winner": aliases[winner_raw],
                    "reason": str(value.get("reason", "")).strip(),
                    "raw_response": response,
                }
            )
        except Exception as exc:
            base["error"] = f"{type(exc).__name__}: {exc}"
        return base

    @staticmethod
    def _build_prompt(
        generated: dict[str, Any],
        reference: dict[str, Any],
    ) -> str:
        reference_solution = str(reference.get("solution") or "").strip()
        if not reference_solution:
            reference_solution = (
                "（数据集未提供；不要仅因该字段缺失而判 B 较差）"
            )
        return (
            "你是 AIME 数学题成对评审。综合比较正确性、表述、"
            "难度匹配和完整性，"
            "判断 A、B 哪一道质量更高；难分高下时返回 Tie。\n\n"
            "问题 A（模型生成）：\n"
            f"题目：{generated.get('problem', '')}\n"
            f"答案：{generated.get('answer', '')}\n"
            f"解答：{generated.get('solution', '')}\n\n"
            "问题 B（真实参考）：\n"
            f"题目：{reference.get('problem', '')}\n"
            f"答案：{reference.get('answer', '')}\n"
            f"解答：{reference_solution}\n\n"
            '仅返回 JSON：{"winner":"A|B|Tie","reason":"..."}'
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

        lines = [
            "# Win Rate 评估报告",
            "",
            f"- 配对数：{result['total_pairs']}",
            f"- 成功评分：{result['evaluated_pairs']}",
            f"- 评分失败：{result['failed_pairs']}",
            f"- 生成题胜率：{percentage(result['win_rate'])}",
            f"- 参考题胜率：{percentage(result['loss_rate'])}",
            f"- 平局率：{percentage(result['tie_rate'])}",
            "",
            "> 位置策略：生成题固定为 A，参考题固定为 B；"
            "正式评估应额外检查位置偏差。",
        ]
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output
