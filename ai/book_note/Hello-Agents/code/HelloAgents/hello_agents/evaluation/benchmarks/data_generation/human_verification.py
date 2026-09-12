"""Persistent human verification and an optional Gradio interface."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from statistics import fmean
from typing import Any

from .dataset import AIDataset
from .llm_judge import SCORE_DIMENSIONS


VERIFICATION_STATUSES = {"approved", "rejected", "needs_revision"}


class HumanVerificationStore:
    """Save one human decision per generated problem."""

    def __init__(
        self,
        data_path: str | Path,
        results_path: str | Path | None = None,
    ) -> None:
        self.data_path = Path(data_path).expanduser().resolve()
        self.problems = AIDataset(
            dataset_type="generated",
            data_path=self.data_path,
        ).load()
        if not self.problems:
            raise ValueError("Generated dataset contains no problems")
        default_path = self.data_path.with_name(
            f"{self.data_path.stem}_verifications.json"
        )
        self.results_path = (
            Path(results_path).expanduser().resolve()
            if results_path is not None
            else default_path
        )
        self.verifications = self._load_existing()

    def record(
        self,
        problem_id: str,
        scores: dict[str, int | float],
        status: str,
        comments: str = "",
        *,
        verified_at: str | None = None,
    ) -> dict[str, Any]:
        if problem_id not in {
            str(problem["problem_id"]) for problem in self.problems
        }:
            raise KeyError(f"Unknown problem_id: {problem_id}")
        if status not in VERIFICATION_STATUSES:
            choices = ", ".join(sorted(VERIFICATION_STATUSES))
            raise ValueError(f"status must be one of: {choices}")
        checked_scores: dict[str, float] = {}
        for dimension in SCORE_DIMENSIONS:
            if dimension not in scores:
                raise ValueError(f"Missing score: {dimension}")
            score = float(scores[dimension])
            if not 1 <= score <= 5:
                raise ValueError(f"{dimension} must be between 1 and 5")
            checked_scores[dimension] = score
        timestamp = verified_at or datetime.now(timezone.utc).isoformat()
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
            r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
            timestamp,
        ):
            raise ValueError("verified_at must be RFC 3339 with a timezone")
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("verified_at must be RFC 3339") from exc
        if parsed.tzinfo is None:
            raise ValueError("verified_at must include a timezone")
        verification = {
            "problem_id": problem_id,
            "scores": checked_scores,
            "average_score": round(fmean(checked_scores.values()), 4),
            "status": status,
            "comments": comments.strip(),
            "verified_at": timestamp,
        }
        self.verifications[problem_id] = verification
        self._save()
        return dict(verification)

    def get(self, problem_id: str) -> dict[str, Any] | None:
        value = self.verifications.get(problem_id)
        return dict(value) if value else None

    def summary(self) -> dict[str, Any]:
        counts = {status: 0 for status in sorted(VERIFICATION_STATUSES)}
        for value in self.verifications.values():
            status = value.get("status")
            if status in counts:
                counts[status] += 1
        verified = len(self.verifications)
        return {
            "total_samples": len(self.problems),
            "verified_samples": verified,
            "remaining_samples": max(len(self.problems) - verified, 0),
            "progress": round(verified / len(self.problems), 4)
            if self.problems
            else None,
            "status_counts": counts,
        }

    def _load_existing(self) -> dict[str, dict[str, Any]]:
        if not self.results_path.exists():
            return {}
        value = json.loads(self.results_path.read_text(encoding="utf-8"))
        records = value.get("verifications", value) if isinstance(value, dict) else value
        if isinstance(records, list):
            return {
                str(item["problem_id"]): item
                for item in records
                if isinstance(item, dict) and item.get("problem_id")
            }
        if isinstance(records, dict):
            return {
                str(key): item
                for key, item in records.items()
                if isinstance(item, dict)
            }
        raise ValueError(f"Invalid verification file: {self.results_path}")

    def _save(self) -> None:
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "data_path": str(self.data_path),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "summary": self.summary(),
            "verifications": list(self.verifications.values()),
        }
        temporary = self.results_path.with_suffix(
            self.results_path.suffix + ".tmp"
        )
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.results_path)


class HumanVerificationUI:
    """Build the chapter's problem-by-problem Gradio review screen."""

    def __init__(self, store: HumanVerificationStore) -> None:
        self.store = store

    def build(self) -> Any:
        try:
            import gradio as gr
        except ImportError as exc:
            raise RuntimeError(
                "Human verification UI requires gradio. Install it first."
            ) from exc

        def view(index: int) -> tuple[Any, ...]:
            index = max(0, min(int(index), len(self.store.problems) - 1))
            problem = self.store.problems[index]
            saved = self.store.get(str(problem["problem_id"])) or {}
            scores = saved.get("scores", {})
            summary = self.store.summary()
            position = (
                f"{index + 1} / {len(self.store.problems)} · "
                f"已审核 {summary['verified_samples']}"
            )
            return (
                index,
                position,
                str(problem["problem"]),
                str(problem["answer"]),
                str(problem.get("solution") or ""),
                scores.get("correctness", 3),
                scores.get("clarity", 3),
                scores.get("difficulty_match", 3),
                scores.get("completeness", 3),
                saved.get("status", "needs_revision"),
                saved.get("comments", ""),
            )

        def submit(
            index: int,
            correctness: float,
            clarity: float,
            difficulty: float,
            completeness: float,
            status: str,
            comments: str,
        ) -> str:
            problem_id = str(self.store.problems[int(index)]["problem_id"])
            saved = self.store.record(
                problem_id,
                {
                    "correctness": correctness,
                    "clarity": clarity,
                    "difficulty_match": difficulty,
                    "completeness": completeness,
                },
                status,
                comments,
            )
            return f"已保存 {problem_id}，均分 {saved['average_score']:.2f}"

        with gr.Blocks(title="AIME 数据人工验证") as app:
            index = gr.State(0)
            heading = gr.Markdown()
            problem = gr.Textbox(label="题目", lines=6, interactive=False)
            answer = gr.Textbox(label="答案", interactive=False)
            solution = gr.Textbox(label="解答", lines=8, interactive=False)
            with gr.Row():
                correctness = gr.Slider(1, 5, value=3, step=1, label="正确性")
                clarity = gr.Slider(1, 5, value=3, step=1, label="清晰度")
                difficulty = gr.Slider(1, 5, value=3, step=1, label="难度匹配")
                completeness = gr.Slider(1, 5, value=3, step=1, label="完整性")
            status = gr.Radio(
                ["approved", "rejected", "needs_revision"],
                value="needs_revision",
                label="审核状态",
            )
            comments = gr.Textbox(label="备注", lines=3)
            message = gr.Markdown()
            with gr.Row():
                previous = gr.Button("上一题")
                save = gr.Button("保存", variant="primary")
                next_button = gr.Button("下一题")

            view_outputs = [
                index,
                heading,
                problem,
                answer,
                solution,
                correctness,
                clarity,
                difficulty,
                completeness,
                status,
                comments,
            ]
            app.load(view, inputs=index, outputs=view_outputs)
            previous.click(lambda value: int(value) - 1, index, index).then(
                view, index, view_outputs
            )
            next_button.click(lambda value: int(value) + 1, index, index).then(
                view, index, view_outputs
            )
            save.click(
                submit,
                [
                    index,
                    correctness,
                    clarity,
                    difficulty,
                    completeness,
                    status,
                    comments,
                ],
                message,
            )
        return app
