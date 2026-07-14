#!/usr/bin/env python3
"""Select a same-category, low-risk product set from scene-one JSONL."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any


CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "小家电",
        (
            "电热水壶",
            "养生壶",
            "电热水瓶",
            "煮蛋器",
            "电压力锅",
            "电煮锅",
            "厨师机",
            "揉面",
            "电动牙刷",
            "电风扇",
            "循环扇",
        ),
    ),
    (
        "服饰鞋包",
        (
            "上衣",
            "裤",
            "裙",
            "外套",
            "防晒衣",
            "连衣裙",
            "衬衫",
            "鞋",
            "袜",
            "包",
            "帽",
        ),
    ),
    (
        "厨房用品",
        (
            "保鲜盒",
            "保温杯",
            "水杯",
            "茶杯",
            "餐具",
            "砧板",
            "刀具",
            "锅具",
        ),
    ),
    (
        "家居日用",
        (
            "除味盒",
            "香氛",
            "收纳",
            "清洁",
            "抹布",
            "纸巾",
            "床品",
            "凉席",
            "被",
            "枕",
        ),
    ),
    (
        "普通食品",
        (
            "巧克力",
            "饼干",
            "面包",
            "果干",
            "坚果",
            "水果",
            "蟠枣",
            "虾仁",
            "肉",
            "丸",
            "酱",
            "面",
        ),
    ),
]

CATEGORY_ALIASES = {
    "small-appliance": "小家电",
    "apparel": "服饰鞋包",
    "kitchen": "厨房用品",
    "home": "家居日用",
    "food": "普通食品",
}

HIGH_RISK_TERMS = (
    "酒",
    "保健",
    "医疗",
    "器械",
    "医用",
    "药品",
    "中药",
    "处方",
    "理疗",
    "治疗",
    "检测",
    "械字号",
    "血压",
    "血糖",
    "成人用品",
    "避孕",
    "壮阳",
    "减肥",
    "草珊瑚",
    "化橘红",
    "润喉",
)

SPEC_FRAGMENT_PATTERNS = (
    re.compile(r"^\s*(?:规格|款式|颜色|尺码|已选)\s*[:：]"),
    re.compile(r"^\s*(?:高配款|低配款|基础款|标配款)(?:\s|[（(])"),
    re.compile(
        r"^\s*\d+(?:\.\d+)?\s*(?:盒|袋|瓶|个|件|台|组|套|斤|克|g|kg|l|ml)\b",
        re.IGNORECASE,
    ),
    re.compile(r"^\s*[¥￥]\s*\d"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从场景一 products.jsonl 中选择同一低风险品类商品"
    )
    parser.add_argument("--input", required=True, help="场景一 products.jsonl")
    parser.add_argument("--output", required=True, help="每行一个商品名的输出文件")
    parser.add_argument("--report", help="选择报告 JSON；默认 <output>.report.json")
    parser.add_argument("--count", type=int, default=6, help="目标商品数，默认 6")
    parser.add_argument(
        "--category",
        help="指定品类：小家电/服饰鞋包/厨房用品/家居日用/普通食品，或英文别名",
    )
    parser.add_argument(
        "--exclude-file", help="可选；每行一个需要排除的失败商品名"
    )
    parser.add_argument(
        "--exclude-results",
        action="append",
        help="可选；场景二 results.jsonl，可重复传入；排除其中已尝试的商品",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"第 {line_number} 行不是有效 JSON: {error}") from error
            if not isinstance(value, dict):
                raise ValueError(f"第 {line_number} 行必须是 JSON 对象")
            records.append(value)
    return records


def load_exclusions(path: Path | None) -> set[str]:
    if path is None:
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def load_result_exclusions(paths: list[Path]) -> set[str]:
    excluded: set[str] = set()
    for path in paths:
        for _, _, record in load_jsonl_with_source(path):
            title = str(record.get("target_title", "")).strip()
            if title:
                excluded.add(title)
    return excluded


def load_jsonl_with_source(
    path: Path,
) -> list[tuple[str, int, dict[str, Any]]]:
    records: list[tuple[str, int, dict[str, Any]]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} 必须是 JSON 对象")
            records.append((str(path), line_number, value))
    return records


def classify(title: str) -> str | None:
    for category, keywords in CATEGORY_RULES:
        if any(keyword in title for keyword in keywords):
            return category
    return None


def fragment_reason(title: str) -> str | None:
    if len(title.strip()) < 4:
        return "title_too_short"
    for pattern in SPEC_FRAGMENT_PATTERNS:
        if pattern.search(title):
            return "spec_fragment"
    return None


def main() -> int:
    args = parse_args()
    if args.count < 1:
        print(json.dumps({"ok": False, "error": "INVALID_COUNT"}, ensure_ascii=False))
        return 2

    input_path = Path(args.input).expanduser()
    output_path = Path(args.output).expanduser()
    report_path = (
        Path(args.report).expanduser()
        if args.report
        else output_path.with_name(output_path.name + ".report.json")
    )
    exclude_path = Path(args.exclude_file).expanduser() if args.exclude_file else None
    result_exclusion_paths = [
        Path(value).expanduser() for value in (args.exclude_results or [])
    ]

    try:
        records = load_jsonl(input_path)
        exclusions = load_exclusions(exclude_path)
        exclusions.update(load_result_exclusions(result_exclusion_paths))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(
            json.dumps(
                {"ok": False, "error": "INPUT_INVALID", "message": str(error)},
                ensure_ascii=False,
            )
        )
        return 2

    requested_category = CATEGORY_ALIASES.get(args.category, args.category)
    valid_categories = {name for name, _ in CATEGORY_RULES}
    if requested_category and requested_category not in valid_categories:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "UNKNOWN_CATEGORY",
                    "category": requested_category,
                    "allowed": sorted(valid_categories),
                },
                ensure_ascii=False,
            )
        )
        return 2

    categorized: dict[str, list[str]] = OrderedDict(
        (category, []) for category, _ in CATEGORY_RULES
    )
    excluded: list[dict[str, str]] = []
    seen: set[str] = set()

    for record in records:
        title = str(record.get("title", "")).strip()
        if not title or title in seen:
            if title:
                excluded.append({"title": title, "reason": "duplicate"})
            continue
        seen.add(title)

        if title in exclusions:
            excluded.append({"title": title, "reason": "operator_excluded"})
            continue

        reason = fragment_reason(title)
        if reason:
            excluded.append({"title": title, "reason": reason})
            continue

        matched_risk = next((term for term in HIGH_RISK_TERMS if term in title), None)
        if matched_risk:
            excluded.append(
                {"title": title, "reason": f"high_risk_keyword:{matched_risk}"}
            )
            continue

        category = classify(title)
        if category is None:
            excluded.append({"title": title, "reason": "unclassified"})
            continue
        categorized[category].append(title)

    if requested_category:
        selected_category = requested_category
    else:
        selected_category = max(
            categorized,
            key=lambda name: (len(categorized[name]), -list(categorized).index(name)),
        )

    selected = categorized[selected_category][: args.count]
    report = {
        "ok": len(selected) == args.count,
        "action": "select-safe-products",
        "source": str(input_path),
        "target_count": args.count,
        "selection_mode": "requested_category" if requested_category else "auto_safe_same_category",
        "selected_category": selected_category,
        "selected_count": len(selected),
        "selected_products": selected,
        "category_counts": {name: len(items) for name, items in categorized.items()},
        "excluded": excluded,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if len(selected) != args.count:
        report["error"] = "SAFE_SAME_CATEGORY_NOT_ENOUGH"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=False))
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(selected) + "\n", encoding="utf-8")
    report["output"] = str(output_path)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
