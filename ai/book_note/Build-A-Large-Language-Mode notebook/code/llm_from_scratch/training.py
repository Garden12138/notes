"""因果语言模型的损失、评估、学习率调度、梯度裁剪与训练循环。"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Sequence

import torch
import torch.nn.functional as F
from torch import nn

from .generation import generate_token_ids, text_to_token_ids, token_ids_to_text

__all__ = [
    "causal_lm_batch_loss",
    "causal_lm_loader_loss",
    "evaluate_causal_lm",
    "generate_and_print_sample",
    "linear_warmup_lr",
    "cosine_decay_lr",
    "clip_gradient_norm",
    "train_causal_lm",
    "plot_losses",
]


def _limited_batch_count(data_loader: Any, num_batches: int | None) -> int:
    """返回实际要读取的批次数，并统一处理边界值。"""
    if num_batches is not None and num_batches <= 0:
        raise ValueError("num_batches 必须为正整数或 None")

    available_batches = len(data_loader)
    if available_batches == 0:
        return 0
    if num_batches is None:
        return available_batches
    return min(num_batches, available_batches)


def _causal_lm_loss_sum(
    input_batch: torch.Tensor,
    target_batch: torch.Tensor,
    model: nn.Module,
    device: str | torch.device,
    *,
    ignore_index: int = -100,
) -> tuple[torch.Tensor, int]:
    input_batch = input_batch.to(device)
    target_batch = target_batch.to(device)

    logits = model(input_batch)
    flat_logits = logits.flatten(0, 1)
    flat_targets = target_batch.flatten()
    valid_tokens = int((flat_targets != ignore_index).sum().item())

    if valid_tokens == 0:
        return flat_logits.sum() * 0.0, 0

    loss_sum = F.cross_entropy(
        flat_logits,
        flat_targets,
        ignore_index=ignore_index,
        reduction="sum",
    )
    return loss_sum, valid_tokens


def causal_lm_batch_loss(
    input_batch: torch.Tensor,
    target_batch: torch.Tensor,
    model: nn.Module,
    device: str | torch.device,
    *,
    ignore_index: int = -100,
) -> torch.Tensor:
    """计算一个批次中所有有效目标 token 的平均交叉熵。"""
    loss_sum, valid_tokens = _causal_lm_loss_sum(
        input_batch,
        target_batch,
        model,
        device,
        ignore_index=ignore_index,
    )
    if valid_tokens == 0:
        raise ValueError("target_batch 中没有可参与损失计算的 token")
    return loss_sum / valid_tokens


def causal_lm_loader_loss(
    data_loader: Any,
    model: nn.Module,
    device: str | torch.device,
    num_batches: int | None = None,
    *,
    ignore_index: int = -100,
) -> float:
    """按有效 token 数加权计算 DataLoader 的平均交叉熵。

    空 DataLoader 返回 ``nan``；``num_batches<=0`` 被视为调用错误。
    """
    batch_count = _limited_batch_count(data_loader, num_batches)
    if batch_count == 0:
        return float("nan")

    total_loss = 0.0
    total_tokens = 0
    was_training = model.training
    model.eval()

    try:
        with torch.no_grad():
            for batch_index, (input_batch, target_batch) in enumerate(data_loader):
                if batch_index >= batch_count:
                    break
                loss_sum, valid_tokens = _causal_lm_loss_sum(
                    input_batch,
                    target_batch,
                    model,
                    device,
                    ignore_index=ignore_index,
                )
                total_loss += loss_sum.item()
                total_tokens += valid_tokens
    finally:
        model.train(was_training)

    if total_tokens == 0:
        return float("nan")
    return total_loss / total_tokens


def evaluate_causal_lm(
    model: nn.Module,
    train_loader: Any,
    val_loader: Any,
    device: str | torch.device,
    eval_iter: int,
) -> tuple[float, float]:
    """使用有限批次快速估算训练集与验证集损失。"""
    train_loss = causal_lm_loader_loss(
        train_loader,
        model,
        device,
        num_batches=eval_iter,
    )
    val_loss = causal_lm_loader_loss(
        val_loader,
        model,
        device,
        num_batches=eval_iter,
    )
    return train_loss, val_loss


def generate_and_print_sample(
    model: nn.Module,
    tokenizer: Any,
    device: str | torch.device,
    start_context: str,
    *,
    max_new_tokens: int = 50,
) -> str:
    """生成一段训练观察样本，打印并返回解码文本。"""
    was_training = model.training
    model.eval()
    context_size = model.pos_emb.weight.shape[0]
    input_ids = text_to_token_ids(start_context, tokenizer).to(device)

    try:
        output_ids = generate_token_ids(
            model=model,
            idx=input_ids,
            max_new_tokens=max_new_tokens,
            context_size=context_size,
            temperature=0.0,
        )
        decoded_text = token_ids_to_text(output_ids, tokenizer)
        print(decoded_text.replace("\n", " "))
        return decoded_text
    finally:
        model.train(was_training)


def linear_warmup_lr(
    step: int,
    *,
    warmup_steps: int,
    initial_lr: float,
    peak_lr: float,
) -> float:
    """返回指定更新步的线性预热学习率。

    ``step=0`` 使用 ``initial_lr``；达到 ``warmup_steps`` 后固定使用
    ``peak_lr``。传入 ``warmup_steps=0`` 表示关闭预热。
    """
    if step < 0:
        raise ValueError("step 不能为负数")
    if warmup_steps < 0:
        raise ValueError("warmup_steps 不能为负数")
    if peak_lr < 0:
        raise ValueError("peak_lr 不能为负数")
    if warmup_steps == 0:
        return peak_lr
    if initial_lr < 0:
        raise ValueError("initial_lr 不能为负数")
    if initial_lr > peak_lr:
        raise ValueError("initial_lr 不能大于 peak_lr")

    if step >= warmup_steps:
        return peak_lr

    progress = step / warmup_steps
    return initial_lr + progress * (peak_lr - initial_lr)


def cosine_decay_lr(
    step: int,
    *,
    warmup_steps: int,
    total_training_steps: int,
    peak_lr: float,
    min_lr: float,
) -> float:
    """返回预热结束后指定更新步的余弦衰减学习率。

    ``step=warmup_steps`` 时返回 ``peak_lr``；``step`` 到达
    ``total_training_steps`` 时返回 ``min_lr``。超过终点的 step 会固定在
    ``min_lr``，从而避免学习率继续沿余弦曲线回升。
    """
    if step < 0:
        raise ValueError("step 不能为负数")
    if warmup_steps < 0:
        raise ValueError("warmup_steps 不能为负数")
    if total_training_steps <= warmup_steps:
        raise ValueError("total_training_steps 必须大于 warmup_steps")
    if step < warmup_steps:
        raise ValueError("余弦衰减阶段的 step 不能小于 warmup_steps")
    if peak_lr < 0 or min_lr < 0:
        raise ValueError("peak_lr 和 min_lr 不能为负数")
    if min_lr > peak_lr:
        raise ValueError("min_lr 不能大于 peak_lr")

    progress = (step - warmup_steps) / (
        total_training_steps - warmup_steps
    )
    progress = min(progress, 1.0)
    cosine_factor = 0.5 * (1.0 + math.cos(math.pi * progress))
    return min_lr + (peak_lr - min_lr) * cosine_factor


def clip_gradient_norm(
    model: nn.Module,
    max_norm: float = 1.0,
) -> torch.Tensor:
    """按所有参数梯度的总体 L2 范数进行原地裁剪。

    返回裁剪前的总体梯度范数；梯度未超过 ``max_norm`` 时保持不变。
    """
    if not math.isfinite(max_norm) or max_norm <= 0:
        raise ValueError("max_norm 必须是有限的正数")
    return torch.nn.utils.clip_grad_norm_(
        model.parameters(),
        max_norm=max_norm,
        norm_type=2.0,
    )


def train_causal_lm(
    model: nn.Module,
    train_loader: Any,
    val_loader: Any,
    optimizer: torch.optim.Optimizer,
    device: str | torch.device,
    num_epochs: int,
    eval_freq: int,
    eval_iter: int,
    start_context: str | None = None,
    tokenizer: Any | None = None,
    *,
    warmup_steps: int = 0,
    initial_lr: float = 0.0,
    min_lr: float | None = None,
    max_grad_norm: float | None = None,
) -> tuple[list[float], list[float], list[int]]:
    """执行书中使用的简洁因果语言模型训练循环。

    优化器中配置的学习率是每个参数组的峰值学习率。``warmup_steps``
    大于 0 时，前若干次参数更新会从 ``initial_lr`` 线性升至各组峰值；
    传入 ``min_lr`` 后，预热结束的学习率会沿半个余弦周期降至该下限。
    传入 ``max_grad_norm`` 后，会在预热结束后、参数更新前裁剪总体梯度
    L2 范数。三个可选功能均未启用时保持原来的训练行为。
    """
    if num_epochs <= 0:
        raise ValueError("num_epochs 必须为正整数")
    if eval_freq <= 0:
        raise ValueError("eval_freq 必须为正整数")
    if eval_iter <= 0:
        raise ValueError("eval_iter 必须为正整数")
    if warmup_steps < 0:
        raise ValueError("warmup_steps 不能为负数")
    if max_grad_norm is not None and (
        not math.isfinite(max_grad_norm) or max_grad_norm <= 0
    ):
        raise ValueError("max_grad_norm 必须是有限的正数或 None")
    if (start_context is None) != (tokenizer is None):
        raise ValueError("start_context 与 tokenizer 必须同时提供或同时省略")
    if len(train_loader) == 0:
        raise ValueError("train_loader 不能为空")

    total_training_steps = len(train_loader) * num_epochs
    peak_lrs = [float(group["lr"]) for group in optimizer.param_groups]
    if warmup_steps > 0:
        for peak_lr in peak_lrs:
            linear_warmup_lr(
                0,
                warmup_steps=warmup_steps,
                initial_lr=initial_lr,
                peak_lr=peak_lr,
            )
    if min_lr is not None:
        for peak_lr in peak_lrs:
            cosine_decay_lr(
                warmup_steps,
                warmup_steps=warmup_steps,
                total_training_steps=total_training_steps,
                peak_lr=peak_lr,
                min_lr=min_lr,
            )

    model.to(device)
    train_losses: list[float] = []
    val_losses: list[float] = []
    tokens_seen_at_eval: list[int] = []
    tokens_seen = 0
    global_step = -1

    for epoch in range(num_epochs):
        model.train()
        for input_batch, target_batch in train_loader:
            global_step += 1
            if warmup_steps > 0 and global_step < warmup_steps:
                for param_group, peak_lr in zip(
                    optimizer.param_groups,
                    peak_lrs,
                ):
                    param_group["lr"] = linear_warmup_lr(
                        global_step,
                        warmup_steps=warmup_steps,
                        initial_lr=initial_lr,
                        peak_lr=peak_lr,
                    )
            elif min_lr is not None:
                for param_group, peak_lr in zip(
                    optimizer.param_groups,
                    peak_lrs,
                ):
                    param_group["lr"] = cosine_decay_lr(
                        global_step,
                        warmup_steps=warmup_steps,
                        total_training_steps=total_training_steps,
                        peak_lr=peak_lr,
                        min_lr=min_lr,
                    )
            elif warmup_steps > 0:
                for param_group, peak_lr in zip(
                    optimizer.param_groups,
                    peak_lrs,
                ):
                    param_group["lr"] = peak_lr

            optimizer.zero_grad(set_to_none=True)
            loss = causal_lm_batch_loss(
                input_batch,
                target_batch,
                model,
                device,
            )
            loss.backward()
            if (
                max_grad_norm is not None
                and global_step > warmup_steps
            ):
                clip_gradient_norm(model, max_grad_norm)
            optimizer.step()

            tokens_seen += input_batch.numel()

            if global_step % eval_freq == 0:
                train_loss, val_loss = evaluate_causal_lm(
                    model,
                    train_loader,
                    val_loader,
                    device,
                    eval_iter,
                )
                train_losses.append(train_loss)
                val_losses.append(val_loss)
                tokens_seen_at_eval.append(tokens_seen)
                print(
                    f"Ep {epoch + 1} (Step {global_step:06d}): "
                    f"Train loss {train_loss:.3f}, Val loss {val_loss:.3f}"
                )

        if start_context is not None and tokenizer is not None:
            generate_and_print_sample(
                model,
                tokenizer,
                device,
                start_context,
            )

    return train_losses, val_losses, tokens_seen_at_eval


def plot_losses(
    epochs_seen: Sequence[float] | torch.Tensor,
    tokens_seen: Sequence[int],
    train_losses: Sequence[float],
    val_losses: Sequence[float],
    output_path: str | Path = "losses.png",
) -> Path:
    """绘制训练/验证损失，并把累计 token 数显示在上方横轴。"""
    if not (
        len(epochs_seen)
        == len(tokens_seen)
        == len(train_losses)
        == len(val_losses)
    ):
        raise ValueError("epochs、tokens 和损失序列的长度必须一致")

    import matplotlib.pyplot as plt

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, axis = plt.subplots(figsize=(5, 3))
    axis.plot(epochs_seen, train_losses, label="Training loss")
    axis.plot(epochs_seen, val_losses, linestyle="-.", label="Validation loss")
    axis.set_xlabel("Epochs")
    axis.set_ylabel("Loss")
    axis.legend(loc="upper right")

    token_axis = axis.twiny()
    token_axis.plot(tokens_seen, train_losses, alpha=0)
    token_axis.set_xlabel("Tokens seen")

    fig.tight_layout()
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output
