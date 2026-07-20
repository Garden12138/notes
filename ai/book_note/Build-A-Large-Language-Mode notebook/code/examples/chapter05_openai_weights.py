"""第 5 章：加载 OpenAI GPT-2 权重并生成文本。"""

from __future__ import annotations

import argparse
from pathlib import Path

import tiktoken
import torch

from llm_from_scratch.config import GPT2_MODEL_CONFIGS
from llm_from_scratch.generation import (
    generate_token_ids,
    text_to_token_ids,
    token_ids_to_text,
)
from llm_from_scratch.openai_weights import load_pretrained_gpt2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-name",
        choices=GPT2_MODEL_CONFIGS,
        default="gpt2-small (124M)",
    )
    parser.add_argument("--models-dir", type=Path, default=Path("gpt2"))
    parser.add_argument("--script-path", type=Path, default=Path("gpt_download.py"))
    parser.add_argument("--prompt", default="Every effort moves you")
    parser.add_argument("--max-new-tokens", type=int, default=25)
    parser.add_argument("--temperature", type=float, default=1.5)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--device", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    device = torch.device(
        args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    )
    model, config = load_pretrained_gpt2(
        args.model_name,
        models_dir=args.models_dir,
        script_path=args.script_path,
        device=device,
    )
    tokenizer = tiktoken.get_encoding("gpt2")
    torch.manual_seed(123)
    output_ids = generate_token_ids(
        model,
        text_to_token_ids(args.prompt, tokenizer, device=device),
        max_new_tokens=args.max_new_tokens,
        context_size=config.context_length,
        temperature=args.temperature,
        top_k=args.top_k,
    )
    print(token_ids_to_text(output_ids, tokenizer))


if __name__ == "__main__":
    main()

