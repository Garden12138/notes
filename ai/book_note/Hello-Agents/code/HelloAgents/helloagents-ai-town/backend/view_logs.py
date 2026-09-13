"""Read or follow Cyber Town's daily dialogue log."""

from __future__ import annotations

import argparse
import os
import time
from collections import deque
from datetime import date
from pathlib import Path


def read_tail(path: Path, line_count: int = 80) -> list[str]:
    if line_count < 1:
        raise ValueError("line_count 必须大于 0")
    with path.open("r", encoding="utf-8") as stream:
        return list(deque(stream, maxlen=line_count))


def follow(path: Path) -> None:
    with path.open("r", encoding="utf-8") as stream:
        stream.seek(0, os.SEEK_END)
        try:
            while True:
                line = stream.readline()
                if line:
                    print(line, end="", flush=True)
                else:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n已停止日志跟踪。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="查看赛博小镇对话日志")
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="日志日期，格式 YYYY-MM-DD",
    )
    parser.add_argument("--lines", type=int, default=80, help="显示末尾行数")
    parser.add_argument("--follow", action="store_true", help="持续等待新日志")
    parser.add_argument(
        "--log-dir",
        default=os.getenv("LOG_PATH", "./logs"),
        help="日志目录",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        selected_date = date.fromisoformat(args.date).isoformat()
    except ValueError:
        print("日期格式错误，应为 YYYY-MM-DD。")
        return 2
    path = Path(args.log_dir) / f"dialogue_{selected_date}.log"
    if not path.is_file():
        print(f"日志文件不存在：{path}")
        return 1
    for line in read_tail(path, args.lines):
        print(line, end="")
    if args.follow:
        follow(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
