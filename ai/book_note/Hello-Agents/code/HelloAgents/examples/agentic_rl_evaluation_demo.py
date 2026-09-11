"""Offline metric preview and runnable model comparison for chapter 11.5."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Sequence, Tuple

from hello_agents.rl import evaluate_prediction_records
from hello_agents.tools import RLTrainingTool


METRICS = [
    "accuracy",
    "accuracy_at_k",
    "numerical_error",
    "average_length",
    "average_steps",
    "inference_time",
    "format_correctness",
]


def sample_records() -> List[Dict[str, Any]]:
    """Return fixed completions covering the chapter's four error types."""
    return [
        {
            "question": "48 个夹子加上其一半，共有多少个？",
            "predictions": [
                "Step 1: 48 / 2 = 24\nStep 2: 48 + 24 = 72\nFinal Answer: 72",
                "Final Answer: 70",
                "Final Answer: 71",
            ],
            "ground_truth": "72",
            "full_answer": "48/2 = <<48/2=24>>24\n48+24 = <<48+24=72>>72\n#### 72",
            "token_lengths": [17, 3, 3],
            "inference_time": 0.12,
        },
        {
            "question": "同一道题的另一组候选。",
            "predictions": [
                "Step 1: 48 / 2 = 25\nStep 2: 48 + 25 = 73\nFinal Answer: 73",
                "Step 1: 48 / 2 = 24\nStep 2: 48 + 24 = 72\nFinal Answer: 72",
                "Final Answer: 70",
            ],
            "ground_truth": "72",
            "full_answer": "48/2 = <<48/2=24>>24\n48+24 = <<48+24=72>>72\n#### 72",
            "token_lengths": [17, 17, 3],
            "inference_time": 0.14,
        },
        {
            "question": "一个需要三步计算的问题。",
            "predictions": [
                "我无法确定答案。",
                "答案可能是 9。",
                "答案可能是 10。",
            ],
            "ground_truth": "12",
            "full_answer": "a <<1+1=2>>\nb <<2+2=4>>\nc <<4*3=12>>\n#### 12",
            "token_lengths": [1, 4, 4],
            "inference_time": 0.08,
        },
        {
            "question": "一个需要五步推理的问题。",
            "predictions": [
                "Step 1: 先使用错误的解题顺序。\nFinal Answer: 20",
                "Final Answer: 21",
                "Final Answer: 22",
            ],
            "ground_truth": "24",
            "full_answer": (
                "a <<1+1=2>>\nb <<2+2=4>>\nc <<4+4=8>>\n"
                "d <<8+8=16>>\ne <<16+8=24>>\n#### 24"
            ),
            "token_lengths": [6, 3, 3],
            "inference_time": 0.11,
        },
        {
            "question": "一天卖鸡蛋可以收入多少美元？",
            "predictions": [
                "Final Answer: 30",
                "Final Answer: 28",
                "Final Answer: 26",
            ],
            "ground_truth": "18",
            "full_answer": (
                "剩余鸡蛋 <<16-3-4=9>>9 个，每个 2 美元。\n#### 18"
            ),
            "token_lengths": [3, 3, 3],
            "inference_time": 0.10,
        },
    ]


def offline_preview() -> Dict[str, Any]:
    report = evaluate_prediction_records(
        sample_records(),
        metrics=METRICS,
        k=3,
        return_details=True,
    )
    print("=== 11.5 评估逻辑预览 ===")
    print(f"samples: {report['num_samples']}")
    print(f"accuracy: {report['accuracy']:.2%}")
    print(f"accuracy@3: {report['accuracy_at_k']:.2%}")
    print(f"numerical_error: {report['numerical_error']:.2f}")
    print(f"average_length: {report['average_length']:.2f}")
    print(f"average_steps: {report['average_steps']:.2f}")
    print(f"average_inference_time: {report['average_inference_time']:.2f}s")
    print(f"format_correctness: {report['format_correctness']:.2%}")
    print(f"error_distribution: {report['error_distribution']}")
    print(f"accuracy_by_difficulty: {report['accuracy_by_difficulty']}")
    print("model_loaded: False (add --run to evaluate real checkpoints)")
    return report


def parse_models(values: Sequence[str] | None) -> List[Tuple[str, str]]:
    if not values:
        return [
            ("预训练模型", "Qwen/Qwen3-0.6B"),
            ("SFT模型", "./output/sft_full"),
            ("GRPO模型", "./output/grpo_full"),
        ]
    models = []
    for value in values:
        if "=" not in value:
            raise ValueError("--model must use NAME=PATH")
        name, path = value.split("=", 1)
        if not name.strip() or not path.strip():
            raise ValueError("--model name and path cannot be empty")
        models.append((name.strip(), path.strip()))
    return models


def evaluate_models(
    models: Sequence[Tuple[str, str]],
    max_samples: int,
    k: int,
    max_new_tokens: int,
) -> None:
    tool = RLTrainingTool()
    rows = []
    for name, path in models:
        result = json.loads(
            tool.run(
                {
                    "action": "evaluate",
                    "model_path": path,
                    "max_samples": max_samples,
                    "metrics": METRICS,
                    "k": k,
                    "max_new_tokens": max_new_tokens,
                    "return_details": True,
                    "seed": 42,
                }
            )
        )
        if result.get("status") != "success":
            raise RuntimeError(f"{name}: {result.get('message', 'evaluation failed')}")
        rows.append((name, result))

    print("\n=== 模型对比 ===")
    print(
        f"{'模型':<12} {'Accuracy':>10} {'Accuracy@K':>12} "
        f"{'平均Token':>10} {'格式正确率':>12}"
    )
    for name, result in rows:
        print(
            f"{name:<12} {result['accuracy']:>9.2%} "
            f"{result['accuracy_at_k']:>11.2%} "
            f"{result['average_length']:>10.1f} "
            f"{result['format_correctness']:>11.2%}"
        )
        print(f"  错误分布: {result['error_distribution']}")
        print(f"  难度分组: {result['accuracy_by_difficulty']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Chapter 11.5 evaluation practice")
    parser.add_argument(
        "--run",
        action="store_true",
        help="load checkpoints and evaluate the GSM8K test split",
    )
    parser.add_argument(
        "--model",
        action="append",
        help="model to compare, in NAME=PATH form; may be repeated",
    )
    parser.add_argument("--max-samples", type=int, default=200)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    if min(args.max_samples, args.k, args.max_new_tokens) <= 0:
        parser.error("sample count, k and max_new_tokens must be positive")
    offline_preview()
    if args.run:
        evaluate_models(
            parse_models(args.model),
            args.max_samples,
            args.k,
            args.max_new_tokens,
        )


if __name__ == "__main__":
    main()
