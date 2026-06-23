---
name: "youzan-product-promotion-v1-0-0"
description: "有赞商品管理按名称筛选商品，生成并复制微信小程序推广链接。"
---

# 有赞商品推广链接生成 v1.0.0

Use this skill to generate and extract a WeChat mini program promotion link for one Youzan shop product.

## Inputs

Require a product name or sufficiently unique product-name keyword from the user.

If the user does not provide a product name, ask for it before opening or operating Youzan pages.

## Safety Boundaries

- Use only the user's pre-logged-in browser session.
- Do not handle login, password, captcha, or 2FA; stop and ask the user to complete them.
- Do not edit商品信息, prices, inventory, status, groups, or marketing settings.
- Do not publish external messages or send the copied link to WeChat/groups unless the user separately asks and confirms.
- The intended output is only the copied promotion link.
- If any selector or click target cannot be located confidently, stop and ask the user for a screenshot or pointer instead of guessing destructive actions.

## Browser Setup

- Use OpenClaw browser automation with `--browser-profile user` to attach to the user's logged-in Chrome.
- Start with `status` and `tabs` when browser state is uncertain.
- Reuse an existing Youzan goods-management tab when possible; otherwise open the entry URL in a new tab.
- Snapshot before clicking, and snapshot again after dropdowns, dialogs, and page transitions.

## Entry URL

Open or reuse:

`https://www.youzan.com/v4/goods/manage/list?from=PC-SHARED-NAV#/`

Wait until the商品管理页面 and `商品筛选` area are visible.

## Workflow

1. Locate `商品筛选` search conditions.
2. Enter the provided product name into the product-name/search keyword input.
3. Click `筛选`.
4. Wait for the商品列表 to refresh.
5. In the商品列表, use the first product row returned by the search.
6. In that first row, locate the far-right operation menu `...`.
7. Click `...`.
8. In the dropdown, click `推广`.
9. Wait for the `推广` dialog/window.
10. Locate and click the `微信小程序` menu/tab.
11. In the right side area `推广至微信与朋友圈`, locate `生成链接`.
12. Click `生成链接`.
13. In the `生成链接` dialog, click `确定`.
14. Wait until the original `生成链接` button becomes `复制`.
15. Click `复制`.
16. Extract the copied promotion link and return it to the user.

## Link Extraction

Prefer reliable extraction methods in this order:

1. If the page exposes the generated link in an input, textarea, DOM attribute, or visible text near `复制`, read it directly.
2. After clicking `复制`, read the browser clipboard if the tool/environment supports it.
3. Inspect relevant page DOM around the `推广至微信与朋友圈` section for URLs or mini-program link values.
4. If the UI reports copied successfully but the link cannot be read programmatically, ask the user to paste the clipboard content or provide a screenshot.

When returning the result, include the product name searched and the extracted link.

## Verification

Before final response, verify:

- The searched product name/keyword is the one requested by the user.
- The first result row was used.
- The `推广` window was opened.
- `微信小程序` was the selected menu/tab.
- The `生成链接` flow completed and the button changed to `复制`, or an equivalent copied-success state was observed.
- The returned string is a plausible link or mini-program promotion URL/token from the Youzan page/clipboard.

## Blockers

Stop and ask the user for help if:

- The page is not logged in or asks for captcha/2FA.
- The商品筛选 area, product-name input, or `筛选` button cannot be found.
- The search returns no products.
- The first product row is ambiguous or not visible.
- The row operation `...` cannot be located.
- The dropdown does not contain `推广`.
- The推广 window does not contain `微信小程序`.
- `生成链接`, `确定`, or `复制` cannot be located.
- The browser says the link is copied but automation cannot access the clipboard or DOM link.

When blocked on visual location, ask the user for a screenshot of the current page and describe exactly which control is needed.

## Notes

- The operation menu is row-scoped; do not click `...` for a different product row.
- Some Youzan controls may be icon-only or custom components; use snapshots plus DOM/evaluate inspection, and coordinate clicks only after confirming the target region.
- Avoid blind repeated clicks. After every dropdown/dialog action, inspect visible state before continuing.
