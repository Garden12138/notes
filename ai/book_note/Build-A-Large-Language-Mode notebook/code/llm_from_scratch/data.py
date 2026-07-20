"""Text-window datasets and data loaders used for GPT pretraining."""

from __future__ import annotations

from collections.abc import Collection
from typing import Any

import tiktoken
import torch
from torch.utils.data import DataLoader, Dataset


DEFAULT_ALLOWED_SPECIAL = frozenset({"<|endoftext|>"})


class GPTDataset(Dataset):
    """Create next-token prediction samples with a sliding text window."""

    def __init__(
        self,
        text: str,
        tokenizer: Any,
        max_length: int,
        stride: int,
        *,
        allowed_special: Collection[str] | str = DEFAULT_ALLOWED_SPECIAL,
    ) -> None:
        if max_length <= 0:
            raise ValueError(f"max_length must be greater than 0, got {max_length}")
        if stride <= 0:
            raise ValueError(f"stride must be greater than 0, got {stride}")

        self.input_ids: list[torch.Tensor] = []
        self.target_ids: list[torch.Tensor] = []

        token_ids = tokenizer.encode(text, allowed_special=allowed_special)
        for start in range(0, len(token_ids) - max_length, stride):
            input_chunk = token_ids[start : start + max_length]
            target_chunk = token_ids[start + 1 : start + max_length + 1]
            self.input_ids.append(torch.tensor(input_chunk, dtype=torch.long))
            self.target_ids.append(torch.tensor(target_chunk, dtype=torch.long))

    def __len__(self) -> int:
        return len(self.input_ids)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.input_ids[index], self.target_ids[index]


def create_text_dataloader(
    text: str,
    batch_size: int = 4,
    max_length: int = 256,
    stride: int = 128,
    shuffle: bool = True,
    drop_last: bool = True,
    num_workers: int = 0,
    *,
    tokenizer: Any | None = None,
    encoding_name: str = "gpt2",
    allowed_special: Collection[str] | str = DEFAULT_ALLOWED_SPECIAL,
) -> DataLoader:
    """Create a loader of input and target token-ID batches."""
    if batch_size <= 0:
        raise ValueError(f"batch_size must be greater than 0, got {batch_size}")
    if num_workers < 0:
        raise ValueError(f"num_workers must be non-negative, got {num_workers}")

    if tokenizer is None:
        tokenizer = tiktoken.get_encoding(encoding_name)

    dataset = GPTDataset(
        text=text,
        tokenizer=tokenizer,
        max_length=max_length,
        stride=stride,
        allowed_special=allowed_special,
    )
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=drop_last,
        num_workers=num_workers,
    )


# Compatibility names retained for the original book API and chapters 5-7.
GPTDatasetV1 = GPTDataset
create_dataloader_v1 = create_text_dataloader


__all__ = [
    "DEFAULT_ALLOWED_SPECIAL",
    "GPTDataset",
    "GPTDatasetV1",
    "create_text_dataloader",
    "create_dataloader_v1",
]
