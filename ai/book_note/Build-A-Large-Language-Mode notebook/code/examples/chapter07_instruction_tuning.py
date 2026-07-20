"""第 7 章：对 GPT-2 medium 执行监督式指令微调。"""

from __future__ import annotations

import argparse
from pathlib import Path

import tiktoken
import torch

from llm_from_scratch.checkpoint import save_model_weights
from llm_from_scratch.instruction import (
    create_instruction_dataloaders,
    download_and_load_json,
    format_instruction_prompt,
    generate_instruction_responses,
    save_instruction_responses,
    split_instruction_data,
)
from llm_from_scratch.openai_weights import load_pretrained_gpt2
from llm_from_scratch.training import causal_lm_loader_loss, train_causal_lm


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-file",
        type=Path,
        default=Path("instruction-data.json"),
    )
    parser.add_argument("--models-dir", type=Path, default=Path("gpt2"))
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--device", default=None)
    parser.add_argument(
        "--responses-output",
        type=Path,
        default=Path("instruction-data-with-response.json"),
    )
    parser.add_argument(
        "--model-output",
        type=Path,
        default=Path("gpt2-medium355M-sft.pth"),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    data = download_and_load_json(args.data_file)
    train_data, validation_data, test_data = split_instruction_data(data)
    tokenizer = tiktoken.get_encoding("gpt2")
    train_loader, validation_loader, _ = create_instruction_dataloaders(
        train_data,
        validation_data,
        test_data,
        tokenizer,
        batch_size=args.batch_size,
        allowed_max_length=1024,
    )

    device = torch.device(
        args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    )
    model, config = load_pretrained_gpt2(
        "gpt2-medium (355M)",
        models_dir=args.models_dir,
        script_path=args.models_dir.parent / "gpt_download.py",
        device=device,
    )
    print(
        "Initial training loss:",
        causal_lm_loader_loss(train_loader, model, device, num_batches=5),
    )
    print(
        "Initial validation loss:",
        causal_lm_loader_loss(validation_loader, model, device, num_batches=5),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5, weight_decay=0.1)
    train_causal_lm(
        model,
        train_loader,
        validation_loader,
        optimizer,
        device,
        num_epochs=args.epochs,
        eval_freq=5,
        eval_iter=5,
        start_context=format_instruction_prompt(validation_data[0]),
        tokenizer=tokenizer,
    )
    responses = generate_instruction_responses(
        test_data,
        model,
        tokenizer,
        device,
        context_size=config.context_length,
        max_new_tokens=256,
        eos_id=50256,
    )
    save_instruction_responses(responses, args.responses_output)
    save_model_weights(model, args.model_output)


if __name__ == "__main__":
    main()

