"""Validate the minimum graduation-project deliverables from section 16.1."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


IGNORED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}
SAFE_PROJECT_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DEMO_SUFFIXES = {
    ".gif",
    ".jpeg",
    ".jpg",
    ".mp4",
    ".png",
    ".svg",
    ".webm",
}
DATA_SUFFIXES = {".csv", ".json", ".jsonl", ".parquet"}


@dataclass(frozen=True)
class ProjectCheck:
    """One deterministic check in the submission contract."""

    code: str
    description: str
    required: bool
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraduationProjectReport:
    """Complete structural validation result for one project directory."""

    project_root: str
    checks: tuple[ProjectCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.passed for check in self.checks if check.required)

    @property
    def failed_required_codes(self) -> tuple[str, ...]:
        return tuple(
            check.code
            for check in self.checks
            if check.required and not check.passed
        )

    @property
    def required_progress(self) -> tuple[int, int]:
        required = [check for check in self.checks if check.required]
        return sum(check.passed for check in required), len(required)

    def to_dict(self) -> dict[str, Any]:
        passed, total = self.required_progress
        return {
            "project_root": self.project_root,
            "ready": self.ready,
            "required_passed": passed,
            "required_total": total,
            "failed_required_codes": list(self.failed_required_codes),
            "checks": [check.to_dict() for check in self.checks],
        }


class GraduationProjectValidator:
    """Turn section 16.1's open-source deliverables into executable checks."""

    def __init__(
        self,
        project_root: str | Path,
        github_username: str | None = None,
    ) -> None:
        self.project_root = Path(project_root).expanduser()
        self.github_username = (
            github_username.strip() if github_username is not None else None
        )

    def validate(self) -> GraduationProjectReport:
        files = self._project_files()
        python_files = [path for path in files if path.suffix == ".py"]
        notebooks = [path for path in files if path.suffix == ".ipynb"]
        root_entries = [
            path
            for path in files
            if path.parent == self.project_root
            and path.suffix in {".py", ".ipynb"}
        ]

        checks = (
            self._directory_check(),
            self._name_check(),
            self._readme_check(),
            self._requirements_check(),
            ProjectCheck(
                code="runnable_entry",
                description="包含根目录 Python 脚本或 Jupyter Notebook",
                required=True,
                passed=bool(root_entries),
                detail=(
                    ", ".join(path.name for path in root_entries)
                    if root_entries
                    else "未找到根目录 .py 或 .ipynb 入口"
                ),
            ),
            self._python_syntax_check(python_files),
            self._notebook_format_check(notebooks),
            self._dependency_content_check(),
            self._optional_material_check(files),
        )
        return GraduationProjectReport(
            project_root=str(self.project_root.resolve()),
            checks=checks,
        )

    def _project_files(self) -> list[Path]:
        if not self.project_root.is_dir():
            return []
        return sorted(
            path
            for path in self.project_root.rglob("*")
            if path.is_file() and not self._is_ignored(path)
        )

    def _is_ignored(self, path: Path) -> bool:
        relative_parts = path.relative_to(self.project_root).parts[:-1]
        return any(part in IGNORED_DIRECTORIES for part in relative_parts)

    def _directory_check(self) -> ProjectCheck:
        exists = self.project_root.is_dir()
        return ProjectCheck(
            code="project_directory",
            description="项目目录存在",
            required=True,
            passed=exists,
            detail=(
                str(self.project_root.resolve())
                if exists
                else f"目录不存在：{self.project_root}"
            ),
        )

    def _name_check(self) -> ProjectCheck:
        name = self.project_root.name
        username = self.github_username
        if username:
            prefix = f"{username}-"
            project_part = name.removeprefix(prefix)
            passed = (
                name.startswith(prefix)
                and bool(project_part)
                and SAFE_PROJECT_PART.fullmatch(project_part) is not None
            )
            expected = f"{username}-<项目名称>"
        else:
            username_part, separator, project_part = name.partition("-")
            passed = (
                bool(separator)
                and SAFE_PROJECT_PART.fullmatch(username_part) is not None
                and SAFE_PROJECT_PART.fullmatch(project_part) is not None
            )
            expected = "<GitHub用户名>-<项目名称>"
        return ProjectCheck(
            code="project_name",
            description="项目名遵循 GitHub用户名-项目名称",
            required=True,
            passed=passed,
            detail=name if passed else f"当前为 {name!r}，期望 {expected}",
        )

    def _readme_check(self) -> ProjectCheck:
        path = self.project_root / "README.md"
        content = self._read_text(path)
        passed = content is not None and bool(content.strip())
        if not path.is_file():
            detail = "缺少 README.md"
        elif not passed:
            detail = "README.md 为空或无法按 UTF-8 读取"
        elif not any(
            line.lstrip().startswith("#")
            for line in content.splitlines()
        ):
            passed = False
            detail = "README.md 缺少 Markdown 标题"
        else:
            detail = "README.md 存在且包含标题"
        return ProjectCheck(
            code="readme",
            description="提供清晰的 README.md",
            required=True,
            passed=passed,
            detail=detail,
        )

    def _requirements_check(self) -> ProjectCheck:
        path = self.project_root / "requirements.txt"
        exists = path.is_file()
        return ProjectCheck(
            code="requirements_file",
            description="提供 requirements.txt",
            required=True,
            passed=exists,
            detail=(
                "requirements.txt 已存在" if exists else "缺少 requirements.txt"
            ),
        )

    def _python_syntax_check(self, python_files: list[Path]) -> ProjectCheck:
        errors: list[str] = []
        for path in python_files:
            content = self._read_text(path)
            if content is None:
                errors.append(f"{path.name}: 无法按 UTF-8 读取")
                continue
            try:
                compile(content, str(path), "exec")
            except SyntaxError as error:
                errors.append(
                    f"{path.name}:{error.lineno or '?'}: {error.msg}"
                )
        passed = not errors
        return ProjectCheck(
            code="python_syntax",
            description="Python 文件可通过语法编译",
            required=True,
            passed=passed,
            detail=(
                f"检查 {len(python_files)} 个 Python 文件"
                if passed
                else "; ".join(errors)
            ),
        )

    def _notebook_format_check(self, notebooks: list[Path]) -> ProjectCheck:
        errors: list[str] = []
        for path in notebooks:
            content = self._read_text(path)
            if content is None:
                errors.append(f"{path.name}: 无法按 UTF-8 读取")
                continue
            try:
                document = json.loads(content)
            except json.JSONDecodeError as error:
                errors.append(f"{path.name}: JSON 格式错误（{error.msg}）")
                continue
            cells = document.get("cells") if isinstance(document, dict) else None
            if not isinstance(cells, list):
                errors.append(f"{path.name}: 缺少 cells 数组")
                continue
            if not any(
                isinstance(cell, dict) and cell.get("cell_type") == "code"
                for cell in cells
            ):
                errors.append(f"{path.name}: 不包含代码单元")
        passed = not errors
        return ProjectCheck(
            code="notebook_format",
            description="Notebook 是有效 JSON 且包含代码单元",
            required=True,
            passed=passed,
            detail=(
                f"检查 {len(notebooks)} 个 Notebook"
                if passed
                else "; ".join(errors)
            ),
        )

    def _dependency_content_check(self) -> ProjectCheck:
        path = self.project_root / "requirements.txt"
        content = self._read_text(path)
        entries = [] if content is None else [
            line.strip()
            for line in content.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        return ProjectCheck(
            code="dependency_entries",
            description="依赖文件列出第三方依赖",
            required=False,
            passed=bool(entries),
            detail=(
                f"声明 {len(entries)} 项依赖"
                if entries
                else "未声明第三方依赖；若项目仅用标准库可忽略"
            ),
        )

    def _optional_material_check(self, files: list[Path]) -> ProjectCheck:
        demo_files = [
            path for path in files if path.suffix.lower() in DEMO_SUFFIXES
        ]
        data_files = [
            path
            for path in files
            if path.suffix.lower() in DATA_SUFFIXES
            and "data" in {part.lower() for part in path.parts}
        ]
        found = [*demo_files, *data_files]
        return ProjectCheck(
            code="optional_materials",
            description="提供截图、视频或数据集等展示材料",
            required=False,
            passed=bool(found),
            detail=(
                f"发现 {len(found)} 个可选材料"
                if found
                else "未提供可选展示材料"
            ),
        )

    @staticmethod
    def _read_text(path: Path) -> str | None:
        if not path.is_file():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return None
