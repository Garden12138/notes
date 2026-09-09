"""Dataset formatting and reward-function practice for chapter 11.2."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any, Dict, List, Sequence

from hello_agents.rl import (
    count_reasoning_steps,
    create_accuracy_reward,
    create_composite_reward,
    create_length_penalty_reward,
    create_step_reward,
    format_math_dataset,
    format_rl_sample,
    format_sft_sample,
)

CUSTOM_DATA = [
    {"question": "What is 2+2?", "answer": "2+2=4. #### 4"},
    {"question": "What is 5*3?", "answer": "5*3=15. #### 15"},
    {"question": "What is 10+7?", "answer": "10+7=17. #### 17"},
]


class DemoTokenizer:
    """Render the Qwen-style boundary markers without downloading a model."""

    eos_token = "<|im_end|>"

    def apply_chat_template(
        self,
        messages: Sequence[Dict[str, str]],
        *,
        tokenize: bool,
        add_generation_prompt: bool,
    ) -> str:
        if tokenize:
            raise ValueError("the demo only renders text")
        parts = [
            f"<|im_start|>{message['role']}\n"
            f"{message['content']}<|im_end|>\n"
            for message in messages
        ]
        if add_generation_prompt:
            parts.append("<|im_start|>assistant\n")
        return "".join(parts)


def tolerant_reward(
    completions: Sequence[str],
    **kwargs: Any,
) -> List[float]:
    """Give partial credit by numeric error, following the article example."""
    truths = kwargs.get("ground_truth")
    if truths is None or len(completions) != len(truths):
        raise ValueError("matching ground_truth values are required")
    rewards = []
    for completion, truth in zip(completions, truths):
        numbers = re.findall(r"-?\d+(?:\.\d+)?", completion.replace(",", ""))
        if not numbers:
            rewards.append(0.0)
            continue
        try:
            prediction = float(numbers[-1])
            expected = float(str(truth).replace(",", ""))
        except (TypeError, ValueError):
            rewards.append(0.0)
            continue
        error = abs(prediction - expected)
        if error < 0.01:
            reward = 1.0
        elif error < 1.0:
            reward = 0.8
        elif error < 5.0:
            reward = 0.5
        else:
            reward = 0.0
        if reward > 0 and ("step" in completion.lower() or "=" in completion):
            reward += 0.1
        rewards.append(min(reward, 1.0))
    return rewards


def local_demo() -> None:
    tokenizer = DemoTokenizer()
    sample = {
        "question": "Natalia sold 48 clips in April and half as many in May. "
        "How many did she sell altogether?",
        "answer": (
            "Natalia sold 48/2 = 24 clips in May.\n"
            "Natalia sold 48+24 = 72 clips altogether.\n#### 72"
        ),
    }
    sft = format_sft_sample(sample, tokenizer)
    rl = format_rl_sample(sample, tokenizer)
    print("=== 数据格式 ===")
    print(f"SFT fields: {list(sft)}")
    print(f"SFT prompt uses chat template: {sft['prompt'].startswith('<|im_start|>')}")
    print(f"RL fields: {list(rl)}")
    print(f"RL ground_truth: {rl['ground_truth']}")

    accuracy = create_accuracy_reward()
    accuracy_values = accuracy(
        ["Final Answer: 72", "Final Answer: 72.0", "Final Answer: 73"],
        ground_truth=["72", "72", "72"],
    )
    print("\n=== 准确率奖励 ===")
    print(accuracy_values)

    concise = "Final Answer: 72"
    answer_suffix = "\nFinal Answer: 72"
    verbose = "x" * (500 - len(answer_suffix)) + answer_suffix
    length_reward = create_length_penalty_reward(
        accuracy,
        max_length=200,
        penalty_weight=0.001,
    )
    print("\n=== 长度惩罚 ===")
    for text, reward in zip(
        [concise, verbose, "Final Answer: 73"],
        length_reward(
            [concise, verbose, "Final Answer: 73"],
            ground_truth=["72", "72", "72"],
        ),
    ):
        print(f"length={len(text):3d}, reward={reward:.3f}")

    no_steps = "Final Answer: 72"
    two_steps = "Step 1: 48/2=24\nStep 2: 48+24=72\nFinal Answer: 72"
    wrong_steps = "Step 1: 48/2=24\nStep 2: 48+24=73\nFinal Answer: 73"
    step_reward = create_step_reward(accuracy, step_bonus=0.1, max_steps=10)
    print("\n=== 步骤奖励 ===")
    for text, reward in zip(
        [no_steps, two_steps, wrong_steps],
        step_reward(
            [no_steps, two_steps, wrong_steps],
            ground_truth=["72", "72", "72"],
        ),
    ):
        print(f"steps={count_reasoning_steps(text)}, reward={reward:.3f}")

    combined = create_composite_reward(
        accuracy,
        max_length=40,
        penalty_weight=0.001,
        step_bonus=0.1,
    )
    combined_value = combined([two_steps], ground_truth=["72"])[0]
    print("\n=== 组合奖励 ===")
    print(f"reward={combined_value:.3f}")
    print("tolerant:", tolerant_reward(
        ["Step 1: estimate\nFinal Answer: 72.5", "Final Answer: 75"],
        ground_truth=["72", "72"],
    ))


def huggingface_demo(model_name: str) -> None:
    """Convert and register a real Dataset; this may download a tokenizer."""
    from datasets import Dataset
    from hello_agents.tools import RLTrainingTool

    raw_dataset = Dataset.from_list(CUSTOM_DATA)
    sft_dataset = format_math_dataset(
        raw_dataset,
        format_type="sft",
        model_name=model_name,
    )
    rl_dataset = format_math_dataset(
        raw_dataset,
        format_type="rl",
        model_name=model_name,
    )
    tool = RLTrainingTool()
    tool.register_dataset("my_math_dataset", rl_dataset)
    tool.register_reward_function("my_math_dataset", tolerant_reward)
    print(json.dumps({
        "sft_columns": sft_dataset.column_names,
        "rl_columns": rl_dataset.column_names,
        "registered_datasets": list(tool.custom_datasets),
        "registered_rewards": list(tool.custom_reward_functions),
    }, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Chapter 11.2 practice")
    parser.add_argument(
        "--with-huggingface",
        action="store_true",
        help="also build a real Dataset and download the selected tokenizer",
    )
    parser.add_argument("--model-name", default="Qwen/Qwen3-0.6B")
    args = parser.parse_args()
    local_demo()
    if args.with_huggingface:
        print("\n=== 自定义 Dataset 注册 ===")
        huggingface_demo(args.model_name)


if __name__ == "__main__":
    main()
