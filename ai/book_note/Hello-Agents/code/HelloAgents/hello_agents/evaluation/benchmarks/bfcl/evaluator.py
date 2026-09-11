"""Run an Agent against BFCL records and export auditable results."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping, Sequence

from .ast_matcher import extract_function_calls, match_function_calls
from .dataset import BFCLDataset
from .metrics import BFCLMetrics


class BFCLEvaluator:
    """Educational BFCL evaluator following Dataset → Agent → AST → Metrics."""

    def __init__(
        self,
        dataset: BFCLDataset | Sequence[Mapping[str, Any]],
        category: str | None = None,
        evaluation_mode: str = "ast",
        *,
        reset_history_between_cases: bool = True,
    ) -> None:
        if evaluation_mode != "ast":
            raise ValueError("only evaluation_mode='ast' is supported")
        self.dataset = dataset
        self.category = category or getattr(dataset, "category", "unknown")
        self.evaluation_mode = evaluation_mode
        self.reset_history_between_cases = reset_history_between_cases
        self.metrics_calculator = BFCLMetrics()

    def evaluate(
        self,
        agent: Any,
        max_samples: int | None = None,
        category_weights: Mapping[str, float] | None = None,
    ) -> dict[str, Any]:
        """Evaluate independent cases with ``agent.run(prompt)``."""
        if max_samples is not None and max_samples < 0:
            raise ValueError("max_samples cannot be negative")
        predictor = self._resolve_predictor(agent)
        data = self._load_data(max_samples)
        if not data:
            raise ValueError("the selected BFCL dataset is empty")

        results = []
        for item in data:
            if self.reset_history_between_cases:
                clear_history = getattr(agent, "clear_history", None)
                if callable(clear_history):
                    clear_history()
            prompt = self._build_prompt(item)
            started = perf_counter()
            response = ""
            error = None
            try:
                raw_response = predictor(prompt)
                if not isinstance(raw_response, str):
                    raise TypeError("agent.run must return text")
                response = raw_response
                prediction = extract_function_calls(
                    response,
                    item.get("function", []),
                )
                is_correct = match_function_calls(
                    prediction,
                    item.get("ground_truth", []),
                )
            except Exception as exc:
                prediction = []
                is_correct = False
                error = f"{type(exc).__name__}: {exc}"
            results.append(
                {
                    "id": item["id"],
                    "category": item.get("category", self.category),
                    "question": item.get("question"),
                    "response": response,
                    "prediction": prediction,
                    "ground_truth": item.get("ground_truth", []),
                    "is_correct": is_correct,
                    "duration_seconds": max(0.0, perf_counter() - started),
                    "error": error,
                }
            )

        metrics = self.metrics_calculator.compute_metrics(
            results,
            category_weights=category_weights,
        )
        return {
            "status": "success",
            "category": self.category,
            "evaluation_mode": self.evaluation_mode,
            "total_samples": len(results),
            "correct_samples": sum(item["is_correct"] for item in results),
            **metrics,
            "results": results,
        }

    def export_to_bfcl_format(
        self,
        evaluation: Mapping[str, Any],
        output_path: str | Path,
    ) -> Path:
        """Write BFCL's JSONL result envelope while preserving raw responses."""
        output = Path(output_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for result in evaluation.get("results", []):
                entry = {
                    "id": result["id"],
                    "result": result.get("response", ""),
                    "latency": result.get("duration_seconds", 0.0),
                }
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return output

    def generate_report(
        self,
        evaluation: Mapping[str, Any],
        output_path: str | Path,
        agent_name: str = "Agent",
    ) -> Path:
        """Generate a compact Markdown report with per-case evidence."""
        output = Path(output_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# BFCL 评估报告",
            "",
            (
                "- 生成时间："
                f"{datetime.now().astimezone().isoformat(timespec='seconds')}"
            ),
            f"- 智能体：{agent_name}",
            f"- 类别：{evaluation.get('category', self.category)}",
            (
                f"- 样本：{evaluation.get('correct_samples', 0)}/"
                f"{evaluation.get('total_samples', 0)}"
            ),
            (
                "- 本地 AST 匹配率："
                f"{float(evaluation.get('ast_match_rate', 0.0)):.2%}"
            ),
            "",
            (
                "> 这是 HelloAgents 教学匹配器的本地结果，"
                "不是 BFCL 官方排行榜分数。"
            ),
            "",
            "## 分类结果",
            "",
            "| 类别 | 正确 | 总数 | 准确率 |",
            "| --- | ---: | ---: | ---: |",
        ]
        for category, stats in evaluation.get(
            "category_statistics", {}
        ).items():
            lines.append(
                f"| {category} | {stats['correct']} | {stats['total']} | "
                f"{float(stats['accuracy']):.2%} |"
            )
        lines.extend(
            [
                "",
                "## 样本详情",
                "",
                "| ID | 类别 | 通过 | 预测调用 |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in evaluation.get("results", []):
            prediction = json.dumps(
                item.get("prediction", []),
                ensure_ascii=False,
            ).replace("|", "\\|")
            lines.append(
                f"| {item['id']} | {item.get('category', '')} | "
                f"{'是' if item.get('is_correct') else '否'} | `{prediction}` |"
            )
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output

    def _load_data(self, max_samples: int | None) -> list[dict[str, Any]]:
        if isinstance(self.dataset, BFCLDataset):
            return self.dataset.load(max_samples=max_samples)
        data = [dict(item) for item in self.dataset]
        if max_samples not in (None, 0):
            data = data[:max_samples]
        return data

    @staticmethod
    def _resolve_predictor(agent: Any) -> Callable[[str], str]:
        run = getattr(agent, "run", None)
        if callable(run):
            return run
        if callable(agent):
            return agent
        raise TypeError("agent must be callable or expose run(prompt)")

    @staticmethod
    def _build_prompt(item: Mapping[str, Any]) -> str:
        question = _format_question(item.get("question", ""))
        functions = json.dumps(
            item.get("function", []),
            ensure_ascii=False,
            indent=2,
        )
        return (
            "请根据用户请求选择并构造函数调用。\n\n"
            f"用户请求：\n{question}\n\n"
            f"可用函数：\n{functions}\n\n"
            "只输出函数调用，不要解释。可以使用以下任一格式：\n"
            '- JSON：{"name":"函数名","arguments":{"参数名":值}}\n'
            "- Python：函数名(参数名=值)\n"
            "需要多个调用时输出 JSON 数组或多行 Python 调用；"
            "无需调用时输出 []。"
        )


def _format_question(value: Any) -> str:
    if isinstance(value, str):
        return value
    messages: list[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, Mapping) and "content" in item:
            role = item.get("role", "user")
            messages.append(f"{role}: {item['content']}")
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif item is not None:
            messages.append(str(item))

    visit(value)
    return "\n".join(messages)
