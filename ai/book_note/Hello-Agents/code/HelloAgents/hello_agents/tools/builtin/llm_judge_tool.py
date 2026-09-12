"""Tool wrapper for absolute data-generation quality scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ...evaluation.benchmarks.data_generation import (
    AIDataset,
    LLMJudgeEvaluator,
)
from ..base import Tool, ToolParameter


class LLMJudgeTool(Tool):
    """Evaluate generated AIME-style data with an LLM judge."""

    def __init__(self, judge: Any) -> None:
        super().__init__(
            name="llm_judge_evaluation",
            description="使用四维 LLM Judge 评估生成数学题质量",
        )
        self.judge = judge

    def run(self, parameters: Dict[str, Any]) -> str:
        try:
            result = self._run(parameters)
        except Exception as exc:
            result = {
                "status": "error",
                "message": f"{type(exc).__name__}: {exc}",
            }
        return json.dumps(result, ensure_ascii=False, indent=2, default=str)

    def _run(self, parameters: Dict[str, Any]) -> dict[str, Any]:
        data_path = parameters.get("generated_data_path")
        if not data_path:
            raise ValueError("generated_data_path is required")
        max_samples = int(parameters.get("max_samples", 0))
        dataset = AIDataset("generated", data_path).load(max_samples)
        evaluator = LLMJudgeEvaluator(
            self.judge,
            pass_threshold=float(parameters.get("pass_threshold", 3.5)),
            excellent_threshold=float(
                parameters.get("excellent_threshold", 4.5)
            ),
        )
        result = evaluator.evaluate(dataset)
        output_dir = Path(
            parameters.get("output_dir", "./evaluation_results/llm_judge")
        ).expanduser().resolve()
        result_path = evaluator.export_results(
            result,
            output_dir / "llm_judge_results.json",
        )
        report_path = evaluator.generate_report(
            result,
            output_dir / "llm_judge_report.md",
        )
        return {
            **result,
            "result_path": str(result_path),
            "report_path": str(report_path),
        }

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="generated_data_path",
                type="string",
                description="生成题 JSON 或 JSONL 路径",
            ),
            ToolParameter(
                name="output_dir",
                type="string",
                description="评估结果目录",
                required=False,
                default="./evaluation_results/llm_judge",
            ),
            ToolParameter(
                name="max_samples",
                type="integer",
                description="最大样本数，0 表示全部",
                required=False,
                default=0,
            ),
            ToolParameter(
                name="pass_threshold",
                type="number",
                description="通过均分阈值",
                required=False,
                default=3.5,
            ),
            ToolParameter(
                name="excellent_threshold",
                type="number",
                description="优秀均分阈值",
                required=False,
                default=4.5,
            ),
        ]

