#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 4:
        print("Usage: export_csv.py <run-json> <contents-csv> <comments-csv>")
        sys.exit(1)

    obj = json.loads(Path(sys.argv[1]).read_text())
    results = obj['results']
    contents_path = Path(sys.argv[2])
    comments_path = Path(sys.argv[3])

    with contents_path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['contentId','url','desc','publishTime','authorNickname','diggCount','commentCount','collectCount','shareCount','capturedCommentCount','hasComments','hasFiveComments','status','error'])
        for r in results:
            comments = r.get('comments', []) or []
            stats = r.get('stats', {}) or {}
            w.writerow([
                r.get('awemeId'), r.get('url'), r.get('desc'), r.get('publishTime'), r.get('authorNickname'),
                stats.get('diggCount'), stats.get('commentCount'), stats.get('collectCount'), stats.get('shareCount'),
                len(comments), len(comments) > 0, len(comments) >= 5, r.get('ok'), r.get('error')
            ])

    with comments_path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['contentId','contentUrl','authorNickname','commentIndex','commentText','commentMeta','commentLikes','replyCount'])
        for r in results:
            for i, c in enumerate(r.get('comments', []) or [], start=1):
                w.writerow([
                    r.get('awemeId'),
                    r.get('url'),
                    r.get('authorNickname'),
                    i,
                    c.get('text'),
                    c.get('meta'),
                    c.get('likes'),
                    c.get('replyCount')
                ])

    print(contents_path)
    print(comments_path)


if __name__ == '__main__':
    main()
