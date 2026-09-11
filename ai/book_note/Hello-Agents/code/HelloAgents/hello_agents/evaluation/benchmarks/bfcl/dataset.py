"""Load BFCL JSONL test data and its ``possible_answer`` files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable


_FILE_PATTERN = re.compile(r"^BFCL_v\d+_(.+)\.json$")


def _read_records(path: Path) -> list[dict[str, Any]]:
    """Read either a JSON array/object or the JSONL used by official BFCL."""
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSONL in {path} at line {line_number}: {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise ValueError(
                    f"each JSONL entry in {path} must be an object"
                )
            records.append(value)
        return records

    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value
    raise ValueError(f"{path} must contain a JSON object, array, or JSONL")


class BFCLDataset:
    """Load one BFCL v4 category without downloading data implicitly."""

    def __init__(
        self,
        bfcl_data_dir: str | Path,
        category: str = "simple_python",
    ) -> None:
        self.data_dir = Path(bfcl_data_dir).expanduser().resolve()
        self.category = category.strip()
        if not self.category:
            raise ValueError("category cannot be empty")
        self.data: list[dict[str, Any]] = []
        self.ground_truth: list[dict[str, Any]] = []

    def get_available_categories(self) -> list[str]:
        """Return categories represented by test files in the data directory."""
        if not self.data_dir.is_dir():
            return []
        categories = []
        for path in self.data_dir.glob("BFCL_v*_*.json"):
            match = _FILE_PATTERN.match(path.name)
            if match:
                categories.append(match.group(1))
        return sorted(set(categories))

    def load(self, max_samples: int | None = None) -> list[dict[str, Any]]:
        """Merge prompt and ground-truth records by stable BFCL ID."""
        if max_samples is not None and max_samples < 0:
            raise ValueError("max_samples cannot be negative")
        prompt_path = self._find_category_file(self.data_dir)
        prompt_records = _read_records(prompt_path)
        if not prompt_records:
            raise ValueError(f"no BFCL records found in {prompt_path}")

        answer_dir = self.data_dir / "possible_answer"
        answer_path = self._find_category_file(answer_dir, required=False)
        if answer_path is None:
            if "irrelevance" not in self.category:
                raise FileNotFoundError(
                    f"ground truth not found for category {self.category!r} "
                    f"under {answer_dir}"
                )
            answer_records: list[dict[str, Any]] = []
        else:
            answer_records = _read_records(answer_path)

        prompt_ids = self._unique_by_id(prompt_records, prompt_path)
        answers_by_id = self._unique_by_id(
            answer_records,
            answer_path or answer_dir,
        )
        if answers_by_id:
            missing = sorted(set(prompt_ids) - set(answers_by_id))
            extra = sorted(set(answers_by_id) - set(prompt_ids))
            if missing or extra:
                raise ValueError(
                    "prompt and ground-truth IDs differ: "
                    f"missing={missing[:3]}, extra={extra[:3]}"
                )

        merged = []
        for case_id, record in prompt_ids.items():
            functions = record.get("function", record.get("functions", []))
            if not isinstance(functions, list):
                raise ValueError(f"{case_id}: function must be a list")
            answer = answers_by_id.get(case_id, {})
            ground_truth = answer.get(
                "ground_truth",
                answer.get("possible_answer", record.get("ground_truth", [])),
            )
            merged.append(
                {
                    **record,
                    "id": case_id,
                    "function": functions,
                    "ground_truth": ground_truth,
                    "category": record.get("category", self.category),
                }
            )

        if max_samples not in (None, 0):
            merged = merged[:max_samples]
        self.data = merged
        self.ground_truth = [
            {"id": item["id"], "ground_truth": item["ground_truth"]}
            for item in merged
        ]
        return list(self.data)

    def _find_category_file(
        self,
        directory: Path,
        *,
        required: bool = True,
    ) -> Path | None:
        candidates = sorted(directory.glob(f"BFCL_v*_{self.category}.json"))
        if not candidates:
            legacy = directory / f"BFCL_{self.category}.json"
            if legacy.is_file():
                return legacy
            if required:
                available = ", ".join(self.get_available_categories()) or "none"
                raise FileNotFoundError(
                    f"BFCL category {self.category!r} not found in {directory}; "
                    f"available categories: {available}"
                )
            return None
        return candidates[-1]

    @staticmethod
    def _unique_by_id(
        records: Iterable[dict[str, Any]],
        source: Path,
    ) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for record in records:
            case_id = str(record.get("id", "")).strip()
            if not case_id:
                raise ValueError(f"record without id in {source}")
            if case_id in indexed:
                raise ValueError(f"duplicate BFCL id {case_id!r} in {source}")
            indexed[case_id] = record
        return indexed

