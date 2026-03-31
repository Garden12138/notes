---
name: douyin-most-liked-crawler
description: Crawl Douyin search results specifically under the “最多点赞” sort mode through a real logged-in browser session. Use when extracting high-engagement Douyin content, creators, metrics, and top comments for a keyword such as 异宠. Prefer this skill when the workflow must first open the 搜索页筛选 menu, switch 排序依据 to 最多点赞, then collect search pages and detail-page comments.
---

# Douyin Most-Liked Crawler

Use a real logged-in browser profile. Do not rely on anonymous headless browsing for Douyin search work.

## Dependency

This skill depends on the installed `playwright` skill and a working Playwright runtime.

Before using this skill:
- ensure the local `playwright` skill is installed and available
- ensure Playwright can launch a visible browser
- ensure a persistent browser profile exists
- ensure Douyin login can be completed in that profile

Use the `playwright` skill for browser-session setup and browser automation primitives. Use this skill for the Douyin-specific “最多点赞” workflow, sort-switch interaction, pagination logic, schema, and exports.

## Core workflow

1. Open Douyin keyword search in a visible browser with a persistent logged-in profile.
2. Keep the browser window and viewport stable.
3. Hover the `筛选` control to reveal the dropdown.
4. Click the exact `最多点赞` option under `排序依据`.
5. Confirm that search requests switch to filtered mode.
6. Capture first-page results from `aweme/v1/web/general/search/stream`.
7. Capture subsequent pages from `aweme/v1/web/general/search/single`.
8. Extract `aweme_id`, `desc`, author info, and metrics from search responses.
9. Visit `https://www.douyin.com/video/<aweme_id>` for each candidate.
10. Extract publish time, author stats, and up to 5 comments from the detail page.
11. Normalize output into structured JSON, then export operator-friendly CSVs.

## Important findings

- This workflow is different from default search ordering and should live in a separate skill.
- The `筛选` control behaves like a hover dropdown; direct click-only behavior is unreliable.
- A stable way to surface the menu is:
  - locate the `筛选` container
  - move the mouse over it
  - wait for dropdown content to appear
- The precise node for `最多点赞` was identified as:
  - `<span data-index1="0" data-index2="2">最多点赞</span>`
- Successful filtered requests showed:
  - `is_filter_search=1`
  - `filter_selected={"sort_type":"1","publish_time":"0"}`
  - `search_source=tab_search`
- Use one browser instance for “open sort mode” and “collect data”. Do not hand off to a second instance using the same profile during the same run.
- Do not hard-code click coordinates. The stable part is the node identity pattern; the unstable part is its on-screen position.
- Fix the browser layout first, then measure the target node at runtime with `getBoundingClientRect()`.

## Scripts

Use bundled scripts when they fit the task instead of rewriting the same code:

- `scripts/export_csv.py`
  - Export `contents.csv` and `comments.csv` from most-liked run JSON.
- `scripts/two-stage-notes.md`
  - Notes on the one-instance / two-stage orchestration problem and the fix.
- `scripts/interaction-notes.md`
  - Notes on how the `筛选` hover dropdown behaves and how `最多点赞` was identified.

## Output expectations

Prefer this final shape:

- top-level `summary`
- top-level `results[]`
- per result:
  - `awemeId`
  - `url`
  - `desc`
  - `authorNickname`
  - `stats`
  - `publishTime`
  - `comments`
  - `ok`
  - `error`

## Read references as needed

- Read `references/workflow.md` for the end-to-end most-liked workflow.
- Read `references/findings.md` for empirically observed behavior from the verified `异宠` run.
- Read `references/schema.md` for CSV export shape and result structure.
- Read `references/interaction-stability.md` for why window size must stay fixed and why click points must be measured dynamically.

## Guardrails

- Keep requests low-volume and human-paced.
- Prefer visible browser automation over aggressive headless crawling.
- Treat comment extraction as best-effort; some videos may yield zero comments and should be marked, not crash the run.
- For operator delivery, export two CSVs linked by `contentId`:
  - `contents.csv`
  - `comments.csv`
