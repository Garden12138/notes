"""Deterministic offline practice for section 16.5."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence

from graduation_project import (
    CommandResult,
    ManualTestEvidence,
    PullRequestMetadata,
    PullRequestReadinessChecker,
    PullRequestSelfCheck,
)
from examples.graduation_project_development_demo import create_ready_project


class FakeGitRunner:
    """Return fixed local Git results without pushing or using GitHub."""

    def __init__(self, repository: Path, project_directory: str) -> None:
        prefix = ("git", "-C", str(repository))
        branch = "feature/code-review-agent"
        changed = "\n".join(
            f"Co-creation-projects/{project_directory}/{name}"
            for name in (
                ".gitignore",
                "README.md",
                "main.ipynb",
                "requirements.txt",
            )
        )
        self.responses = {
            (*prefix, "branch", "--show-current"): CommandResult(0, branch),
            (*prefix, "status", "--porcelain"): CommandResult(0, ""),
            (*prefix, "remote", "get-url", "origin"): CommandResult(
                0,
                "git@github.com:demo-user/hello-agents.git",
            ),
            (*prefix, "remote", "get-url", "upstream"): CommandResult(
                0,
                "https://github.com/datawhalechina/hello-agents.git",
            ),
            (
                *prefix,
                "show-ref",
                "--verify",
                "--quiet",
                f"refs/remotes/origin/{branch}",
            ): CommandResult(0),
            (
                *prefix,
                "rev-list",
                "--count",
                "upstream/main..HEAD",
            ): CommandResult(0, "1"),
            (*prefix, "log", "-1", "--pretty=%s"): CommandResult(
                0,
                "feat: 添加 CodeReviewAgent 毕业设计项目",
            ),
            (
                *prefix,
                "diff",
                "--name-only",
                "upstream/main...HEAD",
            ): CommandResult(0, changed),
        }
        self.diff_key = (
            *prefix,
            "diff",
            "--name-only",
            "upstream/main...HEAD",
        )
        self.call_count = 0

    def run(self, arguments: Sequence[str]) -> CommandResult:
        self.call_count += 1
        return self.responses.get(tuple(arguments), CommandResult(1))


def create_metadata() -> PullRequestMetadata:
    return PullRequestMetadata(
        title="[毕业设计] CodeReviewAgent - 智能代码审查助手",
        project_name="CodeReviewAgent",
        author="demo-user",
        project_type="生产力工具",
        description=(
            "CodeReviewAgent 分析 Python 代码结构和常见风格问题，"
            "并生成可追踪的 Markdown 审查报告。"
        ),
        core_features=("代码结构分析", "风格检查", "审查报告生成"),
        technical_highlights=(
            "使用 HelloAgents 工具系统组织检查能力",
            "使用固定样例验证报告结构",
        ),
        self_check=PullRequestSelfCheck(
            code_runs=True,
            readme_complete=True,
            requirements_complete=True,
            usage_example_present=True,
            comments_appropriate=True,
        ),
        demo_url="https://example.com/code-review-agent-demo",
    )


def main() -> None:
    evidence = ManualTestEvidence(True, True, True, True, True)
    metadata = create_metadata()

    with TemporaryDirectory(prefix="hello_agents_pr_") as temporary:
        root = Path(temporary).resolve()
        repository = root / "hello-agents"
        project_parent = repository / "Co-creation-projects"
        project_parent.mkdir(parents=True)
        project = create_ready_project(project_parent)
        runner = FakeGitRunner(repository, project.name)
        checker = PullRequestReadinessChecker(
            repository,
            metadata,
            evidence=evidence,
            command_runner=runner,
        )

        ready_report = checker.check()
        passed, total = ready_report.required_progress
        description = metadata.render_markdown()

        changed = runner.responses[runner.diff_key].stdout
        runner.responses[runner.diff_key] = CommandResult(
            0,
            changed + "\ndocs/chapter16/unrelated.md",
        )
        out_of_scope_report = checker.check()

        print("=== 16.5 Pull Request 就绪检查实践 ===")
        print(f"ready_for_pr: {ready_report.ready}")
        print(f"required_checks: {passed}/{total}")
        print(f"branch: {ready_report.branch}")
        print(
            "change_scope_valid: "
            f"{ready_report.get_check('change_scope').passed}"
        )
        print(
            "sensitive_files_absent: "
            f"{ready_report.get_check('sensitive_files').passed}"
        )
        print(
            "generated_description_sections: "
            f"{description.count('## ')}"
        )
        print(f"out_of_scope_ready: {out_of_scope_report.ready}")
        print(
            "out_of_scope_failed: "
            + ",".join(out_of_scope_report.failed_required_codes)
        )
        print(f"simulated_git_commands: {runner.call_count}")
        print("external_git_commands_executed: 0")
        print("network_calls: 0")
        print("artifacts_location: temporary_directory")


if __name__ == "__main__":
    main()
