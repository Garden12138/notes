"""Evaluate an Agent on GAIA-style questions and attachments."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping, Sequence

from .dataset import GAIADataset
from .metrics import GAIAMetrics
from .quasi_exact_match import (
    extract_final_answer,
    normalize_answer,
    partial_match_score,
    quasi_exact_match,
)


class GAIAEvaluator:
    """Run independent GAIA cases and apply chapter-style answer matching."""

    def __init__(
        self,
        dataset: GAIADataset | Sequence[Mapping[str, Any]],
        level: int | None = None,
        *,
        reset_history_between_cases: bool = True,
        partial_match_threshold: float = 0.5,
    ) -> None:
        if level not in {None, 1, 2, 3}:
            raise ValueError("level must be 1, 2, 3, or None")
        if not 0 <= partial_match_threshold <= 1:
            raise ValueError("partial_match_threshold must be in [0, 1]")
        self.dataset = dataset
        self.level = level
        self.reset_history_between_cases = reset_history_between_cases
        self.partial_match_threshold = partial_match_threshold
        self.metrics_calculator = GAIAMetrics()

    def evaluate(
        self,
        agent: Any,
        max_samples: int | None = None,
    ) -> dict[str, Any]:
        """Evaluate ``agent.run(prompt)`` and retain auditable evidence."""
        if max_samples is not None and max_samples < 0:
            raise ValueError("max_samples cannot be negative")
        predictor = self._resolve_predictor(agent)
        data = self._load_data(max_samples)
        if not data:
            raise ValueError("the selected GAIA dataset is empty")

        results: list[dict[str, Any]] = []
        for item in data:
            if self.reset_history_between_cases:
                clear_history = getattr(agent, "clear_history", None)
                if callable(clear_history):
                    clear_history()
            started = perf_counter()
            response = ""
            predicted = ""
            error = None
            try:
                raw_response = predictor(self._build_prompt(item))
                if not isinstance(raw_response, str):
                    raise TypeError("agent.run must return text")
                response = raw_response
                predicted = extract_final_answer(response)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"

            expected = str(item.get("final_answer", "")).strip()
            is_scorable = bool(expected)
            exact = (
                quasi_exact_match(predicted, expected)
                if is_scorable and error is None
                else (False if is_scorable else None)
            )
            partial_score = (
                partial_match_score(predicted, expected)
                if is_scorable and error is None
                else (0.0 if is_scorable else None)
            )
            steps = getattr(agent, "last_run_steps", None)
            if isinstance(steps, bool) or not isinstance(steps, int):
                steps = None
            results.append(
                {
                    "task_id": item["task_id"],
                    "level": item["level"],
                    "question": item["question"],
                    "attachment_path": item.get("attachment_path"),
                    "attachment_exists": item.get("attachment_exists", False),
                    "response": response,
                    "predicted": predicted,
                    "expected": expected if is_scorable else None,
                    "normalized_predicted": (
                        normalize_answer(predicted, expected)
                        if is_scorable else normalize_answer(predicted)
                    ),
                    "normalized_expected": (
                        normalize_answer(expected, expected)
                        if is_scorable else None
                    ),
                    "exact_match": exact,
                    "partial_match_score": partial_score,
                    "partial_match": (
                        partial_score >= self.partial_match_threshold
                        if partial_score is not None else None
                    ),
                    "reasoning_steps": steps,
                    "duration_seconds": max(0.0, perf_counter() - started),
                    "error": error,
                }
            )

        metrics = self.metrics_calculator.compute_metrics(results)
        return {
            "status": "success",
            "agent_name": str(getattr(agent, "name", "Agent")),
            "level": self.level,
            "level_filter": self.level,
            "total_samples": len(results),
            **metrics,
            "detailed_results": results,
        }

    def export_to_gaia_format(
        self,
        evaluation: Mapping[str, Any],
        output_path: str | Path,
        *,
        include_reasoning: bool = True,
    ) -> Path:
        """Export the chapter's JSONL handoff format without submitting it."""
        output = Path(output_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for result in evaluation.get("detailed_results", []):
                entry = {
                    "task_id": result["task_id"],
                    "model_answer": result.get("predicted", ""),
                }
                if include_reasoning:
                    entry["reasoning_trace"] = result.get("response", "")
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return output

    def generate_report(
        self,
        evaluation: Mapping[str, Any],
        output_path: str | Path,
        *,
        agent_name: str = "Agent",
    ) -> Path:
        """Write a compact report with level results and failure evidence."""
        output = Path(output_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        exact_rate = evaluation.get("exact_match_rate")
        exact_text = (
            f"{exact_rate:.2%}" if exact_rate is not None else "不可评分"
        )
        lines = [
            "# GAIA 评估报告",
            "",
            f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
            f"- 智能体：{agent_name}",
            f"- 样本：{evaluation.get('total_samples', 0)}",
            f"- 可评分样本：{evaluation.get('scored_samples', 0)}",
            f"- 本地准精确匹配率：{exact_text}",
            "",
            "> 本报告来自 HelloAgents 教学实现，不是 GAIA 官方排行榜成绩。",
            "",
            "## 分级结果",
            "",
            "| Level | 正确 | 可评分 | 总数 | 准确率 |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
        for level, stats in evaluation.get("level_metrics", {}).items():
            accuracy = stats.get("accuracy")
            accuracy_text = f"{accuracy:.2%}" if accuracy is not None else "—"
            lines.append(
                f"| {level} | {stats['correct']} | {stats['scored']} | "
                f"{stats['total']} | {accuracy_text} |"
            )
        lines.extend(
            [
                "",
                "## 样本详情",
                "",
                "| Task ID | Level | 匹配 | 预测 | 错误 |",
                "| --- | ---: | --- | --- | --- |",
            ]
        )
        for item in evaluation.get("detailed_results", []):
            matched = item.get("exact_match")
            matched_text = (
                "—" if matched is None else ("是" if matched else "否")
            )
            prediction = str(item.get("predicted", "")).replace("|", "\\|")
            error = str(item.get("error") or "").replace("|", "\\|")
            lines.append(
                f"| {item['task_id']} | {item['level']} | {matched_text} | "
                f"`{prediction}` | {error} |"
            )
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output

    @staticmethod
    def generate_submission_guide(output_path: str | Path) -> Path:
        """Write operational reminders; it performs no network submission."""
        output = Path(output_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "# GAIA 结果交接说明\n\n"
            "1. 确认已接受 GAIA 数据集条款，且没有公开测试集内容。\n"
            "2. 检查 JSONL 中每个 task_id 与 model_answer。\n"
            "3. 固定模型、工具、最大步骤、数据提交和运行时间。\n"
            "4. 按当前官方排行榜页面说明提交；本工具不会自动上传。\n",
            encoding="utf-8",
        )
        return output

    def _load_data(self, max_samples: int | None) -> list[dict[str, Any]]:
        if isinstance(self.dataset, GAIADataset):
            return self.dataset.load(max_samples=max_samples)
        data = [dict(item) for item in self.dataset]
        if self.level is not None:
            data = [
                item
                for item in data
                if int(item.get("level", 0)) == self.level
            ]
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
        parts = [f"Question:\n{item['question']}"]
        attachment = item.get("attachment_path")
        if attachment:
            status = "available" if item.get("attachment_exists") else "missing"
            parts.append(
                f"Attachment ({status}):\n{attachment}\n"
                "Inspect this file with an appropriate tool when the task "
                "requires it."
            )
        parts.append(
            "Finish with `FINAL ANSWER: [answer]`; keep that answer minimal."
        )
        return "\n\n".join(parts)
