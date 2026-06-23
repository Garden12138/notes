---
name: "youzan-product-listing-daily-goods-v1-0-0"
description: "有赞日用百货选品上架、分组、卖点、改价和保存复核。"
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

## Entry

Open or reuse:

`https://www.youzan.com/v4/fenxiao/fxmarket/ranklist`

Target category flow:

1. Choose `15天热销榜`.
2. Choose `日用百货`.
3. Inspect product cards from the top of the list.
4. Prefer products marked `未添加（已合作供货商）`.
5. Skip `已添加` products and products requiring a new supplier cooperation flow unless the user explicitly asks.

## Listing Flow

1. Open the selected product detail page.
2. Confirm the detail page shows the intended product and has `上架到店铺`.
3. Click `上架到店铺`.
4. In `商品上架到店铺`, open `选择商品分组`.
5. Select `日用百货test`.
6. Keep the default资质展示 choice unless the user specified otherwise.
7. Click `确定`.
8. Wait for `商品已上架至店铺`.
9. Click `编辑商品`.

## Edit Product

On the edit page, verify these basics before changing anything:

- Product name matches the selected market product.
- Product group includes `日用百货test`.
- `商品卖点` is present and non-empty, or can be generated.
- `规格明细` is visible and contains expected SKU price inputs.

### 商品卖点

Preferred flow:

1. Click the `商品卖点` input's `智能生成` control.
2. In the right-side文案 panel, click `立即生成`.
3. If a `商品卖点创作` result appears, choose the first generated selling point and apply it.
4. Close the文案 panel before price edits if it blocks the form.

Fallback:

- If the assistant panel opens the wrong task, such as `商品名称创作`, do not write that content into `商品卖点`.
- If the existing `商品卖点` is non-empty and no usable卖点 result appears, preserve the existing selling point and continue.
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

- A product card can still look `未添加` from a stale market list; the detail page may show `查看分销商品`. If so, skip it and choose another `未添加` item.
- AI copy controls can be image-only buttons and may need coordinate click after locating the DOM element.
- The文案 panel may identify the wrong field; preserve a valid existing selling point instead of forcing a bad generated result.
- Youzan forms are React-like and can ignore direct DOM value changes unless input/change events are fired.
- Always re-read values after edits and again after save when possible.
