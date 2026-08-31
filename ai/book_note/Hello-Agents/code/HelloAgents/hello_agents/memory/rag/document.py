"""Document conversion and Markdown-aware chunking for the RAG pipeline."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


TEXT_EXTENSIONS = {
    ".cfg",
    ".conf",
    ".c",
    ".cpp",
    ".css",
    ".csv",
    ".h",
    ".htm",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".log",
    ".md",
    ".py",
    ".scss",
    ".toml",
    ".ts",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(*parts: object) -> str:
    value = "|".join(str(part) for part in parts)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass
class Document:
    """A normalized Markdown document and its source metadata."""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    doc_id: str | None = None

    def __post_init__(self) -> None:
        self.content = self.content.strip()
        if not self.content:
            raise ValueError("document content must not be blank")
        if self.doc_id is None:
            self.doc_id = stable_id(self.content)


@dataclass
class DocumentChunk:
    """One retrievable piece of a normalized document."""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_id: str | None = None
    doc_id: str | None = None
    chunk_index: int = 0
    token_count: int = 0

    def __post_init__(self) -> None:
        self.content = self.content.strip()
        if not self.content:
            raise ValueError("chunk content must not be blank")
        self.token_count = self.token_count or approx_token_len(self.content)
        if self.chunk_id is None:
            self.chunk_id = stable_id(
                self.doc_id or "document",
                self.chunk_index,
                self.content,
            )


class DocumentProcessor:
    """Convert files to Markdown, then split on headings and paragraphs."""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be non-negative and smaller than chunk_size",
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_file(
        self,
        file_path: str | Path,
        document_id: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Document:
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"document does not exist: {path}")
        markdown = convert_to_markdown(path)
        source_metadata = {
            **(metadata or {}),
            "source_path": str(path),
            "source_name": path.name,
            "file_ext": path.suffix.lower(),
            "format": "markdown",
            "loaded_at": utc_iso(),
        }
        return Document(
            content=markdown,
            metadata=source_metadata,
            doc_id=document_id,
        )

    def create_document(
        self,
        content: str,
        document_id: str | None = None,
        **metadata: Any,
    ) -> Document:
        source = metadata.pop("source_path", f"text:{document_id or 'inline'}")
        return Document(
            content=content,
            doc_id=document_id,
            metadata={
                **metadata,
                "source_path": source,
                "source_name": Path(source).name,
                "file_ext": ".md",
                "format": "markdown",
                "loaded_at": utc_iso(),
            },
        )

    def process_document(self, document: Document) -> List[DocumentChunk]:
        paragraphs = split_paragraphs_with_headings(document.content)
        raw_chunks = chunk_paragraphs(
            paragraphs,
            chunk_tokens=self.chunk_size,
            overlap_tokens=self.chunk_overlap,
        )
        total = len(raw_chunks)
        chunks: List[DocumentChunk] = []
        for index, raw in enumerate(raw_chunks):
            metadata = {
                **document.metadata,
                "doc_id": document.doc_id,
                "chunk_index": index,
                "total_chunks": total,
                "heading_path": raw.get("heading_path"),
                "start": raw["start"],
                "end": raw["end"],
                "processed_at": utc_iso(),
            }
            chunks.append(
                DocumentChunk(
                    content=raw["content"],
                    metadata=metadata,
                    doc_id=document.doc_id,
                    chunk_index=index,
                    token_count=raw["token_count"],
                ),
            )
        return chunks

    def process_documents(
        self,
        documents: Iterable[Document],
    ) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        for document in documents:
            chunks.extend(self.process_document(document))
        return chunks


def convert_to_markdown(file_path: str | Path) -> str:
    """Convert a file using MarkItDown with a safe text-only fallback."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in {".md", ".txt"}:
        return read_text(path)

    markitdown = get_markitdown()
    if markitdown is not None:
        try:
            result = markitdown.convert(str(path))
            text = getattr(result, "text_content", None)
            if isinstance(text, str) and text.strip():
                return post_process_markdown(text, is_pdf=suffix == ".pdf")
        except Exception as error:
            if suffix not in TEXT_EXTENSIONS:
                raise RuntimeError(
                    f"MarkItDown could not convert {path.name}: {error}",
                ) from error

    if suffix in TEXT_EXTENSIONS:
        return read_text(path)
    raise RuntimeError(
        "This format requires MarkItDown. Install it with "
        "`pip install 'markitdown[all]'`.",
    )


def get_markitdown() -> Any | None:
    try:
        from markitdown import MarkItDown
    except ImportError:
        return None
    return MarkItDown()


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            text = path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        if text.strip():
            return text
    raise ValueError(f"no readable text found in {path}")


def post_process_markdown(text: str, is_pdf: bool = False) -> str:
    """Remove obvious conversion noise without discarding document structure."""
    lines: List[str] = []
    blank = False
    for raw in text.splitlines():
        line = raw.strip()
        if is_pdf and re.fullmatch(r"\d+", line):
            continue
        if not line:
            if lines and not blank:
                lines.append("")
            blank = True
            continue
        blank = False
        lines.append(line)
    return "\n".join(lines).strip()


def preprocess_markdown_for_embedding(text: str) -> str:
    """Remove markup noise while retaining link labels and code content."""
    value = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"```[^\n]*\n?", "", value)
    value = value.replace("```", "")
    value = re.sub(r"(?<!\w)[*_~]{1,2}|[*_~]{1,2}(?!\w)", "", value)
    value = value.replace("`", "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def split_paragraphs_with_headings(text: str) -> List[Dict[str, Any]]:
    """Split Markdown while carrying the nearest heading hierarchy."""
    headings: List[str] = []
    paragraphs: List[Dict[str, Any]] = []
    buffer: List[str] = []
    buffer_start = 0
    position = 0

    def flush(end: int) -> None:
        nonlocal buffer
        content = "\n".join(buffer).strip()
        if content:
            paragraphs.append(
                {
                    "content": content,
                    "heading_path": " > ".join(headings) or None,
                    "start": buffer_start,
                    "end": end,
                },
            )
        buffer = []

    for raw in text.splitlines(keepends=True):
        line = raw.rstrip("\r\n")
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
        if heading:
            flush(position)
            level = len(heading.group(1))
            headings = headings[: level - 1]
            headings.append(heading.group(2))
        elif not line.strip():
            flush(position)
        else:
            if not buffer:
                buffer_start = position
            buffer.append(line)
        position += len(raw)
    flush(len(text))

    if not paragraphs and text.strip():
        paragraphs.append(
            {
                "content": text.strip(),
                "heading_path": None,
                "start": 0,
                "end": len(text),
            },
        )
    return paragraphs


def chunk_paragraphs(
    paragraphs: List[Dict[str, Any]],
    chunk_tokens: int,
    overlap_tokens: int,
) -> List[Dict[str, Any]]:
    """Pack paragraphs with overlap while guaranteeing forward progress."""
    expanded: List[Dict[str, Any]] = []
    for paragraph in paragraphs:
        expanded.extend(split_oversized_paragraph(paragraph, chunk_tokens))

    chunks: List[Dict[str, Any]] = []
    current: List[Dict[str, Any]] = []
    current_tokens = 0

    def emit() -> None:
        if not current:
            return
        content = "\n\n".join(item["content"] for item in current)
        chunks.append(
            {
                "content": content,
                "heading_path": next(
                    (
                        item["heading_path"]
                        for item in reversed(current)
                        if item.get("heading_path")
                    ),
                    None,
                ),
                "start": current[0]["start"],
                "end": current[-1]["end"],
                "token_count": approx_token_len(content),
            },
        )

    for paragraph in expanded:
        paragraph_tokens = approx_token_len(paragraph["content"])
        if current and current_tokens + paragraph_tokens > chunk_tokens:
            emit()
            kept: List[Dict[str, Any]] = []
            kept_tokens = 0
            for item in reversed(current):
                item_tokens = approx_token_len(item["content"])
                if kept_tokens + item_tokens > overlap_tokens:
                    break
                kept.append(item)
                kept_tokens += item_tokens
            current = list(reversed(kept))
            current_tokens = kept_tokens
            while current and current_tokens + paragraph_tokens > chunk_tokens:
                removed = current.pop(0)
                current_tokens -= approx_token_len(removed["content"])

        current.append(paragraph)
        current_tokens += paragraph_tokens

    emit()
    return deduplicate_chunks(chunks)


def split_oversized_paragraph(
    paragraph: Dict[str, Any],
    max_tokens: int,
) -> List[Dict[str, Any]]:
    content = paragraph["content"]
    if approx_token_len(content) <= max_tokens:
        return [paragraph]

    parts: List[Dict[str, Any]] = []
    remaining = content
    local_offset = 0
    while remaining:
        prefix = prefix_by_token_budget(remaining, max_tokens)
        if len(prefix) < len(remaining):
            boundary = max(
                prefix.rfind("。"),
                prefix.rfind("！"),
                prefix.rfind("？"),
                prefix.rfind(". "),
                prefix.rfind("\n"),
            )
            if boundary >= len(prefix) // 2:
                prefix = prefix[: boundary + 1]
        prefix = prefix.strip()
        if not prefix:
            prefix = remaining[:1]
        start = paragraph["start"] + local_offset
        parts.append(
            {
                **paragraph,
                "content": prefix,
                "start": start,
                "end": start + len(prefix),
            },
        )
        consumed = remaining.find(prefix) + len(prefix)
        local_offset += consumed
        tail = remaining[consumed:]
        remaining = tail.lstrip()
        local_offset += len(tail) - len(remaining)
    return parts


def prefix_by_token_budget(text: str, max_tokens: int) -> str:
    tokens = 0
    index = 0
    in_word = False
    while index < len(text):
        character = text[index]
        if is_cjk(character):
            tokens += 1
            in_word = False
        elif character.isalnum() or character == "_":
            if not in_word:
                tokens += 1
            in_word = True
        else:
            in_word = False
        if tokens > max_tokens:
            break
        index += 1
    return text[: max(1, index)]


def deduplicate_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    unique: List[Dict[str, Any]] = []
    for chunk in chunks:
        digest = stable_id(chunk["content"].strip())
        if digest not in seen:
            seen.add(digest)
            unique.append(chunk)
    return unique


def approx_token_len(text: str) -> int:
    cjk = sum(1 for character in text if is_cjk(character))
    non_cjk = len(re.findall(r"[A-Za-z0-9_]+", text))
    return cjk + non_cjk


def is_cjk(character: str) -> bool:
    code = ord(character)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0x20000 <= code <= 0x2CEAF
    )
