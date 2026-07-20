"""Chapter 4 examples: GPT components, residual paths, and generation."""

from __future__ import annotations

import argparse
from pathlib import Path

import tiktoken
import torch
from torch import nn

from llm_from_scratch.config import GPTConfig
from llm_from_scratch.generation import (
    generate_text_simple,
    text_to_token_ids,
    token_ids_to_text,
)
from llm_from_scratch.model import GELU, GPTModel


class DummyTransformerBlock(nn.Module):
    """Identity placeholder used while introducing the GPT architecture."""

    def __init__(self, cfg: GPTConfig) -> None:
        super().__init__()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x


class DummyLayerNorm(nn.Module):
    """Identity placeholder replaced by the real LayerNorm later in chapter 4."""

    def __init__(self, emb_dim: int) -> None:
        super().__init__()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x


class DummyGPTModel(nn.Module):
    """Early GPT skeleton whose Transformer and normalization are identities."""

    def __init__(self, cfg: GPTConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.emb_dim)
        self.pos_emb = nn.Embedding(cfg.context_length, cfg.emb_dim)
        self.drop_emb = nn.Dropout(cfg.drop_rate)
        self.trf_blocks = nn.Sequential(
            *[DummyTransformerBlock(cfg) for _ in range(cfg.n_layers)]
        )
        self.final_norm = DummyLayerNorm(cfg.emb_dim)
        self.out_head = nn.Linear(cfg.emb_dim, cfg.vocab_size, bias=False)

    def forward(self, in_idx: torch.Tensor) -> torch.Tensor:
        _, seq_len = in_idx.shape
        if seq_len > self.cfg.context_length:
            raise ValueError("Input exceeds the configured context length")
        token_embeddings = self.tok_emb(in_idx)
        position_embeddings = self.pos_emb(
            torch.arange(seq_len, device=in_idx.device)
        )
        x = self.drop_emb(token_embeddings + position_embeddings)
        x = self.trf_blocks(x)
        x = self.final_norm(x)
        return self.out_head(x)


class ExampleDeepNeuralNetwork(nn.Module):
    """Five-layer teaching network with optional residual connections."""

    def __init__(self, layer_sizes: list[int], use_shortcut: bool) -> None:
        super().__init__()
        if len(layer_sizes) != 6:
            raise ValueError("layer_sizes must contain six dimensions")
        self.use_shortcut = use_shortcut
        self.layers = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Linear(input_size, output_size),
                    GELU(),
                )
                for input_size, output_size in zip(
                    layer_sizes[:-1],
                    layer_sizes[1:],
                )
            ]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for layer in self.layers:
            layer_output = layer(x)
            if self.use_shortcut and x.shape == layer_output.shape:
                x = x + layer_output
            else:
                x = layer_output
        return x


def gradient_means(
    model: nn.Module,
    sample_input: torch.Tensor,
) -> dict[str, float]:
    """Backpropagate once and return mean absolute weight gradients."""
    model.zero_grad(set_to_none=True)
    output = model(sample_input)
    loss = nn.functional.mse_loss(output, torch.zeros_like(output))
    loss.backward()
    return {
        name: parameter.grad.abs().mean().item()
        for name, parameter in model.named_parameters()
        if "weight" in name and parameter.grad is not None
    }


def plot_activation_functions(output_path: str | Path) -> Path:
    """Save the GELU/ReLU comparison from chapter 4."""
    import matplotlib.pyplot as plt

    x = torch.linspace(-3, 3, 100)
    curves = [(GELU()(x), "GELU"), (nn.ReLU()(x), "ReLU")]
    figure, axes = plt.subplots(1, 2, figsize=(8, 3))
    for axis, (y, label) in zip(axes, curves):
        axis.plot(x.numpy(), y.detach().numpy())
        axis.set_title(f"{label} activation function")
        axis.set_xlabel("x")
        axis.set_ylabel(f"{label}(x)")
        axis.grid(True)
    figure.tight_layout()

    destination = Path(output_path)
    figure.savefig(destination, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return destination


def demo_residual_gradients() -> None:
    layer_sizes = [3, 3, 3, 3, 3, 1]
    sample_input = torch.tensor([[1.0, 0.0, -1.0]])
    for use_shortcut in (False, True):
        torch.manual_seed(123)
        model = ExampleDeepNeuralNetwork(layer_sizes, use_shortcut)
        label = "with shortcuts" if use_shortcut else "without shortcuts"
        print(f"\nGradient means {label}:")
        for name, value in gradient_means(model, sample_input).items():
            print(f"{name}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default="Hello, I am")
    parser.add_argument("--max-new-tokens", type=int, default=10)
    parser.add_argument(
        "--plot",
        type=Path,
        default=None,
        help="Optional path for the activation-function plot",
    )
    args = parser.parse_args()

    torch.manual_seed(123)
    # A compact configuration keeps this educational example quick to run
    # while preserving the exact GPTModel data flow.
    cfg = GPTConfig(
        vocab_size=50_257,
        context_length=64,
        emb_dim=64,
        n_heads=4,
        n_layers=2,
        drop_rate=0.1,
    )
    model = GPTModel(cfg)
    tokenizer = tiktoken.get_encoding("gpt2")
    input_ids = text_to_token_ids(args.prompt, tokenizer)
    output_ids = generate_text_simple(
        model=model,
        idx=input_ids,
        max_new_tokens=args.max_new_tokens,
        context_size=cfg.context_length,
    )

    print("Model parameters:", f"{sum(p.numel() for p in model.parameters()):,}")
    print("Generated text:", token_ids_to_text(output_ids, tokenizer))
    demo_residual_gradients()

    if args.plot is not None:
        print("Saved plot:", plot_activation_functions(args.plot))


if __name__ == "__main__":
    main()
