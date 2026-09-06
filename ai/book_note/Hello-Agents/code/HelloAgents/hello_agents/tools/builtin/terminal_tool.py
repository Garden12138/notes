"""Restricted command-line access for just-in-time filesystem context."""

from __future__ import annotations

import glob
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List, Sequence

from ..base import Tool, ToolParameter


ALLOWED_COMMANDS = frozenset(
    {
        "ls",
        "dir",
        "tree",
        "cat",
        "head",
        "tail",
        "less",
        "more",
        "find",
        "grep",
        "egrep",
        "fgrep",
        "wc",
        "sort",
        "uniq",
        "cut",
        "awk",
        "sed",
        "pwd",
        "cd",
        "file",
        "stat",
        "du",
        "df",
        "echo",
        "which",
        "whereis",
    },
)

_GLOB_CHARACTERS = frozenset("*?[")
_FORBIDDEN_FIND_ACTIONS = {
    "-delete",
    "-exec",
    "-execdir",
    "-fls",
    "-follow",
    "-fprint",
    "-fprint0",
    "-fprintf",
    "-ok",
    "-okdir",
}


class TerminalTool(Tool):
    """Execute a small read-only command set inside one workspace."""

    def __init__(
        self,
        workspace: str = ".",
        timeout: float = 30,
        max_output_size: int = 10 * 1024 * 1024,
        allow_cd: bool = True,
        allowed_commands: Iterable[str] | None = None,
    ) -> None:
        super().__init__(
            name="terminal",
            description=(
                "在限定工作目录内执行只读文件系统与文本处理"
                "命令，"
                "支持安全管道和 cd 导航。"
            ),
        )
        root = Path(workspace).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"工作目录不存在：{root}")
        if not root.is_dir():
            raise NotADirectoryError(f"工作目录不是目录：{root}")
        if float(timeout) <= 0:
            raise ValueError("timeout 必须大于 0")
        if int(max_output_size) <= 0:
            raise ValueError("max_output_size 必须大于 0")

        selected = set(
            ALLOWED_COMMANDS
            if allowed_commands is None
            else allowed_commands
        )
        unknown = selected - ALLOWED_COMMANDS
        if unknown:
            raise ValueError(
                "allowed_commands 只能缩小内置白名单，"
                "不允许新增命令："
                f"{sorted(unknown)}",
            )

        self.workspace = root
        self.current_dir = root
        self.timeout = float(timeout)
        self.max_output_size = int(max_output_size)
        self.allow_cd = bool(allow_cd)
        self.allowed_commands = frozenset(selected)
        self._lock = RLock()

    def run(
        self,
        parameters: Dict[str, Any] | str,
        **_: Any,
    ) -> str:
        """Execute one command string or pipeline."""
        command = (
            parameters
            if isinstance(parameters, str)
            else parameters.get("command", "")
        )
        command_text = str(command).strip()
        if not command_text:
            return "❌ command 不能为空"

        try:
            with self._lock:
                pipeline = self._parse_pipeline(command_text)
                if pipeline[0][0] == "cd":
                    if len(pipeline) != 1:
                        raise ValueError("cd 不能放在管道中")
                    return self._handle_cd(pipeline[0])
                if pipeline[0][0] == "pwd" and len(pipeline) == 1:
                    if len(pipeline[0]) != 1:
                        raise ValueError("pwd 不接受额外参数")
                    return str(self.current_dir)
                return self._execute_pipeline(pipeline)
        except ValueError as error:
            return f"❌ {error}"
        except (OSError, RuntimeError) as error:
            return f"❌ 命令执行失败：{error}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="command",
                type="string",
                description=(
                    "在工作目录内执行的只读命令，"
                    "可使用 | 连接白名单命令"
                ),
            ),
        ]

    def _parse_pipeline(self, command: str) -> List[List[str]]:
        """Parse a pipeline without invoking a shell."""
        if len(command) > 8192:
            raise ValueError("命令过长")
        if any(character in command for character in ("\n", "\r", "\0")):
            raise ValueError("命令中不能包含换行或空字符")
        if "`" in command or "$(" in command or "${" in command:
            raise ValueError("不支持命令替换或变量展开")

        try:
            lexer = shlex.shlex(
                command,
                posix=True,
                punctuation_chars="|;&<>",
            )
            lexer.whitespace_split = True
            lexer.commenters = ""
            tokens = list(lexer)
        except ValueError as error:
            raise ValueError(f"命令解析失败：{error}") from error

        if not tokens:
            raise ValueError("command 不能为空")

        pipeline: List[List[str]] = []
        segment: List[str] = []
        for token in tokens:
            if token == "|":
                if not segment:
                    raise ValueError("管道两侧都必须有命令")
                pipeline.append(segment)
                segment = []
            elif token and all(character in "|;&<>" for character in token):
                raise ValueError(f"不支持的控制符：{token}")
            else:
                segment.append(token)
        if not segment:
            raise ValueError("管道末尾缺少命令")
        pipeline.append(segment)

        if len(pipeline) > 8:
            raise ValueError("单次最多允许 8 段管道")
        for arguments in pipeline:
            program = arguments[0]
            if "/" in program or program not in self.allowed_commands:
                allowed = ", ".join(sorted(self.allowed_commands))
                raise ValueError(
                    f"不允许的命令：{program}；允许的命令：{allowed}",
                )
            if program in {"cd", "pwd"} and len(pipeline) > 1:
                raise ValueError(f"{program} 不能放在管道中")
        return pipeline

    def _handle_cd(self, arguments: Sequence[str]) -> str:
        if not self.allow_cd:
            raise ValueError("cd 命令已禁用")
        if len(arguments) == 1:
            return f"当前目录：{self.current_dir}"
        if len(arguments) != 2:
            raise ValueError("cd 只接受一个目录参数")

        target = arguments[1]
        if target == "~":
            destination = self.workspace
        elif target.startswith("~/"):
            destination = self.workspace / target[2:]
        else:
            destination = self.current_dir / target
        destination = destination.resolve()
        self._assert_in_workspace(destination)
        if not destination.exists():
            raise ValueError(f"目录不存在：{destination}")
        if not destination.is_dir():
            raise ValueError(f"不是目录：{destination}")

        self.current_dir = destination
        return f"✅ 切换到目录：{self.current_dir}"

    def _execute_pipeline(self, pipeline: Sequence[Sequence[str]]) -> str:
        deadline = time.monotonic() + self.timeout
        standard_input = b""
        diagnostics: List[str] = []
        final_output = b""
        was_truncated = False

        for raw_arguments in pipeline:
            arguments = self._prepare_arguments(list(raw_arguments))
            executable = shutil.which(arguments[0], path=self._safe_path())
            if executable is None:
                return f"❌ 系统中未找到命令：{arguments[0]}"
            arguments[0] = executable

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return f"❌ 命令执行超时（超过 {self.timeout:g} 秒）"
            try:
                result = subprocess.run(
                    arguments,
                    cwd=str(self.current_dir),
                    input=standard_input,
                    capture_output=True,
                    timeout=remaining,
                    env=self._safe_environment(),
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return f"❌ 命令执行超时（超过 {self.timeout:g} 秒）"
            except OSError as error:
                return f"❌ 命令执行失败：{error}"

            standard_input, truncated = self._truncate_bytes(result.stdout)
            was_truncated = was_truncated or truncated
            final_output = standard_input
            if result.stderr:
                diagnostics.append(
                    f"[{raw_arguments[0]} stderr]\n"
                    f"{self._decode(result.stderr).rstrip()}",
                )
            if result.returncode != 0:
                diagnostics.append(
                    f"[{raw_arguments[0]} 返回码：{result.returncode}]",
                )

        output = self._decode(final_output).rstrip()
        if diagnostics:
            output = "\n\n".join(
                part for part in (output, *diagnostics) if part
            )
        encoded = output.encode("utf-8", errors="replace")
        encoded, final_truncated = self._truncate_bytes(encoded)
        output = self._decode(encoded).rstrip()
        was_truncated = was_truncated or final_truncated
        if was_truncated:
            marker = (
                f"⚠️ 输出被截断（超过 {self.max_output_size} 字节）"
            )
            output = f"{output}\n\n{marker}" if output else marker
        return output or "✅ 命令执行成功（无输出）"

    def _prepare_arguments(self, arguments: List[str]) -> List[str]:
        program = arguments[0]
        self._validate_command_features(program, arguments[1:])

        if program == "find":
            return [program, *self._prepare_find_arguments(arguments[1:])]

        protected = self._protected_argument_indices(program, arguments)
        prepared = [program]
        for index, argument in enumerate(arguments[1:], start=1):
            if index in protected:
                prepared.append(argument)
                continue
            self._validate_option_path(argument)
            if argument.startswith("-"):
                prepared.append(argument)
                continue
            if any(character in argument for character in _GLOB_CHARACTERS):
                prepared.extend(self._expand_glob(argument))
            else:
                self._validate_path_if_needed(argument)
                prepared.append(argument)

        if program == "df" and len(prepared) == 1:
            prepared.append(".")
        return prepared

    def _prepare_find_arguments(self, arguments: List[str]) -> List[str]:
        prepared: List[str] = []
        in_expression = False
        for argument in arguments:
            if not in_expression and (
                argument.startswith("-") or argument in {"!", "("}
            ):
                in_expression = True
            if in_expression:
                self._validate_option_path(argument)
                self._validate_path_if_needed(argument)
                prepared.append(argument)
                continue

            if any(character in argument for character in _GLOB_CHARACTERS):
                prepared.extend(self._expand_glob(argument))
            else:
                self._resolve_path(argument)
                prepared.append(argument)
        return prepared

    def _validate_command_features(
        self,
        program: str,
        arguments: Sequence[str],
    ) -> None:
        if program == "find":
            for argument in arguments:
                name = argument.split("=", 1)[0]
                if name in _FORBIDDEN_FIND_ACTIONS or argument in {"-H", "-L"}:
                    raise ValueError(
                        "find 选项可能写文件、执行命令或越过"
                        f"符号链接：{argument}",
                    )
        elif program == "sort":
            for argument in arguments:
                if (
                    argument == "-o"
                    or argument.startswith("-o")
                    or argument.startswith("--output")
                ):
                    raise ValueError("sort 的输出文件选项已禁用")
                if argument.startswith("--compress-program"):
                    raise ValueError("sort 的外部压缩程序选项已禁用")
        elif program in {"tree", "less"}:
            for argument in arguments:
                if (
                    argument in {"-o", "-O"}
                    or argument.startswith(("-o", "-O"))
                    or argument.startswith(("--output", "--log-file"))
                ):
                    raise ValueError(f"{program} 的输出文件选项已禁用")
            if program == "tree" and "-l" in arguments:
                raise ValueError("tree 的符号链接跟随选项已禁用")
        elif program == "sed":
            if any(
                argument == "-i"
                or argument.startswith("-i")
                or argument.startswith("--in-place")
                for argument in arguments
            ):
                raise ValueError("sed 原地写入选项已禁用")
            self._validate_sed_programs(arguments)
        elif program == "awk":
            self._validate_awk_programs(arguments)
        elif program in {"grep", "egrep", "fgrep"}:
            if any(argument == "-R" for argument in arguments):
                raise ValueError("grep -R 会跟随符号链接，请使用 -r")
            self._validate_attached_file_options(
                arguments,
                short_options={"-f"},
                long_options={"--file", "--exclude-from"},
            )
        elif program == "du":
            if any(
                argument in {"-L", "--dereference"}
                for argument in arguments
            ):
                raise ValueError("du 的符号链接跟随选项已禁用")

        if program in {"sed", "awk"}:
            self._validate_attached_file_options(
                arguments,
                short_options={"-f"},
                long_options={"--file"},
            )

    def _validate_attached_file_options(
        self,
        arguments: Sequence[str],
        short_options: set[str],
        long_options: set[str],
    ) -> None:
        for argument in arguments:
            for option in short_options:
                if argument.startswith(option) and argument != option:
                    self._resolve_path(argument[len(option) :])
            for option in long_options:
                prefix = f"{option}="
                if argument.startswith(prefix):
                    self._resolve_path(argument[len(prefix) :])

    def _validate_sed_programs(self, arguments: Sequence[str]) -> None:
        protected = self._protected_argument_indices(
            "sed",
            ["sed", *arguments],
        )
        full_arguments = ["sed", *arguments]
        for index in protected:
            script = full_arguments[index].strip()
            if script.startswith("--expression="):
                script = script.split("=", 1)[1]
            elif script.startswith("-e") and script != "-e":
                script = script[2:]
            address = r"(?:[0-9$]+|/[^/]*/)?(?:,(?:[0-9$]+|/[^/]*/))?"
            if re.search(
                rf"(^|[;{{}}])\s*{address}\s*[ewr](?:\s|$)",
                script,
            ):
                raise ValueError("sed 的执行、读取和写入命令已禁用")
            if re.search(r"s(.).*\1.*\1[^;]*w\s", script):
                raise ValueError("sed 的写文件标志已禁用")

    def _validate_awk_programs(self, arguments: Sequence[str]) -> None:
        protected = self._protected_argument_indices(
            "awk",
            ["awk", *arguments],
        )
        full_arguments = ["awk", *arguments]
        for index in protected:
            script = full_arguments[index]
            if re.search(r"\b(system|getline)\b", script):
                raise ValueError("awk 的外部命令和文件读取能力已禁用")
            if re.search(r"\b(print|printf)\b[^;{}]*[>|]", script):
                raise ValueError("awk 的输出重定向和外部管道已禁用")

    def _protected_argument_indices(
        self,
        program: str,
        arguments: Sequence[str],
    ) -> set[int]:
        """Return indices that contain patterns or programs, not paths."""
        if program in {"grep", "egrep", "fgrep"}:
            return self._grep_pattern_indices(arguments)
        if program == "sed":
            return self._program_indices(
                arguments,
                expression_flags={"-e", "--expression"},
            )
        if program == "awk":
            return self._program_indices(arguments, expression_flags=set())
        if program == "cut":
            protected: set[int] = set()
            for index, argument in enumerate(arguments[:-1]):
                if argument in {"-b", "-c", "-d", "-f"}:
                    protected.add(index + 1)
            return protected
        return set()

    @staticmethod
    def _grep_pattern_indices(arguments: Sequence[str]) -> set[int]:
        protected: set[int] = set()
        explicit_pattern = False
        option_values = {
            "-A",
            "-B",
            "-C",
            "-m",
            "--after-context",
            "--before-context",
            "--context",
            "--max-count",
        }
        file_values = {"-f", "--file", "--exclude-from"}
        index = 1
        while index < len(arguments):
            argument = arguments[index]
            if argument in {"-e", "--regexp"} and index + 1 < len(arguments):
                protected.add(index + 1)
                explicit_pattern = True
                index += 2
                continue
            if argument.startswith("--regexp="):
                protected.add(index)
                explicit_pattern = True
                index += 1
                continue
            if argument.startswith("-e") and len(argument) > 2:
                protected.add(index)
                explicit_pattern = True
                index += 1
                continue
            if argument in option_values and index + 1 < len(arguments):
                protected.add(index + 1)
                index += 2
                continue
            if argument in file_values and index + 1 < len(arguments):
                explicit_pattern = True
                index += 2
                continue
            if (
                argument.startswith("-f") and len(argument) > 2
            ) or argument.startswith("--file="):
                explicit_pattern = True
                index += 1
                continue
            if argument.startswith("-"):
                index += 1
                continue
            if not explicit_pattern:
                protected.add(index)
                explicit_pattern = True
            index += 1
        return protected

    @staticmethod
    def _program_indices(
        arguments: Sequence[str],
        expression_flags: set[str],
    ) -> set[int]:
        protected: set[int] = set()
        has_expression = False
        index = 1
        while index < len(arguments):
            argument = arguments[index]
            if argument in expression_flags and index + 1 < len(arguments):
                protected.add(index + 1)
                has_expression = True
                index += 2
                continue
            attached_expression = next(
                (
                    flag
                    for flag in expression_flags
                    if argument.startswith(flag) and len(argument) > len(flag)
                ),
                None,
            )
            if attached_expression is not None:
                protected.add(index)
                has_expression = True
                index += 1
                continue
            if argument in {"-f", "--file"} and index + 1 < len(arguments):
                has_expression = True
                index += 2
                continue
            if (
                argument.startswith("-f") and len(argument) > 2
            ) or argument.startswith("--file="):
                has_expression = True
                index += 1
                continue
            if argument.startswith("-"):
                index += 1
                continue
            if not has_expression:
                protected.add(index)
                has_expression = True
            index += 1
        return protected

    def _expand_glob(self, pattern: str) -> List[str]:
        if "**" in pattern:
            raise ValueError("不支持递归 glob，请改用 find")
        self._validate_path_if_needed(pattern)
        absolute_pattern = str(self.current_dir / pattern)
        matches = glob.glob(absolute_pattern)
        if len(matches) > 1000:
            raise ValueError("glob 匹配文件过多，请缩小范围")
        if not matches:
            return [pattern]
        expanded = []
        for match in matches:
            path = Path(match).resolve()
            self._assert_in_workspace(path)
            expanded.append(str(path))
        return expanded

    def _validate_option_path(self, argument: str) -> None:
        if not argument.startswith("-") or "=" not in argument:
            return
        value = argument.split("=", 1)[1]
        if self._looks_unsafe_path(value):
            self._resolve_path(value)

    def _validate_path_if_needed(self, argument: str) -> None:
        candidate = self.current_dir / argument
        if self._looks_unsafe_path(argument) or candidate.exists():
            self._resolve_path(argument)

    def _resolve_path(self, value: str) -> Path:
        if value == "~":
            path = self.workspace
        elif value.startswith("~/"):
            path = self.workspace / value[2:]
        else:
            raw_path = Path(value).expanduser()
            path = raw_path if raw_path.is_absolute() else self.current_dir / raw_path
        path = path.resolve()
        self._assert_in_workspace(path)
        return path

    @staticmethod
    def _looks_unsafe_path(value: str) -> bool:
        path = Path(value).expanduser()
        return (
            path.is_absolute()
            or value in {".", "..", "~"}
            or value.startswith(("./", "../", "~/"))
            or "/" in value
        )

    def _assert_in_workspace(self, path: Path) -> None:
        try:
            path.relative_to(self.workspace)
        except ValueError as error:
            raise ValueError(
                f"不允许访问工作目录外的路径：{path}",
            ) from error

    def _truncate_bytes(self, content: bytes) -> tuple[bytes, bool]:
        if len(content) <= self.max_output_size:
            return content, False
        return content[: self.max_output_size], True

    @staticmethod
    def _decode(content: bytes) -> str:
        return content.decode("utf-8", errors="replace")

    @staticmethod
    def _safe_path() -> str:
        candidates = (
            "/usr/bin",
            "/bin",
            "/usr/sbin",
            "/sbin",
            "/opt/homebrew/bin",
            "/usr/local/bin",
        )
        return os.pathsep.join(path for path in candidates if Path(path).is_dir())

    def _safe_environment(self) -> Dict[str, str]:
        return {
            "HOME": str(self.workspace),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
            "LESSSECURE": "1",
            "PAGER": "cat",
            "PATH": self._safe_path(),
        }
