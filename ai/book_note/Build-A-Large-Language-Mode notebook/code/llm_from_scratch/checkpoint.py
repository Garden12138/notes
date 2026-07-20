"""模型权重与训练检查点的保存、加载工具。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from torch import nn

__all__ = [
    "save_model_weights",
    "load_model_weights",
    "save_training_checkpoint",
    "load_training_checkpoint",
]


def save_model_weights(model: nn.Module, path: str | Path) -> Path:
    """只保存模型参数，适用于推理部署。"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_path)
    return output_path


def load_model_weights(
    model: nn.Module,
    path: str | Path,
    device: str | torch.device = "cpu",
) -> nn.Module:
    """将参数加载到已经按相同配置创建的模型中。"""
    state_dict = torch.load(
        Path(path),
        map_location=device,
        weights_only=True,
    )
    model.load_state_dict(state_dict)
    model.to(device)
    return model


def save_training_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    path: str | Path,
    **metadata: Any,
) -> Path:
    """保存可继续训练的模型、优化器状态及可选进度信息。"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "metadata": metadata,
        },
        output_path,
    )
    return output_path


def load_training_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    path: str | Path,
    device: str | torch.device = "cpu",
) -> dict[str, Any]:
    """恢复模型和优化器，并返回保存时附带的进度信息。"""
    model.to(device)
    checkpoint = torch.load(
        Path(path),
        map_location=device,
        weights_only=True,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint.get("metadata", {})
