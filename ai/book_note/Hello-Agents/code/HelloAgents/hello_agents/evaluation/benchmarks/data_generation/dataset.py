"""Dataset loading for AIME-style generation quality evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_GENERATION_DATASET = "TianHongZXY/aime-1983-2025"
DEFAULT_EVALUATION_DATASET = "math-ai/aime25"


class AIDataset:
    """Load generated or real AIME-style problems into one stable schema.

    Network access is opt-in. Local files may be JSON, JSONL or Parquet; a
    JSON object containing a ``problems`` list is also accepted.
    """

    def __init__(
        self,
        dataset_type: str = "generated",
        data_path: str | Path | None = None,
        *,
        year: int | None = None,
        dataset_name: str | None = None,
        split: str = "test",
        auto_download: bool = False,
    ) -> None:
        if dataset_type not in {"generated", "real"}:
            raise ValueError("dataset_type must be 'generated' or 'real'")
        self.dataset_type = dataset_type
        self.data_path = (
            Path(data_path).expanduser().resolve()
            if data_path is not None
            else None
        )
        self.year = year
        self.dataset_name = dataset_name or (
            DEFAULT_EVALUATION_DATASET
            if dataset_type == "real"
            else DEFAULT_GENERATION_DATASET
        )
        self.split = split
        self.auto_download = auto_download
        self._records: list[dict[str, Any]] | None = None

    def load(self, max_samples: int = 0) -> list[dict[str, Any]]:
        """Load, normalize and optionally truncate records."""
        if max_samples < 0:
            raise ValueError("max_samples cannot be negative")
        if self._records is None:
            source = self.data_path
            if source is None or not source.exists():
                if not self.auto_download:
                    raise FileNotFoundError(
                        "AIME data is unavailable locally. Pass data_path or "
                        "set auto_download=True explicitly."
                    )
                source = self._download()
            raw_records = list(self._read_source(source))
            normalized = [
                self._normalize(record, index)
                for index, record in enumerate(raw_records, start=1)
            ]
            if self.year is not None:
                normalized = [
                    record
                    for record in normalized
                    if record.get("year") in {None, self.year}
                ]
            self._records = normalized
        if max_samples == 0:
            return [dict(record) for record in self._records]
        return [dict(record) for record in self._records[:max_samples]]

    def get_statistics(self) -> dict[str, Any]:
        records = self.load()
        topics: dict[str, int] = {}
        for record in records:
            topic = str(record.get("topic") or "unknown")
            topics[topic] = topics.get(topic, 0) + 1
        return {
            "dataset_type": self.dataset_type,
            "dataset_name": self.dataset_name,
            "split": self.split,
            "year": self.year,
            "total_samples": len(records),
            "topics": topics,
        }

    def _download(self) -> Path:
        try:
            from huggingface_hub import snapshot_download
        except ImportError as exc:
            raise RuntimeError(
                "Downloading requires huggingface_hub. Install it first."
            ) from exc
        return Path(
            snapshot_download(
                repo_id=self.dataset_name,
                repo_type="dataset",
            )
        ).resolve()

    def _read_source(self, source: Path) -> Iterable[dict[str, Any]]:
        if source.is_file():
            yield from self._read_file(source)
            return
        if not source.is_dir():
            raise FileNotFoundError(f"Dataset path does not exist: {source}")

        files: list[Path] = []
        for suffix in ("*.jsonl", "*.json", "*.parquet"):
            files.extend(sorted(source.rglob(suffix)))
        if not files:
            raise FileNotFoundError(f"No supported dataset files under {source}")

        split_files = [
            path for path in files if self.split.lower() in path.as_posix().lower()
        ]
        selected = split_files or files
        for path in selected:
            yield from self._read_file(path)

    @staticmethod
    def _read_file(path: Path) -> Iterable[dict[str, Any]]:
        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number} must be an object")
                yield value
            return
        if suffix == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                value = value.get("problems", value.get("data", [value]))
            if not isinstance(value, list):
                raise ValueError(f"{path} must contain a list of objects")
            for record in value:
                if not isinstance(record, dict):
                    raise ValueError(f"{path} contains a non-object record")
                yield record
            return
        if suffix == ".parquet":
            try:
                import pandas as pd
            except ImportError as exc:
                raise RuntimeError(
                    "Reading Parquet requires pandas and pyarrow."
                ) from exc
            for record in pd.read_parquet(path).to_dict(orient="records"):
                yield record
            return
        raise ValueError(f"Unsupported dataset file: {path}")

    def _normalize(
        self,
        record: dict[str, Any],
        index: int,
    ) -> dict[str, Any]:
        problem = record.get("problem", record.get("Problem"))
        answer = record.get("answer", record.get("Answer"))
        if problem is None or not str(problem).strip():
            raise ValueError(f"Record {index} has no problem")
        if answer is None or not str(answer).strip():
            raise ValueError(f"Record {index} has no answer")

        source = record.get("source") or self.dataset_name
        problem_id = (
            record.get("problem_id")
            or record.get("id")
            or record.get("ID")
            or f"{self.dataset_type}_{index:04d}"
        )
        year = record.get("year", record.get("Year", self.year))
        try:
            year = int(year) if year not in {None, ""} else None
        except (TypeError, ValueError):
            year = None
        return {
            **record,
            "problem_id": str(problem_id),
            "problem": str(problem).strip(),
            "answer": str(answer).strip(),
            "solution": str(record.get("solution") or "").strip(),
            "topic": str(record.get("topic") or "unknown").strip(),
            "source": str(source),
            "year": year,
        }

