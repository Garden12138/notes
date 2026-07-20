"""Causal multi-head self-attention used by the GPT model."""

from __future__ import annotations

import torch
from torch import nn


class MultiHeadAttention(nn.Module):
    """Efficient causal self-attention with parallel attention heads."""

    def __init__(
        self,
        d_in: int,
        d_out: int,
        context_length: int,
        dropout: float,
        num_heads: int,
        qkv_bias: bool = False,
    ) -> None:
        super().__init__()

        for name, value in {
            "d_in": d_in,
            "d_out": d_out,
            "context_length": context_length,
            "num_heads": num_heads,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than 0, got {value}")
        if d_out % num_heads != 0:
            raise ValueError(
                "d_out must be divisible by num_heads, "
                f"got d_out={d_out}, num_heads={num_heads}"
            )
        if not 0.0 <= dropout < 1.0:
            raise ValueError(f"dropout must be in the interval [0, 1), got {dropout}")

        self.d_in = d_in
        self.d_out = d_out
        self.num_heads = num_heads
        self.head_dim = d_out // num_heads

        # These names intentionally match the chapter 5 checkpoint mapping.
        self.W_query = nn.Linear(d_in, d_out, bias=qkv_bias)
        self.W_key = nn.Linear(d_in, d_out, bias=qkv_bias)
        self.W_value = nn.Linear(d_in, d_out, bias=qkv_bias)
        self.out_proj = nn.Linear(d_out, d_out)
        self.dropout = nn.Dropout(dropout)

        self.register_buffer(
            "mask",
            torch.triu(
                torch.ones(context_length, context_length, dtype=torch.bool),
                diagonal=1,
            ),
        )

    @property
    def context_length(self) -> int:
        return self.mask.size(0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 3:
            raise ValueError(
                "x must have shape [batch_size, num_tokens, d_in], "
                f"got {tuple(x.shape)}"
            )

        batch_size, num_tokens, input_dim = x.shape
        if input_dim != self.d_in:
            raise ValueError(f"Expected input dimension {self.d_in}, got {input_dim}")
        if num_tokens > self.context_length:
            raise ValueError(
                f"Input has {num_tokens} tokens, but context_length is "
                f"{self.context_length}"
            )

        keys = self.W_key(x)
        queries = self.W_query(x)
        values = self.W_value(x)

        keys = keys.view(batch_size, num_tokens, self.num_heads, self.head_dim)
        queries = queries.view(batch_size, num_tokens, self.num_heads, self.head_dim)
        values = values.view(batch_size, num_tokens, self.num_heads, self.head_dim)

        keys = keys.transpose(1, 2)
        queries = queries.transpose(1, 2)
        values = values.transpose(1, 2)

        attention_scores = queries @ keys.transpose(2, 3)
        causal_mask = self.mask[:num_tokens, :num_tokens]
        attention_scores.masked_fill_(causal_mask, -torch.inf)

        attention_weights = torch.softmax(
            attention_scores / (self.head_dim**0.5),
            dim=-1,
        )
        attention_weights = self.dropout(attention_weights)

        context = (attention_weights @ values).transpose(1, 2).contiguous()
        context = context.view(batch_size, num_tokens, self.d_out)
        return self.out_proj(context)


__all__ = ["MultiHeadAttention"]
