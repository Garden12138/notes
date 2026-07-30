"""Run synchronous registry tools without blocking the event loop."""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any

from .registry import ToolRegistry


class AsyncToolExecutor:
    """Thread-pool adapter for the synchronous ToolRegistry."""

    def __init__(
        self,
        registry: ToolRegistry,
        max_workers: int = 4,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers 必须大于 0")
        self.registry = registry
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
        )
        self._closed = False

    async def execute_tool_async(
        self,
        tool_name: str,
        input_data: str,
    ) -> str:
        """Execute one synchronous tool in the thread pool."""
        if self._closed:
            raise RuntimeError("AsyncToolExecutor 已关闭")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executor,
            self.registry.execute_tool,
            tool_name,
            input_data,
        )

    async def execute_tools_parallel(
        self,
        tasks: list[dict[str, str]],
    ) -> list[str]:
        """Execute independent tool calls concurrently in input order."""
        for index, task in enumerate(tasks):
            if "tool_name" not in task or "input_data" not in task:
                raise ValueError(
                    f"第 {index + 1} 个任务缺少 tool_name 或 input_data",
                )
        async_tasks = [
            self.execute_tool_async(
                task["tool_name"],
                task["input_data"],
            )
            for task in tasks
        ]
        return list(await asyncio.gather(*async_tasks))

    def close(self, wait: bool = True) -> None:
        """Release worker threads explicitly."""
        if not self._closed:
            self.executor.shutdown(wait=wait)
            self._closed = True

    def __enter__(self) -> "AsyncToolExecutor":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        self.close()

    def __del__(self) -> None:
        executor = getattr(self, "executor", None)
        if executor is not None and not getattr(self, "_closed", True):
            executor.shutdown(wait=False)
