"""Deterministic, offline practice for section 12.4."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from hello_agents import (
    AIMEGenerator,
    HumanVerificationStore,
    LLMJudgeTool,
    WinRateTool,
)


class FixedGeneratorAgent:
    """Return three original fixtures without calling a model."""

    def __init__(self) -> None:
        self.index = 0
        self.responses = [
            {
                "problem": (
                    "A jar contains 4 red and 3 blue balls. Two are drawn "
                    "without replacement. If the probability that both are "
                    "red is m/n in lowest terms, find 100m+n."
                ),
                "answer": "207",
                "solution": "The probability is C(4,2)/C(7,2)=6/21=2/7, so 100m+n=207.",
                "topic": "Probability",
            },
            {
                "problem": "The positive roots of x^2-11x+24=0 are a and b. Find a^2+b^2.",
                "answer": "73",
                "solution": "Since a+b=11 and ab=24, a^2+b^2=121-48=73.",
                "topic": "Algebra",
            },
            {
                "problem": "How many integers from 1 through 100 are divisible by 4 but not by 6?",
                "answer": "17",
                "solution": (
                    "There are 25 multiples of 4 and 8 multiples of "
                    "lcm(4,6)=12, leaving 17."
                ),
                "topic": "Number Theory",
            },
        ]

    def run(self, _prompt: str) -> str:
        response = self.responses[self.index]
        self.index += 1
        return json.dumps(response, ensure_ascii=False)


class FixedJudge:
    """Emit known scores and pair decisions for pipeline verification."""

    def __init__(self) -> None:
        self.absolute_index = 0
        self.pair_index = 0

    def run(self, prompt: str) -> str:
        if "分别从 1 到 5" in prompt:
            score = [5, 4, 3][self.absolute_index]
            self.absolute_index += 1
            return json.dumps(
                {
                    "scores": {
                        "correctness": score,
                        "clarity": score,
                        "difficulty_match": score,
                        "completeness": score,
                    },
                    "comments": "固定评分，仅验证聚合逻辑。",
                },
                ensure_ascii=False,
            )
        winner = ["A", "B", "Tie"][self.pair_index]
        self.pair_index += 1
        return json.dumps(
            {"winner": winner, "reason": "固定结果，仅验证成对统计。"},
            ensure_ascii=False,
        )


def main() -> None:
    reference_path = (
        Path(__file__).parent
        / "data"
        / "data_generation"
        / "reference_aime.json"
    )
    with tempfile.TemporaryDirectory(prefix="helloagents-data-quality-") as root:
        output_root = Path(root)
        generation = AIMEGenerator(
            agent=FixedGeneratorAgent(),
            delay_seconds=0,
            use_reference_examples=True,
            reference_data_path=reference_path,
            seed=7,
        ).generate_and_save(
            3,
            output_root / "generated_data",
            checkpoint_every=1,
        )
        assert generation["metadata"]["generated"] == 3
        assert generation["metadata"]["failed"] == 0
        generated_path = generation["output_path"]

        judge = FixedJudge()
        absolute = json.loads(
            LLMJudgeTool(judge).run(
                {
                    "generated_data_path": generated_path,
                    "output_dir": output_root / "evaluation" / "llm_judge",
                }
            )
        )
        paired = json.loads(
            WinRateTool(judge).run(
                {
                    "generated_data_path": generated_path,
                    "reference_data_path": reference_path,
                    "output_dir": output_root / "evaluation" / "win_rate",
                    "seed": 7,
                }
            )
        )
        human = HumanVerificationStore(
            generated_path,
            output_root / "generated_aime_verifications.json",
        )
        human.record(
            "gen_aime_0001",
            {
                "correctness": 5,
                "clarity": 5,
                "difficulty_match": 4,
                "completeness": 4,
            },
            "approved",
            "答案和推导可以复核。",
            verified_at="2026-09-11T10:00:00+08:00",
        )
        human_summary = human.summary()
        latex_record = AIMEGenerator._parse_response(
            r'{"problem":"Find \theta.","answer":"7",'
            r'"solution":"Use \frac{14}{2}.","topic":"Algebra"}'
        )

        assert absolute["average_score"] == 4.0
        assert absolute["pass_rate"] == 0.6667
        assert absolute["excellent_rate"] == 0.3333
        assert paired["wins"] == paired["losses"] == paired["ties"] == 1
        assert human_summary["verified_samples"] == 1
        assert latex_record["solution"] == r"Use \frac{14}{2}."

        print("=== 12.4 数据生成质量评估实践 ===")
        print("generated: 3/3")
        print(f"llm_judge_average: {absolute['average_score']:.2f}/5")
        print(f"llm_judge_pass_rate: {absolute['pass_rate']:.2%}")
        print(f"llm_judge_excellent_rate: {absolute['excellent_rate']:.2%}")
        print(f"pairwise_win_rate: {paired['win_rate']:.2%}")
        print(f"pairwise_loss_rate: {paired['loss_rate']:.2%}")
        print(f"pairwise_tie_rate: {paired['tie_rate']:.2%}")
        print(
            "human_verification_progress: "
            f"{human_summary['verified_samples']}/{human_summary['total_samples']}"
        )
        print("latex_json_escape_repaired: True")
        print("network_calls: 0")
        print("real_model_calls: 0")
        print("artifacts_location: temporary_directory")


if __name__ == "__main__":
    main()
