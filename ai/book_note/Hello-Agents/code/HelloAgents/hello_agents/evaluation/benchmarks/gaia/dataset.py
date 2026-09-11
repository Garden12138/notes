"""Load gated GAIA data from an explicit local snapshot."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Mapping


class GAIADataset:
    """GAIA loader following the chapter's local snapshot layout.

    Both the legacy ``metadata.jsonl`` layout and the Parquet files published in
    October 2025 are supported. Network access is opt-in with ``auto_download``.
    """

    def __init__(
        self,
        dataset_name: str = "gaia-benchmark/GAIA",
        split: str = "validation",
        level: int | None = None,
        local_data_dir: str | Path = "./data/gaia",
        *,
        auto_download: bool = False,
        token: str | None = None,
    ) -> None:
        if split not in {"validation", "test"}:
            raise ValueError("split must be 'validation' or 'test'")
        if level not in {None, 1, 2, 3}:
            raise ValueError("level must be 1, 2, 3, or None")
        self.dataset_name = dataset_name
        self.split = split
        self.level = level
        self.local_data_dir = Path(local_data_dir).expanduser().resolve()
        self.auto_download = auto_download
        self.token = token
        self.data: list[dict[str, Any]] = []

    def download(self) -> Path:
        """Explicitly download the gated dataset with ``huggingface_hub``."""
        token = self.token or os.getenv("HF_TOKEN")
        if not token:
            raise RuntimeError(
                "HF_TOKEN is required after accepting the GAIA dataset terms"
            )
        try:
            from huggingface_hub import snapshot_download
        except ImportError as exc:
            raise RuntimeError(
                "install huggingface_hub before downloading GAIA"
            ) from exc

        downloaded = snapshot_download(
            repo_id=self.dataset_name,
            repo_type="dataset",
            local_dir=str(self.local_data_dir),
            token=token,
        )
        return Path(downloaded).expanduser().resolve()

    def load(self, max_samples: int | None = None) -> list[dict[str, Any]]:
        """Load and standardize one split, optionally filtering by level."""
        if max_samples is not None and max_samples < 0:
            raise ValueError("max_samples cannot be negative")
        try:
            metadata_path = self._find_metadata_path()
        except FileNotFoundError:
            if not self.auto_download:
                raise
            self.download()
            metadata_path = self._find_metadata_path()
        records = (
            self._read_jsonl(metadata_path)
            if metadata_path.suffix == ".jsonl"
            else self._read_parquet(metadata_path)
        )
        items: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for record in records:
            item = self._standardize_item(record)
            if self.level is not None and item["level"] != self.level:
                continue
            if item["task_id"] in seen_ids:
                raise ValueError(f"duplicate GAIA task_id: {item['task_id']}")
            seen_ids.add(item["task_id"])
            items.append(item)

        if max_samples not in (None, 0):
            items = items[:max_samples]
        self.data = items
        return list(items)

    def get_statistics(self) -> dict[str, Any]:
        """Summarize the currently loaded selection."""
        items = self.data or self.load()
        level_distribution = {
            level: sum(item["level"] == level for item in items)
            for level in (1, 2, 3)
        }
        return {
            "total_samples": len(items),
            "level_distribution": level_distribution,
            "attachment_samples": sum(
                bool(item.get("attachment_path")) for item in items
            ),
            "scored_samples": sum(
                bool(item.get("final_answer")) for item in items
            ),
        }

    def _find_metadata_path(self) -> Path:
        split_dir = self.local_data_dir / "2023" / self.split
        candidates = [split_dir / "metadata.jsonl"]
        if self.level is not None:
            candidates.append(split_dir / f"metadata.level{self.level}.parquet")
        candidates.append(split_dir / "metadata.parquet")
        for path in candidates:
            if path.is_file():
                return path
        names = ", ".join(path.name for path in candidates)
        raise FileNotFoundError(
            f"GAIA metadata not found under {split_dir}; expected one of {names}"
        )

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        records = []
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid JSONL in {path} at line {line_number}: {exc}"
                    ) from exc
                if not isinstance(record, dict):
                    raise ValueError(
                        f"GAIA JSONL line {line_number} must be an object"
                    )
                records.append(record)
        return records

    @staticmethod
    def _read_parquet(path: Path) -> list[dict[str, Any]]:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError(
                "reading current GAIA Parquet files requires pandas and pyarrow"
            ) from exc
        try:
            frame = pd.read_parquet(path)
        except ImportError as exc:
            raise RuntimeError(
                "reading current GAIA Parquet files requires pandas and pyarrow"
            ) from exc
        return [dict(item) for item in frame.to_dict(orient="records")]

    def _standardize_item(self, record: Mapping[str, Any]) -> dict[str, Any]:
        task_id = _as_text(record.get("task_id"))
        question = _as_text(record.get("Question", record.get("question")))
        if not task_id:
            raise ValueError("GAIA record is missing task_id")
        if not question:
            raise ValueError(f"GAIA record {task_id!r} is missing Question")
        try:
            level = int(record.get("Level", record.get("level")))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"GAIA record {task_id!r} has invalid Level") from exc
        if level not in {1, 2, 3}:
            raise ValueError(f"GAIA record {task_id!r} has invalid Level {level}")

        file_name = _as_text(record.get("file_name"))
        file_path = _as_text(record.get("file_path"))
        attachment_path = self._resolve_attachment(file_path, file_name)
        metadata = record.get(
            "Annotator Metadata",
            record.get("annotator_metadata", {}),
        )
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {"raw": metadata}
        if not isinstance(metadata, Mapping):
            metadata = {}

        return {
            "task_id": task_id,
            "question": question,
            "level": level,
            "final_answer": _as_text(
                record.get("Final answer", record.get("final_answer"))
            ),
            "file_name": file_name,
            "file_path": file_path,
            "attachment_path": (
                str(attachment_path) if attachment_path is not None else None
            ),
            "attachment_exists": bool(
                attachment_path is not None and attachment_path.is_file()
            ),
            "annotator_metadata": dict(metadata),
        }

    def _resolve_attachment(
        self,
        file_path: str,
        file_name: str,
    ) -> Path | None:
        relative = file_path or file_name
        if not relative:
            return None
        candidate = Path(relative)
        if not file_path:
            candidate = Path("2023") / self.split / candidate
        resolved = (
            candidate.resolve()
            if candidate.is_absolute()
            else (self.local_data_dir / candidate).resolve()
        )
        try:
            resolved.relative_to(self.local_data_dir)
        except ValueError as exc:
            raise ValueError(
                f"attachment path escapes GAIA data directory: {relative}"
            ) from exc
        return resolved


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    return "" if text in {"<NA>", "NaT", "nan"} else text
