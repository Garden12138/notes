"""GPT model components assembled in chapter 4."""

from __future__ import annotations

import math

import torch
from torch import nn

from .attention import MultiHeadAttention
from .config import GPTConfig


class LayerNorm(nn.Module):
    """Layer normalization over each token's embedding dimension."""

    def __init__(self, emb_dim: int, eps: float = 1e-5) -> None:
        super().__init__()
        if emb_dim <= 0:
            raise ValueError(f"emb_dim must be greater than 0, got {emb_dim}")
        if eps <= 0:
            raise ValueError(f"eps must be greater than 0, got {eps}")

        self.eps = eps
        self.scale = nn.Parameter(torch.ones(emb_dim))
        self.shift = nn.Parameter(torch.zeros(emb_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        mean = x.mean(dim=-1, keepdim=True)
        variance = x.var(dim=-1, keepdim=True, unbiased=False)
        normalized = (x - mean) / torch.sqrt(variance + self.eps)
        return self.scale * normalized + self.shift


class GELU(nn.Module):
    """The tanh approximation of GELU used by GPT-2."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return 0.5 * x * (
            1.0
            + torch.tanh(
                math.sqrt(2.0 / math.pi)
                * (x + 0.044715 * torch.pow(x, 3))
            )
        )


class FeedForward(nn.Module):
    """Position-wise feed-forward network used in a Transformer block."""

    def __init__(self, cfg: GPTConfig) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(cfg.emb_dim, 4 * cfg.emb_dim),
            GELU(),
            nn.Linear(4 * cfg.emb_dim, cfg.emb_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


class TransformerBlock(nn.Module):
    """Pre-normalized GPT Transformer block with two residual paths."""

    def __init__(self, cfg: GPTConfig) -> None:
        super().__init__()
        self.att = MultiHeadAttention(
            d_in=cfg.emb_dim,
            d_out=cfg.emb_dim,
            context_length=cfg.context_length,
            dropout=cfg.drop_rate,
            num_heads=cfg.n_heads,
            qkv_bias=cfg.qkv_bias,
        )
        self.ff = FeedForward(cfg)
        self.norm1 = LayerNorm(cfg.emb_dim)
        self.norm2 = LayerNorm(cfg.emb_dim)
        self.drop_shortcut = nn.Dropout(cfg.drop_rate)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shortcut = x
        x = self.norm1(x)
        x = self.att(x)
        x = self.drop_shortcut(x)
        x = x + shortcut

        shortcut = x
        x = self.norm2(x)
        x = self.ff(x)
        x = self.drop_shortcut(x)
        return x + shortcut


class GPTModel(nn.Module):
    """Decoder-only GPT language model built from the chapter components."""

    def __init__(self, cfg: GPTConfig) -> None:
        super().__init__()
        if not isinstance(cfg, GPTConfig):
            raise TypeError(
                "cfg must be a GPTConfig instance; convert dictionaries with "
                "GPTConfig(**config_dict)"
            )

        self.cfg = cfg
        self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.emb_dim)
        self.pos_emb = nn.Embedding(cfg.context_length, cfg.emb_dim)
        self.drop_emb = nn.Dropout(cfg.drop_rate)
        self.trf_blocks = nn.Sequential(
            *[TransformerBlock(cfg) for _ in range(cfg.n_layers)]
        )
        self.final_norm = LayerNorm(cfg.emb_dim)
        self.out_head = nn.Linear(cfg.emb_dim, cfg.vocab_size, bias=False)

    def forward(self, in_idx: torch.Tensor) -> torch.Tensor:
        if in_idx.ndim != 2:
            raise ValueError(
                "in_idx must have shape [batch_size, seq_len], "
                f"got {tuple(in_idx.shape)}"
            )

        _, seq_len = in_idx.shape
        if seq_len == 0:
            raise ValueError("in_idx must contain at least one token")
        if seq_len > self.cfg.context_length:
            raise ValueError(
                f"Input length {seq_len} exceeds context_length "
                f"{self.cfg.context_length}"
            )

        token_embeddings = self.tok_emb(in_idx)
        position_ids = torch.arange(seq_len, device=in_idx.device)
        position_embeddings = self.pos_emb(position_ids)

        x = token_embeddings + position_embeddings
        x = self.drop_emb(x)
        x = self.trf_blocks(x)
        x = self.final_norm(x)
        return self.out_head(x)


__all__ = [
    "LayerNorm",
    "GELU",
    "FeedForward",
    "TransformerBlock",
    "GPTModel",
]
