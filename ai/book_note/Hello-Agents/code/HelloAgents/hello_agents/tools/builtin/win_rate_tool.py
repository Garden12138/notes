"""Tool wrapper for pairwise data-generation quality evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ...evaluation.benchmarks.data_generation import AIDataset, WinRateEvaluator
from ..base import Tool, ToolParameter


class WinRateTool(Tool):
    """Compare generated AIME-style data with real reference problems."""

    def __init__(self, judge: Any) -> None:
        super().__init__(
            name="win_rate_evaluation",
            description="成对比较生成题与真实 AIME 参考题",
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
        generated_path = parameters.get("generated_data_path")
        if not generated_path:
            raise ValueError("generated_data_path is required")
        max_pairs = int(parameters.get("max_pairs", 0))
        generated = AIDataset("generated", generated_path).load()
        reference_path = parameters.get("reference_data_path") or None
        reference = AIDataset(
            "real",
            reference_path,
            dataset_name=str(parameters.get("reference_dataset", "math-ai/aime25")),
            auto_download=bool(parameters.get("download_reference", False)),
        ).load()
        evaluator = WinRateEvaluator(
            self.judge,
            seed=int(parameters.get("seed", 42)),
        )
        result = evaluator.evaluate(
            generated,
            reference,
            max_pairs=max_pairs,
        )
        output_dir = Path(
            parameters.get("output_dir", "./evaluation_results/win_rate")
        ).expanduser().resolve()
        result_path = evaluator.export_results(
            result,
            output_dir / "win_rate_results.json",
        )
        report_path = evaluator.generate_report(
            result,
            output_dir / "win_rate_report.md",
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
                name="reference_data_path",
                type="string",
                description="本地真实参考题路径；缺省时需显式允许下载",
                required=False,
                default="",
            ),
            ToolParameter(
                name="reference_dataset",
                type="string",
                description="Hugging Face 参考数据集",
                required=False,
                default="math-ai/aime25",
            ),
            ToolParameter(
                name="download_reference",
                type="boolean",
                description="本地数据缺失时是否显式下载",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="output_dir",
                type="string",
                description="评估结果目录",
                required=False,
                default="./evaluation_results/win_rate",
            ),
            ToolParameter(
                name="max_pairs",
                type="integer",
                description="最大比较对数，0 表示尽可能多",
                required=False,
                default=0,
            ),
            ToolParameter(
                name="seed",
                type="integer",
                description="参考题抽样随机种子",
                required=False,
                default=42,
            ),
        ]
