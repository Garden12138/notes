"""第 6 章垃圾短信分类数据、损失、训练与推理工具。"""

from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import Dataset


SPAM_DATA_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
DEFAULT_PAD_TOKEN_ID = 50256
DEFAULT_LABEL_NAMES = ("not spam", "spam")

__all__ = [
    "SPAM_DATA_URL",
    "DEFAULT_PAD_TOKEN_ID",
    "DEFAULT_LABEL_NAMES",
    "SpamDataset",
    "download_and_extract_spam_data",
    "create_balanced_dataset",
    "split_dataframe",
    "configure_classifier",
    "classification_batch_loss",
    "classification_loader_loss",
    "classification_accuracy",
    "evaluate_classifier",
    "train_classifier",
    "classify_message",
]


def download_and_extract_spam_data(
    url: str = SPAM_DATA_URL,
    zip_path: str | Path = "sms_spam_collection.zip",
    extracted_path: str | Path = "sms_spam_collection",
    data_file_path: str | Path | None = None,
    *,
    timeout: float = 60.0,
) -> Path:
    """按需下载 UCI SMS Spam Collection，并返回 TSV 文件路径。"""
    extraction_directory = Path(extracted_path)
    destination = (
        Path(data_file_path)
        if data_file_path is not None
        else extraction_directory / "SMSSpamCollection.tsv"
    )
    if destination.exists():
        return destination

    archive_path = Path(zip_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=timeout) as response:
        temporary_archive = archive_path.with_suffix(archive_path.suffix + ".part")
        temporary_archive.write_bytes(response.read())
        temporary_archive.replace(archive_path)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as archive:
        matching_members = [
            name
            for name in archive.namelist()
            if Path(name).name == "SMSSpamCollection"
        ]
        if len(matching_members) != 1:
            raise ValueError(
                "压缩包中应恰好包含一个 SMSSpamCollection 文件，"
                f"实际找到 {len(matching_members)} 个"
            )
        with archive.open(matching_members[0]) as source, destination.open("wb") as target:
            shutil.copyfileobj(source, target)
    return destination


def create_balanced_dataset(
    dataframe: pd.DataFrame,
    *,
    label_column: str = "Label",
    negative_label: str = "ham",
    positive_label: str = "spam",
    seed: int = 123,
) -> pd.DataFrame:
    """下采样多数类，使 ham 与 spam 样本数量相同。"""
    positive_rows = dataframe[dataframe[label_column] == positive_label]
    negative_rows = dataframe[dataframe[label_column] == negative_label]
    if positive_rows.empty or negative_rows.empty:
        raise ValueError("数据必须同时包含 ham 和 spam 样本")
    if len(negative_rows) < len(positive_rows):
        raise ValueError("ham 样本少于 spam，无法按书中方式下采样")

    negative_subset = negative_rows.sample(len(positive_rows), random_state=seed)
    return pd.concat([negative_subset, positive_rows], ignore_index=True)


def split_dataframe(
    dataframe: pd.DataFrame,
    train_fraction: float,
    validation_fraction: float,
    *,
    seed: int = 123,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """固定随机种子打乱并划分训练、验证和测试 DataFrame。"""
    if train_fraction <= 0 or validation_fraction < 0:
        raise ValueError("train_fraction 必须为正，validation_fraction 不能为负")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("训练集与验证集比例之和必须小于 1")

    shuffled = dataframe.sample(frac=1, random_state=seed).reset_index(drop=True)
    train_end = int(len(shuffled) * train_fraction)
    validation_end = train_end + int(len(shuffled) * validation_fraction)
    return (
        shuffled.iloc[:train_end].copy(),
        shuffled.iloc[train_end:validation_end].copy(),
        shuffled.iloc[validation_end:].copy(),
    )


class SpamDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    """把 CSV 短信编码、截断并填充到统一长度。"""

    def __init__(
        self,
        csv_file: str | Path,
        tokenizer: Any,
        max_length: int | None = None,
        pad_token_id: int = DEFAULT_PAD_TOKEN_ID,
    ) -> None:
        self.data = pd.read_csv(csv_file)
        if self.data.empty:
            raise ValueError(f"短信数据为空：{csv_file}")
        if "Text" not in self.data or "Label" not in self.data:
            raise ValueError("CSV 必须包含 Text 和 Label 两列")

        self.encoded_texts = [
            tokenizer.encode(str(text))
            for text in self.data["Text"]
        ]
        if max_length is None:
            max_length = max(len(token_ids) for token_ids in self.encoded_texts)
        if max_length <= 0:
            raise ValueError("max_length 必须为正整数")
        self.max_length = max_length
        self.pad_token_id = pad_token_id

        self.encoded_texts = [
            token_ids[:max_length]
            + [pad_token_id] * (max_length - len(token_ids[:max_length]))
            for token_ids in self.encoded_texts
        ]

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        token_ids = torch.tensor(self.encoded_texts[index], dtype=torch.long)
        label = torch.tensor(int(self.data.iloc[index]["Label"]), dtype=torch.long)
        return token_ids, label

    def __len__(self) -> int:
        return len(self.data)


def configure_classifier(
    model: nn.Module,
    *,
    num_classes: int = 2,
    unfreeze_last_n_blocks: int = 1,
    seed: int = 123,
) -> nn.Module:
    """冻结 GPT 主体，替换分类头并解冻靠后的 Transformer 层。"""
    if num_classes <= 1:
        raise ValueError("num_classes 必须大于 1")
    if unfreeze_last_n_blocks < 0:
        raise ValueError("unfreeze_last_n_blocks 不能为负")
    if unfreeze_last_n_blocks > len(model.trf_blocks):
        raise ValueError("要解冻的 Transformer 层数超过模型实际层数")

    for parameter in model.parameters():
        parameter.requires_grad = False

    torch.manual_seed(seed)
    old_head = model.out_head
    embedding_dimension = old_head.in_features
    new_head = nn.Linear(embedding_dimension, num_classes)
    model.out_head = new_head.to(
        device=old_head.weight.device,
        dtype=old_head.weight.dtype,
    )

    if unfreeze_last_n_blocks:
        for block in list(model.trf_blocks)[-unfreeze_last_n_blocks:]:
            for parameter in block.parameters():
                parameter.requires_grad = True
    for parameter in model.final_norm.parameters():
        parameter.requires_grad = True
    return model


def _classification_loss_sum(
    input_batch: torch.Tensor,
    target_batch: torch.Tensor,
    model: nn.Module,
    device: str | torch.device,
) -> tuple[torch.Tensor, int]:
    input_batch = input_batch.to(device)
    target_batch = target_batch.to(device)
    logits = model(input_batch)[:, -1, :]
    return F.cross_entropy(logits, target_batch, reduction="sum"), target_batch.shape[0]


def classification_batch_loss(
    input_batch: torch.Tensor,
    target_batch: torch.Tensor,
    model: nn.Module,
    device: str | torch.device,
) -> torch.Tensor:
    """计算一个短信批次的平均分类交叉熵。"""
    loss_sum, examples = _classification_loss_sum(
        input_batch,
        target_batch,
        model,
        device,
    )
    if examples == 0:
        raise ValueError("分类批次不能为空")
    return loss_sum / examples


def _limited_batch_count(data_loader: Any, num_batches: int | None) -> int:
    if num_batches is not None and num_batches <= 0:
        raise ValueError("num_batches 必须为正整数或 None")
    available_batches = len(data_loader)
    if available_batches == 0:
        return 0
    return available_batches if num_batches is None else min(num_batches, available_batches)


def classification_loader_loss(
    data_loader: Any,
    model: nn.Module,
    device: str | torch.device,
    num_batches: int | None = None,
) -> float:
    """按样本数加权计算 DataLoader 的平均分类损失。"""
    batch_count = _limited_batch_count(data_loader, num_batches)
    if batch_count == 0:
        return float("nan")

    was_training = model.training
    model.eval()
    total_loss = 0.0
    total_examples = 0
    try:
        with torch.no_grad():
            for batch_index, (input_batch, target_batch) in enumerate(data_loader):
                if batch_index >= batch_count:
                    break
                loss_sum, examples = _classification_loss_sum(
                    input_batch,
                    target_batch,
                    model,
                    device,
                )
                total_loss += loss_sum.item()
                total_examples += examples
    finally:
        model.train(was_training)

    if total_examples == 0:
        return float("nan")
    return total_loss / total_examples


def classification_accuracy(
    data_loader: Any,
    model: nn.Module,
    device: str | torch.device,
    num_batches: int | None = None,
) -> float:
    """计算选定批次中的分类准确率。"""
    batch_count = _limited_batch_count(data_loader, num_batches)
    if batch_count == 0:
        return float("nan")

    was_training = model.training
    model.eval()
    correct_predictions = 0
    total_examples = 0
    try:
        with torch.no_grad():
            for batch_index, (input_batch, target_batch) in enumerate(data_loader):
                if batch_index >= batch_count:
                    break
                input_batch = input_batch.to(device)
                target_batch = target_batch.to(device)
                logits = model(input_batch)[:, -1, :]
                predictions = torch.argmax(logits, dim=-1)
                correct_predictions += (predictions == target_batch).sum().item()
                total_examples += target_batch.shape[0]
    finally:
        model.train(was_training)

    if total_examples == 0:
        return float("nan")
    return correct_predictions / total_examples


def evaluate_classifier(
    model: nn.Module,
    train_loader: Any,
    val_loader: Any,
    device: str | torch.device,
    eval_iter: int,
) -> tuple[float, float]:
    """快速估算训练集和验证集分类损失。"""
    return (
        classification_loader_loss(
            train_loader,
            model,
            device,
            num_batches=eval_iter,
        ),
        classification_loader_loss(
            val_loader,
            model,
            device,
            num_batches=eval_iter,
        ),
    )


def train_classifier(
    model: nn.Module,
    train_loader: Any,
    val_loader: Any,
    optimizer: torch.optim.Optimizer,
    device: str | torch.device,
    num_epochs: int,
    eval_freq: int,
    eval_iter: int,
) -> tuple[list[float], list[float], list[float], list[float], int]:
    """执行书中最后层分类微调循环。"""
    if num_epochs <= 0:
        raise ValueError("num_epochs 必须为正整数")
    if eval_freq <= 0:
        raise ValueError("eval_freq 必须为正整数")
    if eval_iter <= 0:
        raise ValueError("eval_iter 必须为正整数")
    if len(train_loader) == 0:
        raise ValueError("train_loader 不能为空")

    model.to(device)
    train_losses: list[float] = []
    val_losses: list[float] = []
    train_accuracies: list[float] = []
    val_accuracies: list[float] = []
    examples_seen = 0
    global_step = -1

    for epoch in range(num_epochs):
        model.train()
        for input_batch, target_batch in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = classification_batch_loss(
                input_batch,
                target_batch,
                model,
                device,
            )
            loss.backward()
            optimizer.step()
            examples_seen += input_batch.shape[0]
            global_step += 1

            if global_step % eval_freq == 0:
                train_loss, val_loss = evaluate_classifier(
                    model,
                    train_loader,
                    val_loader,
                    device,
                    eval_iter,
                )
                train_losses.append(train_loss)
                val_losses.append(val_loss)
                print(
                    f"Ep {epoch + 1} (Step {global_step:06d}): "
                    f"Train loss {train_loss:.3f}, Val loss {val_loss:.3f}"
                )

        train_accuracy = classification_accuracy(
            train_loader,
            model,
            device,
            num_batches=eval_iter,
        )
        val_accuracy = classification_accuracy(
            val_loader,
            model,
            device,
            num_batches=eval_iter,
        )
        train_accuracies.append(train_accuracy)
        val_accuracies.append(val_accuracy)
        print(
            f"Training accuracy: {train_accuracy * 100:.2f}% | "
            f"Validation accuracy: {val_accuracy * 100:.2f}%"
        )

    return (
        train_losses,
        val_losses,
        train_accuracies,
        val_accuracies,
        examples_seen,
    )


def classify_message(
    text: str,
    model: nn.Module,
    tokenizer: Any,
    device: str | torch.device,
    max_length: int,
    *,
    pad_token_id: int = DEFAULT_PAD_TOKEN_ID,
    label_names: Sequence[str] = DEFAULT_LABEL_NAMES,
) -> str:
    """使用与训练阶段相同的长度和填充规则分类一条短信。"""
    if max_length <= 0:
        raise ValueError("max_length 必须为正整数")
    if len(label_names) != model.out_head.out_features:
        raise ValueError("label_names 数量必须与分类头输出类别数一致")

    supported_context_length = model.pos_emb.weight.shape[0]
    if max_length > supported_context_length:
        raise ValueError(
            f"max_length={max_length} 超过模型上下文长度 {supported_context_length}"
        )

    input_ids = tokenizer.encode(text)[:max_length]
    input_ids += [pad_token_id] * (max_length - len(input_ids))
    input_tensor = torch.tensor(
        input_ids,
        dtype=torch.long,
        device=device,
    ).unsqueeze(0)

    was_training = model.training
    model.eval()
    try:
        with torch.no_grad():
            logits = model(input_tensor)[:, -1, :]
        predicted_label = int(torch.argmax(logits, dim=-1).item())
    finally:
        model.train(was_training)
    return label_names[predicted_label]
