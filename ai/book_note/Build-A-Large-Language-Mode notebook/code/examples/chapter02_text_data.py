"""Chapter 2 examples: tokenization, sliding windows, and embeddings."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import torch
from torch import nn

from llm_from_scratch.data import create_text_dataloader


TOKEN_PATTERN = re.compile(r"""([,.:;?_!"()']|--|\s)""")
END_OF_TEXT_TOKEN = "<|endoftext|>"
UNKNOWN_TOKEN = "<|unk|>"


def tokenize_with_regex(text: str) -> list[str]:
    """Split text using the deliberately simple tokenizer from chapter 2."""
    pieces = TOKEN_PATTERN.split(text)
    return [piece.strip() for piece in pieces if piece.strip()]


def build_vocabulary(
    tokens: list[str],
    *,
    include_special_tokens: bool = False,
) -> dict[str, int]:
    vocabulary_tokens = sorted(set(tokens))
    if include_special_tokens:
        vocabulary_tokens.extend([END_OF_TEXT_TOKEN, UNKNOWN_TOKEN])
    return {token: token_id for token_id, token in enumerate(vocabulary_tokens)}


class SimpleTokenizerV1:
    """Educational tokenizer that raises KeyError for unknown tokens."""

    def __init__(self, vocabulary: dict[str, int]) -> None:
        self.str_to_int = vocabulary
        self.int_to_str = {
            token_id: token for token, token_id in vocabulary.items()
        }

    def encode(self, text: str) -> list[int]:
        return [self.str_to_int[token] for token in tokenize_with_regex(text)]

    def decode(self, token_ids: list[int]) -> str:
        text = " ".join(self.int_to_str[token_id] for token_id in token_ids)
        return re.sub(r"""\s+([,.?!"()'])""", r"\1", text)


class SimpleTokenizerV2(SimpleTokenizerV1):
    """Educational tokenizer that maps unknown tokens to a special token."""

    def encode(self, text: str) -> list[int]:
        tokens = tokenize_with_regex(text)
        tokens = [
            token if token in self.str_to_int else UNKNOWN_TOKEN
            for token in tokens
        ]
        return [self.str_to_int[token] for token in tokens]


class DocumentTokenEmbedding(nn.Module):
    """Add trainable absolute-position embeddings to token embeddings."""

    def __init__(
        self,
        vocab_size: int = 50_257,
        context_length: int = 256,
        embedding_dim: int = 768,
    ) -> None:
        super().__init__()
        self.context_length = context_length
        self.token_embedding_layer = nn.Embedding(vocab_size, embedding_dim)
        self.position_embedding_layer = nn.Embedding(
            context_length,
            embedding_dim,
        )

    def forward(
        self,
        input_ids: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        if input_ids.ndim != 2:
            raise ValueError(
                "input_ids must have shape [batch_size, seq_len], "
                f"got {tuple(input_ids.shape)}"
            )
        seq_len = input_ids.size(1)
        if seq_len > self.context_length:
            raise ValueError(
                f"Input length {seq_len} exceeds context_length "
                f"{self.context_length}"
            )

        token_embeddings = self.token_embedding_layer(input_ids)
        position_ids = torch.arange(seq_len, device=input_ids.device)
        position_embeddings = self.position_embedding_layer(position_ids)
        input_embeddings = token_embeddings + position_embeddings
        return token_embeddings, position_embeddings, input_embeddings


def create_token_embeddings_from_file(
    file_path: str | Path,
    *,
    batch_size: int = 1,
    max_length: int = 4,
    stride: int = 1,
    embedding_dim: int = 3,
    shuffle: bool = False,
) -> dict[str, torch.Tensor]:
    """Run the chapter's first-batch embedding demonstration."""
    text = Path(file_path).read_text(encoding="utf-8")
    loader = create_text_dataloader(
        text,
        batch_size=batch_size,
        max_length=max_length,
        stride=stride,
        shuffle=shuffle,
        drop_last=True,
    )
    try:
        inputs, targets = next(iter(loader))
    except StopIteration as exc:
        raise ValueError(
            "The document is too short to produce a complete batch with the "
            "selected batch_size and max_length"
        ) from exc

    embedding = DocumentTokenEmbedding(
        context_length=max_length,
        embedding_dim=embedding_dim,
    ).to(inputs.device)
    token_embeddings, position_embeddings, input_embeddings = embedding(inputs)
    return {
        "inputs": inputs,
        "targets": targets,
        "token_embeddings": token_embeddings,
        "position_embeddings": position_embeddings,
        "input_embeddings": input_embeddings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "text_file",
        type=Path,
        nargs="?",
        default=Path("the-verdict.txt"),
        help="UTF-8 text file to sample (default: the-verdict.txt)",
    )
    args = parser.parse_args()

    torch.manual_seed(123)
    result = create_token_embeddings_from_file(args.text_file)
    for name, tensor in result.items():
        print(f"{name}: shape={tuple(tensor.shape)}")
        print(tensor)


if __name__ == "__main__":
    main()
