"""Tool wrapper around the chapter 12 BFCL teaching evaluator."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from ...evaluation import BFCLDataset, BFCLEvaluator
from ..base import Tool, ToolParameter


class BFCLEvaluationTool(Tool):
    """Load BFCL data, run an Agent, export JSONL and write a report."""

    def __init__(self, bfcl_data_dir: str | Path | None = None) -> None:
        super().__init__(
            name="bfcl_evaluation",
            description="使用 BFCL 数据评估智能体的工具调用结构",
        )
        self.bfcl_data_dir = (
            Path(bfcl_data_dir).expanduser().resolve()
            if bfcl_data_dir is not None
            else None
        )

    def run(self, parameters: Dict[str, Any]) -> str:
        try:
            return json.dumps(
                self._run(parameters),
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        except Exception as exc:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"{type(exc).__name__}: {exc}",
                },
                ensure_ascii=False,
                indent=2,
            )

    def _run(self, parameters: Dict[str, Any]) -> dict[str, Any]:
        if "agent" not in parameters:
            raise ValueError("agent is required")
        category = str(parameters.get("category", "simple_python"))
        max_samples = int(parameters.get("max_samples", 0))
        if max_samples < 0:
            raise ValueError("max_samples cannot be negative")

        data_dir_value = parameters.get("bfcl_data_dir") or self.bfcl_data_dir
        if data_dir_value is None:
            raise ValueError(
                "bfcl_data_dir is required; point it to bfcl_eval/data"
            )
        dataset = BFCLDataset(data_dir_value, category=category)
        evaluator = BFCLEvaluator(dataset, category=category)
        evaluation = evaluator.evaluate(
            parameters["agent"],
            max_samples=max_samples,
            category_weights=parameters.get("category_weights"),
        )

        output_dir = Path(
            parameters.get("output_dir", "./evaluation_results")
        ).expanduser().resolve()
        artifact_paths: dict[str, str | None] = {
            "bfcl_result_path": None,
            "report_path": None,
        }
        if bool(parameters.get("export_results", True)):
            result_path = output_dir / "bfcl_official" / (
                f"BFCL_v4_{category}_result.json"
            )
            artifact_paths["bfcl_result_path"] = str(
                evaluator.export_to_bfcl_format(evaluation, result_path)
            )
        if bool(parameters.get("generate_report", True)):
            report_path = output_dir / f"bfcl_report_{category}.md"
            agent_name = str(
                getattr(parameters["agent"], "name", "Agent")
            )
            artifact_paths["report_path"] = str(
                evaluator.generate_report(
                    evaluation,
                    report_path,
                    agent_name=agent_name,
                )
            )

        official = {"requested": False, "status": "not_run"}
        if bool(parameters.get("run_official_eval", False)):
            result_path = artifact_paths["bfcl_result_path"]
            if result_path is None:
                raise ValueError(
                    "export_results must be true before official evaluation"
                )
            official = self._run_official_evaluation(
                result_path=Path(result_path),
                category=category,
                model_name=str(parameters.get("model_name", "")),
                official_root=parameters.get("official_root"),
            )

        return {
            **evaluation,
            **artifact_paths,
            "official_evaluation": official,
            "score_scope": "helloagents_local_matcher",
        }

    @staticmethod
    def _run_official_evaluation(
        *,
        result_path: Path,
        category: str,
        model_name: str,
        official_root: str | Path | None,
    ) -> dict[str, Any]:
        if not model_name:
            raise ValueError("model_name is required for official evaluation")
        if official_root is None:
            raise ValueError(
                "official_root is required and must point to the cloned "
                "berkeley-function-call-leaderboard directory"
            )
        root = Path(official_root).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"official_root does not exist: {root}")
        executable = shutil.which("bfcl")
        if executable is None:
            raise RuntimeError("bfcl executable not found in PATH")

        model_dir = model_name.replace("/", "_")
        official_result = (
            root
            / "result"
            / model_dir
            / f"BFCL_v4_{category}_result.json"
        )
        official_result.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(result_path, official_result)
        command = [
            executable,
            "evaluate",
            "--model",
            model_name,
            "--test-category",
            category,
            "--partial-eval",
        ]
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        return {
            "requested": True,
            "status": "success" if completed.returncode == 0 else "error",
            "returncode": completed.returncode,
            "command": command,
            "result_path": str(official_result),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="agent",
                type="object",
                description="待评估的 Agent，需提供 run(prompt) 方法",
            ),
            ToolParameter(
                name="category",
                type="string",
                description="BFCL 类别，例如 simple_python",
                required=False,
                default="simple_python",
            ),
            ToolParameter(
                name="bfcl_data_dir",
                type="string",
                description="官方 bfcl_eval/data 或兼容数据目录",
                required=False,
            ),
            ToolParameter(
                name="max_samples",
                type="integer",
                description="最大样本数，0 表示全部",
                required=False,
                default=0,
            ),
            ToolParameter(
                name="output_dir",
                type="string",
                description="导出结果和报告的目录",
                required=False,
                default="./evaluation_results",
            ),
            ToolParameter(
                name="run_official_eval",
                type="boolean",
                description="是否显式调用已安装的 BFCL 官方 CLI",
                required=False,
                default=False,
            ),
        ]

