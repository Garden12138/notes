"""Project-development quality checks for section 16.4 of Hello-Agents."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .submission import GraduationProjectValidator


MAX_PROJECT_BYTES = 5_000_000
LARGE_DATASET_BYTES = 1_000_000
IGNORED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}
VIDEO_SUFFIXES = {".avi", ".mkv", ".mov", ".mp4", ".webm"}
MODEL_SUFFIXES = {
    ".bin",
    ".ckpt",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
}
DATASET_SUFFIXES = {
    ".csv",
    ".gz",
    ".json",
    ".jsonl",
    ".parquet",
    ".tar",
    ".zip",
}
README_CORE_SECTIONS = {
    "project_intro": ("项目简介", "项目介绍"),
    "core_features": ("核心功能",),
    "technology_stack": ("技术栈",),
    "quick_start": ("快速开始",),
    "usage_example": ("使用示例",),
}
README_EXTENDED_SECTIONS = {
    "highlights": ("项目亮点",),
    "evaluation": ("性能评估",),
    "future_work": ("未来计划", "未来改进"),
    "contributing": ("贡献指南",),
    "license": ("许可证",),
    "author": ("作者",),
    "acknowledgements": ("致谢",),
}
NOTEBOOK_CORE_SECTIONS = {
    "project_intro": ("项目介绍", "项目简介"),
    "environment": ("环境配置",),
    "tools": ("工具定义",),
    "agent": ("智能体构建",),
    "demonstration": ("功能演示", "使用示例"),
    "summary": ("总结与展望", "项目总结"),
}


@dataclass(frozen=True)
class ManualTestEvidence:
    """Human-confirmed items that static inspection cannot prove."""

    code_runs: bool
    usage_example_verified: bool
    output_matches_expectation: bool
    common_exceptions_handled: bool
    comments_reviewed: bool

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ManualTestEvidence":
        field_names = (
            "code_runs",
            "usage_example_verified",
            "output_matches_expectation",
            "common_exceptions_handled",
            "comments_reviewed",
        )
        values: dict[str, bool] = {}
        for field_name in field_names:
            value = data.get(field_name)
            if not isinstance(value, bool):
                raise ValueError(f"{field_name} must be a boolean")
            values[field_name] = value
        return cls(**values)

    @property
    def passed(self) -> bool:
        return all(asdict(self).values())

    @property
    def incomplete_items(self) -> tuple[str, ...]:
        return tuple(
            name for name, passed in asdict(self).items() if not passed
        )


@dataclass(frozen=True)
class QualityCheck:
    """One automated or recorded project-development check."""

    code: str
    description: str
    required: bool
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectDevelopmentReport:
    """Combined documentation, structure, evidence and size report."""

    project_root: str
    total_bytes: int
    checks: tuple[QualityCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.passed for check in self.checks if check.required)

    @property
    def required_progress(self) -> tuple[int, int]:
        required = [check for check in self.checks if check.required]
        return sum(check.passed for check in required), len(required)

    @property
    def failed_required_codes(self) -> tuple[str, ...]:
        return tuple(
            check.code
            for check in self.checks
            if check.required and not check.passed
        )

    def get_check(self, code: str) -> QualityCheck:
        for check in self.checks:
            if check.code == code:
                return check
        raise KeyError(code)

    def to_dict(self) -> dict[str, object]:
        passed, total = self.required_progress
        return {
            "project_root": self.project_root,
            "total_bytes": self.total_bytes,
            "ready": self.ready,
            "required_passed": passed,
            "required_total": total,
            "failed_required_codes": list(self.failed_required_codes),
            "checks": [check.to_dict() for check in self.checks],
        }


class ProjectDevelopmentValidator:
    """Apply section 16.4's project-development checklist."""

    def __init__(
        self,
        project_root: str | Path,
        *,
        github_username: str | None = None,
        evidence: ManualTestEvidence | None = None,
        max_project_bytes: int = MAX_PROJECT_BYTES,
        large_dataset_bytes: int = LARGE_DATASET_BYTES,
    ) -> None:
        if max_project_bytes <= 0:
            raise ValueError("max_project_bytes must be positive")
        if large_dataset_bytes <= 0:
            raise ValueError("large_dataset_bytes must be positive")
        self.project_root = Path(project_root).expanduser().resolve()
        self.github_username = github_username
        self.evidence = evidence
        self.max_project_bytes = max_project_bytes
        self.large_dataset_bytes = large_dataset_bytes

    def validate(self) -> ProjectDevelopmentReport:
        files = self._project_files()
        total_bytes = sum(path.stat().st_size for path in files)
        checks = (
            self._minimum_delivery_check(),
            *self._readme_checks(),
            self._requirements_check(),
            *self._notebook_checks(),
            self._manual_evidence_check(),
            self._project_size_check(total_bytes),
            self._prohibited_assets_check(files),
            self._gitignore_check(),
        )
        return ProjectDevelopmentReport(
            project_root=str(self.project_root),
            total_bytes=total_bytes,
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

    def _minimum_delivery_check(self) -> QualityCheck:
        report = GraduationProjectValidator(
            self.project_root,
            github_username=self.github_username,
        ).validate()
        return QualityCheck(
            code="minimum_delivery",
            description="满足毕业设计最低交付契约",
            required=True,
            passed=report.ready,
            detail=(
                "最低交付物完整"
                if report.ready
                else "缺失：" + ",".join(report.failed_required_codes)
            ),
        )

    def _readme_checks(self) -> tuple[QualityCheck, QualityCheck]:
        content = self._read_text(self.project_root / "README.md") or ""
        headings = self._markdown_headings(content)
        missing_core = self._missing_sections(
            headings,
            README_CORE_SECTIONS,
        )
        missing_extended = self._missing_sections(
            headings,
            README_EXTENDED_SECTIONS,
        )
        return (
            QualityCheck(
                code="readme_core_sections",
                description=(
                    "README 覆盖项目简介、功能、技术栈与使用方法"
                ),
                required=True,
                passed=not missing_core,
                detail=(
                    "README 核心章节完整"
                    if not missing_core
                    else "缺少：" + ",".join(missing_core)
                ),
            ),
            QualityCheck(
                code="readme_extended_sections",
                description="README 提供评估、计划、贡献与项目信息",
                required=False,
                passed=not missing_extended,
                detail=(
                    "README 扩展章节完整"
                    if not missing_extended
                    else "可补充：" + ",".join(missing_extended)
                ),
            ),
        )

    def _requirements_check(self) -> QualityCheck:
        content = self._read_text(
            self.project_root / "requirements.txt"
        ) or ""
        entries = [
            line.strip()
            for line in content.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        normalized = [
            re.sub(r"\s+", "", entry.lower()).replace("_", "-")
            for entry in entries
        ]
        passed = any(
            entry.startswith("hello-agents[all]") for entry in normalized
        )
        return QualityCheck(
            code="hello_agents_dependency",
            description="requirements.txt 声明 hello-agents[all]",
            required=True,
            passed=passed,
            detail=(
                f"共声明 {len(entries)} 项依赖"
                if passed
                else "缺少 hello-agents[all] 依赖"
            ),
        )

    def _notebook_checks(self) -> tuple[QualityCheck, QualityCheck]:
        path = self.project_root / "main.ipynb"
        if not path.is_file():
            return (
                QualityCheck(
                    code="notebook_core_sections",
                    description="Notebook 按开发阶段组织内容",
                    required=False,
                    passed=True,
                    detail="项目未使用 main.ipynb，本项不适用",
                ),
                QualityCheck(
                    code="notebook_evaluation_section",
                    description="Notebook 包含可选的性能评估部分",
                    required=False,
                    passed=True,
                    detail="项目未使用 main.ipynb，本项不适用",
                ),
            )

        content = self._read_text(path)
        try:
            document = json.loads(content or "")
        except json.JSONDecodeError:
            document = None
        notebook_text = self._notebook_markdown(document)
        normalized = self._normalize(notebook_text)
        missing = [
            code
            for code, aliases in NOTEBOOK_CORE_SECTIONS.items()
            if not any(self._normalize(alias) in normalized for alias in aliases)
        ]
        has_evaluation = self._normalize("性能评估") in normalized
        return (
            QualityCheck(
                code="notebook_core_sections",
                description="Notebook 按开发阶段组织内容",
                required=True,
                passed=not missing,
                detail=(
                    "Notebook 核心部分完整"
                    if not missing
                    else "缺少：" + ",".join(missing)
                ),
            ),
            QualityCheck(
                code="notebook_evaluation_section",
                description="Notebook 包含可选的性能评估部分",
                required=False,
                passed=has_evaluation,
                detail=(
                    "已提供性能评估部分"
                    if has_evaluation
                    else "未提供性能评估部分"
                ),
            ),
        )

    def _manual_evidence_check(self) -> QualityCheck:
        if self.evidence is None:
            passed = False
            detail = "未提供人工运行与结果确认记录"
        else:
            passed = self.evidence.passed
            detail = (
                "运行、示例、输出、异常和注释均已确认"
                if passed
                else "未确认：" + ",".join(self.evidence.incomplete_items)
            )
        return QualityCheck(
            code="manual_test_evidence",
            description="记录无法由静态检查证明的测试项",
            required=True,
            passed=passed,
            detail=detail,
        )

    def _project_size_check(self, total_bytes: int) -> QualityCheck:
        passed = total_bytes <= self.max_project_bytes
        return QualityCheck(
            code="project_size",
            description="项目总大小不超过 5 MB",
            required=True,
            passed=passed,
            detail=(
                f"{self._format_bytes(total_bytes)} / "
                f"{self._format_bytes(self.max_project_bytes)}"
            ),
        )

    def _prohibited_assets_check(
        self,
        files: list[Path],
    ) -> QualityCheck:
        prohibited: list[str] = []
        for path in files:
            suffix = path.suffix.lower()
            relative = str(path.relative_to(self.project_root))
            if suffix in VIDEO_SUFFIXES or suffix in MODEL_SUFFIXES:
                prohibited.append(relative)
            elif (
                suffix in DATASET_SUFFIXES
                and path.stat().st_size > self.large_dataset_bytes
            ):
                prohibited.append(relative)
        return QualityCheck(
            code="prohibited_assets",
            description="未直接提交视频、模型或大型数据集",
            required=True,
            passed=not prohibited,
            detail=(
                "未发现应外置的大文件"
                if not prohibited
                else "应改为外部链接或示例数据：" + ",".join(prohibited)
            ),
        )

    def _gitignore_check(self) -> QualityCheck:
        content = self._read_text(self.project_root / ".gitignore") or ""
        patterns = {
            line.strip().lower()
            for line in content.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        missing: list[str] = []
        if ".env" not in patterns:
            missing.append(".env")
        if not ({"__pycache__/", "__pycache__"} & patterns):
            missing.append("__pycache__/")
        if not patterns.intersection(
            {"*.bin", "*.ckpt", "*.mp4", "*.pt", "*.safetensors"}
        ):
            missing.append("大文件模式")
        return QualityCheck(
            code="gitignore",
            description=".gitignore 排除密钥、缓存和大文件",
            required=False,
            passed=not missing,
            detail=(
                ".gitignore 包含关键规则"
                if not missing
                else "建议补充：" + ",".join(missing)
            ),
        )

    @classmethod
    def _markdown_headings(cls, content: str) -> tuple[str, ...]:
        return tuple(
            cls._normalize(match.group(1))
            for match in re.finditer(r"^#{2,6}\s+(.+)$", content, re.MULTILINE)
        )

    @classmethod
    def _missing_sections(
        cls,
        headings: tuple[str, ...],
        sections: Mapping[str, tuple[str, ...]],
    ) -> list[str]:
        return [
            code
            for code, aliases in sections.items()
            if not any(
                cls._normalize(alias) in heading
                for alias in aliases
                for heading in headings
            )
        ]

    @classmethod
    def _notebook_markdown(cls, document: object) -> str:
        if not isinstance(document, dict):
            return ""
        cells = document.get("cells")
        if not isinstance(cells, list):
            return ""
        parts: list[str] = []
        for cell in cells:
            if not isinstance(cell, dict) or cell.get("cell_type") != "markdown":
                continue
            source = cell.get("source", "")
            if isinstance(source, str):
                parts.append(source)
            elif isinstance(source, list) and all(
                isinstance(item, str) for item in source
            ):
                parts.append("".join(source))
        return "\n".join(parts)

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(
            character.lower() for character in value if character.isalnum()
        )

    @staticmethod
    def _format_bytes(size: int) -> str:
        if size < 1000:
            return f"{size} B"
        if size < 1_000_000:
            return f"{size / 1000:.1f} kB"
        return f"{size / 1_000_000:.2f} MB"

    @staticmethod
    def _read_text(path: Path) -> str | None:
        if not path.is_file():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return None
