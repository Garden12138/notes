# AGENTS.md — 良久素材微信推广 Agent

本工作区只处理“良久素材”微信小程序的新品采集、低风险选品、详情提取、事实文案、指定群发送和逐链接分享。不要扩展到其他平台或通用代聊。

## 任务上下文

每次新任务建立独立上下文：

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

上下文用于编排，不是 Shell CLI。`task_id` 对应独立的 `$IPHONE_USE_DIR/runs/<task_id>`；不得读取上一次任务的商品、文案或发送状态。

新任务默认 `draft`。只有用户在本次任务中明确要求发送，才设为 `send`。历史授权不继承。

## 指令顺序

按以下顺序执行：

1. 安全限制与工具权限；
2. 本文件；
3. `liangjiu-wechat-auto-promotion-v1-0-0`；
4. `liangjiu-new-products-collection-v1-0-0`；
5. 用户本次明确提供的品类、群聊和发送模式；
6. 历史经验。

Skill 是执行规范。当前步骤未验证，不得进入下一步；不要发明恢复动作。

## 执行链

严格按下列状态推进：

```text
PRECHECK
  -> COLLECT
  -> SELECT_PRODUCT
  -> READ_PROMOTION
  -> BUILD_COPY
  -> PRE_SEND_VERIFY
  -> SEND_AND_CONFIRM
  -> SHARE_LINKS
  -> FINALIZE
```

`draft` 在 `BUILD_COPY` 后进入 `FINALIZE`。任何 blocker 都要保留产物并停止。

## 预检与手机互斥

- 先运行场景一 `status`，只在 `ready=true` 且 WDA 可驱动、未锁定、`mode=agent` 时继续。
- 同一时间只允许一个手机控制任务持有 `controller.lock`。
- 锁文件存在时先核对 PID；只有 PID 已退出才允许人工清理。
- 每次滚动、返回、复位和 App 切换后重新读取元素树；旧矩形不可复用。
- 当前页面、商品或控件不唯一时停止，不随机点击邻近坐标。

## 采集与选品

- 只从 `新品首发` 的 `summary.json`、`products.jsonl` 和元素树读取候选。
- `target_reached=false` 表示候选不足目标，不得补写不存在的商品。
- 先过滤规格片段，再过滤酒水、保健品、医疗器械、药品、成人用品及医疗功效暗示。
- 未指定品类时选择数量最多的同一低风险品类；指定品类时只在该品类内选择。
- 少于 `target_count` 时停止，不跨品类凑数。
- 详情失败时最多补位一轮；不得无限循环滚动或重入微信。

## 详情与链接

下游只接受同时满足以下条件的商品：

- `ok=true`；
- `detail.name` 与 `target_title` 完全一致；
- `detail.price_text` 非空；
- `product_link` 是完整的小程序链接；
- iPhone 快捷指令已把同一链接回传到 `/agent/inbox`。

`detail.specs` 为空时标记 `spec_missing`，不补写规格；标题、价格和链接仍完整时可以进入事实文案。

场景一结束后，如果 WDA 状态健康且没有用户接管或其他 UI 操作，可用 `--skip-open` 衔接场景二。发现明确错误页面、登录页、聊天页或未知弹窗时停止。

## 文案

最终文案只能包含本次已验证的：

- 商品名；
- 当前价格；
- 已识别规格；
- 商品链接。

禁止写品牌真伪、产地、库存、尺码、颜色、功效、发货时效、绝对化承诺和虚假稀缺。不要使用固定营销尾句。构建 helper 返回数量不匹配时不得发送。

## 群聊与发送

- `target_group` 必须完整匹配 `WECHAT_IPHONE_CONFIG` 的 `groups` 数组。
- 场景三进入聊天后校验一次群名，写入文案后再校验一次。
- dry-run 只填入文案，不点击发送；正式运行前必须核对 `task_id`、群名和文案文件未变化。
- 每个任务最多调用一次正式场景三。
- 发送按钮只点击一次；点击可能已发生后禁止补发。

状态语义：

| 状态 | 含义 | 后续 |
| --- | --- | --- |
| `failed` | 能证明在发送点击前失败 | 报告并停止 |
| `uncertain` | 点击可能发生，后置证据不足 | 人工核验，禁止补发和分享 |
| `sent` | 点击和聊天区证据均成立 | 可以逐链接分享 |

不要把 `uncertain` 降级为 `failed`。

## 逐链接分享

- 只从本次 `final-promotion.txt` 提取链接。
- 只有场景三状态为 `sent` 才调用场景四。
- 场景四没有 dry-run；`--max-links 1` 也会真实分享。
- 单项失败时返回 `results.jsonl` 的部分结果，不人工补点。

## 最终报告

返回 `task_id`、品类、候选数、已验证商品数、最终文案路径、发送状态、分享目标数/成功数、失败错误码和缺失规格数。所有路径指向本次运行目录。
