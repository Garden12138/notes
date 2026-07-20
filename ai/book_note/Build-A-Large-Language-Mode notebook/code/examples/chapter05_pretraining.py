"""第 5 章：在 The Verdict 上运行小型预训练实践。"""

from __future__ import annotations

import argparse
from pathlib import Path

import tiktoken
import torch

from llm_from_scratch.checkpoint import (
    load_training_checkpoint,
    save_model_weights,
    save_training_checkpoint,
)
from llm_from_scratch.config import GPT_CONFIG_124M
from llm_from_scratch.data import create_text_dataloader
from llm_from_scratch.model import GPTModel
from llm_from_scratch.training import (
    causal_lm_loader_loss,
    plot_losses,
    train_causal_lm,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text-file", type=Path, default=Path("the-verdict.txt"))
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--device", default=None)
    parser.add_argument("--model-output", type=Path, default=Path("model.pth"))
    parser.add_argument(
        "--checkpoint-output",
        type=Path,
        default=Path("model_and_optimizer.pth"),
    )
    parser.add_argument(
        "--resume-checkpoint",
        type=Path,
        default=None,
        help="Optional checkpoint whose model and optimizer state should resume",
    )
    parser.add_argument("--plot-output", type=Path, default=Path("losses.png"))
    return parser


def resolve_device(requested: str | None) -> torch.device:
    if requested:
        return torch.device(requested)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main() -> None:
    args = build_parser().parse_args()
    text = args.text_file.read_text(encoding="utf-8")
    split_index = int(len(text) * 0.9)
    train_text, validation_text = text[:split_index], text[split_index:]
    tokenizer = tiktoken.get_encoding("gpt2")

    train_loader = create_text_dataloader(
        train_text,
        batch_size=args.batch_size,
        max_length=args.max_length,
        stride=args.max_length,
        shuffle=True,
        drop_last=True,
        tokenizer=tokenizer,
    )
    validation_loader = create_text_dataloader(
        validation_text,
        batch_size=args.batch_size,
        max_length=args.max_length,
        stride=args.max_length,
        shuffle=False,
        drop_last=False,
        tokenizer=tokenizer,
    )

    torch.manual_seed(123)
    device = resolve_device(args.device)
    model = GPTModel(GPT_CONFIG_124M).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=4e-4, weight_decay=0.1)
    completed_epochs = 0
    tokens_seen_before = 0
    if args.resume_checkpoint is not None:
        metadata = load_training_checkpoint(
            model,
            optimizer,
            args.resume_checkpoint,
            device,
        )
        completed_epochs = int(metadata.get("completed_epochs", 0))
        tokens_seen_before = int(metadata.get("tokens_seen", 0))
        print(
            f"Resumed {args.resume_checkpoint} after "
            f"{completed_epochs} completed epoch(s)"
        )

    print("Initial training loss:", causal_lm_loader_loss(train_loader, model, device))
    print(
        "Initial validation loss:",
        causal_lm_loader_loss(validation_loader, model, device),
    )

    train_losses, validation_losses, tokens_seen = train_causal_lm(
        model,
        train_loader,
        validation_loader,
        optimizer,
        device,
        num_epochs=args.epochs,
        eval_freq=5,
        eval_iter=1,
        start_context="Every effort moves you",
        tokenizer=tokenizer,
    )
    save_model_weights(model, args.model_output)
    tokens_seen_this_run = (
        args.epochs
        * len(train_loader)
        * args.batch_size
        * args.max_length
    )
    save_training_checkpoint(
        model,
        optimizer,
        args.checkpoint_output,
        completed_epochs=completed_epochs + args.epochs,
        tokens_seen=tokens_seen_before + tokens_seen_this_run,
        tokens_seen_at_eval=[tokens_seen_before + value for value in tokens_seen],
    )
    epochs_seen = torch.linspace(0, args.epochs, len(train_losses))
    plot_losses(
        epochs_seen,
        tokens_seen,
        train_losses,
        validation_losses,
        args.plot_output,
    )


if __name__ == "__main__":
    main()
