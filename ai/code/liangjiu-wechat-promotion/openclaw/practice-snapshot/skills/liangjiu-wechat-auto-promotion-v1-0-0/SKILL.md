---
name: "liangjiu-wechat-auto-promotion-v1-0-0"
description: "良久微信推广：继承场景一后 WDA 衔接检查"
---

# 良久素材微信综合开团 v1.0.0

Use this skill when the user wants the full verified Liangjiu flow: collect products from `新品首发`, choose 6 products either for a requested category or by automatic safe same-category selection, generate final promotion copy, send it to a target WeChat group, then share each product link individually into that group.

## Dependencies

Before acting, read and follow:

- `liangjiu-new-products-collection-v1-0-0`

If the dependency reports a blocker or incomplete product set, stop and report it before sending anything.

The dependency's scene 1 to scene 2 WDA handoff rule is part of this full workflow. After scene 1 succeeds, require the dependency's WDA status check; when it is ready, continue into scene 2 instead of stopping only because the agent cannot visually inspect the current page.

## Required Inputs

Require these before starting:

- Whether this run is `draft only` or `send now`.
- The target product category is optional. If the user provides one, pass it into the collection/detail skill. If the user does not provide one, use automatic safe same-category selection in the dependency and do not ask for a category before collection.
- The target WeChat group name if it is not the default `<TARGET_WECHAT_GROUP>`.

## Local Environment

Base directory:

`$IPHONE_USE_DIR/scripts`

Scripts used after collection:

- `wechat-iphone-scenario3-v6-send-button-fixed.sh`
- `wechat-iphone-scenario4-v2-share-confirm-send.sh`

Default final promotion file:

`$IPHONE_USE_DIR/scripts/scenario3-final-promotion.txt`

## Safety Boundaries

- Do not send or share anything unless the user explicitly asked in this run.
- Final copy must use verified facts only.
- Do not resend because of partial verification noise.
- Do not manually tap fallback coordinates to replace a failed send/share step that the script already handled or partially handled.
- If a product is missing its link, do not include it in the final send.
- Automatic selection inherits the dependency's exclusion rules: do not select alcohol, health supplements, medical devices, medicine, adult products, or health/medical-claim products unless the user explicitly allows that category in the current run.

## Workflow

### 1. Run the collection/detail skill

Complete `liangjiu-new-products-collection-v1-0-0` first.

- If the user specified a category, the dependency must select 6 verified products from that category.
- If the user did not specify a category, the dependency must report the automatically chosen safe category and the 6 selected product names before detail extraction.
- After scene 1 collection succeeds, the dependency must check WDA/iphone-use status before scene 2. If `ready: true` and the required `status` fields are healthy, treat the handoff as valid and continue scene 2; do not ask for a screenshot merely to inspect the current page.

The next stage requires exactly 6 products with:

- verified title
- verified price
- verified spec
- non-empty `product_link`

## 2. Generate final promotion copy

For each of the 6 products:

- Write one marketing sentence in Chinese, about 40 characters or fewer.
- Base it only on verified title, price, spec, and link.
- Keep the tone natural and sales-oriented, but avoid fake scarcity and unsupported claims.

Then assemble the final text with this structure:

```text
⏰{当前时间}{商品总结}综合开团！

{商品名称1}｜{商品价格1}
{商品营销文案1}

{商品链接1}

{商品名称2}｜{商品价格2}
{商品营销文案2}

{商品链接2}

... 共 6 个商品 ...

[庆祝]大牌正品现货充足，尺码颜色齐全，看中直接报单下单，早拍早发货！[爱心]
```

Rules:

- `当前时间` uses the current local time in `HH:MM`.
- `商品总结` should be a short combined summary, such as `鲜嫩虾仁+韩式拌饭酱`.
- Keep the six products in the selected order.
- Use one product link block per product.
- Do not omit blank lines between product sections.

Write the final text to:

`$IPHONE_USE_DIR/scripts/scenario3-final-promotion.txt`

## 3. Draft-only mode

If the user asked for draft only:

- stop after writing the final promotion file;
- return the selected category, selected products, final copy, and file path;
- do not call scene 3 or scene 4.

## 4. Send the final promotion copy to the target group

Run from the scripts directory:

```bash
./wechat-iphone-scenario3-v6-send-button-fixed.sh send-promotion \
  --group "<TARGET_WECHAT_GROUP>" \
  --message-file "./scenario3-final-promotion.txt"
```

If the target group is different, replace `--group`.

Interpretation rules:

- If the result JSON says `sent: true`, treat the message as already sent.
- If the script exits with code `2`, that still means the send action happened; verification was incomplete, but you must not auto-resend.
- If the script fails before the send action with something like `SEND_BUTTON_NOT_FOUND` or `WRONG_CHAT_BEFORE_SEND`, report the blocker and stop.

## 5. Share each product link into the target group

Only after the final promotion text is finalized should you run:

```bash
./wechat-iphone-scenario4-v2-share-confirm-send.sh share-product-links \
  --promotion-file "./scenario3-final-promotion.txt" \
  --target-group "<TARGET_WECHAT_GROUP>"
```

Optional:

- If the user wants a small test first, add `--max-links 1`.

Interpretation rules:

- The source of truth is the final promotion file.
- The script extracts `#小程序://` links from that file and processes them one by one.
- If any item fails, report partial success from `results.jsonl`; do not manually compensate by random UI clicks.

## Final Report

Return a concise report with:

- requested category, or `自动选品` plus the automatically selected category
- the 6 selected products
- final promotion file path
- whether the run stopped at draft, send, or full share
- scene 3 send result
- scene 4 share result
- any blockers or partial failures
