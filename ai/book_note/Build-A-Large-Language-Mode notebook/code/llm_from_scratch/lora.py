"""用于分类或指令微调的低秩适配（LoRA）组件。"""

from __future__ import annotations

import math
from numbers import Real

import torch
from torch import nn


__all__ = [
    "LoRALayer",
    "LinearWithLoRA",
    "replace_linear_with_lora",
    "apply_lora",
    "count_trainable_parameters",
]


def _validate_lora_hyperparameters(rank: int, alpha: float) -> None:
    if isinstance(rank, bool) or not isinstance(rank, int) or rank <= 0:
        raise ValueError("rank 必须是正整数")
    if (
        isinstance(alpha, bool)
        or not isinstance(alpha, Real)
        or not math.isfinite(alpha)
        or alpha <= 0
    ):
        raise ValueError("alpha 必须是有限的正数")


class LoRALayer(nn.Module):
    """计算缩放后的低秩增量 ``(alpha / rank) * x @ A @ B``。"""

    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        rank: int,
        alpha: float,
    ) -> None:
        super().__init__()
        if in_dim <= 0 or out_dim <= 0:
            raise ValueError("in_dim 和 out_dim 必须为正整数")
        _validate_lora_hyperparameters(rank, alpha)

        self.A = nn.Parameter(torch.empty(in_dim, rank))
        self.B = nn.Parameter(torch.zeros(rank, out_dim))
        nn.init.kaiming_uniform_(self.A, a=math.sqrt(5))

        self.rank = rank
        self.alpha = float(alpha)
        self.scaling = self.alpha / self.rank

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.scaling * (x @ self.A @ self.B)


class LinearWithLoRA(nn.Module):
    """保留原始线性层，并把 LoRA 低秩增量加到其输出。"""

    def __init__(
        self,
        linear: nn.Linear,
        rank: int,
        alpha: float,
    ) -> None:
        super().__init__()
        if not isinstance(linear, nn.Linear):
            raise TypeError("linear 必须是 torch.nn.Linear")

        self.linear = linear
        self.lora = LoRALayer(
            linear.in_features,
            linear.out_features,
            rank,
            alpha,
        ).to(
            device=linear.weight.device,
            dtype=linear.weight.dtype,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x) + self.lora(x)


def replace_linear_with_lora(
    model: nn.Module,
    rank: int,
    alpha: float,
) -> int:
    """递归替换 ``nn.Linear``，返回本次替换的层数。

    已经包装过的 ``LinearWithLoRA`` 会被跳过，避免重复包装
    其中的原始线性层。
    """
    _validate_lora_hyperparameters(rank, alpha)
    replacements = 0

    for name, child in list(model.named_children()):
        if isinstance(child, LinearWithLoRA):
            continue
        if isinstance(child, nn.Linear):
            setattr(model, name, LinearWithLoRA(child, rank, alpha))
            replacements += 1
        else:
            replacements += replace_linear_with_lora(child, rank, alpha)

    return replacements


def apply_lora(
    model: nn.Module,
    rank: int = 16,
    alpha: float = 16.0,
) -> int:
    """冻结原模型并为全部线性层添加 LoRA。

    返回被替换的线性层数。
    """
    _validate_lora_hyperparameters(rank, alpha)
    if any(isinstance(module, LinearWithLoRA) for module in model.modules()):
        raise ValueError("模型已经包含 LinearWithLoRA，不能重复应用 LoRA")
    if not any(isinstance(module, nn.Linear) for module in model.modules()):
        raise ValueError("模型中没有可替换的 nn.Linear")

    for parameter in model.parameters():
        parameter.requires_grad = False

    return replace_linear_with_lora(model, rank, alpha)


def count_trainable_parameters(model: nn.Module) -> int:
    """统计当前 ``requires_grad=True`` 的参数数量。"""
    return sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )
