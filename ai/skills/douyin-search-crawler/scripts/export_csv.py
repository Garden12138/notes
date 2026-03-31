#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 4:
        print("Usage: export_csv.py <final-json> <contents-csv> <comments-csv>")
        sys.exit(1)

    obj = json.loads(Path(sys.argv[1]).read_text())
    items = obj["items"]
    contents_path = Path(sys.argv[2])
    comments_path = Path(sys.argv[3])

    with contents_path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow([
            'contentId','url','title','desc','publishTime','createTime',
            'authorUid','authorNickname','authorUniqueId','authorSecUid','authorVerified',
            'fans','totalLikes',
            'diggCount','commentCount','collectCount','shareCount','playCount',
            'tags','capturedCommentCount','hasComments','hasFiveComments',
            'isValidVideo','hasStructuredTitle','hasPublishTime','hasAuthorStats','needsReview','status','error'
        ])
        for item in items:
            c = item.get('content', {})
            a = item.get('author', {})
            m = item.get('metrics', {})
            cs = item.get('commentSummary', {})
            q = item.get('quality', {})
            w.writerow([
                item.get('id'), item.get('url'), c.get('title'), c.get('desc'), c.get('publishTime'), c.get('createTime'),
                a.get('uid'), a.get('nickname'), a.get('uniqueId'), a.get('secUid'), a.get('verified'),
                a.get('fans'), a.get('totalLikes'),
                m.get('diggCount'), m.get('commentCount'), m.get('collectCount'), m.get('shareCount'), m.get('playCount'),
                '|'.join(c.get('tags', []) or []), cs.get('capturedCount'), cs.get('hasComments'), cs.get('hasFiveComments'),
                q.get('isValidVideo'), q.get('hasStructuredTitle'), q.get('hasPublishTime'), q.get('hasAuthorStats'), q.get('needsReview'), item.get('status'), item.get('error')
            ])

    with comments_path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['contentId','contentTitle','contentUrl','authorNickname','commentIndex','commentText','commentMeta','commentLikes','replyCount'])
        for item in items:
            for idx, c in enumerate(item.get('comments', []) or [], start=1):
                w.writerow([
                    item.get('id'),
                    (item.get('content') or {}).get('title'),
                    item.get('url'),
                    (item.get('author') or {}).get('nickname'),
                    idx,
                    c.get('text'),
                    c.get('meta'),
                    c.get('likes'),
                    c.get('replyCount')
                ])

    print(contents_path)
    print(comments_path)


if __name__ == '__main__':
    main()
