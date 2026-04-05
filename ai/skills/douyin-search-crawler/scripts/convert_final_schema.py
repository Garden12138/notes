#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


def clean_text(s):
    return re.sub(r"\s+", " ", s or "").strip()


def extract_tags(desc):
    if not desc:
        return []
    tags = re.findall(r"#([^#\s]+)", desc)
    out = []
    for t in tags:
        if t and t not in out:
            out.append(t)
    return out


def derive_title(item):
    raw = clean_text(item.get("detailTitle") or item.get("desc") or "")
    if not raw or raw == "抖音-记录美好生活":
        return None
    return raw.split("#")[0].strip() or raw


def normalize_comment_text(text):
    t = clean_text(text)
    t = re.sub(r"^[^\.。…]{1,20}\.\.\.\s*", "", t)
    t = re.sub(r"^[^ ]+\s+\.\.\.\s*", "", t)
    return t.strip()


def build_quality(item, title):
    has_structured_title = bool(title)
    has_publish_time = bool(item.get("publishTime"))
    has_author_stats = bool(item.get("authorStats"))
    is_valid_video = has_structured_title and title != "抖音-记录美好生活"
    needs_review = (not is_valid_video) or (not has_publish_time) or (not has_author_stats)
    return {
        "isValidVideo": is_valid_video,
        "hasStructuredTitle": has_structured_title,
        "hasPublishTime": has_publish_time,
        "hasAuthorStats": has_author_stats,
        "needsReview": needs_review,
    }


def convert(src):
    input_obj = json.loads(Path(src).read_text())
    summary = input_obj["summary"]
    results = input_obj["results"]

    out = {
        "meta": {
            "keyword": summary["keyword"],
            "collectedAt": summary["collectedAt"],
            "targetCount": summary["targetCount"],
            "fetchedCount": summary["fetchedSearchItems"],
            "processedCount": summary["processed"],
            "successCount": summary["okCount"],
            "failedCount": summary["failedCount"],
            "withCommentsCount": summary["withComments"],
            "withFiveCommentsCount": summary["withFiveComments"],
            "pipeline": {
                "searchFirstPage": "aweme/v1/web/general/search/stream",
                "searchPagination": "aweme/v1/web/general/search/single",
                "detailPattern": "https://www.douyin.com/video/<aweme_id>",
            },
        },
        "items": [],
    }

    for item in results:
        title = derive_title(item)
        tags = extract_tags(item.get("desc"))
        comments = [
            {
                "text": normalize_comment_text(c.get("text")),
                "meta": c.get("meta"),
                "likes": c.get("likes"),
                "replyCount": c.get("replyCount"),
            }
            for c in (item.get("comments") or [])
        ]
        out["items"].append(
            {
                "id": item.get("awemeId"),
                "url": item.get("url"),
                "status": "ok" if item.get("ok") else "error",
                "source": {
                    "type": "search_single" if item.get("source") == "single" else (item.get("source") or "unknown"),
                    "keyword": summary["keyword"],
                },
                "content": {
                    "title": title,
                    "desc": item.get("desc"),
                    "publishTime": item.get("publishTime"),
                    "createTime": item.get("createTime"),
                    "tags": tags,
                },
                "author": {
                    "uid": (item.get("author") or {}).get("uid"),
                    "nickname": (item.get("author") or {}).get("nickname"),
                    "uniqueId": (item.get("author") or {}).get("uniqueId"),
                    "secUid": (item.get("author") or {}).get("secUid"),
                    "verified": (item.get("author") or {}).get("verified", False),
                    "fans": (item.get("authorStats") or {}).get("fans"),
                    "totalLikes": (item.get("authorStats") or {}).get("totalLikes"),
                },
                "metrics": {
                    "diggCount": (item.get("stats") or {}).get("diggCount"),
                    "commentCount": (item.get("stats") or {}).get("commentCount"),
                    "collectCount": (item.get("stats") or {}).get("collectCount"),
                    "shareCount": (item.get("stats") or {}).get("shareCount"),
                    "playCount": (item.get("stats") or {}).get("playCount"),
                },
                "comments": comments,
                "commentSummary": {
                    "capturedCount": len(comments),
                    "hasComments": len(comments) > 0,
                    "hasFiveComments": len(comments) >= 5,
                },
                "quality": build_quality(item, title),
                "error": None if item.get("ok") else item.get("error"),
            }
        )
    return out


def main():
    if len(sys.argv) < 3:
        print("Usage: convert_final_schema.py <raw-json> <output-json>")
        sys.exit(1)
    out = convert(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(sys.argv[2])


if __name__ == "__main__":
    main()
