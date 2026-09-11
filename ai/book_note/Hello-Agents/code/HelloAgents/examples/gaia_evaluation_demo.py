"""Deterministic, offline practice for section 12.3."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from hello_agents import GAIADataset, GAIAEvaluationTool
from hello_agents.evaluation import normalize_answer, quasi_exact_match


class FixedGAIAAgent:
    """Return known outputs while exposing actual step counts for the demo."""

    name = "FixedGAIAAgent"
    last_run_steps = 0

    def clear_history(self) -> None:
        pass

    def run(self, prompt: str) -> str:
        if "receipt" in prompt:
            self.last_run_steps = 1
            return "Calculated the total.\nFINAL ANSWER: [$1,234.50]"
        if "largest ocean" in prompt:
            self.last_run_steps = 1
            return "FINAL ANSWER: [The Pacific Ocean.]"
        if "alphabetically" in prompt:
            self.last_run_steps = 2
            return "FINAL ANSWER: [Paris, Berlin, London]"
        if "project code" in prompt:
            self.last_run_steps = 2
            return "I inspected the attachment.\nFINAL ANSWER: [HARBOR-7]"
        self.last_run_steps = 4
        return "FINAL ANSWER: [41]"


def main() -> None:
    data_dir = Path(__file__).parent / "data" / "gaia"
    dataset = GAIADataset(local_data_dir=data_dir)
    statistics = dataset.get_statistics()
    tool = GAIAEvaluationTool(data_dir)
    with tempfile.TemporaryDirectory(prefix="helloagents-gaia-") as output_dir:
        result = json.loads(
            tool.run(
                {
                    "agent": FixedGAIAAgent(),
                    "split": "validation",
                    "level": 0,
                    "max_samples": 0,
                    "output_dir": output_dir,
                    "download": False,
                }
            )
        )
        assert result["status"] == "success", result
        assert result["total_samples"] == 5
        assert result["correct_samples"] == 4
        assert result["exact_match_rate"] == 0.8
        assert result["level_metrics"]["1"]["accuracy"] == 1.0
        assert result["level_metrics"]["2"]["accuracy"] == 1.0
        assert result["level_metrics"]["3"]["accuracy"] == 0.0

        exported = Path(result["gaia_result_path"])
        report = Path(result["report_path"])
        guide = Path(result["submission_guide_path"])
        exported_records = [
            json.loads(line)
            for line in exported.read_text(encoding="utf-8").splitlines()
        ]
        assert exported_records[0]["task_id"] == "demo_gaia_001"
        assert "reasoning_trace" in exported_records[0]
        print("=== 12.3 GAIA 通用助手评估实践 ===")
        print(f"samples: {result['total_samples']}")
        print(f"attachments: {statistics['attachment_samples']}")
        print(f"exact_match_rate: {result['exact_match_rate']:.2%}")
        print(f"partial_match_rate: {result['partial_match_rate']:.2%}")
        print("level_accuracy:")
        for level, metrics in result["level_metrics"].items():
            print(f"  level_{level}: {metrics['accuracy']:.2%}")
        print("difficulty_drop_rates:")
        for transition, value in result["difficulty_drop_rates"].items():
            print(f"  {transition}: {value:.2%}")
        print(
            f"average_reasoning_steps: {result['average_reasoning_steps']:.2f}"
        )
        print(
            "numeric_comma_match: "
            f"{quasi_exact_match('$1,234.50', '1234.5')}"
        )
        print(
            "normalized_list: "
            f"{normalize_answer('Paris, Berlin, London', 'London, Paris, Berlin')}"
        )
        print(f"gaia_jsonl_records: {len(exported_records)}")
        print(f"report_generated: {report.is_file()}")
        print(f"submission_guide_generated: {guide.is_file()}")
        print(f"official_submission: {result['official_submission']}")


if __name__ == "__main__":
    main()
