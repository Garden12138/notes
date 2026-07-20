"""GPT model configuration shared by the later chapter implementations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any


@dataclass(frozen=True, slots=True)
class GPTConfig:
    """Configuration for the GPT model built throughout the notes."""

    vocab_size: int = 50_257
    context_length: int = 1_024
    emb_dim: int = 768
    n_heads: int = 12
    n_layers: int = 12
    drop_rate: float = 0.1
    qkv_bias: bool = False

    def __post_init__(self) -> None:
        positive_fields = {
            "vocab_size": self.vocab_size,
            "context_length": self.context_length,
            "emb_dim": self.emb_dim,
            "n_heads": self.n_heads,
            "n_layers": self.n_layers,
        }
        for name, value in positive_fields.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than 0, got {value}")

        if self.emb_dim % self.n_heads != 0:
            raise ValueError(
                "emb_dim must be divisible by n_heads, "
                f"got emb_dim={self.emb_dim}, n_heads={self.n_heads}"
            )

        if not 0.0 <= self.drop_rate < 1.0:
            raise ValueError(
                f"drop_rate must be in the interval [0, 1), got {self.drop_rate}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary for logging or serialization."""
        return asdict(self)

    def with_updates(self, **changes: Any) -> "GPTConfig":
        """Create a validated copy with selected fields replaced."""
        return replace(self, **changes)


GPT_CONFIG_124M = GPTConfig()


# These names match chapters 5-7. Only dimensions that differ between model
# sizes live here; create_gpt2_config applies the common checkpoint settings.
GPT2_MODEL_CONFIGS: dict[str, dict[str, int]] = {
    "gpt2-small (124M)": {
        "emb_dim": 768,
        "n_layers": 12,
        "n_heads": 12,
    },
    "gpt2-medium (355M)": {
        "emb_dim": 1_024,
        "n_layers": 24,
        "n_heads": 16,
    },
    "gpt2-large (774M)": {
        "emb_dim": 1_280,
        "n_layers": 36,
        "n_heads": 20,
    },
    "gpt2-xl (1558M)": {
        "emb_dim": 1_600,
        "n_layers": 48,
        "n_heads": 25,
    },
}


def create_gpt2_config(
    model_name: str,
    *,
    drop_rate: float = 0.0,
    qkv_bias: bool = True,
) -> GPTConfig:
    """Build a configuration compatible with an official GPT-2 checkpoint.

    Official GPT-2 attention projections contain bias parameters, so
    qkv_bias defaults to True here. The from-scratch configuration above
    intentionally retains the book's False default.
    """
    try:
        model_dimensions = GPT2_MODEL_CONFIGS[model_name]
    except KeyError as exc:
        supported = ", ".join(GPT2_MODEL_CONFIGS)
        raise ValueError(
            f"Unknown GPT-2 model {model_name!r}. Supported models: {supported}"
        ) from exc

    return GPTConfig(
        vocab_size=50_257,
        context_length=1_024,
        emb_dim=model_dimensions["emb_dim"],
        n_heads=model_dimensions["n_heads"],
        n_layers=model_dimensions["n_layers"],
        drop_rate=drop_rate,
        qkv_bias=qkv_bias,
    )


__all__ = [
    "GPTConfig",
    "GPT_CONFIG_124M",
    "GPT2_MODEL_CONFIGS",
    "create_gpt2_config",
]
