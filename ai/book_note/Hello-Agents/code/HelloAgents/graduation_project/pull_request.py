"""Pull-request preparation helpers for section 16.5 of Hello-Agents."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from .development import ManualTestEvidence, ProjectDevelopmentValidator
from .environment import CommandResult, CommandRunner, SubprocessCommandRunner


PROJECT_TYPES = {
    "生产力工具",
    "学习辅助",
    "创意娱乐",
    "数据分析",
    "生活服务",
}
COMMIT_PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|test|chore):\s+\S"
)
PR_TITLE_PATTERN = re.compile(r"^\[毕业设计\]\s+(.+?)\s+-\s+(.+)$")
SAFE_PROJECT_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SENSITIVE_NAMES = {".env", "id_ed25519", "id_rsa"}
SENSITIVE_SUFFIXES = {".key", ".pem"}


@dataclass(frozen=True)
class PullRequestSelfCheck:
    """The five self-check items from the chapter's PR template."""

    code_runs: bool
    readme_complete: bool
    requirements_complete: bool
    usage_example_present: bool
    comments_appropriate: bool

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PullRequestSelfCheck":
        field_names = (
            "code_runs",
            "readme_complete",
            "requirements_complete",
            "usage_example_present",
            "comments_appropriate",
        )
        values: dict[str, bool] = {}
        for field_name in field_names:
            value = data.get(field_name)
            if not isinstance(value, bool):
                raise ValueError(f"self_check.{field_name} must be a boolean")
            values[field_name] = value
        return cls(**values)

    @property
    def passed(self) -> bool:
        return all(asdict(self).values())


@dataclass(frozen=True)
class PullRequestMetadata:
    """Structured form of the section 16.5 pull-request template."""

    title: str
    project_name: str
    author: str
    project_type: str
    description: str
    core_features: tuple[str, ...]
    technical_highlights: tuple[str, ...]
    self_check: PullRequestSelfCheck
    demo_url: str | None = None
    other_notes: str = "无"

    def __post_init__(self) -> None:
        text_fields = {
            "title": self.title,
            "project_name": self.project_name,
            "author": self.author,
            "description": self.description,
        }
        for field_name, value in text_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} cannot be empty")
        if SAFE_PROJECT_PART.fullmatch(self.username) is None:
            raise ValueError("author must contain a valid GitHub username")
        if SAFE_PROJECT_PART.fullmatch(self.project_name.strip()) is None:
            raise ValueError("project_name must be safe for a directory name")
        if self.project_type not in PROJECT_TYPES:
            raise ValueError(f"unsupported project_type: {self.project_type}")
        if not self.core_features or any(
            not isinstance(feature, str) or not feature.strip()
            for feature in self.core_features
        ):
            raise ValueError("core_features must contain non-empty strings")
        if not self.technical_highlights or any(
            not isinstance(highlight, str) or not highlight.strip()
            for highlight in self.technical_highlights
        ):
            raise ValueError(
                "technical_highlights must contain non-empty strings"
            )
        if self.demo_url is not None and not self.demo_url.strip():
            raise ValueError("demo_url cannot be blank")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PullRequestMetadata":
        def required_text(name: str) -> str:
            value = data.get(name)
            if not isinstance(value, str):
                raise ValueError(f"{name} must be a string")
            return value

        def string_list(name: str) -> tuple[str, ...]:
            value = data.get(name)
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                raise ValueError(f"{name} must be a list of strings")
            return tuple(value)

        self_check_data = data.get("self_check")
        if not isinstance(self_check_data, Mapping):
            raise ValueError("self_check must be an object")
        demo_url = data.get("demo_url")
        if demo_url is not None and not isinstance(demo_url, str):
            raise ValueError("demo_url must be a string or null")
        other_notes = data.get("other_notes", "无")
        if not isinstance(other_notes, str):
            raise ValueError("other_notes must be a string")
        return cls(
            title=required_text("title"),
            project_name=required_text("project_name"),
            author=required_text("author"),
            project_type=required_text("project_type"),
            description=required_text("description"),
            core_features=string_list("core_features"),
            technical_highlights=string_list("technical_highlights"),
            self_check=PullRequestSelfCheck.from_dict(self_check_data),
            demo_url=demo_url,
            other_notes=other_notes,
        )

    @property
    def username(self) -> str:
        return self.author.strip().removeprefix("@")

    @property
    def project_directory_name(self) -> str:
        return f"{self.username}-{self.project_name.strip()}"

    def render_markdown(self) -> str:
        feature_lines = "\n".join(
            f"- [x] {feature}" for feature in self.core_features
        )
        highlight_lines = "\n".join(
            f"- {highlight}" for highlight in self.technical_highlights
        )
        demo = self.demo_url or "未提供"
        checklist = (
            ("代码能够正常运行", self.self_check.code_runs),
            ("README 文档完整", self.self_check.readme_complete),
            (
                "requirements.txt 完整",
                self.self_check.requirements_complete,
            ),
            ("有清晰的使用示例", self.self_check.usage_example_present),
            ("代码有适当的注释", self.self_check.comments_appropriate),
        )
        checklist_lines = "\n".join(
            f"- [{'x' if passed else ' '}] {label}"
            for label, passed in checklist
        )
        return (
            "## 项目信息\n\n"
            f"- **项目名称**：{self.project_name}\n"
            f"- **作者**：@{self.username}\n"
            f"- **项目类型**：{self.project_type}\n\n"
            "## 项目简介\n\n"
            f"{self.description.strip()}\n\n"
            "## 核心功能\n\n"
            f"{feature_lines}\n\n"
            "## 技术亮点\n\n"
            f"{highlight_lines}\n\n"
            "## 演示效果\n\n"
            f"{demo}\n\n"
            "## 自检清单\n\n"
            f"{checklist_lines}\n\n"
            "## 其他说明\n\n"
            f"{self.other_notes.strip() or '无'}\n"
        )


@dataclass(frozen=True)
class PullRequestCheck:
    """One local condition required before creating a pull request."""

    code: str
    description: str
    required: bool
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PullRequestReadinessReport:
    """Git, project-quality and PR-description readiness."""

    repository_root: str
    project_root: str
    branch: str
    checks: tuple[PullRequestCheck, ...]

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

    def get_check(self, code: str) -> PullRequestCheck:
        for check in self.checks:
            if check.code == code:
                return check
        raise KeyError(code)

    def to_dict(self) -> dict[str, object]:
        passed, total = self.required_progress
        return {
            "repository_root": self.repository_root,
            "project_root": self.project_root,
            "branch": self.branch,
            "ready": self.ready,
            "required_passed": passed,
            "required_total": total,
            "failed_required_codes": list(self.failed_required_codes),
            "checks": [check.to_dict() for check in self.checks],
        }


class PullRequestReadinessChecker:
    """Perform read-only checks before the user opens a GitHub PR."""

    def __init__(
        self,
        repository_root: str | Path,
        metadata: PullRequestMetadata,
        *,
        evidence: ManualTestEvidence | None = None,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self.repository_root = Path(repository_root).expanduser().resolve()
        self.metadata = metadata
        self.evidence = evidence
        self.command_runner = command_runner or SubprocessCommandRunner()
        self.project_root = (
            self.repository_root
            / "Co-creation-projects"
            / metadata.project_directory_name
        )

    def check(self) -> PullRequestReadinessReport:
        branch_result = self._git("branch", "--show-current")
        branch = branch_result.stdout.strip()
        changed_files = self._changed_files()
        checks = (
            self._project_quality_check(),
            self._feature_branch_check(branch_result, branch),
            self._worktree_check(),
            self._remote_check("origin", official=False),
            self._remote_check("upstream", official=True),
            self._pushed_branch_check(branch),
            self._commits_ahead_check(),
            self._commit_message_check(),
            self._change_scope_check(changed_files),
            self._sensitive_file_check(changed_files),
            self._pr_title_check(),
            self._pr_description_check(),
        )
        return PullRequestReadinessReport(
            repository_root=str(self.repository_root),
            project_root=str(self.project_root),
            branch=branch,
            checks=checks,
        )

    def _git(self, *arguments: str) -> CommandResult:
        return self.command_runner.run(
            ("git", "-C", str(self.repository_root), *arguments)
        )

    def _project_quality_check(self) -> PullRequestCheck:
        report = ProjectDevelopmentValidator(
            self.project_root,
            github_username=self.metadata.username,
            evidence=self.evidence,
        ).validate()
        return PullRequestCheck(
            code="project_quality",
            description="项目通过 16.4 开发质量检查",
            required=True,
            passed=report.ready,
            detail=(
                "项目质量检查通过"
                if report.ready
                else "未通过：" + ",".join(report.failed_required_codes)
            ),
        )

    @staticmethod
    def _feature_branch_check(
        result: CommandResult,
        branch: str,
    ) -> PullRequestCheck:
        passed = (
            result.succeeded
            and branch.startswith("feature/")
            and len(branch) > len("feature/")
        )
        return PullRequestCheck(
            code="feature_branch",
            description="当前位于 feature/<项目名称> 分支",
            required=True,
            passed=passed,
            detail=branch if passed else "当前分支不符合 feature/* 约定",
        )

    def _worktree_check(self) -> PullRequestCheck:
        result = self._git("status", "--porcelain")
        passed = result.succeeded and not result.stdout.strip()
        return PullRequestCheck(
            code="clean_worktree",
            description="工作区修改已检查并提交",
            required=True,
            passed=passed,
            detail="工作区干净" if passed else "仍有未提交或未跟踪文件",
        )

    def _remote_check(
        self,
        remote_name: str,
        *,
        official: bool,
    ) -> PullRequestCheck:
        result = self._git("remote", "get-url", remote_name)
        normalized = self._normalize_remote(result.stdout)
        expected = (
            "github.com/datawhalechina/hello-agents"
            if official
            else f"github.com/{self.metadata.username.lower()}/hello-agents"
        )
        passed = result.succeeded and normalized.endswith(expected)
        return PullRequestCheck(
            code=f"git_remote_{remote_name}",
            description=f"{remote_name} 指向正确的 GitHub 仓库",
            required=True,
            passed=passed,
            detail=(
                f"{remote_name} 配置正确"
                if passed
                else f"{remote_name} 未指向 {expected}"
            ),
        )

    def _pushed_branch_check(self, branch: str) -> PullRequestCheck:
        remote_ref = f"refs/remotes/origin/{branch}" if branch else ""
        result = self._git(
            "show-ref",
            "--verify",
            "--quiet",
            remote_ref,
        )
        passed = bool(branch) and result.succeeded
        return PullRequestCheck(
            code="branch_pushed",
            description="当前功能分支已推送到 origin",
            required=True,
            passed=passed,
            detail=(
                f"origin/{branch} 已存在"
                if passed
                else "请先将功能分支推送到 origin"
            ),
        )

    def _commits_ahead_check(self) -> PullRequestCheck:
        result = self._git("rev-list", "--count", "upstream/main..HEAD")
        try:
            commit_count = int(result.stdout.strip())
        except ValueError:
            commit_count = 0
        passed = result.succeeded and commit_count > 0
        return PullRequestCheck(
            code="commits_ahead",
            description="相对 upstream/main 存在待提交的项目提交",
            required=True,
            passed=passed,
            detail=(
                f"领先 {commit_count} 个提交"
                if passed
                else "未发现相对 upstream/main 的新提交"
            ),
        )

    def _commit_message_check(self) -> PullRequestCheck:
        result = self._git("log", "-1", "--pretty=%s")
        message = result.stdout.strip()
        passed = result.succeeded and COMMIT_PATTERN.match(message) is not None
        return PullRequestCheck(
            code="commit_message",
            description="最新提交使用约定的类型前缀",
            required=True,
            passed=passed,
            detail=(
                message
                if passed
                else "提交信息应使用 feat:、fix: 等前缀"
            ),
        )

    def _changed_files(self) -> tuple[str, ...]:
        result = self._git(
            "diff",
            "--name-only",
            "upstream/main...HEAD",
        )
        if not result.succeeded:
            return ()
        return tuple(
            line.strip() for line in result.stdout.splitlines() if line.strip()
        )

    def _change_scope_check(
        self,
        changed_files: Sequence[str],
    ) -> PullRequestCheck:
        prefix = f"Co-creation-projects/{self.metadata.project_directory_name}/"
        outside = [path for path in changed_files if not path.startswith(prefix)]
        passed = bool(changed_files) and not outside
        if not changed_files:
            detail = "未读取到相对 upstream/main 的变更文件"
        elif outside:
            detail = "包含项目目录外变更：" + ",".join(outside)
        else:
            detail = f"{len(changed_files)} 个文件均位于项目目录"
        return PullRequestCheck(
            code="change_scope",
            description="PR 仅包含当前毕业设计项目文件",
            required=True,
            passed=passed,
            detail=detail,
        )

    def _sensitive_file_check(
        self,
        changed_files: Sequence[str],
    ) -> PullRequestCheck:
        sensitive = [
            path
            for path in changed_files
            if self._is_sensitive_path(path)
        ]
        return PullRequestCheck(
            code="sensitive_files",
            description="PR 不包含 .env、私钥或证书密钥",
            required=True,
            passed=not sensitive,
            detail=(
                "未发现敏感文件"
                if not sensitive
                else "必须移除：" + ",".join(sensitive)
            ),
        )

    def _pr_title_check(self) -> PullRequestCheck:
        match = PR_TITLE_PATTERN.fullmatch(self.metadata.title.strip())
        passed = bool(
            match
            and match.group(1).strip() == self.metadata.project_name.strip()
            and match.group(2).strip()
        )
        return PullRequestCheck(
            code="pr_title",
            description="PR 标题符合 [毕业设计] 项目名称 - 简短描述",
            required=True,
            passed=passed,
            detail=(
                "PR 标题格式正确"
                if passed
                else "PR 标题格式或项目名称不匹配"
            ),
        )

    def _pr_description_check(self) -> PullRequestCheck:
        passed = self.metadata.self_check.passed
        return PullRequestCheck(
            code="pr_description",
            description="PR 描述包含项目信息、功能、亮点和完整自检",
            required=True,
            passed=passed,
            detail=(
                "PR 描述信息完整"
                if passed
                else "PR 自检清单仍有未完成项"
            ),
        )

    @staticmethod
    def _normalize_remote(url: str) -> str:
        return (
            url.strip()
            .lower()
            .replace(":", "/")
            .removesuffix(".git")
            .rstrip("/")
        )

    @staticmethod
    def _is_sensitive_path(path: str) -> bool:
        pure_path = PurePosixPath(path)
        name = pure_path.name.lower()
        environment_file = name == ".env" or (
            name.startswith(".env.") and name != ".env.example"
        )
        return (
            environment_file
            or name in SENSITIVE_NAMES
            or pure_path.suffix.lower() in SENSITIVE_SUFFIXES
        )
