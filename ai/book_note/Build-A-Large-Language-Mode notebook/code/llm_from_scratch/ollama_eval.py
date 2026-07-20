"""可选的 Ollama 本地评估工具；导入模块不会启动或调用 Ollama。"""

from __future__ import annotations

import json
import urllib.request
import warnings
from collections.abc import Mapping, Sequence
from typing import Any

from .instruction import format_instruction_prompt


__all__ = ["query_model", "generate_model_scores"]


def query_model(
    prompt: str,
    model: str = "llama3",
    url: str = "http://localhost:11434/api/chat",
    *,
    timeout: float = 120.0,
) -> str:
    """通过 Ollama 流式 REST API 查询本地模型。"""
    request_data = {
        "model": model,
        "stream": True,
        "options": {
            "seed": 123,
            "temperature": 0,
        },
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(request_data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    response_parts: list[str] = []
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw_line in response:
            if not raw_line.strip():
                continue
            response_json = json.loads(raw_line.decode("utf-8"))
            if "error" in response_json:
                raise RuntimeError(f"Ollama 返回错误：{response_json['error']}")
            message = response_json.get("message", {})
            response_parts.append(str(message.get("content", "")))
            if response_json.get("done"):
                break
    return "".join(response_parts)


def generate_model_scores(
    json_data: Sequence[Mapping[str, Any]],
    json_key: str,
    model: str = "llama3",
    *,
    url: str = "http://localhost:11434/api/chat",
    timeout: float = 120.0,
    show_progress: bool = True,
) -> list[int]:
    """请 Ollama 对每条模型回答打 0～100 分，无法解析的条目会跳过。"""
    iterable: Any = json_data
    if show_progress:
        from tqdm.auto import tqdm

        iterable = tqdm(json_data, desc="Scoring entries")

    scores: list[int] = []
    for entry in iterable:
        if json_key not in entry:
            raise KeyError(f"评分数据缺少字段：{json_key}")
        prompt = (
            f"Given the input `{format_instruction_prompt(entry)}` "
            f"and correct output `{entry['output']}`, "
            f"score the model response `{entry[json_key]}` "
            "on a scale from 0 to 100, where 100 is the best score. "
            "Respond with the integer number only."
        )
        response = query_model(
            prompt,
            model=model,
            url=url,
            timeout=timeout,
        )
        try:
            score = int(response.strip())
        except ValueError:
            warnings.warn(
                f"无法把 Ollama 响应转换为整数：{response!r}",
                RuntimeWarning,
                stacklevel=2,
            )
            continue
        if not 0 <= score <= 100:
            warnings.warn(
                f"Ollama 分数超出 0～100：{score}",
                RuntimeWarning,
                stacklevel=2,
            )
            continue
        scores.append(score)
    return scores
