# Schema

## Run JSON shape

```json
{
  "summary": {
    "keyword": "异宠",
    "sortMode": "最多点赞",
    "filteredRequestCount": 1,
    "fetchedSearchItems": 3,
    "processed": 3,
    "withComments": 3,
    "withFiveComments": 3
  },
  "results": [
    {
      "ok": true,
      "source": "single",
      "awemeId": "7408543586926464290",
      "url": "https://www.douyin.com/video/7408543586926464290",
      "desc": "10岁小朋友也来开箱爬宠咯...",
      "createTime": 1724935982,
      "authorNickname": "小宇和她的动物朋友们",
      "stats": {
        "diggCount": 4018,
        "commentCount": 170,
        "collectCount": 586,
        "shareCount": 1666
      },
      "publishTime": "2024-08-29 20:53",
      "comments": [
        {
          "text": "蓝舌拉屎巨臭，随时都有可能喷屎，其他还可以",
          "meta": "1年前·天津",
          "likes": "17",
          "replyCount": "1"
        }
      ]
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
- `desc`
- `publishTime`
- `authorNickname`
- `diggCount`
- `commentCount`
- `collectCount`
- `shareCount`
- `capturedCommentCount`
- `hasComments`
- `hasFiveComments`
- `status`
- `error`

### comments.csv

One row per comment.

Recommended columns:
- `contentId`
- `contentUrl`
- `authorNickname`
- `commentIndex`
- `commentText`
- `commentMeta`
- `commentLikes`
- `replyCount`

Use `contentId` as the join key.
