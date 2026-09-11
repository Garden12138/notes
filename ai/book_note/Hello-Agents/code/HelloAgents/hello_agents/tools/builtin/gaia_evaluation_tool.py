"""Tool wrapper around the chapter-compatible GAIA evaluator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ...evaluation import GAIADataset, GAIAEvaluator
from ..base import Tool, ToolParameter


class GAIAEvaluationTool(Tool):
    """Load GAIA data, run an Agent, and write local artifacts."""

    def __init__(self, local_data_dir: str | Path | None = None) -> None:
        super().__init__(
            name="gaia_evaluation",
            description="使用 GAIA 数据评估智能体的通用任务解决能力",
        )
        self.local_data_dir = (
            Path(local_data_dir).expanduser().resolve()
            if local_data_dir is not None
            else None
        )

    def run(self, parameters: Dict[str, Any]) -> str:
        try:
            result = self._run(parameters)
        except Exception as exc:
            result = {
                "status": "error",
                "message": f"{type(exc).__name__}: {exc}",
            }
        return json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    def _run(self, parameters: Dict[str, Any]) -> dict[str, Any]:
        if "agent" not in parameters:
            raise ValueError("agent is required")
        split = str(parameters.get("split", "validation"))
        level_value = parameters.get("level")
        level = None if level_value in {None, "", 0, "0"} else int(level_value)
        max_samples = int(parameters.get("max_samples", 0))
        if max_samples < 0:
            raise ValueError("max_samples cannot be negative")
        data_dir_value = parameters.get("local_data_dir") or self.local_data_dir
        if data_dir_value is None:
            data_dir_value = "./data/gaia"

        dataset = GAIADataset(
            dataset_name=str(
                parameters.get("dataset_name", "gaia-benchmark/GAIA")
            ),
            split=split,
            level=level,
            local_data_dir=data_dir_value,
            auto_download=bool(parameters.get("download", False)),
        )
        evaluator = GAIAEvaluator(dataset, level=level)
        evaluation = evaluator.evaluate(
            parameters["agent"],
            max_samples=max_samples,
        )

        output_dir = Path(
            parameters.get("output_dir", "./evaluation_results")
        ).expanduser().resolve()
        level_name = f"level{level}" if level is not None else "all"
        artifacts: dict[str, str | None] = {
            "gaia_result_path": None,
            "report_path": None,
            "submission_guide_path": None,
        }
        if bool(parameters.get("export_results", True)):
            path = output_dir / "gaia_official" / f"gaia_{level_name}_results.jsonl"
            artifacts["gaia_result_path"] = str(
                evaluator.export_to_gaia_format(
                    evaluation,
                    path,
                    include_reasoning=bool(
                        parameters.get("include_reasoning", True)
                    ),
                )
            )
        if bool(parameters.get("generate_report", True)):
            path = output_dir / f"gaia_report_{level_name}.md"
            artifacts["report_path"] = str(
                evaluator.generate_report(
                    evaluation,
                    path,
                    agent_name=str(
                        getattr(parameters["agent"], "name", "Agent")
                    ),
                )
            )
        if bool(parameters.get("generate_submission_guide", True)):
            path = output_dir / "GAIA_SUBMISSION_GUIDE.md"
            artifacts["submission_guide_path"] = str(
                evaluator.generate_submission_guide(path)
            )

        return {
            **evaluation,
            **artifacts,
            "dataset_statistics": dataset.get_statistics(),
            "score_scope": "helloagents_chapter_quasi_exact_match",
            "official_submission": "not_run",
        }

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="agent",
                type="object",
                description="待评估的 Agent，需提供 run(prompt) 方法",
            ),
            ToolParameter(
                name="split",
                type="string",
                description="GAIA 数据划分：validation 或 test",
                required=False,
                default="validation",
            ),
            ToolParameter(
                name="dataset_name",
                type="string",
                description="Hugging Face 数据集名称",
                required=False,
                default="gaia-benchmark/GAIA",
            ),
            ToolParameter(
                name="level",
                type="integer",
                description="难度 1、2、3；0 表示全部",
                required=False,
                default=0,
            ),
            ToolParameter(
                name="local_data_dir",
                type="string",
                description="GAIA 本地快照目录",
                required=False,
                default="./data/gaia",
            ),
            ToolParameter(
                name="max_samples",
                type="integer",
                description="最大样本数，0 表示全部",
                required=False,
                default=0,
            ),
            ToolParameter(
                name="download",
                type="boolean",
                description="本地数据缺失时是否显式下载受限数据",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="output_dir",
                type="string",
                description="结果、报告和交接说明的输出目录",
                required=False,
                default="./evaluation_results",
            ),
            ToolParameter(
                name="export_results",
                type="boolean",
                description="是否导出章节兼容的 GAIA JSONL",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="include_reasoning",
                type="boolean",
                description="导出 JSONL 时是否保留原始响应",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="generate_report",
                type="boolean",
                description="是否生成 Markdown 评估报告",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="generate_submission_guide",
                type="boolean",
                description="是否生成结果交接检查说明",
                required=False,
                default=True,
            ),
        ]
