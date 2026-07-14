#!/usr/bin/env python3
"""Build fact-only promotion copy from verified scene-two results."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


MINI_LINK_RE = re.compile(r"^#小程序://[^/\s]+/\S+$")
PRICE_RE = re.compile(r"^[¥￥]\s*\d+(?:\.\d+)?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从场景二 results.jsonl 生成只含已验证事实的推广文案"
    )
    parser.add_argument(
        "--results",
        action="append",
        required=True,
        help="场景二 results.jsonl；补跑结果可重复传入",
    )
    parser.add_argument("--output", required=True, help="最终推广文案文件")
    parser.add_argument("--report", help="构建报告 JSON；默认 <output>.report.json")
    parser.add_argument("--expected-count", type=int, default=6, help="默认 6")
    parser.add_argument("--time", help="标题时间 HH:MM；默认当前本地时间")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的输出文件")
    return parser.parse_args()


def load_records(paths: list[Path]) -> list[tuple[str, int, dict[str, Any]]]:
    records: list[tuple[str, int, dict[str, Any]]] = []
    for path in paths:
        with path.open(encoding="utf-8") as file:
            for line_number, line in enumerate(file, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number} 必须是 JSON 对象")
                records.append((str(path), line_number, value))
    return records


def validate_record(record: dict[str, Any]) -> tuple[bool, str]:
    if record.get("ok") is not True:
        return False, str(record.get("error") or "result_not_ok")

    target_title = str(record.get("target_title", "")).strip()
    detail = record.get("detail")
    link_copy = record.get("link_copy")
    if not target_title or not isinstance(detail, dict) or not isinstance(link_copy, dict):
        return False, "required_fields_missing"

    detail_name = str(detail.get("name", "")).strip()
    if detail_name != target_title:
        return False, "detail_title_mismatch"

    price_text = str(detail.get("price_text", "")).strip()
    if not PRICE_RE.fullmatch(price_text):
        return False, "price_not_verified"

    product_link = str(record.get("product_link", "")).strip()
    if (
        not MINI_LINK_RE.fullmatch(product_link)
        or "<" in product_link
        or ">" in product_link
    ):
        return False, "product_link_invalid"

    if link_copy.get("copy_action_verified") is not True:
        return False, "copy_action_not_verified"
    if link_copy.get("status") != "iphone_shortcut_inbox_received":
        return False, "link_not_received_from_iphone_inbox"
    if str(link_copy.get("product_link", "")).strip() != product_link:
        return False, "link_copy_mismatch"
    return True, ""


def main() -> int:
    args = parse_args()
    if args.expected_count < 1:
        print(json.dumps({"ok": False, "error": "INVALID_EXPECTED_COUNT"}))
        return 2

    if args.time and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", args.time):
        print(json.dumps({"ok": False, "error": "INVALID_TIME"}))
        return 2

    result_paths = [Path(value).expanduser() for value in args.results]
    output_path = Path(args.output).expanduser()
    report_path = (
        Path(args.report).expanduser()
        if args.report
        else output_path.with_name(output_path.name + ".report.json")
    )

    if output_path.exists() and not args.force:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "OUTPUT_EXISTS",
                    "output": str(output_path),
                },
                ensure_ascii=False,
            )
        )
        return 2

    try:
        records = load_records(result_paths)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(
            json.dumps(
                {"ok": False, "error": "RESULTS_INVALID", "message": str(error)},
                ensure_ascii=False,
            )
        )
        return 2

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    seen_links: set[str] = set()

    for source, line_number, record in records:
        valid, reason = validate_record(record)
        title = str(record.get("target_title", "")).strip()
        link = str(record.get("product_link", "")).strip()
        if not valid:
            rejected.append(
                {
                    "source": source,
                    "line": line_number,
                    "title": title,
                    "reason": reason,
                }
            )
            continue
        if title in seen_titles:
            rejected.append(
                {
                    "source": source,
                    "line": line_number,
                    "title": title,
                    "reason": "duplicate_title",
                }
            )
            continue
        if link in seen_links:
            rejected.append(
                {
                    "source": source,
                    "line": line_number,
                    "title": title,
                    "reason": "duplicate_link",
                }
            )
            continue
        seen_titles.add(title)
        seen_links.add(link)
        accepted.append(record)

    selected = accepted
    report: dict[str, Any] = {
        "ok": len(selected) == args.expected_count,
        "action": "build-verified-promotion",
        "sources": [str(path) for path in result_paths],
        "expected_count": args.expected_count,
        "verified_count": len(accepted),
        "verified_titles": [item["target_title"] for item in selected],
        "rejected": rejected,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    if len(accepted) != args.expected_count:
        report["error"] = (
            "VERIFIED_PRODUCTS_NOT_ENOUGH"
            if len(accepted) < args.expected_count
            else "VERIFIED_PRODUCTS_TOO_MANY"
        )
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=False))
        return 2

    timestamp = args.time or datetime.now().strftime("%H:%M")
    blocks = [f"⏰{timestamp} 本次新品推荐"]
    for item in selected:
        detail = item["detail"]
        lines = [
            f"{detail['name']}｜{detail['price_text']}",
        ]
        specs = [
            str(value).strip()
            for value in detail.get("specs", [])
            if str(value).strip()
        ]
        if specs:
            lines.append("规格：" + "；".join(specs))
        lines.append(str(item["product_link"]).strip())
        blocks.append("\n".join(lines))

    final_text = "\n\n".join(blocks) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(output_path.name + ".tmp")
    temporary_path.write_text(final_text, encoding="utf-8")
    temporary_path.replace(output_path)

    report.update(
        {
            "output": str(output_path),
            "product_link_count": args.expected_count,
            "spec_missing_count": sum(
                1 for item in selected if not item["detail"].get("specs")
            ),
        }
    )
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
