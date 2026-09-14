"""Deterministic offline practice for section 16.4."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from graduation_project import ManualTestEvidence, ProjectDevelopmentValidator


README = """# CodeReviewAgent

> 自动检查代码并生成结构化审查报告。

## 项目简介

项目面向需要快速发现常见代码问题的开发者。

## 核心功能

- 检查代码质量、潜在 Bug、性能和安全问题。

## 技术栈

- HelloAgents

## 快速开始

安装依赖、配置 `.env`，然后运行 `main.ipynb`。

## 使用示例

输入示例代码，输出 Markdown 审查报告。

## 项目亮点

- 结构化输出。

## 性能评估

使用固定样例记录检查结果。

## 未来计划

- [ ] 增加更多语言。

## 贡献指南

欢迎提交 Issue 和 Pull Request。

## 许可证

MIT License

## 作者

demo-user

## 致谢

感谢 Datawhale 和 Hello-Agents 社区。
"""


def markdown_cell(text: str) -> dict[str, object]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [text],
    }


def code_cell(source: str) -> dict[str, object]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [source],
    }


def create_ready_project(root: Path) -> Path:
    project = root / "demo-user-CodeReviewAgent"
    project.mkdir()
    (project / "README.md").write_text(README, encoding="utf-8")
    (project / "requirements.txt").write_text(
        "hello-agents[all]>=0.2.7\npython-dotenv>=1.0.0\n",
        encoding="utf-8",
    )
    (project / ".gitignore").write_text(
        ".env\n__pycache__/\n*.mp4\n*.safetensors\n",
        encoding="utf-8",
    )
    notebook = {
        "cells": [
            markdown_cell("# 项目介绍\nCodeReviewAgent 演示。"),
            markdown_cell("## 环境配置"),
            code_cell("print('environment ready')"),
            markdown_cell("## 工具定义"),
            code_cell("def inspect_code(code):\n    return {'length': len(code)}"),
            markdown_cell("## 智能体构建"),
            code_cell("agent_name = 'CodeReviewAgent'"),
            markdown_cell("## 功能演示"),
            code_cell("print(inspect_code('print(1)'))"),
            markdown_cell("## 性能评估\n使用固定样例检查输出结构。"),
            markdown_cell("## 总结与展望\n当前完成最小开发闭环。"),
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
    evidence = ManualTestEvidence(
        code_runs=True,
        usage_example_verified=True,
        output_matches_expectation=True,
        common_exceptions_handled=True,
        comments_reviewed=True,
    )

    with TemporaryDirectory(prefix="hello_agents_development_") as temporary:
        project = create_ready_project(Path(temporary).resolve())
        validator = ProjectDevelopmentValidator(
            project,
            github_username="demo-user",
            evidence=evidence,
        )
        ready_report = validator.validate()
        passed, total = ready_report.required_progress

        (project / "demo.mp4").write_bytes(b"placeholder")
        video_report = validator.validate()

        print("=== 16.4 项目开发质量检查实践 ===")
        print(f"ready_project: {ready_report.ready}")
        print(f"required_checks: {passed}/{total}")
        print(
            "readme_core_complete: "
            f"{ready_report.get_check('readme_core_sections').passed}"
        )
        print(
            "notebook_core_complete: "
            f"{ready_report.get_check('notebook_core_sections').passed}"
        )
        print(
            "manual_evidence_complete: "
            f"{ready_report.get_check('manual_test_evidence').passed}"
        )
        print(
            "project_size_within_limit: "
            f"{ready_report.get_check('project_size').passed}"
        )
        print(f"video_added_ready: {video_report.ready}")
        print(
            "video_failed: "
            + ",".join(video_report.failed_required_codes)
        )
        print("network_calls: 0")
        print("model_calls: 0")
        print("artifacts_location: temporary_directory")


if __name__ == "__main__":
    main()
