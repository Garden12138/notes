"""Token conversion and autoregressive text-generation helpers."""

from __future__ import annotations

import math
from collections.abc import Collection
from typing import Any

import torch
from torch import nn


DEFAULT_ALLOWED_SPECIAL = frozenset({"<|endoftext|>"})


def text_to_token_ids(
    text: str,
    tokenizer: Any,
    *,
    device: str | torch.device | None = None,
    allowed_special: Collection[str] | str = DEFAULT_ALLOWED_SPECIAL,
) -> torch.Tensor:
    """Encode one string as a tensor shaped [1, num_tokens]."""
    token_ids = tokenizer.encode(text, allowed_special=allowed_special)
    return torch.tensor(token_ids, dtype=torch.long, device=device).unsqueeze(0)


def token_ids_to_text(token_ids: torch.Tensor, tokenizer: Any) -> str:
    """Decode a one-dimensional or single-item batch of token IDs."""
    if token_ids.ndim == 2:
        if token_ids.size(0) != 1:
            raise ValueError(
                "token_ids_to_text accepts one sequence at a time; "
                f"got batch_size={token_ids.size(0)}"
            )
        token_ids = token_ids.squeeze(0)
    elif token_ids.ndim != 1:
        raise ValueError(
            "token_ids must have shape [num_tokens] or [1, num_tokens], "
            f"got {tuple(token_ids.shape)}"
        )

    return tokenizer.decode(token_ids.detach().cpu().tolist())


def _validate_generation_arguments(
    idx: torch.Tensor,
    max_new_tokens: int,
    context_size: int,
    temperature: float,
    top_k: int | None,
    eos_id: int | None,
) -> None:
    if idx.ndim != 2:
        raise ValueError(
            "idx must have shape [batch_size, num_tokens], "
            f"got {tuple(idx.shape)}"
        )
    if idx.size(0) == 0 or idx.size(1) == 0:
        raise ValueError("idx must contain at least one sequence and one token")
    if max_new_tokens < 0:
        raise ValueError(
            f"max_new_tokens must be non-negative, got {max_new_tokens}"
        )
    if context_size <= 0:
        raise ValueError(f"context_size must be greater than 0, got {context_size}")
    if temperature < 0.0 or not math.isfinite(temperature):
        raise ValueError(
            f"temperature must be finite and non-negative, got {temperature}"
        )
    if top_k is not None and top_k <= 0:
        raise ValueError(f"top_k must be greater than 0, got {top_k}")
    if eos_id is not None and eos_id < 0:
        raise ValueError(f"eos_id must be non-negative, got {eos_id}")


def generate_token_ids(
    model: nn.Module,
    idx: torch.Tensor,
    max_new_tokens: int,
    context_size: int,
    temperature: float = 0.0,
    top_k: int | None = None,
    eos_id: int | None = None,
) -> torch.Tensor:
    """Generate IDs with greedy decoding or temperature sampling.

    For batched generation, rows that reach eos_id are held at EOS while
    unfinished rows continue. Generation stops once every row is finished.
    The model's original training/evaluation mode is always restored.
    """
    _validate_generation_arguments(
        idx=idx,
        max_new_tokens=max_new_tokens,
        context_size=context_size,
        temperature=temperature,
        top_k=top_k,
        eos_id=eos_id,
    )

    was_training = model.training
    model.eval()
    finished = torch.zeros(idx.size(0), dtype=torch.bool, device=idx.device)

    try:
        with torch.no_grad():
            for _ in range(max_new_tokens):
                idx_cond = idx[:, -context_size:]
                logits = model(idx_cond)
                if logits.ndim != 3 or logits.size(0) != idx.size(0):
                    raise ValueError(
                        "model must return logits shaped "
                        "[batch_size, num_tokens, vocab_size]"
                    )
                logits = logits[:, -1, :]
                vocab_size = logits.size(-1)

                if top_k is not None:
                    if top_k > vocab_size:
                        raise ValueError(
                            f"top_k={top_k} exceeds vocabulary size {vocab_size}"
                        )
                    top_values = torch.topk(logits, top_k).values
                    cutoff = top_values[:, -1].unsqueeze(-1)
                    logits = logits.masked_fill(logits < cutoff, -torch.inf)

                if eos_id is not None and eos_id >= vocab_size:
                    raise ValueError(
                        f"eos_id={eos_id} is outside vocabulary size {vocab_size}"
                    )

                if temperature > 0.0:
                    probabilities = torch.softmax(logits / temperature, dim=-1)
                    idx_next = torch.multinomial(probabilities, num_samples=1)
                else:
                    idx_next = torch.argmax(logits, dim=-1, keepdim=True)

                if eos_id is not None:
                    eos_tokens = torch.full_like(idx_next, eos_id)
                    idx_next = torch.where(
                        finished.unsqueeze(-1),
                        eos_tokens,
                        idx_next,
                    )
                    finished = finished | idx_next.squeeze(-1).eq(eos_id)

                idx = torch.cat((idx, idx_next), dim=1)

                if eos_id is not None and finished.all():
                    break
    finally:
        model.train(was_training)

    return idx


def generate_text_simple(
    model: nn.Module,
    idx: torch.Tensor,
    max_new_tokens: int,
    context_size: int,
) -> torch.Tensor:
    """Compatibility wrapper for the book's greedy generation function."""
    return generate_token_ids(
        model=model,
        idx=idx,
        max_new_tokens=max_new_tokens,
        context_size=context_size,
        temperature=0.0,
    )


__all__ = [
    "DEFAULT_ALLOWED_SPECIAL",
    "text_to_token_ids",
    "token_ids_to_text",
    "generate_token_ids",
    "generate_text_simple",
]
