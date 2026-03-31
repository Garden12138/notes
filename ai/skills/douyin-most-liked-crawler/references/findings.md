# Findings from the verified `异宠` most-liked run

## What was hardest

The hardest part was not pagination or detail crawling. It was reliably switching the search UI into `最多点赞` mode.

## UI behavior findings

- The `筛选` control behaved like a hover dropdown, not a simple persistent click menu.
- Pure click attempts were unreliable.
- Hovering could reveal dropdown content.
- The dropdown could disappear quickly if interaction timing was wrong.
- Random popup ids and class names were not reliable anchors.
- The most useful stable node was the actual `最多点赞` option text plus its `data-index` attributes.

## Request-level confirmation

A successful `最多点赞` switch produced a filtered search request containing:
- `is_filter_search=1`
- `filter_selected={"sort_type":"1","publish_time":"0"}`
- `search_source=tab_search`

## Verified 3-item run

A one-instance verified run for keyword `异宠` under `最多点赞` produced:
- 3 content items
- 3 detail pages processed
- 3 items with comments
- 3 items with 5 comments each
- 15 comments total

Example content ids from that run:
- `7408543586926464290`
- `7616316656944064421`
- `7534325502534847786`

## Practical implication

For high-engagement operator-facing samples, use this skill instead of the default ordering crawler.
