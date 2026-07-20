"""第 6 章：把 GPT-2 small 微调为垃圾短信分类器。"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import tiktoken
import torch
from torch.utils.data import DataLoader

from llm_from_scratch.checkpoint import save_model_weights
from llm_from_scratch.classification import (
    SpamDataset,
    classification_accuracy,
    classify_message,
    configure_classifier,
    create_balanced_dataset,
    download_and_extract_spam_data,
    split_dataframe,
    train_classifier,
)
from llm_from_scratch.openai_weights import load_pretrained_gpt2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path("."))
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--device", default=None)
    parser.add_argument(
        "--model-output",
        type=Path,
        default=Path("review_classifier.pth"),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    data_path = download_and_extract_spam_data(
        zip_path=args.work_dir / "sms_spam_collection.zip",
        extracted_path=args.work_dir / "sms_spam_collection",
    )
    dataframe = pd.read_csv(
        data_path,
        sep="\t",
        header=None,
        names=["Label", "Text"],
    )
    balanced = create_balanced_dataset(dataframe)
    balanced["Label"] = balanced["Label"].map({"ham": 0, "spam": 1})
    train_df, validation_df, test_df = split_dataframe(balanced, 0.7, 0.1)
    paths = {
        "train": args.work_dir / "train.csv",
        "validation": args.work_dir / "validation.csv",
        "test": args.work_dir / "test.csv",
    }
    train_df.to_csv(paths["train"], index=False)
    validation_df.to_csv(paths["validation"], index=False)
    test_df.to_csv(paths["test"], index=False)

    tokenizer = tiktoken.get_encoding("gpt2")
    train_dataset = SpamDataset(paths["train"], tokenizer)
    validation_dataset = SpamDataset(
        paths["validation"], tokenizer, max_length=train_dataset.max_length
    )
    test_dataset = SpamDataset(
        paths["test"], tokenizer, max_length=train_dataset.max_length
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        drop_last=True,
    )
    train_eval_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        drop_last=False,
    )
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=args.batch_size,
        shuffle=False,
    )
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    device = torch.device(
        args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    )
    model, _ = load_pretrained_gpt2(
        "gpt2-small (124M)",
        models_dir=args.work_dir / "gpt2",
        script_path=args.work_dir / "gpt_download.py",
        device=device,
    )
    configure_classifier(model)
    model.to(device)
    optimizer = torch.optim.AdamW(
        (parameter for parameter in model.parameters() if parameter.requires_grad),
        lr=5e-5,
        weight_decay=0.1,
    )
    train_classifier(
        model,
        train_loader,
        validation_loader,
        optimizer,
        device,
        num_epochs=args.epochs,
        eval_freq=50,
        eval_iter=5,
    )
    print(
        "Train accuracy:",
        classification_accuracy(train_eval_loader, model, device),
    )
    print(
        "Validation accuracy:",
        classification_accuracy(validation_loader, model, device),
    )
    print("Test accuracy:", classification_accuracy(test_loader, model, device))
    print(
        classify_message(
            "You are a winner selected to receive a cash award.",
            model,
            tokenizer,
            device,
            train_dataset.max_length,
        )
    )
    save_model_weights(model, args.model_output)


if __name__ == "__main__":
    main()
