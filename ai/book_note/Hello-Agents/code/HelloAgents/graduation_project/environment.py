"""Development-environment checks for section 16.3 of Hello-Agents."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Callable, Literal, Protocol, Sequence

from .submission import GraduationProjectValidator


EntryMode = Literal["script", "notebook"]
PackageVersionResolver = Callable[[str], str]


@dataclass(frozen=True)
class CommandResult:
    """Sanitized result returned by a command runner."""

    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


class CommandRunner(Protocol):
    """Small command interface that keeps environment checks testable."""

    def run(self, arguments: Sequence[str]) -> CommandResult:
        ...


class SubprocessCommandRunner:
    """Run read-only checks without invoking a shell."""

    def __init__(self, timeout: float = 5.0) -> None:
        self.timeout = timeout

    def run(self, arguments: Sequence[str]) -> CommandResult:
        try:
            completed = subprocess.run(
                list(arguments),
                capture_output=True,
                check=False,
                text=True,
                timeout=self.timeout,
            )
        except FileNotFoundError as error:
            return CommandResult(127, stderr=str(error))
        except subprocess.TimeoutExpired:
            return CommandResult(124, stderr="command timed out")
        except OSError as error:
            return CommandResult(1, stderr=str(error))
        return CommandResult(
            completed.returncode,
            stdout=completed.stdout.strip(),
            stderr=completed.stderr.strip(),
        )


@dataclass(frozen=True)
class EnvironmentCheck:
    """One required or recommended setup condition."""

    code: str
    description: str
    required: bool
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DevelopmentEnvironmentReport:
    """Aggregated environment, repository and project readiness."""

    repository_root: str
    project_root: str
    entry_mode: EntryMode
    checks: tuple[EnvironmentCheck, ...]

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

    def get_check(self, code: str) -> EnvironmentCheck:
        for check in self.checks:
            if check.code == code:
                return check
        raise KeyError(code)

    def to_dict(self) -> dict[str, object]:
        passed, total = self.required_progress
        return {
            "repository_root": self.repository_root,
            "project_root": self.project_root,
            "entry_mode": self.entry_mode,
            "ready": self.ready,
            "required_passed": passed,
            "required_total": total,
            "failed_required_codes": list(self.failed_required_codes),
            "checks": [check.to_dict() for check in self.checks],
        }


class DevelopmentEnvironmentChecker:
    """Audit the setup sequence described in section 16.3."""

    def __init__(
        self,
        repository_root: str | Path,
        project_root: str | Path,
        *,
        github_username: str | None = None,
        entry_mode: EntryMode = "script",
        home: str | Path | None = None,
        command_runner: CommandRunner | None = None,
        python_version: tuple[int, int, int] | None = None,
        package_version_resolver: PackageVersionResolver | None = None,
    ) -> None:
        if entry_mode not in {"script", "notebook"}:
            raise ValueError("entry_mode must be 'script' or 'notebook'")
        self.repository_root = Path(repository_root).expanduser().resolve()
        self.project_root = Path(project_root).expanduser().resolve()
        self.github_username = github_username
        self.entry_mode = entry_mode
        self.home = (
            Path(home).expanduser().resolve()
            if home is not None
            else Path.home()
        )
        self.command_runner = command_runner or SubprocessCommandRunner()
        self.python_version = python_version or (
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        )
        self.package_version_resolver = package_version_resolver or version

    def check(self) -> DevelopmentEnvironmentReport:
        checks = (
            self._python_check(),
            self._hello_agents_check(),
            self._git_check(),
            self._git_identity_check("user.name", "git_user_name"),
            self._git_identity_check("user.email", "git_user_email"),
            self._repository_check(),
            self._remote_check("origin", official_upstream=False),
            self._remote_check("upstream", official_upstream=True),
            self._branch_check(),
            self._jupyter_check(),
            self._ssh_public_key_check(),
            self._project_location_check(),
            self._project_contract_check(),
            self._entry_file_check(),
        )
        return DevelopmentEnvironmentReport(
            repository_root=str(self.repository_root),
            project_root=str(self.project_root),
            entry_mode=self.entry_mode,
            checks=checks,
        )

    def _python_check(self) -> EnvironmentCheck:
        version_text = ".".join(str(part) for part in self.python_version)
        passed = self.python_version >= (3, 10, 0)
        return EnvironmentCheck(
            code="python_version",
            description="Python 版本不低于 3.10",
            required=True,
            passed=passed,
            detail=f"Python {version_text}",
        )

    def _hello_agents_check(self) -> EnvironmentCheck:
        try:
            installed_version = self.package_version_resolver("hello-agents")
        except PackageNotFoundError:
            installed_version = ""
        except Exception:
            installed_version = ""
        return EnvironmentCheck(
            code="hello_agents_package",
            description="安装 hello-agents[all]",
            required=True,
            passed=bool(installed_version),
            detail=(
                f"已安装 hello-agents {installed_version}"
                if installed_version
                else "未找到 hello-agents 发行包"
            ),
        )

    def _git_check(self) -> EnvironmentCheck:
        result = self.command_runner.run(("git", "--version"))
        version_text = result.stdout if result.succeeded else "未找到 Git"
        return EnvironmentCheck(
            code="git",
            description="Git 命令可用",
            required=True,
            passed=result.succeeded and bool(result.stdout),
            detail=version_text,
        )

    def _git_identity_check(
        self,
        key: str,
        code: str,
    ) -> EnvironmentCheck:
        result = self.command_runner.run(
            ("git", "config", "--global", "--get", key)
        )
        passed = result.succeeded and bool(result.stdout.strip())
        return EnvironmentCheck(
            code=code,
            description=f"Git 全局 {key} 已配置",
            required=True,
            passed=passed,
            detail=f"{key} 已设置" if passed else f"{key} 未设置",
        )

    def _repository_command(self, *arguments: str) -> CommandResult:
        return self.command_runner.run(
            ("git", "-C", str(self.repository_root), *arguments)
        )

    def _repository_check(self) -> EnvironmentCheck:
        result = self._repository_command("rev-parse", "--show-toplevel")
        if result.succeeded and result.stdout:
            detected_root = Path(result.stdout).expanduser().resolve()
            passed = detected_root == self.repository_root
        else:
            passed = False
        return EnvironmentCheck(
            code="repository",
            description="目标目录是 Hello-Agents Git 仓库根目录",
            required=True,
            passed=passed,
            detail="Git 仓库根目录有效" if passed else "目录不是目标仓库根目录",
        )

    def _remote_check(
        self,
        remote_name: str,
        *,
        official_upstream: bool,
    ) -> EnvironmentCheck:
        result = self._repository_command(
            "remote",
            "get-url",
            remote_name,
        )
        url = result.stdout.strip()
        passed = result.succeeded and bool(url)
        normalized = (
            url.lower().replace(":", "/").removesuffix(".git").rstrip("/")
        )
        if passed and official_upstream:
            passed = normalized.endswith(
                "github.com/datawhalechina/hello-agents"
            )
        elif passed and self.github_username:
            expected_fork = (
                f"github.com/{self.github_username.lower()}/hello-agents"
            )
            passed = normalized.endswith(expected_fork)
        if passed:
            detail = f"{remote_name} 已配置"
        elif official_upstream:
            detail = "upstream 未指向 datawhalechina/hello-agents"
        elif self.github_username:
            detail = (
                f"origin 未指向 {self.github_username}/hello-agents"
            )
        else:
            detail = f"{remote_name} 未配置"
        return EnvironmentCheck(
            code=f"git_remote_{remote_name}",
            description=f"Git {remote_name} 远程仓库有效",
            required=True,
            passed=passed,
            detail=detail,
        )

    def _branch_check(self) -> EnvironmentCheck:
        result = self._repository_command("branch", "--show-current")
        branch = result.stdout.strip()
        passed = (
            result.succeeded
            and branch.startswith("feature/")
            and len(branch) > len("feature/")
        )
        return EnvironmentCheck(
            code="feature_branch",
            description="当前位于 feature/<项目名称> 开发分支",
            required=True,
            passed=passed,
            detail=branch if passed else "当前分支不符合 feature/* 约定",
        )

    def _jupyter_check(self) -> EnvironmentCheck:
        result = self.command_runner.run(("jupyter", "--version"))
        required = self.entry_mode == "notebook"
        passed = result.succeeded
        return EnvironmentCheck(
            code="jupyter",
            description="Jupyter 命令可用",
            required=required,
            passed=passed,
            detail=(
                "Jupyter 已安装"
                if passed
                else "Notebook 项目需要安装 Jupyter"
                if required
                else "脚本项目可以不安装 Jupyter"
            ),
        )

    def _ssh_public_key_check(self) -> EnvironmentCheck:
        ssh_directory = self.home / ".ssh"
        public_keys = sorted(ssh_directory.glob("id_*.pub"))
        return EnvironmentCheck(
            code="ssh_public_key",
            description="存在用于 GitHub 的 SSH 公钥",
            required=False,
            passed=bool(public_keys),
            detail=(
                f"发现 {len(public_keys)} 个公钥文件"
                if public_keys
                else "未发现 SSH 公钥；也可改用 HTTPS"
            ),
        )

    def _project_location_check(self) -> EnvironmentCheck:
        expected_parent = self.repository_root / "Co-creation-projects"
        passed = (
            self.project_root.is_dir()
            and self.project_root.parent == expected_parent
        )
        return EnvironmentCheck(
            code="project_location",
            description="项目位于 Co-creation-projects 目录",
            required=True,
            passed=passed,
            detail=(
                "项目目录位置正确"
                if passed
                else f"期望位于 {expected_parent}"
            ),
        )

    def _project_contract_check(self) -> EnvironmentCheck:
        report = GraduationProjectValidator(
            self.project_root,
            github_username=self.github_username,
        ).validate()
        return EnvironmentCheck(
            code="project_contract",
            description="项目满足命名与最低交付物契约",
            required=True,
            passed=report.ready,
            detail=(
                "项目交付结构完整"
                if report.ready
                else "缺失：" + ",".join(report.failed_required_codes)
            ),
        )

    def _entry_file_check(self) -> EnvironmentCheck:
        suffix = ".ipynb" if self.entry_mode == "notebook" else ".py"
        entries = sorted(self.project_root.glob(f"*{suffix}"))
        return EnvironmentCheck(
            code="selected_entry_mode",
            description=f"项目包含所选 {self.entry_mode} 入口",
            required=True,
            passed=bool(entries),
            detail=(
                ", ".join(path.name for path in entries)
                if entries
                else f"根目录缺少 {suffix} 文件"
            ),
        )
