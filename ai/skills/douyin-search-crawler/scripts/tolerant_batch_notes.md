# Tolerant batch notes

Implement batch detail crawling with per-item fault tolerance.

## Required behavior

- Never let one bad detail page abort the whole batch.
- Wrap each detail-page crawl in its own try/catch.
- Record `ok=false` and an `error` string when a detail page fails.
- Continue to the next item.

## Minimum output per item

- `awemeId`
- `url`
- `ok`
- `error` if failed
- `comments` as an array, even when empty

## Recommended summary fields

- `targetCount`
- `fetchedSearchItems`
- `processed`
- `okCount`
- `failedCount`
- `withComments`
- `withFiveComments`

## Observed batch result from the `异宠` run

- targetCount: 21
- fetchedSearchItems: 21
- processed: 21
- okCount: 21
- failedCount: 0
- withComments: 12
- withFiveComments: 4

Use these numbers as a sanity-check baseline, not a strict guarantee.
