---
name: liangjiu-wechat-auto-promotion-v1-0-0
description: 编排良久素材新品采集、事实文案、指定微信群单次发送和逐链接分享，并在结果不确定时停止。
---

# 良久素材微信推广

当用户要求“选择今天的新品”“生成推广草稿”“发送到指定微信群”或“逐个分享商品链接”时使用本 Skill。

## 依赖与任务上下文

先完整执行 `liangjiu-new-products-collection-v1-0-0`。

建立以下编排上下文：

```json
{
  "task_id": "liangjiu-promo-YYYYMMDD-001",
  "source_page": "新品首发",
  "target_count": 6,
  "selection_mode": "auto_safe_same_category",
  "target_group": "<TARGET_WECHAT_GROUP>",
  "mode": "draft"
}
```

这些字段是 OpenClaw 的业务契约，不是场景脚本的直接 CLI。新任务默认 `draft`；只有用户在本次任务中明确要求发送，才把 `mode` 改为 `send`。

## 安全约束

- 不继承历史发送授权。
- 目标群必须存在于 `WECHAT_IPHONE_CONFIG` 的 `groups` 数组。
- 只使用本次详情提取结果中的事实。
- 标题、价格或链接缺失的商品不进入文案；规格缺失时省略规格行。
- 不写库存、尺码、颜色、产地、功效、发货时效或虚假稀缺。
- 每个任务最多执行一次正式场景三。
- 场景三点击可能发生后，不因确认噪声补发。
- 不用随机坐标替代脚本失败的发送或分享动作。

## 1. 构建事实文案

收集依赖 Skill 返回的一个或两个 `results.jsonl`。运行：

```bash
python3 "$IPHONE_USE_DIR/scripts/build_verified_promotion.py" \
  --results "$RUN_DIR/details/results.jsonl" \
  --results "$RUN_DIR/details-repair/results.jsonl" \
  --expected-count "$TARGET_COUNT" \
  --output "$RUN_DIR/final-promotion.txt" \
  --report "$RUN_DIR/final-promotion.report.json"
```

没有补位文件时省略第二个 `--results`。helper 会校验标题一致、价格格式、iPhone inbox 链接回传、标题与链接去重；验证数量少于或多于目标数都会失败，不得进入发送。

生成的默认文案只包含时间、商品名、价格、已识别规格和链接。不要附加固定营销尾句。

## 2. 草稿门

回显以下内容：

- `task_id`
- 选中品类和商品数
- 目标群
- `final-promotion.txt` 全文
- 缺失规格和被拒记录

`mode=draft` 时到此结束。不得调用场景三或场景四。

## 3. 发送前验证

`mode=send` 时先确认用户本次授权仍指向同一 `task_id`、同一目标群和同一文案文件。然后 dry-run：

```bash
./wechat-iphone-scenario3-v6-send-button-fixed.sh send-promotion \
  --group "$TARGET_GROUP" \
  --message-file "$RUN_DIR/final-promotion.txt" \
  --dry-run
```

要求结果为 `ok=true`、`dry_run=true`、`sent=false`，并再次回显完全匹配的群名。公开版场景三在写入文案前会清空输入框，因此正式运行不会叠加 dry-run 草稿。

## 4. 单次正式发送

确认本任务未出现过正式场景三记录后，只执行一次：

```bash
./wechat-iphone-scenario3-v6-send-button-fixed.sh send-promotion \
  --group "$TARGET_GROUP" \
  --message-file "$RUN_DIR/final-promotion.txt"
```

按以下语义处理：

- `sent=true` 且 `send_verified=true`：状态为 `sent`，可继续分享。
- `sent=true` 且校验不足，或退出码 2：状态为 `uncertain`，立即停止并人工核验；禁止补发和分享。
- 明确在点击前返回 `GROUP_NOT_ALLOWED`、`WRONG_CHAT_BEFORE_SEND`、`SEND_BUTTON_NOT_FOUND` 等：状态为 `failed`，报告后停止。

不得把 `uncertain` 改写成 `failed`。

## 5. 逐链接分享

只在场景三状态为 `sent` 时执行：

```bash
./wechat-iphone-scenario4-v2-share-confirm-send.sh share-product-links \
  --promotion-file "$RUN_DIR/final-promotion.txt" \
  --target-group "$TARGET_GROUP"
```

场景四没有 dry-run；`--max-links 1` 仍会真实分享一个链接，只能在用户明确允许真实回归时使用。

读取场景四返回的 `target_count`、`success_count` 和 `results_jsonl`。单项失败时报告部分结果，不人工补点。

## 最终报告

返回：

- `task_id`、品类和已验证商品数
- 最终文案与构建报告路径
- 状态停在 `draft`、`failed`、`uncertain`、`sent` 或 `shared`
- 场景三发送结果
- 场景四目标数与成功数
- 失败、缺失规格和需要人工核验的事项
