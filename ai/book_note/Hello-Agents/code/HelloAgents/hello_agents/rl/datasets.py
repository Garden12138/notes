"""GSM8K loading and formatting for the SFT and GRPO examples."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def split_gsm8k_answer(answer: str) -> tuple[str, str]:
    """Split GSM8K's reasoning text from its final ``####`` answer."""
    if "####" not in answer:
        return answer.strip(), answer.strip()
    reasoning, final_answer = answer.rsplit("####", 1)
    return reasoning.strip(), final_answer.strip()


def format_sft_sample(example: Dict[str, Any]) -> Dict[str, str]:
    """Convert one GSM8K row to prompt/completion/text fields."""
    question = str(example["question"]).strip()
    reasoning, final_answer = split_gsm8k_answer(str(example["answer"]))
    prompt = f"Question: {question}\n\nLet's solve this step by step:\n"
    completion = f"{reasoning}\n\nFinal Answer: {final_answer}"
    return {
        "prompt": prompt,
        "completion": completion,
        "text": prompt + completion,
    }


def format_rl_sample(
    example: Dict[str, Any],
    tokenizer: Any = None,
) -> Dict[str, Any]:
    """Convert one row to the prompt and reference answer expected by GRPO."""
    question = str(example["question"]).strip()
    _, final_answer = split_gsm8k_answer(str(example["answer"]))
    prompt_content = f"Question: {question}\n\nLet's solve this step by step:"
    if tokenizer is None:
        prompt: Any = prompt_content
    else:
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt_content}],
            tokenize=False,
            add_generation_prompt=True,
        )
    return {
        "prompt": prompt,
        "ground_truth": final_answer,
        "question": question,
        "full_answer": str(example["answer"]),
    }


class GSM8KDataset:
    """Load GSM8K and expose one of the two formats used in the chapter."""

    def __init__(
        self,
        split: str = "train",
        max_samples: Optional[int] = None,
        format_type: str = "sft",
        tokenizer: Any = None,
    ) -> None:
        if split not in {"train", "test"}:
            raise ValueError("split must be 'train' or 'test'")
        if format_type not in {"sft", "rl"}:
            raise ValueError("format_type must be 'sft' or 'rl'")
        if max_samples is not None and max_samples <= 0:
            raise ValueError("max_samples must be positive")

        try:
            from datasets import load_dataset
        except ImportError as exc:
            raise ImportError("加载 GSM8K 需要安装 datasets") from exc

        self.split = split
        self.format_type = format_type
        self.tokenizer = tokenizer
        self.dataset = load_dataset("openai/gsm8k", "main", split=split)
        if max_samples is not None:
            size = min(max_samples, len(self.dataset))
            self.dataset = self.dataset.select(range(size))

    def get_dataset(self) -> Any:
        formatter = (
            format_sft_sample
            if self.format_type == "sft"
            else lambda row: format_rl_sample(row, self.tokenizer)
        )
        return self.dataset.map(
            formatter,
            remove_columns=self.dataset.column_names,
        )

    def __len__(self) -> int:
        return len(self.dataset)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        row = self.dataset[index]
        if self.format_type == "sft":
            return format_sft_sample(row)
        return format_rl_sample(row, self.tokenizer)


def _load_tokenizer(model_name: str) -> Any:
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ImportError("RL 格式需要安装 transformers") from exc
    return AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)


def create_math_dataset(
    dataset_name: str = "gsm8k",
    split: str = "train",
    max_samples: Optional[int] = None,
    format_type: str = "sft",
    tokenizer: Any = None,
) -> Any:
    if dataset_name.lower() != "gsm8k":
        raise ValueError("currently only the gsm8k dataset is supported")
    return GSM8KDataset(
        split=split,
        max_samples=max_samples,
        format_type=format_type,
        tokenizer=tokenizer,
    ).get_dataset()


def format_math_dataset(
    dataset: Any,
    format_type: str = "sft",
    model_name: str = "Qwen/Qwen3-0.6B",
) -> Any:
    """Format a compatible custom dataset without reloading GSM8K."""
    required = {"question", "answer"}
    if not required.issubset(set(dataset.column_names)):
        raise ValueError("dataset must contain question and answer columns")
    if format_type == "sft":
        formatter = format_sft_sample
    elif format_type == "rl":
        tokenizer = _load_tokenizer(model_name)
        formatter = lambda row: format_rl_sample(row, tokenizer)
    else:
        raise ValueError("format_type must be 'sft' or 'rl'")
    return dataset.map(formatter, remove_columns=dataset.column_names)


def create_sft_dataset(
    max_samples: Optional[int] = 1000,
    split: str = "train",
) -> Any:
    return create_math_dataset(
        split=split,
        max_samples=max_samples,
        format_type="sft",
    )


def create_rl_dataset(
    max_samples: Optional[int] = 1000,
    split: str = "train",
    model_name: str = "Qwen/Qwen3-0.6B",
) -> Any:
    tokenizer = _load_tokenizer(model_name)
    return create_math_dataset(
        split=split,
        max_samples=max_samples,
        format_type="rl",
        tokenizer=tokenizer,
    )


def preview_dataset(dataset: Any, num_samples: int = 3) -> List[Dict[str, Any]]:
    """Return serializable samples without printing inside library code."""
    if num_samples < 0:
        raise ValueError("num_samples cannot be negative")
    return [dict(dataset[index]) for index in range(min(num_samples, len(dataset)))]
