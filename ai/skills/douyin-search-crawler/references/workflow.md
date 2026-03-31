# Workflow

## 1. Prepare the browser session

- Launch a visible browser with a persistent user data dir.
- Log in to Douyin manually if needed.
- Reuse the same profile for search and detail extraction.

## 2. First-page search capture

Open:
- `https://www.douyin.com/search/<keyword>`

Listen for:
- `aweme/v1/web/general/search/stream`

What to extract from its response:
- `aweme_info.aweme_id`
- `aweme_info.desc`
- `aweme_info.create_time`
- `aweme_info.author`
- `aweme_info.statistics`
- `cursor`
- `has_more`

Observed result for keyword `异宠`:
- first page returned 10 unique aweme IDs when `count=10`

## 3. Pagination capture

Do not continue paginating via `stream`.

Listen for:
- `aweme/v1/web/general/search/single`

Observed request characteristics:
- `offset=10&count=10` returned 9 unique aweme items
- `offset=20&count=10` returned 8 unique aweme items
- response included `cursor` and `has_more`
- request included `search_id`

Recommended approach:
- Treat `search/single` as the true subsequent-page endpoint.
- Preserve the browser session and search context.
- Record the full request template whenever possible.
- Continue page acquisition by following the observed pagination pattern.

## 4. Detail crawling

For each `aweme_id`, open:
- `https://www.douyin.com/video/<aweme_id>`

Extract from detail page text where available:
- detail title
- publish time
- author fan stats
- visible comment snippets

## 5. Comment extraction

Use best-effort extraction.

Recommended behavior:
- wait for DOM content
- wait additional time for comments
- scroll once or twice to expose comment blocks
- parse up to 5 visible comments
- if no comments are found, record empty comments and continue

## 6. Fault tolerance

Batch runs must not abort on one bad item.

Per item:
- wrap detail crawling in try/catch
- record `error`
- move on to the next item

## 7. Final delivery

Produce:
- normalized JSON
- `contents.csv`
- `comments.csv`

Use `contentId` as the join key between content and comment exports.
