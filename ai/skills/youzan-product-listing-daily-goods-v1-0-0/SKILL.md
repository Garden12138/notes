---
name: "youzan-product-listing-daily-goods-v1-0-0"
description: "强化智能生成按钮精确定位、错误面板关闭验证回归流程、价格编辑前的面板关闭验证"
---

# 有赞日用百货选品上架 v1.0.0

Use this skill to list exactly one suitable daily-goods product from 有赞分销市场 into the shop, assign it to `日用百货test`, adjust SKU prices, save, and verify the result.

## Safety Boundaries

- Treat this as a live store operation.
- Continue only when the user has explicitly asked to上架商品 or otherwise clearly confirmed a listing action.
- Stop and ask before any unrelated live changes: bulk edits, deletion,下架, group restructuring, order/payment actions, external WeChat sharing, or changing more than the current product.
- Stop on login, captcha, 2FA, missing permissions, missing `日用百货test`, or unresolved validation errors.
- Never complete a checkout or payment if the page jumps to a cashier or buyer flow; use it only as a preview/verification page.

## Browser Setup

- Use OpenClaw browser automation with the user's existing logged-in Chrome profile: `--browser-profile user`.
- Do not use the old `chrome` / Browser Relay profile.
- Do not create a new browser instance, repeat login, close the user's tabs, or reset browser state.
- Start with browser `status`, `tabs`, then focus/reuse an existing Youzan tab when available.
- Prefer snapshots before actions and re-snapshot after navigation, modal changes, and submits.
- Avoid concurrent browser commands against the same page; focus/open/read should run one at a time if the browser channel is slow.

## Entry

Open or reuse:

`https://www.youzan.com/v4/fenxiao/fxmarket/ranklist`

Target category flow:

1. Choose `15天热销榜`.
2. Choose `日用百货`.
3. Prefer the `getHotGoodsListMore.json` response for the current `日用百货` list. Scan the returned `data` array from `data[0]` in its original response order, skipping only records that are incomplete or have `isAdded === true`, and select the first complete product whose `isAdded` is `false`.
4. Use list-card hover status only as a fallback when the API response is unavailable, incomplete, or cannot be verified.
5. Once a `未添加` product is found by API or fallback hover, start the listing flow immediately; do not keep scanning more products.
6. Skip products requiring a new supplier cooperation flow unless the user explicitly asks.

## Hard Gate: API-First 未添加 Verification

The primary selection source is the current logged-in rank-list API response for `日用百货`, not model visual inference.

Use or observe this endpoint after entering `15天热销榜 > 日用百货`:

`https://www.youzan.com/v4/fenxiao/fxmarket/ranklist/getHotGoodsListMore.json?category=dailySuppliers&scene=2&csrf_token={currentToken}`

Rules:

- Do not hard-code a previous `csrf_token`; use the current page/session token or run a same-origin browser-context request so cookies and token match the active Youzan session.
- Require `code === 0`, `msg` success or equivalent success state, and `data` as an array.
- Treat the `data` array's original order as mandatory. Start at `data[0]` and check each record in ascending index order.
- Do not reorder, pre-filter, or jump ahead by page position, sales, title preference, price, profit rate, category impression, or any other field.
- For each candidate, require `title`, `alias`, `algId`, and boolean `isAdded`.
- `isAdded === false` means the product can be selected as `未添加`.
- `isAdded === true` means the product is already added and must be skipped.
- Use `isAdded` as the primary status field. Do not use `isSeller` alone to decide `未添加` or `已添加`; record `isSeller` and `isFollower` only as audit fields.
- `isFollower` may explain the `已合作供应商` suffix, but it is not the selection gate.
- Select the first response-order product whose fields are complete and whose `isAdded === false`; do not keep scanning after the first valid unadded candidate.
- Record the selected product's `title`, `alias`, `algId`, `isAdded`, `isSeller`, and `isFollower`.
- Build the detail page from the same selected record:

```text
https://www.youzan.com/v4/fenxiao/fxmarket/detail/{alias}?alg={algId}
```

- If `isAdded` is missing, non-boolean, or contradicts visible page state, do not guess. Fall back to the list-card hover gate or stop if the contradiction cannot be resolved safely.
- Do not infer status from product title or selling-point text. Words such as `无添加` on a product image/title are product claims, not listing status.
- Do not use detail-page controls such as `查看分销商品`, `编辑商品`, or `推广商品` as the normal selection gate. The normal gate is API `isAdded`, with list-card hover only as fallback.

If opening a selected API `未添加` product later shows a page or modal that clearly contradicts the API state and only offers already-listed controls, stop that product, return to the list, and choose the next API or hover-verified candidate. Treat that as an exception, not the standard screening method.

## Fallback Gate: List-Card Hover 未添加 Verification

Use hover verification only when the API path is unavailable, incomplete, or unverifiable.

Before listing any fallback product, verify on the current rank-list page:

- Hover the mouse over the product card.
- Read the status badge at the bottom of the card overlay.
- `未添加（已合作供应商）` or a clear `未添加` badge means the product can be selected.
- `已添加（已合作供应商）` or a clear `已添加` badge means the product is already listed and must be skipped.
- If the hover badge cannot be read from DOM text, use a screenshot/visual check of the card while hovered.
- Announce or log the decision per candidate in the form: `第N个商品：列表悬停显示已添加，跳过` or `第N个商品：列表悬停显示未添加，开始上架`.

### Fast Visual Hover Path for Slow Rank Lists

When the rank-list page is slow, do not run broad DOM/evaluate scans, repeated full snapshots, or browser-tool hover calls across many cards. Use a visual coordinate workflow instead:

1. Take one screenshot of the visible rank-list page.
2. From the screenshot, determine the current grid card coordinates and row/column positions.
3. Move the mouse to the candidate card's image or lower image/status area, then wait briefly for the hover overlay.
4. Take a screenshot and read the bottom badge visually.
5. If the badge says `已添加` / `已添加（已合作供应商/供货商）`, skip to the next visible card.
6. If the badge says `未添加` / `未添加（已合作供应商/供货商）`, click that card immediately and continue listing; do not keep scanning.
7. If the page has scrolled or the mouse coordinate appears wrong, re-take a screenshot and recalibrate coordinates before judging the card.

Operational constraints:

- Avoid large `document.querySelectorAll('body *')` / `evaluate` scans on the rank-list page; they can stall the browser gateway.
- Avoid chaining `hover + wait + snapshot` in one command on the rank-list page when the gateway is slow. Prefer one visible screenshot, one mouse move, one screenshot.
- If using OS-level mouse movement, verify the current mouse coordinate after movement or confirm visually that the intended card shows the hover badge.
- Do not treat a screenshot without the hover badge as a product status. It means hover did not trigger or coordinates are wrong; recalibrate and retry that card once.
- Keep the selection loop concise: visible-coordinate hover, screenshot, status decision, next card.

## Listing Flow

1. From the `日用百货` rank-list page, select the first API record in `data[0]`, `data[1]`, `data[2]`... order whose fields are complete and whose `isAdded === false`; if API selection is unavailable, use the hover fallback until one card shows `未添加` / `未添加（已合作供应商）`.
2. Record the selected product name and selection evidence: API `title`, `alias`, `algId`, `isAdded`, `isSeller`, `isFollower`, or fallback hover status.
3. Open the detail page built from `alias` and `algId`, or click the selected card/list-card listing entry point if using fallback hover.
4. Verify the detail page product title matches the selected API/card product; then proceed to the available `上架到店铺` action when present.
5. If the page/modal clearly shows only already-listed controls and no listing action, abort this product and return to the rank-list API or hover selection flow.
6. Click `上架到店铺`.
7. In `商品上架到店铺`, open `选择商品分组`.
8. Select `日用百货test`.
9. Keep the default资质展示 choice unless the user specified otherwise.
10. Click `确定`.
11. Wait for `商品已上架至店铺`.
12. Click `编辑商品`.

### Detail-Page `上架到店铺` Locator

When the selected unlisted product opens a detail page, locate the listing button directly by its visible text. Do not spend time wandering through unrelated DOM or using detail-page status as a screening gate.

Preferred pattern:

```js
const button = [...document.querySelectorAll('button,a,div,span')]
  .find((el) => {
    const text = (el.innerText || el.textContent || '').trim();
    const rect = el.getBoundingClientRect();
    return text === '上架到店铺' && rect.width > 0 && rect.height > 0;
  });

if (button) {
  button.scrollIntoView({ block: 'center', inline: 'center' });
  button.click();
}
```

Operational rule:

- First try a direct visible-text locator for `上架到店铺`.
- If multiple visible matches exist, prefer the real clickable ancestor (`button`/`a`) or the visible element with the largest clickable rect near the action area.
- After clicking, verify the `商品上架到店铺` dialog appears.
- Only if the direct text locator fails should you fall back to screenshot/coordinate inspection.
- Do not repeatedly scan unrelated page sections once the visible `上架到店铺` text is present.

## Edit Product

On the edit page, verify these basics before changing anything:

- Product name matches the selected market product.
- Product group includes `日用百货test`.
- `商品卖点` is present and non-empty, or can be generated.
- `规格明细` is visible and contains expected SKU price inputs.

### 商品卖点

**CRITICAL:** The edit page contains MULTIPLE `智能生成` buttons — one near `商品名称`, one near `商品卖点`, one near `商品图片`, and possibly others. They look similar and are easy to confuse. You MUST click only the `智能生成` that belongs to the `商品卖点` input area.

#### Step A — Locate the Correct 智能生成

Before clicking any `智能生成`, verify you are targeting the correct one:

1. Locate the `商品卖点` label or input field on the page FIRST. If needed, take a screenshot and visually identify where `商品卖点` is.
2. Find the `智能生成` button that is visually NEAR / INSIDE the `商品卖点` field area — NOT the one near `商品名称`, `商品图片`, or any other field.
3. The correct `智能生成` button is typically located directly beside or inside the `商品卖点` input field.
4. When using a DOM-based locator, ALWAYS scope the search to the `商品卖点` section:

```js
// Step 1: Find the 商品卖点 label or form-item
const label = [...document.querySelectorAll('label,div,span')]
  .find(el => {
    const text = (el.textContent || '').trim();
    return text === '商品卖点' && el.getBoundingClientRect().width > 0;
  });

// Step 2: Find the nearest ancestor that wraps the field
const container = label
  ? (label.closest('.form-item') || label.closest('.form-group') || label.closest('[class*="form"]') || label.closest('div[class]'))
  : null;

// Step 3: Find 智能生成 ONLY within that container
if (container) {
  const smartBtn = [...container.querySelectorAll('button,a,span,div')]
    .find(el => (el.textContent || '').trim() === '智能生成');
  if (smartBtn) {
    smartBtn.scrollIntoView({ block: 'center' });
    smartBtn.click();
  }
}
```

#### Step B — Verify the Correct Panel Opened (MANDATORY)

**IMMEDIATELY after clicking 智能生成**, you MUST verify what panel opened. Do NOT skip this step.

1. Take a snapshot or screenshot of the page.
2. Check the panel title text or heading. It **MUST** say `商品卖点创作`.
3. Common wrong panels and their indicators:
   - `商品名称创作` → You clicked the 智能生成 near `商品名称`
   - `商品图片` / `商品主图` / image-related text → You clicked the 智能生成 near `商品图片`
4. **If the panel title says ANYTHING other than `商品卖点创作`, you have opened the WRONG panel. Go immediately to Step E (Recover From Wrong Panel).**
5. Only if the panel title is confirmed as `商品卖点创作`, proceed to Step C.

#### Step C — Generate Selling Point (Only When Correct Panel Is Open)

When the panel title shows `商品卖点创作`:

1. Click `立即生成` in the panel.
2. Wait for the generation result to appear.
3. Choose the first generated selling point and apply it.
4. Verify the `商品卖点` input on the main form now shows the applied text.

#### Step D — Close the Panel With Verification

After applying the卖点, you MUST close the right-side panel before proceeding to price edits. The panel obscures the form and interferes with price input.

1. Locate the close/× button on the right-side文案 panel (usually top-right corner).
2. Click the close button.
3. **MANDATORY VERIFICATION — confirm the panel actually closed:**
   - Take a snapshot or screenshot.
   - Check: Is the right-side panel still visible? Is the `商品卖点` input no longer obscured?
   - Only answer "panel is closed" when you can SEE that the panel is gone from the page.
4. If the panel is still open, try the close button again (max 2 close attempts total).
5. **Only after the panel is visually confirmed closed**, proceed to price edits.

**IMPORTANT:** Saying "closing the panel" or "I should close it" without actually executing the click AND verifying the result is NOT sufficient. The close action is a real step that requires execution + visual confirmation, just like any other step.

#### Step E — Recover From Wrong Panel

If you opened the wrong panel (e.g., `商品名称创作`, `商品图片`, etc.):

1. **Do NOT use any content from the wrong panel.** Discard it entirely.
2. Locate the close/× button at the top-right of the opened assistant panel.
3. Click the close button.
4. **Verify the panel actually closed:**
   - Take a snapshot or screenshot.
   - Confirm visually that the panel is GONE from the page.
   - Confirm the main form is visible and unobscured.
5. If the panel did not close on the first attempt:
   - Try the close button once more (max 2 close attempts total).
   - If it still won't close, stop, take a screenshot, and report the blocker.
6. Once the panel is confirmed closed, go back to Step A and try again — this time being MORE precise about locating the `商品卖点` area's `智能生成`.
7. If you cannot close the panel after 2 attempts, stop and take a screenshot for manual review. Do NOT proceed to price edits.

**Rule:** Every regression/correction step (closing the wrong panel) is a real action that must be EXECUTED and VERIFIED, not just acknowledged in text.

#### Step F — Fallback If Generation Fails or Is Not Needed

- If `商品卖点创作` generates unusable or empty content, preserve the existing `商品卖点` and continue.
- If the existing `商品卖点` is already non-empty and acceptable, you may skip generation entirely and proceed to price edits.
- Do not invent unsupported medical, efficacy, or compliance claims.

## Price Rule

For every enabled SKU in `规格明细`, set selling price to default price + `5.00`.

Examples:

- `69.00` -> `74.00`
- `128.00` -> `133.00`
- `29.60` -> `34.60`

For constrained prices:

- If the page shows `价格最大不能超过 X`, do not force the +5 price.
- Hover/read the relevant SKU's suggested retail price when available.
- Use the highest allowed suggested retail price.
- If the allowed price is `0.01`, keep `0.01`.
- Do not save while any red price validation remains.

## Reliable Price Input

**Prerequisite:** The 商品卖点 assistant panel MUST be closed before starting price edits. If the panel is still visible, prices may be obscured or input may fail. Verify panel closure per Step D above.

Avoid blind `fill` on Youzan price fields. It may append or corrupt values, such as `69.01` or `128.0013300`.

Recommended sequence:

1. Read all visible SKU price input values and count them.
2. Compute the target values.
3. Prefer a native input value setter with bubbling `input` and `change` events, or careful select-all typing if the browser action reliably replaces the value.
4. Also update the summary/main price field when the form exposes one and it follows the lowest SKU price.
5. Re-read the actual DOM values after editing.
6. Confirm the preview price range reflects the new values before saving when possible.

Native setter pattern for an already identified input:

```js
function setInputValue(input, value) {
  input.focus();
  const proto = Object.getPrototypeOf(input);
  const desc = Object.getOwnPropertyDescriptor(proto, 'value') ||
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
  desc.set.call(input, value);
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  input.blur();
}
```

Use this only after identifying the correct SKU price inputs from the current page. Never rely on stale indexes across different products without re-checking the surrounding labels and values.

## Save

Before clicking `保存并查看`, verify:

- `商品分组` is `日用百货test`.
- `商品卖点` is non-empty.
- SKU price inputs equal the intended targets.
- There are no `价格最大不能超过`, required-field, stock, SKU, or other visible validation errors.
- Current operation only affects this product.

Then click `保存并查看`.

## Verification

After saving, verify at least one of these states:

- The product preview/detail page opens and shows the expected price range.
- Returning to `编辑本商品` shows the saved SKU prices and group.
- 商品管理 list contains the product in the expected group/status.

For preview pages:

- `保存并查看` may navigate to a `tuicashier.youzan.com/pay/wscgoods_order?...` preview/buyer page.
- Use this page only to verify displayed product name, selling point, and price range.
- Do not click purchase, checkout, payment, cart, coupon purchase, or order actions.

## Known Pitfalls

- API `isAdded` is the primary status field. `isSeller` can correlate with listed state, but do not use it alone as the gate.
- Never hard-code an old `csrf_token`; stale tokens can return misleading failures or another session's invalid state.
- `alias` and `algId` must come from the same selected API record before building the detail URL.
- `未添加（已合作供应商）` / `已添加（已合作供应商）` appears only after hovering the product card in the list and is now a fallback signal.
- The hover badge can be red for `未添加` and gray for `已添加`; read the text, not only the color.
- The word `无添加` on a market card may be a product ingredient/selling point, not an unlisted status.
- Do not keep searching after finding the first API record with `isAdded === false` or first fallback card whose hover badge clearly says `未添加`; start the listing flow immediately.
- On slow rank-list pages, prefer API selection; if forced to use hover fallback, prefer visual hover screenshots over broad DOM/evaluate scans.
- A screenshot without a hover badge is not a status; it usually means the mouse coordinate missed the card or the hover did not trigger.
- On the detail page, use direct visible text `上架到店铺` to locate and click the listing button; do not perform slow indirect DOM wandering after the text is visible.
- If the later page contradicts the API or hover selection and lacks an上架 action, return to the list and choose another verified `未添加` candidate.
- **The edit page has MULTIPLE `智能生成` buttons — one for `商品名称`, one for `商品卖点`, one for `商品图片`, etc. They look almost identical. Always scope your search to the correct field's container before clicking.**
- **Opening the wrong AI panel is a common and recoverable mistake. Verify the panel title (`商品卖点创作`) immediately after clicking. If the title is wrong, close the panel, verify it closed, and retry.**
- **Closing the AI panel is a real action — it requires clicking the close button AND taking a screenshot/snapshot to verify the panel is gone. "I should close it" without execution is not a close.**
- AI copy controls can be image-only buttons and may need coordinate click after locating the DOM element.
- The文案 panel may identify the wrong field; preserve a valid existing selling point instead of forcing a bad generated result.
- Youzan forms are React-like and can ignore direct DOM value changes unless input/change events are fired.
- Always re-read values after edits and again after save when possible.
- **The 商品卖点 AI panel must be verified closed before editing prices. An open panel may obscure SKU inputs or interfere with value setting.**
