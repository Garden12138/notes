# Interaction notes

## Reliable trigger pattern

The `筛选` control behaved more like a hover dropdown than a persistent click dropdown.

Observed useful behavior:
- hover over the `筛选` container
- wait briefly
- the dropdown content can appear

## Precise node

Successful identification of the `最多点赞` option used:

```html
<span data-index1="0" data-index2="2">最多点赞</span>
```

## Why this matters

- popup ids may be random
- class names may be unstable
- direct body-wide text search can return ancestors like `<html>` or `<body>`
- using the smallest visible node with stable text and `data-index` attributes is more reliable

## Confirmation target

A successful click must be confirmed at the request layer, not only visually.

Required request markers:
- `is_filter_search=1`
- `filter_selected={"sort_type":"1","publish_time":"0"}`
- `search_source=tab_search`
