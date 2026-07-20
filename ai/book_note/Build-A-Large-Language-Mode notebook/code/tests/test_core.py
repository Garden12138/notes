"""Focused tests for the shared chapter 2-4 implementation."""

from __future__ import annotations

import pytest
import torch
from torch import nn

from llm_from_scratch.attention import MultiHeadAttention
from llm_from_scratch.config import GPTConfig, create_gpt2_config
from llm_from_scratch.data import (
    GPTDataset,
    GPTDatasetV1,
    create_dataloader_v1,
    create_text_dataloader,
)
from llm_from_scratch.generation import (
    generate_text_simple,
    generate_token_ids,
    text_to_token_ids,
    token_ids_to_text,
)
from llm_from_scratch.model import GPTModel


class IntegerTokenizer:
    def encode(self, text: str, *, allowed_special: object) -> list[int]:
        return [int(piece) for piece in text.split()]

    def decode(self, token_ids: list[int]) -> str:
        return " ".join(str(token_id) for token_id in token_ids)


def tiny_config(**updates: object) -> GPTConfig:
    values = {
        "vocab_size": 32,
        "context_length": 8,
        "emb_dim": 12,
        "n_heads": 3,
        "n_layers": 2,
        "drop_rate": 0.0,
        "qkv_bias": False,
    }
    values.update(updates)
    return GPTConfig(**values)


def test_gpt2_config_factory_uses_checkpoint_compatible_bias() -> None:
    config = create_gpt2_config("gpt2-medium (355M)")
    assert config.emb_dim == 1_024
    assert config.n_layers == 24
    assert config.n_heads == 16
    assert config.drop_rate == 0.0
    assert config.qkv_bias is True


def test_config_rejects_incompatible_head_dimension() -> None:
    with pytest.raises(ValueError, match="divisible"):
        tiny_config(emb_dim=10)


def test_dataset_builds_shifted_sliding_windows_and_aliases() -> None:
    tokenizer = IntegerTokenizer()
    dataset = GPTDataset(
        "0 1 2 3 4 5 6 7",
        tokenizer,
        max_length=3,
        stride=2,
    )
    assert len(dataset) == 3
    input_ids, target_ids = dataset[0]
    assert input_ids.tolist() == [0, 1, 2]
    assert target_ids.tolist() == [1, 2, 3]
    assert GPTDatasetV1 is GPTDataset
    assert create_dataloader_v1 is create_text_dataloader


def test_data_loader_honors_num_workers_and_shapes() -> None:
    loader = create_text_dataloader(
        "0 1 2 3 4 5 6 7",
        batch_size=2,
        max_length=3,
        stride=1,
        shuffle=False,
        drop_last=False,
        num_workers=0,
        tokenizer=IntegerTokenizer(),
    )
    inputs, targets = next(iter(loader))
    assert inputs.shape == targets.shape == (2, 3)
    assert loader.num_workers == 0


def test_attention_is_causal_and_preserves_shape() -> None:
    torch.manual_seed(123)
    attention = MultiHeadAttention(
        d_in=6,
        d_out=6,
        context_length=4,
        dropout=0.0,
        num_heads=2,
    )
    attention.eval()
    inputs = torch.randn(1, 4, 6)
    changed_future = inputs.clone()
    changed_future[:, 2:] += 100.0

    original = attention(inputs)
    changed = attention(changed_future)
    assert original.shape == (1, 4, 6)
    torch.testing.assert_close(original[:, :2], changed[:, :2])


def test_model_shape_and_checkpoint_attribute_paths() -> None:
    model = GPTModel(tiny_config())
    logits = model(torch.randint(0, 32, (2, 5)))
    assert logits.shape == (2, 5, 32)

    block = model.trf_blocks[0]
    assert block.att.W_query is not None
    assert block.att.W_key is not None
    assert block.att.W_value is not None
    assert block.ff.layers[0] is not None
    assert block.norm1.scale is not None
    assert block.norm2.shift is not None
    assert model.tok_emb is not None
    assert model.pos_emb is not None
    assert model.out_head is not None


class BatchedEOSModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        self.calls += 1
        logits = torch.zeros(idx.size(0), idx.size(1), 4)
        if self.calls == 1:
            logits[0, -1, 3] = 10.0
            logits[1, -1, 1] = 10.0
        else:
            logits[0, -1, 2] = 10.0
            logits[1, -1, 3] = 10.0
        return logits


def test_batched_eos_and_model_mode_restoration() -> None:
    model = BatchedEOSModel()
    model.train()
    output = generate_token_ids(
        model,
        idx=torch.tensor([[0], [0]]),
        max_new_tokens=5,
        context_size=4,
        eos_id=3,
    )
    assert output.tolist() == [[0, 3, 3], [0, 1, 3]]
    assert model.training is True


def test_generation_validation_restores_mode_after_runtime_error() -> None:
    model = BatchedEOSModel()
    model.train()
    with pytest.raises(ValueError, match="exceeds vocabulary"):
        generate_token_ids(
            model,
            idx=torch.tensor([[0], [0]]),
            max_new_tokens=1,
            context_size=4,
            top_k=5,
        )
    assert model.training is True


def test_simple_generation_and_token_conversion() -> None:
    tokenizer = IntegerTokenizer()
    input_ids = text_to_token_ids("0 1", tokenizer)
    assert token_ids_to_text(input_ids, tokenizer) == "0 1"

    model = BatchedEOSModel()
    generated = generate_text_simple(
        model,
        idx=torch.tensor([[0], [0]]),
        max_new_tokens=1,
        context_size=4,
    )
    assert generated.shape == (2, 2)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_new_tokens": -1}, "max_new_tokens"),
        ({"context_size": 0}, "context_size"),
        ({"temperature": -0.1}, "temperature"),
        ({"top_k": 0}, "top_k"),
        ({"eos_id": -1}, "eos_id"),
    ],
)
def test_generation_rejects_invalid_arguments(
    kwargs: dict[str, object],
    message: str,
) -> None:
    parameters = {
        "model": BatchedEOSModel(),
        "idx": torch.tensor([[0], [0]]),
        "max_new_tokens": 1,
        "context_size": 4,
    }
    parameters.update(kwargs)
    with pytest.raises(ValueError, match=message):
        generate_token_ids(**parameters)
