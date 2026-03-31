#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


def parse_chunked_like_text(text: str):
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError('JSON object bounds not found')
    return json.loads(text[start:end+1])


def extract_from_payload(payload):
    out = []
    seen = set()
    for item in payload.get('data', []):
        aw = item.get('aweme_info') or {}
        aweme_id = aw.get('aweme_id')
        if not aweme_id or aweme_id in seen:
            continue
        seen.add(aweme_id)
        out.append({
            'awemeId': aweme_id,
            'url': f'https://www.douyin.com/video/{aweme_id}',
            'desc': aw.get('desc'),
            'createTime': aw.get('create_time'),
            'authorNickname': (aw.get('author') or {}).get('nickname'),
            'diggCount': (aw.get('statistics') or {}).get('digg_count'),
            'commentCount': (aw.get('statistics') or {}).get('comment_count'),
            'collectCount': (aw.get('statistics') or {}).get('collect_count'),
            'shareCount': (aw.get('statistics') or {}).get('share_count')
        })
    return out


def main():
    if len(sys.argv) < 3:
        print('Usage: extract_aweme_ids_from_search.py <response-body.txt> <output.json>')
        sys.exit(1)
    raw = Path(sys.argv[1]).read_text()
    payload = parse_chunked_like_text(raw)
    out = {
        'cursor': payload.get('cursor'),
        'has_more': payload.get('has_more'),
        'items': extract_from_payload(payload)
    }
    Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(sys.argv[2])


if __name__ == '__main__':
    main()
