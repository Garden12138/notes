# Schema

## Normalized JSON

```json
{
  "meta": {
    "keyword": "异宠",
    "collectedAt": "2026-03-31T06:03:31.184Z",
    "targetCount": 21,
    "fetchedCount": 21,
    "processedCount": 21,
    "successCount": 21,
    "failedCount": 0,
    "withCommentsCount": 12,
    "withFiveCommentsCount": 4,
    "pipeline": {
      "searchFirstPage": "aweme/v1/web/general/search/stream",
      "searchPagination": "aweme/v1/web/general/search/single",
      "detailPattern": "https://www.douyin.com/video/<aweme_id>"
    }
  },
  "items": [
    {
      "id": "7563815102002318591",
      "url": "https://www.douyin.com/video/7563815102002318591",
      "status": "ok",
      "source": {
        "type": "search_single",
        "keyword": "异宠"
      },
      "content": {
        "title": "蜜袋鼯能够低空滑翔，被称为会飞的小袋鼠",
        "desc": "蜜袋鼯能够低空滑翔，被称为会飞的小袋鼠#动物科普 #蜜袋鼯 #动物解说 #神奇动物在抖音",
        "publishTime": "2025-10-22 07:07",
        "createTime": 1761088054,
        "tags": ["动物科普", "蜜袋鼯", "动物解说", "神奇动物在抖音"]
      },
      "author": {
        "uid": "1665129882058772",
        "nickname": "萌主小世界",
        "uniqueId": null,
        "secUid": "MS4wLjABAAAAJpVKMxaz8yFDNewpIBeacAMUiwAk217LmOjJXpC0QcLvFd2SoV6Zdol3ueBAV75s",
        "verified": false,
        "fans": "2.7万",
        "totalLikes": "147.3万"
      },
      "metrics": {
        "diggCount": 30567,
        "commentCount": 1201,
        "collectCount": 4814,
        "shareCount": 23273,
        "playCount": 0
      },
      "comments": [
        {
          "text": "我养的蜜袋鼯死了",
          "meta": "2周前·广东",
          "likes": "1",
          "replyCount": "2"
        }
      ],
      "commentSummary": {
        "capturedCount": 1,
        "hasComments": true,
        "hasFiveComments": false
      },
      "quality": {
        "isValidVideo": true,
        "hasStructuredTitle": true,
        "hasPublishTime": true,
        "hasAuthorStats": true,
        "needsReview": false
      },
      "error": null
    }
  ]
}
```

## CSV exports

### contents.csv

One row per content item.

Recommended columns:
- `contentId`
- `url`
- `title`
- `desc`
- `publishTime`
- `createTime`
- `authorUid`
- `authorNickname`
- `authorUniqueId`
- `authorSecUid`
- `authorVerified`
- `fans`
- `totalLikes`
- `diggCount`
- `commentCount`
- `collectCount`
- `shareCount`
- `playCount`
- `tags`
- `capturedCommentCount`
- `hasComments`
- `hasFiveComments`
- `isValidVideo`
- `hasStructuredTitle`
- `hasPublishTime`
- `hasAuthorStats`
- `needsReview`
- `status`
- `error`

### comments.csv

One row per comment.

Recommended columns:
- `contentId`
- `contentTitle`
- `contentUrl`
- `authorNickname`
- `commentIndex`
- `commentText`
- `commentMeta`
- `commentLikes`
- `replyCount`

Use `contentId` as the join key.
