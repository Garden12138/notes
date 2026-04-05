# Workflow

## 1. Prepare browser session

- Launch a visible browser with a persistent user data dir.
- Log in to Douyin manually if needed.
- Reuse the same profile for search and detail extraction.

## 2. Open keyword search

Example:
- `https://www.douyin.com/search/异宠`

## 3. Switch to 最多点赞

This is the key difference from the default crawler.

Observed reliable interaction pattern:
- locate the `筛选` container in the search toolbar
- hover over it
- wait for dropdown content to appear
- identify the precise `最多点赞` option node
- click it

Important: do not rely on random class names or popup ids as stable identifiers.

Observed precise option node during a successful run:

```html
<span data-index1="0" data-index2="2" class="eXMmo3JR">最多点赞</span>
```

The stable parts are:
- text: `最多点赞`
- `data-index1="0"`
- `data-index2="2"`

## 4. Confirm filtered search requests

Success criteria for the most-liked state:
- `is_filter_search=1`
- `filter_selected={"sort_type":"1","publish_time":"0"}`
- `search_source=tab_search`

## 5. Collect search results

First-page endpoint:
- `aweme/v1/web/general/search/stream`

Subsequent-page endpoint:
- `aweme/v1/web/general/search/single`

Filter search hits by the three markers above before extracting candidates.

## 6. Collect detail pages

For each `aweme_id`, open:
- `https://www.douyin.com/video/<aweme_id>`

Extract:
- publish time
- basic author stats
- visible comments, up to 5

## 7. One-instance orchestration

Use one browser instance for the whole run.

Do not:
- switch to most-liked in one browser instance
- then launch a second browser instance with the same profile for collection

Reason:
- Chromium profile locking and state handoff issues
- inconsistent carry-over of filtered UI state

Correct pattern:
- open search
- switch to most-liked
- confirm filtered request
- continue collection in the same page/context

## 8. Delivery

Produce:
- run JSON
- `contents.csv`
- `comments.csv`

Use `contentId` as the join key.
