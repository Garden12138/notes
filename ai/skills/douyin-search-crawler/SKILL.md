---
name: douyin-search-crawler
description: Crawl Douyin search results and detail-page comments through a real logged-in browser session. Use when extracting Douyin content lists, aweme IDs, creators, metrics, and top comments for a keyword such as 异宠. Prefer this skill when DOM clicking is unstable and you need to rely on Douyin search APIs discovered from browser traffic, especially `aweme/v1/web/general/search/stream` for first-page results and `aweme/v1/web/general/search/single` for subsequent pages.
---

# Douyin Search Crawler

Use a real logged-in browser profile. Do not rely on anonymous headless browsing for Douyin search work.

## Dependency

This skill depends on the installed `playwright` skill and a working Playwright runtime.

Before using this skill:
- ensure the local `playwright` skill is installed and available
- ensure Playwright can launch a visible browser
- ensure a persistent browser profile exists
- ensure Douyin login can be completed in that profile

Use the `playwright` skill for browser-session setup and browser automation primitives. Use this skill for the Douyin-specific workflow, pagination logic, schema, and exports.

## Core workflow

1. Open Douyin search in a visible browser with a persistent logged-in profile.
2. Capture first-page search results from `aweme/v1/web/general/search/stream`.
3. Capture subsequent pages from `aweme/v1/web/general/search/single`.
4. Extract `aweme_id`, `desc`, author info, and metrics from search responses.
5. Visit `https://www.douyin.com/video/<aweme_id>` for each candidate.
6. Extract publish time, author stats, and up to 5 comments from the detail page.
7. Normalize output into structured JSON, then export CSVs for operators if needed.

## Important findings

- Use a real browser plus login state. Headless access often falls back to Douyin verification pages.
- Do not depend on search-result DOM clicks for ID discovery. Search DOM is unstable and may not expose direct `/video/<id>` links.
- First page is provided by `general/search/stream`.
- Pagination is provided by `general/search/single`.
- In the tested flow:
  - `stream` first page returned 10 unique aweme items for `异宠`.
  - `single?offset=10&count=10` returned 9 unique aweme items.
  - `single?offset=20&count=10` returned 8 unique aweme items.
- `single` responses included `cursor` and `has_more` fields, so continue pagination there instead of trying to paginate `stream`.
- Batch detail crawling must tolerate per-item failures and continue.

## Scripts

Use bundled scripts when they fit the task instead of rewriting the same code:

- `scripts/convert_final_schema.py`
  - Convert tolerant raw results into normalized final JSON schema.
- `scripts/export_csv.py`
  - Export `contents.csv` and `comments.csv` from normalized JSON.
- `scripts/extract_aweme_ids_from_search.py`
  - Read captured search responses and extract aweme candidates.
- `scripts/tolerant_batch_notes.md`
  - Notes for implementing batch detail crawling with per-item fault tolerance.

## Output expectations

Prefer this final shape:

- top-level `meta`
- top-level `items[]`
- per item:
  - `id`
  - `url`
  - `status`
  - `source`
  - `content`
  - `author`
  - `metrics`
  - `comments`
  - `commentSummary`
  - `quality`
  - `error`

## Read references as needed

- Read `references/workflow.md` for the end-to-end collection flow and pagination logic.
- Read `references/schema.md` for the recommended normalized JSON and CSV shapes.
- Read `references/findings.md` for empirically observed behavior from the `异宠` run.

## Guardrails

- Keep requests low-volume and human-paced.
- Prefer visible browser automation over aggressive headless crawling.
- Treat comment extraction as best-effort; some videos may yield zero comments and should be marked, not crash the run.
- For operator delivery, export two CSVs linked by `contentId`:
  - `contents.csv`
  - `comments.csv`
