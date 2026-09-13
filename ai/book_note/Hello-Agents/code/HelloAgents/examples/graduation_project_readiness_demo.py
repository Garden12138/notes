"""Deterministic offline practice for section 16.1."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from graduation_project import GraduationProjectValidator


def create_valid_project(parent: Path) -> Path:
    project = parent / "demo-user-AgentLearningLab"
    project.mkdir()
    (project / "README.md").write_text(
        "# Agent Learning Lab\n\n"
        "把教材内容整理成可追踪的学习任务，并输出复习建议。\n",
        encoding="utf-8",
    )
    (project / "requirements.txt").write_text(
        "hello-agents[all]\n",
        encoding="utf-8",
    )
    (project / "main.py").write_text(
        "def main():\n"
        "    print('Agent Learning Lab')\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )
    return project


def create_incomplete_project(parent: Path) -> Path:
    project = parent / "AgentLearningLab"
    project.mkdir()
    (project / "README.md").write_text(
        "# 尚未完成的项目\n",
        encoding="utf-8",
    )
    return project


def main() -> None:
    with TemporaryDirectory(prefix="hello_agents_graduation_") as temporary:
        root = Path(temporary)
        valid = GraduationProjectValidator(
            create_valid_project(root),
            github_username="demo-user",
        ).validate()
        incomplete = GraduationProjectValidator(
            create_incomplete_project(root),
            github_username="demo-user",
        ).validate()

        passed, total = valid.required_progress
        print("=== 16.1 毕业设计交付自检实践 ===")
        print(f"valid_project_ready: {valid.ready}")
        print(f"required_checks: {passed}/{total}")
        optional_materials = next(
            check
            for check in valid.checks
            if check.code == "optional_materials"
        )
        print(
            "optional_materials_required: "
            f"{optional_materials.required}"
        )
        print(f"incomplete_project_ready: {incomplete.ready}")
        print(
            "incomplete_failed: "
            f"{','.join(incomplete.failed_required_codes)}"
        )
        print("network_calls: 0")
        print("model_calls: 0")
        print("artifacts_location: temporary_directory")


if __name__ == "__main__":
    main()
