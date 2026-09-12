"""AIME-style problem generator following the chapter's workflow."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import random
import re
import time
from typing import Any, Callable

from .dataset import AIDataset, DEFAULT_GENERATION_DATASET


AIME_TOPICS = {
    "Algebra",
    "Geometry",
    "Number Theory",
    "Combinatorics",
    "Probability",
}


class AIMEGenerator:
    """Generate validated AIME-style records with optional references."""

    def __init__(
        self,
        llm: Any | None = None,
        *,
        agent: Any | None = None,
        delay_seconds: float = 1.0,
        use_reference_examples: bool = True,
        reference_dataset: str = DEFAULT_GENERATION_DATASET,
        reference_data_path: str | Path | None = None,
        download_reference: bool = False,
        seed: int = 42,
        max_retries: int = 2,
    ) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        self.llm = llm
        self.agent = agent
        self.delay_seconds = delay_seconds
        self.use_reference_examples = use_reference_examples
        self.reference_dataset = reference_dataset
        self.reference_data_path = reference_data_path
        self.download_reference = download_reference
        self.random = random.Random(seed)
        self.max_retries = max_retries
        self._reference_records: list[dict[str, Any]] | None = None

    def generate_single(self, index: int) -> dict[str, Any]:
        if index < 1:
            raise ValueError("index must start at 1")
        reference = self._choose_reference()
        prompt = self._build_prompt(reference)
        last_error: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                agent = self._get_agent()
                if hasattr(agent, "clear_history"):
                    agent.clear_history()
                response = agent.run(prompt)
                record = self._parse_response(str(response))
                record.update(
                    {
                        "problem_id": f"gen_aime_{index:04d}",
                        "source": "llm_generated",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "reference_problem_id": (
                            reference.get("problem_id") if reference else None
                        ),
                    }
                )
                return record
            except (ValueError, json.JSONDecodeError) as exc:
                last_error = exc
        raise ValueError(
            f"Failed to generate a valid problem after retries: {last_error}"
        )

    def generate_and_save(
        self,
        num_problems: int,
        output_dir: str | Path,
        *,
        output_path: str | Path | None = None,
        checkpoint_every: int = 5,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        if num_problems <= 0:
            raise ValueError("num_problems must be positive")
        if checkpoint_every < 0:
            raise ValueError("checkpoint_every cannot be negative")
        directory = Path(output_dir).expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        final_path = (
            Path(output_path).expanduser().resolve()
            if output_path is not None
            else directory / "generated_aime.json"
        )
        checkpoint_path = directory / f".{final_path.stem}.checkpoint.json"
        records: list[dict[str, Any]] = []
        failures: list[dict[str, str | int]] = []

        for index in range(1, num_problems + 1):
            if index > 1 and self.delay_seconds:
                time.sleep(self.delay_seconds)
            try:
                records.append(self.generate_single(index))
            except Exception as exc:
                failures.append({"index": index, "error": str(exc)})
            if progress_callback:
                progress_callback(index, num_problems)
            if checkpoint_every and index % checkpoint_every == 0:
                self._write_payload(
                    checkpoint_path,
                    records,
                    requested=num_problems,
                    failures=failures,
                    complete=False,
                )

        payload = self._write_payload(
            final_path,
            records,
            requested=num_problems,
            failures=failures,
            complete=True,
        )
        if checkpoint_path.exists():
            checkpoint_path.unlink()
        payload["output_path"] = str(final_path)
        return payload

    def _get_agent(self) -> Any:
        if self.agent is not None:
            return self.agent
        if self.llm is None:
            from ....core.llm import HelloAgentsLLM

            self.llm = HelloAgentsLLM()
        from ....agents.simple_agent import SimpleAgent

        self.agent = SimpleAgent(
            name="AIMEProblemGenerator",
            llm=self.llm,
            system_prompt=(
                "你是一名数学竞赛命题专家。生成严谨、原创、可验证的 "
                "AIME 风格题目，并严格按用户指定的 JSON 格式作答。"
            ),
            enable_tool_calling=False,
        )
        return self.agent

    def _choose_reference(self) -> dict[str, Any] | None:
        if not self.use_reference_examples:
            return None
        if self._reference_records is None:
            self._reference_records = AIDataset(
                dataset_type="real",
                data_path=self.reference_data_path,
                dataset_name=self.reference_dataset,
                auto_download=self.download_reference,
            ).load()
        if not self._reference_records:
            raise ValueError("Reference dataset contains no records")
        return self.random.choice(self._reference_records)

    @staticmethod
    def _build_prompt(reference: dict[str, Any] | None) -> str:
        reference_text = ""
        if reference:
            reference_text = (
                "下面只提供难度和风格参考，不得改写或复用其数字、"
                "情境和解法：\n"
                f"参考题目：{reference['problem']}\n"
                f"参考答案：{reference['answer']}\n\n"
            )
        return (
            f"{reference_text}"
            "请生成一道全新的 AIME 风格数学竞赛题，"
            "难度接近 AIME 第 6–9 题。\n"
            "要求：答案必须是 0 到 999 的整数；"
            "解答过程完整可检查；topic 只能是 "
            "Algebra、Geometry、Number Theory、Combinatorics 或 Probability。\n"
            "仅返回一个 JSON 对象，不要 Markdown 围栏：\n"
            '{"problem":"...","answer":"...","solution":"...","topic":"..."}'
        )

    @staticmethod
    def _parse_response(response: str) -> dict[str, str]:
        text = response.strip()
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
        if fenced:
            text = fenced.group(1)
        else:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("Model response contains no JSON object")
            text = text[start : end + 1]
        # Prefer LaTeX commands in math text while retaining valid JSON escapes.
        text = AIMEGenerator._repair_json_escapes(text)
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError("Generated response must be a JSON object")
        for field in ("problem", "answer", "solution", "topic"):
            if not str(value.get(field, "")).strip():
                raise ValueError(f"Generated response has no {field}")
        answer_text = str(value["answer"]).strip()
        if not re.fullmatch(r"\d+", answer_text):
            raise ValueError("AIME answer must be an integer")
        answer = int(answer_text)
        if not 0 <= answer <= 999:
            raise ValueError("AIME answer must be between 0 and 999")
        topic = str(value["topic"]).strip()
        if topic not in AIME_TOPICS:
            raise ValueError(f"Unsupported AIME topic: {topic}")
        return {
            "problem": str(value["problem"]).strip(),
            "answer": str(answer),
            "solution": str(value["solution"]).strip(),
            "topic": topic,
        }

    @staticmethod
    def _repair_json_escapes(text: str) -> str:
        """Double likely LaTeX backslashes before decoding JSON."""
        result: list[str] = []
        index = 0
        while index < len(text):
            char = text[index]
            if char != "\\" or index + 1 >= len(text):
                result.append(char)
                index += 1
                continue
            following = text[index + 1]
            if following in {'"', "\\", "/"}:
                result.extend((char, following))
                index += 2
                continue
            if following == "u" and re.fullmatch(
                r"[0-9a-fA-F]{4}", text[index + 2 : index + 6]
            ):
                result.append(char)
                index += 1
                continue
            after_escape = text[index + 2 : index + 3]
            if following in "bfnrt" and not after_escape.islower():
                result.append(char)
                index += 1
                continue
            result.extend(("\\", "\\"))
            index += 1
        return "".join(result)

    @staticmethod
    def _write_payload(
        path: Path,
        records: list[dict[str, Any]],
        *,
        requested: int,
        failures: list[dict[str, str | int]],
        complete: bool,
    ) -> dict[str, Any]:
        payload = {
            "metadata": {
                "requested": requested,
                "generated": len(records),
                "failed": len(failures),
                "complete": complete,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            },
            "problems": records,
            "failures": failures,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)
        return payload
