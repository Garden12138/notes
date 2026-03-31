# Interaction stability

## Why coordinates cannot be hard-coded

The successful `最多点赞` click used a runtime-measured bounding box for the option node. That box can change when any of these change:
- browser window size
- viewport size
- browser zoom
- system display scaling
- page layout mode
- language / font rendering differences

Do not treat one captured `(x, y)` point as a permanent constant.

## What to stabilize instead

Stabilize the browser environment first:
- use a fixed visible browser window size
- use a fixed Playwright viewport
- avoid changing zoom
- avoid resizing the browser during the run
- keep layout mode stable

## Recommended pattern

1. Launch the browser with a fixed viewport.
2. Keep the browser window size stable across runs.
3. Open the search page.
4. Trigger the hover dropdown.
5. Find the precise `最多点赞` node dynamically in DOM.
6. Read its current `getBoundingClientRect()`.
7. Click the node center based on that current measurement.

## Why this still matters even with a known node

The stable part is the node identity pattern:

```html
<span data-index1="0" data-index2="2">最多点赞</span>
```

The unstable part is its on-screen position.

So the reusable rule is:
- keep browser layout fixed
- still measure node position at runtime

## Practical recommendation for this skill

Use a consistent viewport such as `1440x900` for all most-liked runs unless there is a strong reason to change it.

If changing viewport is necessary, re-validate the interaction before batch crawling.
