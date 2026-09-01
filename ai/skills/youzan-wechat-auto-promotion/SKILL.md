---
name: "youzan-wechat-auto-promotion"
description: "有赞上架、链接生成、单条无换行文案并发送微信群。"
---

# 有赞微信自动推广

Use this skill when the user wants to complete the tested end-to-end flow: list one Youzan product, generate its WeChat mini-program promotion link, write one polished promotion message, and send it to an allowlisted WeChat group.

## Dependencies

Before acting, read and follow these active skills:

- `youzan-product-listing-daily-goods-v1-0-0`
- `youzan-product-promotion-v1-0-0`
- `wechat-iphone`

If a dependency reports a blocker, stop and report it. Do not bypass login, captcha, payment, deletion, bulk edits, down-shelf operations, or other risky store actions.

## Required Inputs

Require these before starting:

- Product source or permission to select one suitable product.
- Target WeChat group name.
- Whether to send immediately or produce a draft only.

Do not send to WeChat unless the user explicitly asked to send in this run and the group is allowed by `wechat-iphone`.

## Workflow

1. Run the Youzan listing skill. For product selection, follow its API-first `isAdded === false` gate: scan the API `data` array from `data[0]` in original response order, skip only incomplete records or `isAdded === true`, and select the first complete `isAdded === false` product. Use list-card hover only as fallback. Capture the final product name, group/status verification, saved selling point, verified price, and visible product facts.
2. Run the Youzan promotion skill for the exact product. Close any stale promotion dialog first. Verify the matched row is the intended product and the copied mini-program link belongs to the current product alias/path. Never reuse a clipboard or stale dialog link from an earlier product.
3. Draft one sales message from verified facts only. Include the promotion link in the same message. Avoid unverified claims, fake scarcity, medical claims, absolute claims such as `全网最低`, and unsupported shipping/stock promises.
4. Before sending, convert the approved copy to one physical line: replace all line breaks and blank lines with spaces, then collapse repeated spaces. The string passed to `wechat-iphone send --message` must contain no newline characters, because iPhone/WeChat text input can split multiline text into multiple messages.
5. Check `wechat-iphone status` and require ready/actionable/unlocked/drivable agent mode before sending. Let the script verify the target group and page state.
6. Send exactly once:

```bash
{wechatBaseDir}/scripts/wechat-iphone send --group "目标群聊名称" --message "最终完整推广文案（单行、含链接）"
```

**防重复发送规则（严格执行）：**
- 只调用 `wechat-iphone send` **一次**。无论结果如何，都不得再次调用。
- 如果脚本退出码非零（如 `SEND_BUTTON_NOT_FOUND`），**禁止**手动通过 WDA/tap/click 等方式补点「发送」按钮。直接报告失败原因。
- 如果脚本返回 `sent=true, verified=false`（发送成功但验证不全），也**禁止重试**，按发送成功处理。
- 如果脚本返回 `sent=false`（确实没发送成功），报告失败，等待人工介入，不要自己补发。
- 读取 `wechat-iphone send` 的 stdout 输出（JSON），检查其中 `sent` 和 `verified` 字段，不要解析脚本的 stderr 日志重复操作。

## Final Report

Return the product name, listing verification summary, promotion link, final copy sent or drafted, target group, and WeChat send result. Keep the report concise.
