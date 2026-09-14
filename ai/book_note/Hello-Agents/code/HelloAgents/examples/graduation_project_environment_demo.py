"""Deterministic offline practice for section 16.3."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence

from graduation_project import (
    CommandResult,
    DevelopmentEnvironmentChecker,
)


class FakeCommandRunner:
    """Return fixed command results without invoking external programs."""

    def __init__(self, repository: Path) -> None:
        prefix = ("git", "-C", str(repository))
        self.responses = {
            ("git", "--version"): CommandResult(0, "git version 2.46.0"),
            (
                "git",
                "config",
                "--global",
                "--get",
                "user.name",
            ): CommandResult(0, "Demo User"),
            (
                "git",
                "config",
                "--global",
                "--get",
                "user.email",
            ): CommandResult(0, "demo@example.com"),
            (*prefix, "rev-parse", "--show-toplevel"): CommandResult(
                0,
                str(repository),
            ),
            (*prefix, "remote", "get-url", "origin"): CommandResult(
                0,
                "git@github.com:demo-user/hello-agents.git",
            ),
            (*prefix, "remote", "get-url", "upstream"): CommandResult(
                0,
                "https://github.com/datawhalechina/hello-agents.git",
            ),
            (*prefix, "branch", "--show-current"): CommandResult(
                0,
                "feature/code-review-agent",
            ),
            ("jupyter", "--version"): CommandResult(0, "Jupyter core packages"),
        }
        self.call_count = 0

    def run(self, arguments: Sequence[str]) -> CommandResult:
        self.call_count += 1
        return self.responses.get(tuple(arguments), CommandResult(1))


def create_notebook_project(repository: Path) -> Path:
    project = repository / "Co-creation-projects" / "demo-user-CodeReviewAgent"
    project.mkdir(parents=True)
    (project / "README.md").write_text(
        "# CodeReviewAgent\n\n检查代码并生成结构化审查报告。\n",
        encoding="utf-8",
    )
    (project / "requirements.txt").write_text(
        "hello-agents[all]\n",
        encoding="utf-8",
    )
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["print('CodeReviewAgent')"],
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (project / "main.ipynb").write_text(
        json.dumps(notebook, ensure_ascii=False),
        encoding="utf-8",
    )
    return project


def main() -> None:
    with TemporaryDirectory(prefix="hello_agents_environment_") as temporary:
        # macOS may expose /var through the canonical /private/var path.  Resolve
        # once so the fake Git responses use the same path as the checker.
        root = Path(temporary).resolve()
        repository = root / "hello-agents"
        repository.mkdir()
        project = create_notebook_project(repository)
        ssh_directory = root / "home" / ".ssh"
        ssh_directory.mkdir(parents=True)
        (ssh_directory / "id_ed25519.pub").write_text(
            "demo public key placeholder\n",
            encoding="utf-8",
        )

        runner = FakeCommandRunner(repository)
        report = DevelopmentEnvironmentChecker(
            repository_root=repository,
            project_root=project,
            github_username="demo-user",
            entry_mode="notebook",
            home=root / "home",
            command_runner=runner,
            python_version=(3, 12, 1),
            package_version_resolver=lambda _: "0.2.7",
        ).check()

        passed, total = report.required_progress
        print("=== 16.3 开发环境准备自检实践 ===")
        print(f"environment_ready: {report.ready}")
        print(f"required_checks: {passed}/{total}")
        print(
            "python_check: "
            f"{report.get_check('python_version').detail}"
        )
        print(
            "git_branch: "
            f"{report.get_check('feature_branch').detail}"
        )
        print(
            "project_contract_ready: "
            f"{report.get_check('project_contract').passed}"
        )
        print(f"simulated_command_responses: {runner.call_count}")
        print("external_commands_executed: 0")
        print("network_calls: 0")
        print("artifacts_location: temporary_directory")


if __name__ == "__main__":
    main()
