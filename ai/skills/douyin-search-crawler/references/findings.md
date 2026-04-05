# Findings from the `异宠` run

## Browser and login behavior

- Anonymous or headless browsing often reached Douyin verification pages.
- A visible browser plus a persistent logged-in profile worked reliably enough for search and detail extraction.

## Search-layer findings

### First page

Observed endpoint:
- `aweme/v1/web/general/search/stream`

Observed first-page behavior:
- request carried `count=10` and `offset=0`
- full response contained 10 unique aweme items for `异宠`
- response contained `cursor: 10` and `has_more: 1`

### Subsequent pages

Observed endpoint:
- `aweme/v1/web/general/search/single`

Observed behavior:
- `offset=10&count=10` returned 9 unique aweme items
- `offset=20&count=10` returned 8 unique aweme items
- `search_id` appeared in the request
- response contained `cursor` and `has_more`

Implication:
- use `stream` for first page
- use `single` for subsequent pages

## Detail-layer findings

- Direct detail URL pattern worked: `https://www.douyin.com/video/<aweme_id>`
- Some detail pages returned complete title, publish time, author stats, and visible comments.
- Some detail pages degraded to generic `抖音-记录美好生活` pages or incomplete metadata.
- Those items should be retained but marked with quality flags for review.

## Batch-run findings

For a tolerant 21-item run:
- fetched search items: 21
- processed detail pages: 21
- failed items: 0
- items with at least 1 comment: 12
- items with 5 comments captured: 4

Implication:
- search pagination worked well enough for batch candidate discovery
- detail comment extraction remained only partially successful
- batch runs must tolerate empty comments and continue

## Delivery findings

Operator-friendly delivery worked best as:
- normalized JSON
- `contents.csv`
- `comments.csv`

Use `contentId` to link comments back to their content rows.
