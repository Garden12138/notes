"""第 7 章指令数据格式化、动态填充与回答导出工具。"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from .generation import generate_token_ids, text_to_token_ids, token_ids_to_text


INSTRUCTION_DATA_URL = (
    "https://raw.githubusercontent.com/rasbt/LLMs-from-scratch/"
    "main/ch07/01_main-chapter-code/instruction-data.json"
)
DEFAULT_EOS_TOKEN_ID = 50256
DEFAULT_IGNORE_INDEX = -100

__all__ = [
    "INSTRUCTION_DATA_URL",
    "DEFAULT_EOS_TOKEN_ID",
    "DEFAULT_IGNORE_INDEX",
    "InstructionDataset",
    "download_and_load_json",
    "format_instruction_prompt",
    "format_instruction_example",
    "split_instruction_data",
    "collate_instruction_batch",
    "create_instruction_dataloaders",
    "generate_instruction_responses",
    "save_instruction_responses",
]


def download_and_load_json(
    file_path: str | Path,
    url: str = INSTRUCTION_DATA_URL,
    *,
    timeout: float = 60.0,
) -> list[dict[str, Any]]:
    """按需下载 JSON 指令数据并读取为字典列表。"""
    path = Path(file_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = response.read()
        temporary_path = path.with_suffix(path.suffix + ".part")
        temporary_path.write_bytes(payload)
        temporary_path.replace(path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list) or not all(isinstance(entry, dict) for entry in data):
        raise ValueError("指令数据必须是 JSON 对象列表")
    return data


def format_instruction_prompt(entry: Mapping[str, Any]) -> str:
    """把一条记录格式化为不含参考回答的 Alpaca 风格提示词。"""
    instruction = str(entry["instruction"])
    input_value = entry.get("input", "")
    instruction_text = (
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request."
        f"\n\n### Instruction:\n{instruction}"
    )
    input_text = f"\n\n### Input:\n{input_value}" if input_value else ""
    return instruction_text + input_text


def format_instruction_example(entry: Mapping[str, Any]) -> str:
    """格式化完整的“提示词 + 参考回答”训练文本。"""
    response = str(entry["output"])
    return format_instruction_prompt(entry) + f"\n\n### Response:\n{response}"


def split_instruction_data(
    data: Sequence[Mapping[str, Any]],
    *,
    train_fraction: float = 0.85,
    test_fraction: float = 0.10,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """按书中顺序切分数据，返回 train、validation、test。"""
    if train_fraction <= 0 or test_fraction < 0:
        raise ValueError("train_fraction 必须为正，test_fraction 不能为负")
    if train_fraction + test_fraction >= 1:
        raise ValueError("训练集与测试集比例之和必须小于 1")

    train_end = int(len(data) * train_fraction)
    test_end = train_end + int(len(data) * test_fraction)
    train_data = [dict(entry) for entry in data[:train_end]]
    test_data = [dict(entry) for entry in data[train_end:test_end]]
    validation_data = [dict(entry) for entry in data[test_end:]]
    return train_data, validation_data, test_data


class InstructionDataset(Dataset[list[int]]):
    """在初始化阶段格式化并编码全部指令记录。"""

    def __init__(self, data: Sequence[Mapping[str, Any]], tokenizer: Any) -> None:
        self.data = [dict(entry) for entry in data]
        self.encoded_texts = [
            tokenizer.encode(format_instruction_example(entry))
            for entry in self.data
        ]

    def __getitem__(self, index: int) -> list[int]:
        return self.encoded_texts[index]

    def __len__(self) -> int:
        return len(self.encoded_texts)


def collate_instruction_batch(
    batch: Sequence[Sequence[int]],
    pad_token_id: int = DEFAULT_EOS_TOKEN_ID,
    ignore_index: int = DEFAULT_IGNORE_INDEX,
    allowed_max_length: int | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """动态填充指令批次，并构造错开一位的语言模型目标。

    collate 始终返回 CPU 张量。超长样本先截断输入 token，再把最后一个
    目标设为 EOS，因此截断后仍保留明确的结束监督。
    """
    if not batch:
        raise ValueError("batch 不能为空")
    if allowed_max_length is not None and allowed_max_length <= 0:
        raise ValueError("allowed_max_length 必须为正整数或 None")

    trimmed_batch: list[list[int]] = []
    for item in batch:
        token_ids = list(item)
        if allowed_max_length is not None:
            token_ids = token_ids[:allowed_max_length]
        if not token_ids:
            raise ValueError("指令样本编码后不能为空")
        trimmed_batch.append(token_ids)

    batch_max_length = max(len(item) for item in trimmed_batch)
    input_tensors: list[torch.Tensor] = []
    target_tensors: list[torch.Tensor] = []

    for token_ids in trimmed_batch:
        padding_length = batch_max_length - len(token_ids)
        inputs = token_ids + [pad_token_id] * padding_length
        targets = (
            token_ids[1:]
            + [pad_token_id]
            + [ignore_index] * padding_length
        )
        input_tensors.append(torch.tensor(inputs, dtype=torch.long))
        target_tensors.append(torch.tensor(targets, dtype=torch.long))

    return torch.stack(input_tensors), torch.stack(target_tensors)


def create_instruction_dataloaders(
    train_data: Sequence[Mapping[str, Any]],
    validation_data: Sequence[Mapping[str, Any]],
    test_data: Sequence[Mapping[str, Any]],
    tokenizer: Any,
    *,
    batch_size: int = 8,
    allowed_max_length: int = 1024,
    num_workers: int = 0,
    seed: int = 123,
) -> tuple[DataLoader[Any], DataLoader[Any], DataLoader[Any]]:
    """创建训练、验证和测试指令 DataLoader。"""
    if batch_size <= 0:
        raise ValueError("batch_size 必须为正整数")
    collate_function = partial(
        collate_instruction_batch,
        allowed_max_length=allowed_max_length,
    )
    generator = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(
        InstructionDataset(train_data, tokenizer),
        batch_size=batch_size,
        collate_fn=collate_function,
        shuffle=True,
        drop_last=True,
        num_workers=num_workers,
        generator=generator,
    )
    validation_loader = DataLoader(
        InstructionDataset(validation_data, tokenizer),
        batch_size=batch_size,
        collate_fn=collate_function,
        shuffle=False,
        drop_last=False,
        num_workers=num_workers,
    )
    test_loader = DataLoader(
        InstructionDataset(test_data, tokenizer),
        batch_size=batch_size,
        collate_fn=collate_function,
        shuffle=False,
        drop_last=False,
        num_workers=num_workers,
    )
    return train_loader, validation_loader, test_loader


def generate_instruction_responses(
    data: Sequence[Mapping[str, Any]],
    model: nn.Module,
    tokenizer: Any,
    device: str | torch.device,
    *,
    context_size: int,
    max_new_tokens: int = 256,
    eos_id: int = DEFAULT_EOS_TOKEN_ID,
    show_progress: bool = True,
) -> list[dict[str, Any]]:
    """逐条生成回答，并按 prompt 的 token 数截取新增部分。"""
    if max_new_tokens <= 0:
        raise ValueError("max_new_tokens 必须为正整数")
    if context_size <= 0:
        raise ValueError("context_size 必须为正整数")

    entries = [dict(entry) for entry in data]
    iterable: Any = enumerate(entries)
    if show_progress:
        from tqdm.auto import tqdm

        iterable = tqdm(iterable, total=len(entries), desc="Generating responses")

    was_training = model.training
    model.eval()
    try:
        for index, entry in iterable:
            prompt = format_instruction_prompt(entry)
            input_ids = text_to_token_ids(prompt, tokenizer).to(device)
            output_ids = generate_token_ids(
                model=model,
                idx=input_ids,
                max_new_tokens=max_new_tokens,
                context_size=context_size,
                temperature=0.0,
                eos_id=eos_id,
            )

            response_ids = output_ids[:, input_ids.shape[1]:]
            eos_positions = torch.nonzero(response_ids[0] == eos_id, as_tuple=True)[0]
            if eos_positions.numel():
                response_ids = response_ids[:, : int(eos_positions[0].item())]
            response_text = token_ids_to_text(
                response_ids,
                tokenizer,
            ).strip()
            response_header = "### Response:"
            if response_text.startswith(response_header):
                response_text = response_text[len(response_header):].strip()
            entry["model_response"] = response_text
            entries[index] = entry
    finally:
        model.train(was_training)
    return entries


def save_instruction_responses(
    data: Sequence[Mapping[str, Any]],
    output_path: str | Path,
) -> Path:
    """把带 ``model_response`` 的测试数据保存为 UTF-8 JSON。"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(list(data), file, indent=4, ensure_ascii=False)
    return path
